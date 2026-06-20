from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger("PAD+.emotion_learner")


POSITIVE_WORDS = {
    "спасибо", "отлично", "прекрасно", "здорово", "классно",
    "помог", "помогло", "понял", "поняла", "супер",
    "круто", "благодарю", "thanks", "great", "awesome",
    "perfect", "умница", "молодец", "good", "правильно",
}

NEGATIVE_WORDS = {
    "плохо", "ужасно", "грустно", "злюсь", "ненавижу",
    "проблема", "ошибка", "неправильно", "ерунда", "глупость",
    "бесполезно", "bad", "wrong", "error", "fail",
}

PRAISE_WORDS = {
    "ты лучший", "ты умный", "ты крут", "молодец", "умница",
    "хороший ответ", "отличный ответ", "спасибо большое",
}

CRITICISM_WORDS = {
    "ты не прав", "ты ошибся", "не так", "ты глупый",
    "плохой ответ", "ерунда", "чушь", "бестолково",
}


class EmotionLearner:
    def __init__(self):
        self._dialog_history: List[Dict[str, Any]] = []

    def analyze_sentiment(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        combined = f"{user_message} {ai_response}".lower()

        pos_count = sum(1 for w in POSITIVE_WORDS if w in combined)
        neg_count = sum(1 for w in NEGATIVE_WORDS if w in combined)

        is_praise = any(w in combined for w in PRAISE_WORDS)
        is_criticism = any(w in combined for w in CRITICISM_WORDS)
        is_error = "ошибка" in ai_response.lower() or "проблема" in ai_response.lower()
        is_new_knowledge = len(user_message.split()) >= 5 and not is_error

        if is_praise:
            event = "user_praise"
            intensity = min(0.3 + pos_count * 0.1, 1.0)
        elif is_criticism:
            event = "user_criticism"
            intensity = min(0.3 + neg_count * 0.1, 1.0)
        elif is_error:
            event = "fallback"
            intensity = 0.3
        elif is_new_knowledge:
            event = "new_knowledge"
            intensity = min(0.2 + pos_count * 0.05, 0.5)
        else:
            event = "self_reflection"
            intensity = 0.1

        return {
            "event": event,
            "intensity": intensity,
            "pos_count": pos_count,
            "neg_count": neg_count,
        }

    def learn_from_dialog(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        analysis = self.analyze_sentiment(user_message, ai_response)
        self._dialog_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message[:100],
            "event": analysis["event"],
            "intensity": analysis["intensity"],
        })
        if len(self._dialog_history) > 100:
            self._dialog_history = self._dialog_history[-100:]
        return analysis

    def learn_from_history(self, user_id: Optional[str] = None) -> int:
        try:
            from memory import get_rag
            rag = get_rag()
            recent = rag.get_recent(days=1, n_results=10)
        except Exception as e:
            logger.warning(f"learn_from_history: RAG error: {e}")
            return 0

        from emotion.pad_model import get_pad_model
        pad = get_pad_model()
        applied = 0

        for dialog in recent:
            meta = dialog.get("metadata", {})
            user_msg = meta.get("user_message", "")
            ai_resp = meta.get("ai_response", "")
            if not user_msg:
                continue
            analysis = self.analyze_sentiment(user_msg, ai_resp)
            pad.apply_event(analysis["event"], analysis["intensity"])
            self._dialog_history.append({
                "timestamp": dialog.get("timestamp", datetime.now().isoformat()),
                "user_message": user_msg[:100],
                "event": analysis["event"],
                "intensity": analysis["intensity"],
            })
            applied += 1

        if applied > 0:
            pad.save()
            logger.info(f"EmotionLearner: applied {applied} events from history")

        return applied

    def get_stats(self) -> Dict[str, Any]:
        event_counts = {}
        for d in self._dialog_history:
            ev = d["event"]
            event_counts[ev] = event_counts.get(ev, 0) + 1
        return {
            "total_dialogs_analyzed": len(self._dialog_history),
            "event_distribution": event_counts,
            "recent_events": self._dialog_history[-5:] if self._dialog_history else [],
        }


_emotion_learner: Optional[EmotionLearner] = None


def get_emotion_learner() -> EmotionLearner:
    global _emotion_learner
    if _emotion_learner is None:
        _emotion_learner = EmotionLearner()
    return _emotion_learner
