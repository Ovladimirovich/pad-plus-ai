import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("padplus.learning.experience")

CONTEXT_FEATURES = [
    "topic_complexity",
    "message_length",
    "has_question",
    "strategy",
    "pad_valence",
    "pad_arousal",
    "pad_dominance",
]

COMPLEXITY_THRESHOLDS = {"short": 20, "medium": 100}


class ExperienceLearner:
    DATA_PATH = Path(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ) / "data" / "experience_learner.json"

    MIN_SAMPLES_PER_CONTEXT = 3
    DEFAULT_PSEUDO_COUNT = 2
    DEFAULT_PSEUDO_SCORE = 0.5

    SAVE_INTERVAL = 10

    def __init__(self, data_path: Optional[Path] = None):
        self._data_path = data_path or self.DATA_PATH
        self._interactions: List[Dict[str, Any]] = []
        self._context_strategy_scores: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._strategy_counts: Dict[str, int] = defaultdict(int)
        self._strategy_totals: Dict[str, float] = defaultdict(float)
        self._dirty_count = 0
        self._load()

    def record_interaction(
        self,
        prompt: str,
        strategy: str,
        evaluation: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = self._extract_context(prompt, context)
        ctx_key = self._context_key(ctx)
        overall = evaluation.get("overall", 0.5)
        entry = {
            "timestamp": time.time(),
            "prompt": prompt,
            "strategy": strategy,
            "evaluation": evaluation,
            "context": ctx,
            "context_key": ctx_key,
        }
        self._interactions.append(entry)
        if len(self._interactions) > 1000:
            self._interactions = self._interactions[-1000:]
        self._context_strategy_scores[ctx_key][strategy].append(overall)
        self._strategy_counts[strategy] += 1
        self._strategy_totals[strategy] += overall
        self._dirty_count += 1
        if self._dirty_count % self.SAVE_INTERVAL == 0:
            self._save()

    def get_strategy_recommendation(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        ctx = self._extract_context(prompt, context)
        ctx_key = self._context_key(ctx)
        best = self._best_in_context(ctx_key)
        if best:
            return best
        if self._interactions:
            all_best = self._best_overall()
            if all_best:
                return all_best
        return None

    def get_context_performance(self) -> Dict[str, Any]:
        result = {}
        for ctx_key, strategies in self._context_strategy_scores.items():
            result[ctx_key] = {}
            for strategy, scores in strategies.items():
                avg = sum(scores) / len(scores)
                result[ctx_key][strategy] = {
                    "avg_score": round(avg, 3),
                    "count": len(scores),
                }
        return result

    def get_strategy_performance(self) -> Dict[str, Any]:
        result = {}
        for strategy in self._strategy_counts:
            count = self._strategy_counts[strategy]
            avg = self._strategy_totals[strategy] / count if count > 0 else 0.0
            result[strategy] = {
                "count": count,
                "avg_score": round(avg, 3),
                "total_score": round(self._strategy_totals[strategy], 3),
            }
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_interactions": len(self._interactions),
            "strategies_used": dict(self._strategy_counts),
            "strategy_performance": self.get_strategy_performance(),
            "context_performance": self.get_context_performance(),
            "best_overall": self._best_overall(),
        }

    def _extract_context(
        self, prompt: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        text_len = len(prompt)
        if text_len <= COMPLEXITY_THRESHOLDS["short"]:
            complexity = "short"
        elif text_len <= COMPLEXITY_THRESHOLDS["medium"]:
            complexity = "medium"
        else:
            complexity = "long"
        has_question = any(
            kw in prompt.lower()
            for kw in ["что", "как", "почему", "зачем", "кто", "где", "когда"]
        )
        result = {
            "topic_complexity": complexity,
            "message_length": text_len,
            "has_question": has_question,
        }
        if context:
            for key in ("pad_valence", "pad_arousal", "pad_dominance"):
                val = context.get(key)
                if val is not None:
                    result[key] = val
        return result

    def _context_key(self, ctx: Dict[str, Any]) -> str:
        parts = [f"len={ctx.get('topic_complexity', 'unknown')}"]
        if ctx.get("has_question"):
            parts.append("q=1")
        for dim in ("pad_valence", "pad_arousal", "pad_dominance"):
            val = ctx.get(dim)
            if val is not None:
                bucket = "high" if val > 0.5 else "low"
                parts.append(f"{dim}={bucket}")
        return "|".join(parts)

    def _best_in_context(self, ctx_key: str) -> Optional[str]:
        strategies = self._context_strategy_scores.get(ctx_key)
        if not strategies:
            return None
        best_strategy = None
        best_score = -1.0
        for strategy, scores in strategies.items():
            if len(scores) < self.MIN_SAMPLES_PER_CONTEXT:
                continue
            raw_avg = sum(scores) / len(scores)
            bayesian = (
                (sum(scores) + self.DEFAULT_PSEUDO_COUNT * self.DEFAULT_PSEUDO_SCORE)
                / (len(scores) + self.DEFAULT_PSEUDO_COUNT)
            )
            if bayesian > best_score:
                best_score = bayesian
                best_strategy = strategy
        return best_strategy

    def _best_overall(self) -> Optional[str]:
        best_strategy = None
        best_score = -1.0
        for strategy in self._strategy_counts:
            count = self._strategy_counts[strategy]
            if count < self.MIN_SAMPLES_PER_CONTEXT:
                continue
            avg = self._strategy_totals[strategy] / count
            bayesian = (
                (self._strategy_totals[strategy]
                 + self.DEFAULT_PSEUDO_COUNT * self.DEFAULT_PSEUDO_SCORE)
                / (count + self.DEFAULT_PSEUDO_COUNT)
            )
            if bayesian > best_score:
                best_score = bayesian
                best_strategy = strategy
        return best_strategy

    def get_recent_interactions(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": i["timestamp"],
                "prompt": i["prompt"][:100],
                "strategy": i["strategy"],
                "overall": i["evaluation"].get("overall", 0),
                "context_key": i["context_key"],
            }
            for i in self._interactions[-limit:]
        ]

    def _load(self) -> None:
        path = self._data_path
        if not path.exists():
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._interactions = data.get("interactions", [])
            for entry in self._interactions:
                strategy = entry.get("strategy", "unknown")
                ctx_key = entry.get("context_key", "unknown")
                overall = entry.get("evaluation", {}).get("overall", 0.5)
                self._context_strategy_scores[ctx_key][strategy].append(overall)
                self._strategy_counts[strategy] += 1
                self._strategy_totals[strategy] += overall
        except Exception as e:
            logger.warning("ExperienceLearner load error: %s", e)

    def _save(self) -> None:
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "updated": time.time(),
                "interactions": self._interactions,
            }
            with open(self._data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("ExperienceLearner save error: %s", e)

    def reset(self) -> None:
        self._interactions.clear()
        self._context_strategy_scores.clear()
        self._strategy_counts.clear()
        self._strategy_totals.clear()
        if self._data_path.exists():
            self._data_path.unlink()


_experience_learner: Optional[ExperienceLearner] = None


def get_experience_learner() -> ExperienceLearner:
    global _experience_learner
    if _experience_learner is None:
        _experience_learner = ExperienceLearner()
    return _experience_learner


def reset_experience_learner() -> None:
    global _experience_learner
    _experience_learner = None
