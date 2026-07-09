from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import logging
import re
import time

logger = logging.getLogger("padplus.learning.evaluator")

HEDGING_PATTERNS = [
    r"\bдумаю\b", r"\bвозможно\b", r"\bможет быть\b",
    r"\bкажется\b", r"\bнаверное\b", r"\bвероятно\b",
    r"\bпохоже\b", r"\bне уверен\b", r"\bкак бы\b",
    r"\bвроде\b", r"\bскорее всего\b",
]

CONTRADICTION_PATTERNS = [
    (r"\bно\b", r"\bоднако\b"),
    (r"\bс одной стороны\b", r"\bс другой стороны\b"),
    (r"\bхотя\b", r"\bтем не менее\b"),
]

SAFETY_BLOCKED_WORDS = [
    r"обход.ограничен", r"ignore.*instruction", r"bypass",
    r"я.*могу.*вс[её]", r"отвечу.*любой",
]

QUESTION_KEYWORDS = [
    "что", "как", "почему", "зачем", "кто", "где",
    "когда", "сколько", "какой", "какова", "объясни",
    "расскажи", "сравни", "проанализируй", "опиши",
    "перечисли", "назови",
]


@dataclass
class EvaluationResult:
    completeness: float = 0.0
    consistency: float = 0.0
    safety: float = 1.0
    confidence: float = 0.0
    latency_score: float = 0.0
    novelty: float = 0.0
    overall: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "completeness": round(self.completeness, 3),
            "consistency": round(self.consistency, 3),
            "safety": round(self.safety, 3),
            "confidence": round(self.confidence, 3),
            "latency_score": round(self.latency_score, 3),
            "novelty": round(self.novelty, 3),
            "overall": round(self.overall, 3),
            "details": self.details,
        }


