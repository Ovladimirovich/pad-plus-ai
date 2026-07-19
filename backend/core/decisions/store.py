"""
DecisionStore — персистентное хранилище решений (SQLite).

Схема:
    CREATE TABLE decisions (
        id TEXT PRIMARY KEY,
        timestamp REAL,
        component TEXT,
        decision_type TEXT,
        selected TEXT,
        confidence REAL,
        reason TEXT,
        input_factors TEXT,   -- JSON
        candidates TEXT,      -- JSON
        trace_id TEXT,
        session_id TEXT,
        meta TEXT             -- JSON
    );
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.decisions.models import DecisionRecord

logger = logging.getLogger("padplus.decisions.store")

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
DB_PATH = DATA_DIR / "decisions.db"


class DecisionStore:
    def __init__(self, db_path: Path = DB_PATH):
        self._db_path = db_path
        self._lock = threading.Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS decisions (
                        id TEXT PRIMARY KEY,
                        timestamp REAL,
                        component TEXT,
                        decision_type TEXT,
                        selected TEXT,
                        confidence REAL,
                        reason TEXT,
                        input_factors TEXT,
                        candidates TEXT,
                        trace_id TEXT,
                        session_id TEXT,
                        meta TEXT
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_decisions_component ON decisions(component)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_decisions_type ON decisions(decision_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_decisions_session ON decisions(session_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_decisions_trace ON decisions(trace_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_decisions_ts ON decisions(timestamp)")
                conn.commit()
            finally:
                conn.close()

    def save(self, record: DecisionRecord) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO decisions (
                        id, timestamp, component, decision_type, selected, confidence,
                        reason, input_factors, candidates, trace_id, session_id, meta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.id,
                        record.timestamp,
                        record.component,
                        record.decision_type,
                        record.selected,
                        record.confidence,
                        record.reason,
                        json.dumps(record.input_factors, ensure_ascii=False, default=str),
                        json.dumps(record.candidates, ensure_ascii=False, default=str),
                        record.trace_id,
                        record.session_id,
                        json.dumps(record.meta, ensure_ascii=False, default=str),
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def get(self, decision_id: str) -> Optional[DecisionRecord]:
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
                if not row:
                    return None
                return self._row_to_record(row)
            finally:
                conn.close()

    def query(
        self,
        component: Optional[str] = None,
        decision_type: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> List[DecisionRecord]:
        query = "SELECT * FROM decisions WHERE 1=1"
        params: List[Any] = []
        if component:
            query += " AND component = ?"
            params.append(component)
        if decision_type:
            query += " AND decision_type = ?"
            params.append(decision_type)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if trace_id:
            query += " AND trace_id = ?"
            params.append(trace_id)
        if since:
            query += " AND timestamp >= ?"
            params.append(since)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute(query, params).fetchall()
                return [self._row_to_record(r) for r in rows]
            finally:
                conn.close()

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            conn = self._get_conn()
            try:
                total = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
                by_component = {}
                for row in conn.execute(
                    "SELECT component, COUNT(*) as c FROM decisions GROUP BY component"
                ).fetchall():
                    by_component[row["component"]] = row["c"]
                by_type = {}
                for row in conn.execute(
                    "SELECT decision_type, COUNT(*) as c FROM decisions GROUP BY decision_type"
                ).fetchall():
                    by_type[row["decision_type"]] = row["c"]
                return {"total": total, "by_component": by_component, "by_type": by_type}
            finally:
                conn.close()

    def _row_to_record(self, row: sqlite3.Row) -> DecisionRecord:
        return DecisionRecord(
            id=row["id"],
            timestamp=row["timestamp"],
            component=row["component"],
            decision_type=row["decision_type"],
            selected=row["selected"],
            confidence=row["confidence"],
            reason=row["reason"],
            input_factors=json.loads(row["input_factors"] or "{}"),
            candidates=json.loads(row["candidates"] or "[]"),
            trace_id=row["trace_id"],
            session_id=row["session_id"],
            meta=json.loads(row["meta"] or "{}"),
        )


_store: Optional[DecisionStore] = None


def get_decision_store() -> DecisionStore:
    global _store
    if _store is None:
        _store = DecisionStore()
    return _store
