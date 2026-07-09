import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger("padplus.memory.fusion")

SIMILARITY_THRESHOLD = 0.75
MIN_TEXT_LENGTH = 20
MAX_FUSION_CANDIDATES = 100


@dataclass
class FusionRecord:
    source_ids: List[str] = field(default_factory=list)
    target_type: str = ""
    target_id: str = ""
    merged_fields: Dict[str, Any] = field(default_factory=dict)
    similarity: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "source_ids": self.source_ids,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "merged_fields": self.merged_fields,
            "similarity": round(self.similarity, 3),
            "timestamp": self.timestamp,
        }


class MemoryFusion:
    def __init__(self):
        self._history: List[FusionRecord] = []
        self._max_history = 50

    def find_candidates(
        self,
        episodic_items: List[Dict[str, Any]],
        semantic_items: List[Dict[str, Any]],
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any], float]]:
        pairs = []
        text_map = defaultdict(list)

        for item in episodic_items:
            text = (item.get("user_message", "") + " " + item.get("ai_response", "")).strip()
            if len(text) >= MIN_TEXT_LENGTH:
                text_map["episodic"].append((item, text))

        for item in semantic_items:
            text = item.get("content", item.get("summary", "")).strip()
            if len(text) >= MIN_TEXT_LENGTH:
                text_map["semantic"].append((item, text))

        candidates = []

        ep_items = text_map.get("episodic", [])
        sem_items = text_map.get("semantic", [])

        for ep_item, ep_text in ep_items:
            for sem_item, sem_text in sem_items:
                sim = self._jaccard_similarity(ep_text, sem_text)
                if sim >= SIMILARITY_THRESHOLD:
                    candidates.append((ep_item, sem_item, sim))
                    if len(candidates) >= MAX_FUSION_CANDIDATES:
                        return candidates

        ep_items_list = ep_items
        for i in range(len(ep_items_list)):
            for j in range(i + 1, len(ep_items_list)):
                sim = self._jaccard_similarity(ep_items_list[i][1], ep_items_list[j][1])
                if sim >= SIMILARITY_THRESHOLD:
                    candidates.append((ep_items_list[i][0], ep_items_list[j][0], sim))
                    if len(candidates) >= MAX_FUSION_CANDIDATES:
                        return candidates

        sem_items_list = sem_items
        for i in range(len(sem_items_list)):
            for j in range(i + 1, len(sem_items_list)):
                sim = self._jaccard_similarity(sem_items_list[i][1], sem_items_list[j][1])
                if sim >= SIMILARITY_THRESHOLD:
                    candidates.append((sem_items_list[i][0], sem_items_list[j][0], sim))
                    if len(candidates) >= MAX_FUSION_CANDIDATES:
                        return candidates

        return candidates

    def fuse(
        self,
        source_a: Dict[str, Any],
        source_b: Dict[str, Any],
        similarity: float,
    ) -> Dict[str, Any]:
        merged = {}

        text_a = source_a.get("content") or source_a.get("user_message", "")
        text_b = source_b.get("content") or source_b.get("user_message", "")
        merged["content"] = text_a if len(text_a) >= len(text_b) else text_b

        conf_a = float(source_a.get("confidence", source_a.get("significance", 0.5)))
        conf_b = float(source_b.get("confidence", source_b.get("significance", 0.5)))
        merged["confidence"] = (conf_a + conf_b) / 2.0

        acc_a = int(source_a.get("access_count", source_a.get("count", 0)))
        acc_b = int(source_b.get("access_count", source_b.get("count", 0)))
        merged["access_count"] = acc_a + acc_b

        tags_a = set(source_a.get("tags", source_a.get("keywords", [])))
        tags_b = set(source_b.get("tags", source_b.get("keywords", [])))
        merged["tags"] = sorted(tags_a | tags_b)

        for key in ("knowledge_type", "source", "domain", "topic", "intent"):
            val = source_a.get(key) or source_b.get(key)
            if val:
                merged[key] = val

        return merged

    def record_fusion(self, record: FusionRecord) -> None:
        self._history.append(record)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._history[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_fusions": len(self._history),
            "recent": [r.to_dict() for r in self._history[-5:]],
        }

    def _jaccard_similarity(self, text_a: str, text_b: str) -> float:
        words_a = set(re.findall(r"[а-яёa-z]{3,}", text_a.lower()))
        words_b = set(re.findall(r"[а-яёa-z]{3,}", text_b.lower()))
        if not words_a or not words_b:
            return 0.0
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union if union > 0 else 0.0

    def reset(self) -> None:
        self._history.clear()


_fusion: Optional["MemoryFusion"] = None


def get_fusion() -> MemoryFusion:
    global _fusion
    if _fusion is None:
        _fusion = MemoryFusion()
    return _fusion


def reset_fusion() -> None:
    global _fusion
    _fusion = None
