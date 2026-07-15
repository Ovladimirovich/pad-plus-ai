"""
ExperienceSQLiteStore — SQLite хранилище для Experience Layer.

Используется локально (APP_ENV=development), когда PostgreSQL недоступен.
Хранит данные в data/experience.db
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("padplus.experience_sqlite")

DB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _get_db_path() -> str:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return str(DB_DIR / "experience.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class ExperienceSQLiteStore:
    """SQLite хранилище для записей опыта."""

    def __init__(self):
        self._lock = threading.Lock()
        self._ensure_table()

    def _ensure_table(self):
        with self._lock:
            conn = _get_connection()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS experience_records (
                        id TEXT PRIMARY KEY,
                        dialog_id TEXT,
                        user_message TEXT,
                        ai_response TEXT,
                        interaction_type TEXT,
                        signals TEXT,
                        significance REAL DEFAULT 0,
                        expectation TEXT DEFAULT '',
                        reality TEXT DEFAULT '',
                        delta TEXT DEFAULT '',
                        lessons TEXT DEFAULT '[]',
                        strategy_success REAL DEFAULT 0,
                        impulse_before TEXT DEFAULT '{}',
                        emotion_before TEXT DEFAULT '{}',
                        persona_before TEXT DEFAULT '{}',
                        created_at TEXT DEFAULT (datetime('now'))
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_experience_dialog_id
                    ON experience_records(dialog_id)
                """)
                conn.commit()
            finally:
                conn.close()

    def save(self, record) -> str:
        data = record.to_dict() if hasattr(record, "to_dict") else record
        record_id = data.get("dialog_id", "")
        if not record_id:
            import uuid
            record_id = str(uuid.uuid4())

        with self._lock:
            conn = _get_connection()
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO experience_records
                        (id, dialog_id, user_message, ai_response, interaction_type,
                         signals, significance, expectation, reality, delta,
                         lessons, strategy_success, impulse_before,
                         emotion_before, persona_before, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            datetime('now'))
                    """,
                    (
                        record_id,
                        data.get("dialog_id", record_id),
                        str(data.get("user_message", ""))[:200],
                        str(data.get("ai_response", ""))[:200],
                        data.get("interaction_type", "unknown"),
                        json.dumps(data.get("signals", {}), ensure_ascii=False),
                        float(data.get("significance", 0)),
                        str(data.get("expectation", "")),
                        str(data.get("reality", "")),
                        str(data.get("delta", "")),
                        json.dumps(data.get("lessons", []), ensure_ascii=False),
                        float(data.get("strategy_success", 0)),
                        json.dumps(data.get("impulse_before", {}), ensure_ascii=False),
                        json.dumps(data.get("emotion_before", {}), ensure_ascii=False),
                        json.dumps(data.get("persona_before", {}), ensure_ascii=False),
                    ),
                )
                conn.commit()
                logger.debug("Experience saved to SQLite: %s | type=%s sig=%.3f",
                             record_id, data.get("interaction_type", "?"),
                             float(data.get("significance", 0)))
                return record_id
            except Exception as e:
                logger.error("Failed to save experience to SQLite: %s", e)
                return ""
            finally:
                conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "dialog_id": row["dialog_id"],
            "user_message": row["user_message"] or "",
            "ai_response": row["ai_response"] or "",
            "interaction_type": row["interaction_type"] or "unknown",
            "signals": json.loads(row["signals"]) if row["signals"] else {},
            "significance": float(row["significance"] or 0),
            "expectation": row["expectation"] or "",
            "reality": row["reality"] or "",
            "delta": row["delta"] or "",
            "lessons": json.loads(row["lessons"]) if row["lessons"] else [],
            "strategy_success": float(row["strategy_success"] or 0),
            "impulse_before": json.loads(row["impulse_before"]) if row["impulse_before"] else {},
            "emotion_before": json.loads(row["emotion_before"]) if row["emotion_before"] else {},
            "persona_before": json.loads(row["persona_before"]) if row["persona_before"] else {},
            "timestamp": row["created_at"] or "",
        }

    def load_all(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = _get_connection()
            try:
                rows = conn.execute(
                    "SELECT * FROM experience_records ORDER BY created_at DESC"
                ).fetchall()
                return [self._row_to_dict(r) for r in rows]
            except Exception as e:
                logger.error("Failed to load experiences from SQLite: %s", e)
                return []
            finally:
                conn.close()

    def count(self) -> int:
        with self._lock:
            conn = _get_connection()
            try:
                row = conn.execute("SELECT COUNT(*) AS cnt FROM experience_records").fetchone()
                return row["cnt"] if row else 0
            except Exception as e:
                logger.error("Failed to count experiences: %s", e)
                return 0
            finally:
                conn.close()

    def get_session_records(self, session_id: str, limit: int = 0) -> List[Dict[str, Any]]:
        with self._lock:
            conn = _get_connection()
            try:
                if limit > 0:
                    rows = conn.execute(
                        "SELECT * FROM experience_records WHERE dialog_id=? ORDER BY created_at DESC LIMIT ?",
                        (session_id, limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM experience_records WHERE dialog_id=? ORDER BY created_at DESC",
                        (session_id,),
                    ).fetchall()
                return [self._row_to_dict(r) for r in rows]
            except Exception as e:
                logger.error("Failed to get session records: %s", e)
                return []
            finally:
                conn.close()

    def clear_session(self, session_id: str):
        with self._lock:
            conn = _get_connection()
            try:
                conn.execute("DELETE FROM experience_records WHERE dialog_id=?", (session_id,))
                conn.commit()
            except Exception as e:
                logger.error("Failed to clear session: %s", e)
            finally:
                conn.close()

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            conn = _get_connection()
            try:
                total = conn.execute("SELECT COUNT(*) AS cnt FROM experience_records").fetchone()["cnt"]
                by_type = conn.execute(
                    "SELECT interaction_type, COUNT(*) AS cnt FROM experience_records GROUP BY interaction_type"
                ).fetchall()
                return {
                    "total": total,
                    "by_type": {r["interaction_type"]: r["cnt"] for r in by_type},
                }
            except Exception as e:
                logger.error("Failed to get stats: %s", e)
                return {"total": 0, "by_type": {}}
            finally:
                conn.close()
