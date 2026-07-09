import json
import logging
import os
import threading
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("padplus.learning.collector")

BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "data" / "datasets"

COLLECTIONS = ["dialogs", "feedback", "rewards"]


class DataCollector:
    def __init__(self, base_dir: Optional[Path] = None):
        self._base_dir = Path(base_dir) if base_dir else BASE_DIR
        self._locks: Dict[str, threading.Lock] = {}
        self._ensure_dirs()

    def _ensure_dirs(self):
        for col in COLLECTIONS:
            col_dir = self._base_dir / col
            col_dir.mkdir(parents=True, exist_ok=True)

    def _lock(self, collection: str) -> threading.Lock:
        if collection not in self._locks:
            self._locks[collection] = threading.Lock()
        return self._locks[collection]

    def _daily_path(self, collection: str) -> Path:
        today = date.today().isoformat()
        ym = today[:7]
        day_dir = self._base_dir / collection / ym
        day_dir.mkdir(parents=True, exist_ok=True)
        return day_dir / f"{today}.jsonl"

    def _append_jsonl(self, collection: str, entry: dict) -> None:
        path = self._daily_path(collection)
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock(collection):
            try:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except OSError as e:
                logger.error("Failed to write %s: %s", path, e)

    def record_dialog(
        self,
        prompt: str,
        response: str,
        evaluation: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        dialog_id = uuid.uuid4().hex[:12]
        entry = {
            "id": dialog_id,
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "evaluation": evaluation or {},
            "metadata": metadata or {},
        }
        self._append_jsonl("dialogs", entry)
        return dialog_id

    def record_feedback(
        self,
        dialog_id: str,
        feedback_type: str,
        score: Optional[float] = None,
        comment: Optional[str] = None,
    ) -> None:
        entry = {
            "dialog_id": dialog_id,
            "timestamp": datetime.now().isoformat(),
            "feedback_type": feedback_type,
            "score": score,
            "comment": comment,
        }
        self._append_jsonl("feedback", entry)

    def record_reward(
        self,
        dialog_id: str,
        reward: float,
        source: str = "evaluator",
    ) -> None:
        entry = {
            "dialog_id": dialog_id,
            "timestamp": datetime.now().isoformat(),
            "reward": reward,
            "source": source,
        }
        self._append_jsonl("rewards", entry)

    def export_dataset(
        self,
        collection: str,
        since: Optional[str] = None,
        limit: int = 0,
    ) -> List[Dict[str, Any]]:
        if collection not in COLLECTIONS:
            logger.warning("Unknown collection: %s", collection)
            return []
        col_dir = self._base_dir / collection
        if not col_dir.exists():
            return []
        results: List[Dict[str, Any]] = []
        months = sorted(col_dir.iterdir(), reverse=True) if col_dir.is_dir() else []
        for month_dir in months:
            if not month_dir.is_dir():
                continue
            for day_file in sorted(month_dir.iterdir(), reverse=True):
                if day_file.suffix != ".jsonl":
                    continue
                if since and day_file.stem < since:
                    continue
                try:
                    with open(day_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                results.append(json.loads(line))
                                if limit and len(results) >= limit:
                                    return results
                except (OSError, json.JSONDecodeError) as e:
                    logger.warning("Error reading %s: %s", day_file, e)
        return results

    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        if collection not in COLLECTIONS:
            return {"collection": collection, "total": 0, "error": "unknown collection"}
        records = self.export_dataset(collection)
        total = len(records)
        by_date: Dict[str, int] = {}
        for r in records:
            ts = r.get("timestamp", "")[:10]
            by_date[ts] = by_date.get(ts, 0) + 1
        return {
            "collection": collection,
            "total": total,
            "by_date": dict(sorted(by_date.items())),
        }

    def get_all_stats(self) -> Dict[str, Any]:
        return {
            col: self.get_collection_stats(col)
            for col in COLLECTIONS
        }

    def clear(self):
        for col in COLLECTIONS:
            col_dir = self._base_dir / col
            if col_dir.exists():
                for child in col_dir.rglob("*"):
                    if child.is_file():
                        child.unlink()


_collector: Optional[DataCollector] = None


def get_collector() -> DataCollector:
    global _collector
    if _collector is None:
        _collector = DataCollector()
    return _collector


def reset_collector():
    global _collector
    _collector = None
