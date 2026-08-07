"""
⏰ Lifecycle & Forgetting — единый фреймворк TTL/забывания (D'-3).

Унифицирует управление жизненным циклом памяти для всех компонентов:
- TTL: проактивное забывание элементов старше порога
- Quota: сброс лишних элементов при превышении лимитов
- Importance-based eviction: приоритетное удаление наименее ценных записей

Стратегии забывания (per-component):
- episodic:  ttl+importance  (TTL + важность по значимости/частоте)
- semantic:  importance+access (важность + частота использования)
- rag:       ttl+access      (TTL + частота доступа)
- impulse:   stack+ttl       (лимит стека + TTL)
- emotion:   ttl (decay)     (затухание — уже реализовано в SessionEmotionStore)
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from core.xray.memory_trace import (
    emit_memory_event, MemoryOperation, MemoryComponent, MemoryObjectType, MemoryResult
)

logger = logging.getLogger("padplus.memory.lifecycle")


@dataclass
class MemoryLifecycleConfig:
    """Per-component конфигурация жизненного цикла памяти."""

    ttl_hours: Dict[str, Optional[int]] = field(default_factory=lambda: {
        "episodic": 30 * 24,      # 30 дней
        "semantic": 90 * 24,      # 90 дней
        "rag": 30 * 24,           # 30 дней
        "roots": None,            # навсегда
        "emotion": 24,            # 24 часа (decay)
        "impulse": 7 * 24,        # 7 дней
        "persona": 90 * 24,       # 90 дней
    })

    max_items: Dict[str, Optional[int]] = field(default_factory=lambda: {
        "episodic": 100000,
        "semantic": 50000,
        "rag": 10000,
        "emotion": 5000,
        "impulse": 1000,
    })

    forgetting_strategy: Dict[str, str] = field(default_factory=lambda: {
        "episodic": "ttl+importance",
        "semantic": "importance+access",
        "rag": "ttl+access",
        "impulse": "stack+ttl",
        "emotion": "ttl",
    })

    def get_ttl_hours(self, component: str) -> Optional[int]:
        return self.ttl_hours.get(component)

    def get_max_items(self, component: str) -> Optional[int]:
        return self.max_items.get(component)

    def get_strategy(self, component: str) -> str:
        return self.forgetting_strategy.get(component, "ttl+importance")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ttl_hours": self.ttl_hours,
            "max_items": self.max_items,
            "forgetting_strategy": self.forgetting_strategy,
        }


@dataclass
class ForgettingResult:
    """Результат прогона lifecycle-обслуживания по одному компоненту."""
    component: str
    strategy: str
    scanned: int = 0
    expired: int = 0          # удалено по TTL
    evicted: int = 0          # удалено по quota/важности
    protected: int = 0        # сохранено (высокая важность)
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "strategy": self.strategy,
            "scanned": self.scanned,
            "expired": self.expired,
            "evicted": self.evicted,
            "protected": self.protected,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp.isoformat(),
        }


class MemoryLifecycleManager:
    """
    Единый фреймворк TTL/quota-обслуживания памяти.

    Применяет MemoryLifecycleConfig к конкретным реализациям хранилищ.
    Методы принимают объекты хранилищ (EpisodicMemory, SemanticMemory, ...)
    и работают через duck-typing: если у хранилища нет нужного метода
    (например delete_expired), обработка пропускается безопасно.
    """

    def __init__(self, config: Optional[MemoryLifecycleConfig] = None):
        self.config = config or MemoryLifecycleConfig()
        self._history: List[ForgettingResult] = []
        self._lock = threading.RLock()

    # === Общий entry point ===

    def run_maintenance(
        self,
        episodic=None,
        semantic=None,
        rag=None,
        user_id: Optional[str] = None,
    ) -> Dict[str, ForgettingResult]:
        """Запускает lifecycle-обслуживание по всем переданным хранилищам."""
        results: Dict[str, ForgettingResult] = {}
        import time as _time
        start = _time.perf_counter()

        if episodic is not None:
            results["episodic"] = self.apply_episodic(episodic, user_id=user_id)
        if semantic is not None:
            results["semantic"] = self.apply_semantic(semantic)
        if rag is not None:
            results["rag"] = self.apply_rag(rag)

        total_ms = (_time.perf_counter() - start) * 1000
        logger.info(
            "Lifecycle maintenance done in %.1fms: %s",
            total_ms,
            {k: f"expired={r.expired}, evicted={r.evicted}, protected={r.protected}" for k, r in results.items()},
        )
        return results

    # === Episodic ===

    def apply_episodic(self, episodic, user_id: Optional[str] = None) -> ForgettingResult:
        import time as _time
        strategy = self.config.get_strategy("episodic")
        ttl_hours = self.config.get_ttl_hours("episodic")
        max_items = self.config.get_max_items("episodic")
        res = ForgettingResult(component="episodic", strategy=strategy)

        if ttl_hours is None and max_items is None:
            return res

        start = _time.perf_counter()
        try:
            # 1. TTL — удаляем старые эпизоды (но сохраняем важные)
            if ttl_hours is not None and hasattr(episodic, "delete_expired"):
                expired, protected = episodic.delete_expired(
                    max_age_hours=ttl_hours,
                    user_id=user_id,
                )
                res.expired += expired
                res.protected += protected

            # 2. Quota — если лимит превышен, сбрасываем наименее важные
            if max_items is not None:
                total = None
                if hasattr(episodic, "get_count"):
                    total = episodic.get_count(user_id=user_id)
                elif hasattr(episodic, "get_stats"):
                    stats = episodic.get_stats()
                    total = stats.get("total_episodes") if isinstance(stats, dict) else None

                if total is not None and total > max_items:
                    evicted = self._evict_by_importance(
                        episodic,
                        strategy=strategy,
                        over_limit=total - max_items,
                        item_kind="episode",
                        user_id=user_id,
                    )
                    res.evicted += evicted
                    res.scanned += total
        except Exception as e:
            logger.warning("Episodic lifecycle error: %s", e, exc_info=True)

        res.duration_ms = (_time.perf_counter() - start) * 1000
        res.scanned = max(res.scanned, res.expired + res.protected + res.evicted)
        self._record(res)
        return res

    # === Semantic ===

    def apply_semantic(self, semantic) -> ForgettingResult:
        import time as _time
        strategy = self.config.get_strategy("semantic")
        ttl_hours = self.config.get_ttl_hours("semantic")
        max_items = self.config.get_max_items("semantic")
        res = ForgettingResult(component="semantic", strategy=strategy)

        if ttl_hours is None and max_items is None:
            return res

        start = _time.perf_counter()
        try:
            if ttl_hours is not None and hasattr(semantic, "delete_expired"):
                expired, protected = semantic.delete_expired(max_age_hours=ttl_hours)
                res.expired += expired
                res.protected += protected

            if max_items is not None:
                total = None
                if hasattr(semantic, "get_count"):
                    total = semantic.get_count()
                elif hasattr(semantic, "get_stats"):
                    stats = semantic.get_stats()
                    total = stats.get("total_knowledge") if isinstance(stats, dict) else None

                if total is not None and total > max_items:
                    evicted = self._evict_by_importance(
                        semantic,
                        strategy=strategy,
                        over_limit=total - max_items,
                        item_kind="knowledge",
                    )
                    res.evicted += evicted
                    res.scanned += total
        except Exception as e:
            logger.warning("Semantic lifecycle error: %s", e, exc_info=True)

        res.duration_ms = (_time.perf_counter() - start) * 1000
        res.scanned = max(res.scanned, res.expired + res.protected + res.evicted)
        self._record(res)
        return res

    # === RAG ===

    def apply_rag(self, rag) -> ForgettingResult:
        import time as _time
        strategy = self.config.get_strategy("rag")
        ttl_hours = self.config.get_ttl_hours("rag")
        max_items = self.config.get_max_items("rag")
        res = ForgettingResult(component="rag", strategy=strategy)

        if ttl_hours is None and max_items is None:
            return res

        start = _time.perf_counter()
        try:
            if ttl_hours is not None and hasattr(rag, "delete_expired"):
                expired, protected = rag.delete_expired(max_age_hours=ttl_hours)
                res.expired += expired
                res.protected += protected

            if max_items is not None:
                total = None
                if hasattr(rag, "get_count"):
                    total = rag.get_count()
                elif hasattr(rag, "get_stats"):
                    stats = rag.get_stats()
                    total = stats.get("total_dialogs") if isinstance(stats, dict) else None

                if total is not None and total > max_items:
                    evicted = self._evict_by_importance(
                        rag,
                        strategy=strategy,
                        over_limit=total - max_items,
                        item_kind="dialog",
                    )
                    res.evicted += evicted
                    res.scanned += total
        except Exception as e:
            logger.warning("RAG lifecycle error: %s", e, exc_info=True)

        res.duration_ms = (_time.perf_counter() - start) * 1000
        res.scanned = max(res.scanned, res.expired + res.protected + res.evicted)
        self._record(res)
        return res

    # === Вспомогательные ===

    def _evict_by_importance(
        self,
        store,
        strategy: str,
        over_limit: int,
        item_kind: str,
        user_id: Optional[str] = None,
    ) -> int:
        """
        Удаляет over_limit наименее важных элементов.
        Использует PriorityForgetting для скоринга важности.
        """
        try:
            from memory.forgetting import PriorityForgetting
        except Exception:
            return 0

        # Получаем все элементы в виде словарей
        items = []
        if hasattr(store, "get_all") and callable(store.get_all):
            try:
                raw = store.get_all(limit=over_limit * 3 + 100)
                for it in raw:
                    if hasattr(it, "to_dict"):
                        items.append(it.to_dict())
                    elif isinstance(it, dict):
                        items.append(it)
            except Exception as e:
                logger.debug("get_all failed for %s: %s", item_kind, e)
                return 0

        if not items:
            return 0

        forgetting = PriorityForgetting()
        ranked = forgetting.rank_for_targets(items)
        evicted = 0
        for entry in ranked[:over_limit]:
            item = entry["item"]
            item_id = item.get("id") or item.get("_id")
            if not item_id:
                continue
            try:
                deleted = False
                if hasattr(store, "delete_by_id"):
                    deleted = store.delete_by_id(item_id)
                elif hasattr(store, "delete"):
                    deleted = store.delete(item_id)
                if deleted:
                    evicted += 1
            except Exception as e:
                logger.debug("Delete %s %s failed: %s", item_kind, item_id, e)

        if evicted:
            emit_memory_event(
                operation=MemoryOperation.EVICT,
                component=MemoryComponent.SEMANTIC_MEMORY if item_kind == "knowledge" else MemoryComponent.UNKNOWN,
                object_type=MemoryObjectType.FACT if item_kind == "knowledge" else MemoryObjectType.UNKNOWN,
                result=MemoryResult.EVICTED,
                phase=f"lifecycle.evict_{item_kind}",
                session_id=user_id,
                payload_size_bytes=evicted,
                metadata={"strategy": strategy, "kind": item_kind},
            )
        return evicted

    # === Статистика ===

    def _record(self, res: ForgettingResult) -> None:
        with self._lock:
            self._history.append(res)
            if len(self._history) > 200:
                self._history = self._history[-200:]

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            return [r.to_dict() for r in self._history[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_expired = sum(r.expired for r in self._history)
            total_evicted = sum(r.evicted for r in self._history)
            total_protected = sum(r.protected for r in self._history)
            by_component: Dict[str, Dict[str, int]] = {}
            for r in self._history:
                bucket = by_component.setdefault(r.component, {"runs": 0, "expired": 0, "evicted": 0, "protected": 0})
                bucket["runs"] += 1
                bucket["expired"] += r.expired
                bucket["evicted"] += r.evicted
                bucket["protected"] += r.protected
            return {
                "total_runs": len(self._history),
                "total_expired": total_expired,
                "total_evicted": total_evicted,
                "total_protected": total_protected,
                "by_component": by_component,
                "config": self.config.to_dict(),
                "recent": [r.to_dict() for r in self._history[-5:]],
            }

    def reset(self) -> None:
        with self._lock:
            self._history.clear()


# === Глобальный экземпляр ===
_lifecycle: Optional[MemoryLifecycleManager] = None
_module_lock = threading.Lock()


def get_lifecycle() -> MemoryLifecycleManager:
    """Возвращает глобальный lifecycle-менеджер."""
    global _lifecycle
    with _module_lock:
        if _lifecycle is None:
            _lifecycle = MemoryLifecycleManager()
        return _lifecycle


def reset_lifecycle() -> None:
    """Сброс для тестов."""
    global _lifecycle
    with _module_lock:
        _lifecycle = None
