"""Check current DB state."""
import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')
dsn = os.environ['DATABASE_URL']

conn = psycopg2.connect(dsn, sslmode='require', connect_timeout=10)
conn.autocommit = True
cur = conn.cursor()

try:
    # Check alembic_version table
    cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema='public' AND table_name='alembic_version')")
    has_alembic = cur.fetchone()[0]
    print(f'alembic_version table exists: {has_alembic}')

    if has_alembic:
        cur.execute("SELECT * FROM alembic_version")
        rows = cur.fetchall()
        print(f'alembic_version records ({len(rows)}):')
        for r in rows:
            print(f'  {r[0]}')

    # List all tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    tables = [r[0] for r in cur.fetchall()]
    print(f'\nAll tables ({len(tables)}):')
    for t in tables:
        print(f'  - {t}')

except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
