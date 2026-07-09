import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger("padplus.learning.active")

CONFIDENCE_THRESHOLD = 0.4
NOVELTY_THRESHOLD = 0.3
MIN_DIALOGS_BETWEEN = 3
SHORT_RESPONSE_CHARS = 20


class ActiveLearningPolicy:
    def __init__(
        self,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        novelty_threshold: float = NOVELTY_THRESHOLD,
        min_dialogs_between: int = MIN_DIALOGS_BETWEEN,
        short_response_chars: int = SHORT_RESPONSE_CHARS,
    ):
        self._confidence_threshold = confidence_threshold
        self._novelty_threshold = novelty_threshold
        self._min_dialogs_between = min_dialogs_between
        self._short_response_chars = short_response_chars
        self._dialogs_since_last_ask = min_dialogs_between
        self._total_asks = 0
        self._last_ask_time: Optional[float] = None

    def should_ask_feedback(
        self,
        evaluation: Dict[str, Any],
        response: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not response or len(response.strip()) < self._short_response_chars:
            self._dialogs_since_last_ask += 1
            return False
        if self._dialogs_since_last_ask < self._min_dialogs_between:
            self._dialogs_since_last_ask += 1
            return False
        confidence = evaluation.get("confidence", 0.5)
        novelty = evaluation.get("novelty", 0.0)
        if confidence < self._confidence_threshold and novelty > self._novelty_threshold:
            self._dialogs_since_last_ask = 0
            self._total_asks += 1
            self._last_ask_time = time.time()
            return True
        self._dialogs_since_last_ask += 1
        return False

    def get_policy_state(self) -> Dict[str, Any]:
        return {
            "confidence_threshold": self._confidence_threshold,
            "novelty_threshold": self._novelty_threshold,
            "min_dialogs_between": self._min_dialogs_between,
            "short_response_chars": self._short_response_chars,
            "dialogs_since_last_ask": self._dialogs_since_last_ask,
            "total_asks": self._total_asks,
            "last_ask_time": self._last_ask_time,
        }

    def reset(self) -> None:
        self._dialogs_since_last_ask = self._min_dialogs_between
        self._total_asks = 0
        self._last_ask_time = None


_active_policy: Optional[ActiveLearningPolicy] = None


def get_active_policy() -> ActiveLearningPolicy:
    global _active_policy
    if _active_policy is None:
        _active_policy = ActiveLearningPolicy()
    return _active_policy


def reset_active_policy() -> None:
    global _active_policy
    _active_policy = None
