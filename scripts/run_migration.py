"""Batch migration executor for Supabase PgBouncer (3-statement limit).

Usage:
    python scripts/run_migration.py             # generate SQL, batch-exec
    python scripts/run_migration.py --dry-run   # show batches only
"""

import os
import re
import sys
import time
import tempfile
import subprocess
import psycopg2
from pathlib import Path


BATCH_SIZE = 3
BETWEEN_BATCH_DELAY = 1.0


def dsn() -> str:
    url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")
    if not url:
        print("FATAL: DATABASE_URL not set")
        sys.exit(1)
    return url


def generate_sql(url: str) -> str:
    """Generate migration SQL via alembic upgrade --sql."""
    env = {**os.environ, "DATABASE_URL": url}
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        capture_output=True, text=True, env=env,
        cwd=Path(__file__).resolve().parent.parent,
    )
    # Remove alembic INFO/WARNING lines
    out_lines = [
        l for l in r.stdout.splitlines()
        if not l.startswith("INFO [alembic")
           and not l.startswith("-- Running upgrade")
           and not l.startswith("-- Running downgrade")
           and not l.startswith("-- Running downgrade")
    ]
    sql = "\n".join(out_lines).strip()
    if r.returncode != 0 or not sql:
        print("STDERR:", r.stderr)
        print("STDOUT:", sql[:500])
        raise RuntimeError(f"alembic upgrade --sql failed (rc={r.returncode})")
    return sql


def split_statements(sql_text: str) -> list[str]:
    """Split SQL text into individual statements.

    Handles:
    - $$ ... $$ (dollar-quoted blocks like DO, CREATE FUNCTION)
    - ;; as statement terminator (Alembic convention)
    - ; as statement terminator (INSERT/UPDATE alembic_version, DROP TRIGGER)
    - -- Running upgrade comments
    """
    # Remove BEGIN / COMMIT wrappers
    sql_text = re.sub(r"^\s*BEGIN\s*;\s*", "", sql_text)
    sql_text = re.sub(r"\s*COMMIT\s*;\s*$", "", sql_text)

    # Remove -- Running ... comments (migration boundaries)
    sql_text = re.sub(r"^-- Running .*$", "", sql_text, flags=re.MULTILINE)

    # Extract $$ ... $$ blocks and replace with markers
    blocks: dict[int, str] = {}
    def _save(m: re.Match) -> str:
        idx = len(blocks)
        blocks[idx] = m.group(0)
        return f"__DQ{idx}__"
    sql_text = re.sub(r"\$\$.*?\$\$", _save, sql_text, flags=re.DOTALL)

    # Normalize ;; → ;
    sql_text = sql_text.replace(";;", ";")

    # Split on ; and drop empty parts
    parts = [p.strip() for p in sql_text.split(";")]
    parts = [p for p in parts if p]

    # Restore $$ blocks
    result: list[str] = []
    for p in parts:
        def _restore(m: re.Match) -> str:
            return blocks[int(m.group(1))]
        restored = re.sub(r"__DQ(\d+)__", _restore, p)
        result.append(restored + ";")

    return result


def group_batches(statements: list[str]) -> list[list[str]]:
    return [statements[i:i + BATCH_SIZE]
            for i in range(0, len(statements), BATCH_SIZE)]


def run(dry_run: bool = False) -> None:
    url = dsn()
    print(f"DSN: {url[:60]}...")

    sql = generate_sql(url)
    sql_path = Path(tempfile.gettempdir()) / "migration.sql"
    sql_path.write_text(sql, encoding="utf-8")
    print(f"SQL saved: {sql_path} ({len(sql)} chars)")

    stmts = split_statements(sql)
    batches = group_batches(stmts)
    print(f"Parsed {len(stmts)} statements into {len(batches)} batches"
          f" (max {BATCH_SIZE}/batch)\n")

    if dry_run:
        for idx, batch in enumerate(batches):
            print(f"Batch {idx + 1}/{len(batches)} ({len(batch)} stmts):")
            for s in batch:
                # Show first 150 chars of each statement
                short = s.strip()[:150].replace("\n", " ")
                if len(s) > 150:
                    short += "..."
                print(f"  {short}")
            print()
        print(f"DRY-RUN: {len(batches)} batches, {len(stmts)} statements")
        return

    for idx, batch in enumerate(batches):
        desc = f"Batch {idx + 1}/{len(batches)} ({len(batch)} stmts)"
        print(f"\n{desc} ...", end=" ")
        sys.stdout.flush()

        conn = psycopg2.connect(url, sslmode="require", connect_timeout=10)
        conn.autocommit = True
        cur = conn.cursor()

        try:
            combined = "\n".join(batch)
            cur.execute(combined)
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")
            for i, stmt in enumerate(batch):
                print(f"  [{i}] {stmt.strip()[:200]}")
            conn.close()
            sys.exit(1)
        finally:
            conn.close()

        time.sleep(BETWEEN_BATCH_DELAY)

    print(f"\nAll {len(batches)} batches executed successfully.")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
