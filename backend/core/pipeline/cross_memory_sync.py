from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("padplus.cross_memory_sync")


class CrossMemorySync:
    def __init__(self):
        self._sync_count = 0

    def sync_rag_to_semantic(self, user_id: Optional[str] = None, limit: int = 5) -> List[str]:
        insights = []
        try:
            from memory import get_rag, get_semantic_memory
            rag = get_rag()
            semantic = get_semantic_memory()

            recent = rag.get_recent(days=7, n_results=limit)
            for dialog in recent:
                meta = dialog.get("metadata", {})
                user_msg = meta.get("user_message", "")
                ai_resp = meta.get("ai_response", "")
                topic = dialog.get("topic", "общее")
                if not user_msg or not ai_resp:
                    continue

                existing = semantic.search_knowledge(content=user_msg[:100], limit=1)
                if existing:
                    continue

                summary = f"Диалог на тему '{topic}': {user_msg[:100]}"
                semantic.add_knowledge(
                    content=summary,
                    knowledge_type="factual",
                    summary=summary,
                    source="rag_sync",
                    domain=topic,
                    confidence=0.6,
                )
                insights.append(f"RAG→Semantic: {summary[:60]}...")
        except Exception as e:
            logger.warning(f"sync_rag_to_semantic error: {e}")
        return insights

    def sync_episodic_to_semantic(self, user_id: Optional[str] = None) -> List[str]:
        insights = []
        try:
            from memory import get_episodic_memory, get_semantic_memory
            episodic = get_episodic_memory()
            semantic = get_semantic_memory()

            related = episodic.get_related_episodes("", n_results=10)
            for ep in related:
                ep_content = getattr(ep, "content", "") or getattr(ep, "summary", "")
                user_message = getattr(ep, "user_message", "")
                if not ep_content and not user_message:
                    continue

                existing = semantic.search_knowledge(content=(ep_content or user_message)[:100], limit=1)
                if existing:
                    continue

                content = ep_content or user_message
                semantic.add_knowledge(
                    content=content[:200],
                    knowledge_type="episodic_insight",
                    summary=f"Эпизод: {content[:80]}",
                    source="episodic_sync",
                    confidence=0.5,
                )
                insights.append(f"Episodic→Semantic: {content[:60]}...")
        except Exception as e:
            logger.warning(f"sync_episodic_to_semantic error: {e}")
        return insights

    def sync_semantic_to_roots(self, min_confidence: float = 0.8) -> List[str]:
        insights = []
        try:
            from memory import get_semantic_memory, get_roots_memory
            semantic = get_semantic_memory()
            roots = get_roots_memory()

            high_conf = semantic.search_knowledge(limit=20)
            for k in high_conf:
                if k.confidence < min_confidence:
                    continue
                existing = roots.search_knowledge(content=k.content[:100], limit=1)
                if existing:
                    continue

                roots.add_knowledge(
                    content=k.content[:200],
                    knowledge_type=k.knowledge_type.value if hasattr(k.knowledge_type, "value") else str(k.knowledge_type),
                    summary=k.summary or k.content[:80],
                    source="semantic_sync",
                    confidence=k.confidence,
                )
                insights.append(f"Semantic→Roots: {(k.summary or k.content)[:60]}...")
        except Exception as e:
            logger.warning(f"sync_semantic_to_roots error: {e}")
        return insights

    def sync_all(self, user_id: Optional[str] = None) -> Dict[str, List[str]]:
        return {
            "rag_to_semantic": self.sync_rag_to_semantic(user_id),
            "episodic_to_semantic": self.sync_episodic_to_semantic(user_id),
            "semantic_to_roots": self.sync_semantic_to_roots(),
        }


_cross_memory_sync: Optional[CrossMemorySync] = None


def get_cross_memory_sync() -> CrossMemorySync:
    global _cross_memory_sync
    if _cross_memory_sync is None:
        _cross_memory_sync = CrossMemorySync()
    return _cross_memory_sync