class SelfEvaluator:
    WEIGHTS = {
        "completeness": 0.25,
        "consistency": 0.20,
        "safety": 0.20,
        "confidence": 0.15,
        "latency_score": 0.10,
        "novelty": 0.10,
    }

    LATENCY_THRESHOLD_MS = 5000.0

    def __init__(self):
        self._recent_responses: List[str] = []
        self._max_recent = 50

    def evaluate(
        self,
        prompt: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        metadata = metadata or {}

        completeness = self._eval_completeness(prompt, response)
        consistency = self._eval_consistency(response)
        safety = self._eval_safety(prompt, response)
        confidence = self._eval_confidence(response, metadata)
        latency_score = self._eval_latency(metadata)
        novelty = self._eval_novelty(response)

        overall = (
            completeness * self.WEIGHTS["completeness"]
            + consistency * self.WEIGHTS["consistency"]
            + safety * self.WEIGHTS["safety"]
            + confidence * self.WEIGHTS["confidence"]
            + latency_score * self.WEIGHTS["latency_score"]
            + novelty * self.WEIGHTS["novelty"]
        )

        if self._recent_responses is None:
            self._recent_responses = []
        self._recent_responses.append(response)
        if len(self._recent_responses) > self._max_recent:
            self._recent_responses = self._recent_responses[-self._max_recent:]

        return EvaluationResult(
            completeness=completeness,
            consistency=consistency,
            safety=safety,
            confidence=confidence,
            latency_score=latency_score,
            novelty=novelty,
            overall=overall,
            details={
                "prompt_length": len(prompt),
                "response_length": len(response),
                "hedging_count": self._count_hedging(response),
                "repetition_ratio": self._repetition_ratio(response),
                "has_disclaimer": self._has_disclaimer(response),
            },
        )

    def _eval_completeness(self, prompt: str, response: str) -> float:
        if not response or not response.strip():
            return 0.0
        prompt_lower = prompt.lower()
        response_lower = response.lower()
        has_question_words = any(kw in prompt_lower for kw in QUESTION_KEYWORDS)
        if not has_question_words and len(prompt) < 20:
            return min(1.0, len(response) / 100)

        prompt_keywords = set(re.findall(r"[а-яёa-z]{4,}", prompt_lower))
        if not prompt_keywords:
            return min(1.0, len(response) / 200)
        response_keywords = set(re.findall(r"[а-яёa-z]{4,}", response_lower))
        overlap = len(prompt_keywords & response_keywords)
        ratio = overlap / len(prompt_keywords)
        min_ratio = min(1.0, len(response) / 300)
        return max(0.0, min(1.0, ratio * 0.6 + min_ratio * 0.4))

    def _eval_consistency(self, response: str) -> float:
        if not response or len(response) < 20:
            return 1.0
        rep_ratio = self._repetition_ratio(response)
        score = 1.0 - rep_ratio * 0.5
        contradictions = 0
        for p1, p2 in CONTRADICTION_PATTERNS:
            has_p1 = bool(re.search(p1, response.lower()))
            has_p2 = bool(re.search(p2, response.lower()))
            if has_p1 and has_p2:
                contradictions += 1
        score -= contradictions * 0.15
        return max(0.0, score)

    def _eval_safety(self, prompt: str, response: str) -> float:
        combined = f"{prompt}\n{response}".lower()
        for pattern in SAFETY_BLOCKED_WORDS:
            if re.search(pattern, combined):
                logger.warning("Safety pattern detected: %s", pattern)
                return 0.0
        return 1.0

    def _eval_confidence(self, response: str, metadata: Dict[str, Any]) -> float:
        llm_confidence = metadata.get("confidence")
        if llm_confidence is not None and isinstance(llm_confidence, (int, float)):
            return max(0.0, min(1.0, llm_confidence))
        if not response:
            return 0.0
        hedging = self._count_hedging(response)
        words = len(response.split())
        if words == 0:
            return 0.0
        hedge_penalty = min(0.5, hedging * 0.1)
        short_penalty = 0.3 if words < 5 else 0.0
        base = 0.7 - hedge_penalty - short_penalty
        return max(0.0, min(1.0, base))

    def _eval_latency(self, metadata: Dict[str, Any]) -> float:
        latency = None
        for key in ("execution_time_ms", "latency_ms", "duration_ms"):
            val = metadata.get(key)
            if val is not None:
                latency = float(val)
                break
        if latency is None:
            return 0.5
        if latency <= self.LATENCY_THRESHOLD_MS / 2:
            return 1.0
        score = 1.0 - (latency - self.LATENCY_THRESHOLD_MS / 2) / self.LATENCY_THRESHOLD_MS
        return max(0.0, score)

    def _eval_novelty(self, response: str) -> float:
        if not self._recent_responses or not response:
            return 0.5
        response_words = set(re.findall(r"[а-яёa-z]{4,}", response.lower()))
        if not response_words:
            return 0.5
        max_similarity = 0.0
        for prev in self._recent_responses[-10:]:
            prev_words = set(re.findall(r"[а-яёa-z]{4,}", prev.lower()))
            if not prev_words:
                continue
            intersection = len(response_words & prev_words)
            union = len(response_words | prev_words)
            sim = intersection / union if union > 0 else 0.0
            max_similarity = max(max_similarity, sim)
        return max(0.0, 1.0 - max_similarity)

    def _count_hedging(self, text: str) -> int:
        count = 0
        for pattern in HEDGING_PATTERNS:
            count += len(re.findall(pattern, text.lower()))
        return count

    def _repetition_ratio(self, text: str) -> float:
        sentences = re.split(r"[.!?]+", text.lower())
        sentences = [s.strip() for s in sentences if len(s.strip()) > 3]
        if len(sentences) < 2:
            return 0.0
        unique = set(sentences)
        return 1.0 - len(unique) / len(sentences)

    def _has_disclaimer(self, text: str) -> bool:
        patterns = [
            r"информация.*требует.*проверк",
            r"рекомендуется.*уточнить",
            r"проверь.*источник",
            r"обратись.*специалист",
            r"⚠️",
        ]
        return any(re.search(p, text.lower()) for p in patterns)

    def get_recent_count(self) -> int:
        return len(self._recent_responses) if self._recent_responses else 0


_evaluator: Optional[SelfEvaluator] = None


def get_evaluator() -> SelfEvaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = SelfEvaluator()
    return _evaluator


def reset_evaluator():
    global _evaluator
    _evaluator = None
