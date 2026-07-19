import json
import logging
import os
import sqlite3
import threading
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("padplus.xray")

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "xray_traces.db"

# Старые трассировки старше этого порога удаляются принудительно.
TRACE_RETENTION_DAYS = 30
# Чистка запускается не чаще чем раз на N сохранённых сессий (чтобы
# не делать DELETE на каждый запрос).
CLEANUP_INTERVAL = 50


class XRayHistory:
    def __init__(self, db_path: str | None = None, max_traces: int = 500):
        self.max_traces = max_traces
        self._db_path = str(db_path or DEFAULT_DB_PATH)
        self._lock = threading.Lock()
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._write_count = 0
        self._init_db()
        self._load_cache()

    def _init_db(self):
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS xray_traces (
                    id TEXT PRIMARY KEY,
                    user_message TEXT,
                    response TEXT,
                    model TEXT,
                    provider TEXT,
                    thinking_mode TEXT,
                    total_ms REAL,
                    success INTEGER,
                    timestamp TEXT,
                    spans TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_timestamp
                ON xray_traces(timestamp DESC)
            """)
            conn.commit()

    def _load_cache(self):
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, user_message, response, model, provider, "
                "thinking_mode, total_ms, success, timestamp, spans "
                "FROM xray_traces ORDER BY timestamp DESC LIMIT ?",
                (self.max_traces,),
            ).fetchall()
        for row in rows:
            self._cache[row[0]] = self._row_to_dict(row)

    def _row_to_dict(self, row) -> dict:
        return {
            "id": row[0],
            "user_message": row[1],
            "response": row[2],
            "model": row[3],
            "provider": row[4],
            "thinking_mode": row[5],
            "total_ms": row[6],
            "success": bool(row[7]),
            "timestamp": row[8],
            "spans": json.loads(row[9]) if row[9] else [],
        }

    def add_trace(self, trace) -> None:
        data = trace.to_dict() if hasattr(trace, "to_dict") else trace
        with self._lock:
            trace_id = data.get("id", str(id(data)))
            self._cache[trace_id] = data
            while len(self._cache) > self.max_traces:
                self._cache.popitem(last=False)

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO xray_traces "
                "(id, user_message, response, model, provider, thinking_mode, "
                "total_ms, success, timestamp, spans) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    trace_id,
                    data.get("user_message", ""),
                    data.get("response", ""),
                    data.get("model", ""),
                    data.get("provider", ""),
                    data.get("thinking_mode", ""),
                    data.get("total_ms", 0),
                    1 if data.get("success", False) else 0,
                    data.get("timestamp", datetime.now().isoformat()),
                    json.dumps(data.get("spans", []), ensure_ascii=False),
                ),
            )
            conn.commit()

    def add_trace_session(self, session: dict) -> None:
        """
        Сохраняет сессию трассировки из TraceCollector (X-Ray).

        session: dict от TraceSession.get_summary() + поле "events" (список
        TraceEvent.to_dict()). Отличается от add_trace тем, что хранит
        детализацию по фазам пайплайна, а не по笼统ным span-ам.
        """
        if not session or not session.get("request_id"):
            return
        trace_id = session["request_id"]
        data = {
            "id": trace_id,
            "user_message": session.get("user_message", "")[:200],
            "response": (session.get("metadata", {}) or {}).get("response_preview", "") or "",
            "model": (session.get("metadata", {}) or {}).get("model", "") or "",
            "provider": (session.get("metadata", {}) or {}).get("provider", "") or "",
            "thinking_mode": (session.get("metadata", {}) or {}).get("strategy", "") or "",
            "total_ms": session.get("total_time_ms", 0) or 0,
            "success": bool((session.get("metadata", {}) or {}).get("success", False)),
            "timestamp": session.get("start_time", datetime.now().isoformat()),
            "spans": session.get("events", []),
        }
        with self._lock:
            self._cache[trace_id] = data
            while len(self._cache) > self.max_traces:
                self._cache.popitem(last=False)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO xray_traces "
                "(id, user_message, response, model, provider, thinking_mode, "
                "total_ms, success, timestamp, spans) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    trace_id,
                    data["user_message"],
                    data["response"],
                    data["model"],
                    data["provider"],
                    data["thinking_mode"],
                    data["total_ms"],
                    1 if data["success"] else 0,
                    data["timestamp"],
                    json.dumps(data["spans"], ensure_ascii=False),
                ),
            )
            conn.commit()
        # Периодическая очистка старых трассировок (без нагрузки на каждый запрос)
        self._write_count += 1
        if self._write_count >= CLEANUP_INTERVAL:
            self._write_count = 0
            try:
                self.cleanup_old(TRACE_RETENTION_DAYS)
            except Exception as e:
                logger.warning(f"X-Ray cleanup error: {e}")

    def cleanup_old(self, days: int = TRACE_RETENTION_DAYS) -> int:
        """
        Удаляет трассировки старше `days` дней. Возвращает число удалённых строк.
        """
        cutoff = (datetime.now().timestamp() - days * 86400)
        deleted = 0
        with sqlite3.connect(self._db_path) as conn:
            # timestamp хранится как ISO-строка; сравниваем через datetime
            cur = conn.execute(
                "SELECT id, timestamp FROM xray_traces"
            )
            to_delete = []
            for row in cur.fetchall():
                tid, ts = row
                try:
                    ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if ts_dt.timestamp() < cutoff:
                        to_delete.append(tid)
                except (ValueError, TypeError):
                    continue
            if to_delete:
                conn.executemany(
                    "DELETE FROM xray_traces WHERE id = ?",
                    [(t,) for t in to_delete],
                )
                conn.commit()
                deleted = len(to_delete)
        if deleted:
            logger.info(f"X-Ray cleanup removed {deleted} old traces (>{days}d)")
        return deleted

    def get_trace(self, trace_id: str) -> Optional[dict]:
        with self._lock:
            cached = self._cache.get(trace_id)
            if cached:
                return cached
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT id, user_message, response, model, provider, "
                "thinking_mode, total_ms, success, timestamp, spans "
                "FROM xray_traces WHERE id = ?",
                (trace_id,),
            ).fetchone()
        if row:
            d = self._row_to_dict(row)
            with self._lock:
                self._cache[trace_id] = d
            return d
        return None

    def list_sessions(self, limit: int = 20, offset: int = 0) -> list[dict]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, user_message, model, provider, total_ms, "
                "success, timestamp "
                "FROM xray_traces ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [
            {
                "id": r[0],
                "user_message": r[1][:200] if r[1] else "",
                "model": r[2] or "",
                "provider": r[3] or "",
                "total_ms": r[4],
                "success": bool(r[5]),
                "timestamp": r[6],
            }
            for r in rows
        ]

    def load_session(self, session_id: str) -> Optional[dict]:
        return self.get_trace(session_id)

    def export_session(self, session_id: str, format: str = "json") -> Any:
        trace = self.get_trace(session_id)
        if not trace:
            return None
        if format == "json":
            return trace
        if format == "csv":
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["field", "value"])
            for key, value in trace.items():
                if isinstance(value, (list, dict)):
                    writer.writerow([key, json.dumps(value, ensure_ascii=False)])
                else:
                    writer.writerow([key, value])
            return output.getvalue()

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            self._cache.pop(session_id, None)
        with sqlite3.connect(self._db_path) as conn:
            cur = conn.execute("DELETE FROM xray_traces WHERE id = ?", (session_id,))
            conn.commit()
        return cur.rowcount > 0

    def get_recent(self, limit: int = 20) -> list[dict]:
        return self.list_sessions(limit=limit)

    def get_stats(self) -> dict:
        with sqlite3.connect(self._db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM xray_traces").fetchone()[0]
            errors = conn.execute(
                "SELECT COUNT(*) FROM xray_traces WHERE success = 0"
            ).fetchone()[0]
        return {
            "total_traces": total,
            "total_errors": errors,
            "recent_count": len(self._cache),
            "max_traces": self.max_traces,
            "retention_days": TRACE_RETENTION_DAYS,
        }


_history: Optional[XRayHistory] = None


def get_xray_history() -> XRayHistory:
    global _history
    if _history is None:
        _history = XRayHistory()
    return _history
