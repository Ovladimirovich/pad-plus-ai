import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("padplus.memory.forgetting")

IMPORTANCE_THRESHOLD = 0.2
STORAGE_QUOTA = 10000
FORGET_BATCH_SIZE = 100
DAYS_DECAY = 30.0


@dataclass
class ForgetRecord:
    item_id: str
    item_type: str
    importance: float
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "importance": round(self.importance, 3),
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


class PriorityForgetting:
    def __init__(
        self,
        importance_threshold: float = IMPORTANCE_THRESHOLD,
        storage_quota: int = STORAGE_QUOTA,
        forget_batch_size: int = FORGET_BATCH_SIZE,
    ):
        self._importance_threshold = importance_threshold
        self._storage_quota = storage_quota
        self._forget_batch_size = forget_batch_size
        self._forgotten: List[ForgetRecord] = []
        self._max_history = 200

    def calculate_importance(
        self,
        item: Dict[str, Any],
    ) -> float:
        significance = float(item.get("significance", item.get("confidence", 0.5)))
        access_count = int(item.get("access_count", item.get("count", 0)))
        last_accessed = item.get("last_accessed", item.get("updated_at", item.get("created_at")))

        if last_accessed:
            try:
                if isinstance(last_accessed, (int, float)):
                    days_since = (time.time() - last_accessed) / 86400.0
                else:
                    dt = last_accessed
                    if isinstance(dt, str):
                        dt = dt.replace("T", " ")[:19]
                        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                    days_since = (datetime.now() - dt).total_seconds() / 86400.0
            except (ValueError, TypeError):
                days_since = DAYS_DECAY
        else:
            days_since = DAYS_DECAY

        recency_factor = max(0.1, min(1.0, 1.0 - days_since / DAYS_DECAY))
        importance = significance ** 2 * (access_count + 1) ** 0.5 * recency_factor
        return max(0.0, importance)

    def rank_for_targets(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        ranked = []
        for item in items:
            importance = self.calculate_importance(item)
            ranked.append({
                "item": item,
                "importance": importance,
            })
        ranked.sort(key=lambda x: x["importance"])
        return ranked

    def should_forget(self, item: Dict[str, Any], total_count: int) -> Optional[str]:
        importance = self.calculate_importance(item)
        if importance < self._importance_threshold:
            return f"importance_too_low ({importance:.3f} < {self._importance_threshold})"
        if total_count > self._storage_quota:
            return f"storage_quota_exceeded ({total_count} > {self._storage_quota})"
        return None

    def forget_lowest_ranked(
        self,
        items: List[Dict[str, Any]],
    ) -> List[ForgetRecord]:
        ranked = self.rank_for_targets(items)
        records = []
        count = 0
        for entry in ranked:
            if count >= self._forget_batch_size:
                break
            item = entry["item"]
            importance = entry["importance"]
            reason = self.should_forget(item, len(items))
            if not reason:
                continue
            item_id = item.get("id", item.get("_id", "unknown"))
            item_type = "unknown"
            for key in ("knowledge_type", "type", "source"):
                val = item.get(key)
                if val:
                    item_type = str(val)
                    break
            record = ForgetRecord(
                item_id=item_id,
                item_type=item_type,
                importance=importance,
                reason=reason,
            )
            records.append(record)
            count += 1
        self._forgotten.extend(records)
        if len(self._forgotten) > self._max_history:
            self._forgotten = self._forgotten[-self._max_history:]
        return records

    def get_forgotten_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._forgotten[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_forgotten": len(self._forgotten),
            "importance_threshold": self._importance_threshold,
            "storage_quota": self._storage_quota,
            "recent": [r.to_dict() for r in self._forgotten[-5:]],
        }

    def reset(self) -> None:
        self._forgotten.clear()


_forgetting: Optional["PriorityForgetting"] = None


def get_forgetting() -> PriorityForgetting:
    global _forgetting
    if _forgetting is None:
        _forgetting = PriorityForgetting()
    return _forgetting


def reset_forgetting() -> None:
    global _forgetting
    _forgetting = None
