"""
Миграция существующих JSON-трейсов из traces/ в SQLite.

Использование:
    python scripts/migrate_traces.py
"""

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("padplus.migrate_traces")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

TRACES_DIR = PROJECT_ROOT / "traces"
DONE_FILE = TRACES_DIR / ".migrated"


def migrate():
    from backend.core.xray.history_recorder import get_xray_history

    history = get_xray_history()
    migrated = 0
    errors = 0

    for json_file in sorted(TRACES_DIR.glob("*.json")):
        if json_file.name == ".migrated":
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            trace_id = data.get("trace_id", json_file.stem)
            spans = data.get("spans", [])
            user_message = ""
            for s in spans:
                meta = s.get("metadata", {})
                if meta.get("stage") == "intent" and s.get("name", "").endswith("user_message"):
                    user_message = meta.get("response", "")

            trace_dict = {
                "id": trace_id,
                "user_message": user_message or f"migrated trace {json_file.stem}",
                "response": data.get("result", {}).get("response", ""),
                "model": data.get("result", {}).get("model", ""),
                "provider": data.get("result", {}).get("provider", ""),
                "thinking_mode": "",
                "total_ms": data.get("duration_ms", 0),
                "success": data.get("status") == "ok",
                "timestamp": data.get("started_at", ""),
                "spans": spans,
            }
            history.add_trace(trace_dict)
            migrated += 1
            logger.info(f"  migrated: {json_file.name} ({trace_id})")
        except Exception as e:
            logger.warning(f"  error: {json_file.name}: {e}")
            errors += 1

    DONE_FILE.write_text(f"migrated: {migrated}, errors: {errors}\n")
    logger.info(f"Done. Migrated: {migrated}, Errors: {errors}")


if __name__ == "__main__":
    migrate()
