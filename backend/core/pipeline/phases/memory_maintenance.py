import logging
from typing import Dict, Any, Optional

from ..base import PipelinePhase
from ..models import PhaseResult
from ..registry import register_phase

logger = logging.getLogger("padplus.pipeline.memory_maintenance")

FUSION_INTERVAL_DIALOGS = 10
FORGETTING_INTERVAL_DIALOGS = 25


@register_phase("memory_maintenance", order=19)
class MemoryMaintenancePhase(PipelinePhase):
    def __init__(self):
        self._dialogs_since_fusion = 0
        self._dialogs_since_forgetting = 0

    async def execute(self, ctx) -> PhaseResult:
        self._dialogs_since_fusion += 1
        self._dialogs_since_forgetting += 1

        fusion_result = None
        forgetting_result = None

        if self._dialogs_since_fusion >= FUSION_INTERVAL_DIALOGS:
            fusion_result = await self._run_fusion(ctx)
            self._dialogs_since_fusion = 0

        if self._dialogs_since_forgetting >= FORGETTING_INTERVAL_DIALOGS:
            forgetting_result = await self._run_forgetting(ctx)
            self._dialogs_since_forgetting = 0

        data = {"fusion": fusion_result, "forgetting": forgetting_result}
        ctx.context["memory_maintenance"] = data
        return PhaseResult(success=True, data=data)

    async def _run_fusion(self, ctx) -> Dict[str, Any]:
        try:
            from memory.fusion import MemoryFusion
            from memory import get_episodic_memory, get_semantic_memory

            fusion = MemoryFusion()
            episodic = get_episodic_memory()
            semantic = get_semantic_memory()

            ep_items = episodic.get_all() if hasattr(episodic, "get_all") else []
            sem_items = semantic.get_all() if hasattr(semantic, "get_all") else []
            ep_list = [e.to_dict() if hasattr(e, "to_dict") else e for e in ep_items]
            sem_list = [s.to_dict() if hasattr(s, "to_dict") else s for s in sem_items]

            candidates = fusion.find_candidates(ep_list, sem_list)
            fused_count = 0
            for src_a, src_b, sim in candidates:
                merged = fusion.fuse(src_a, src_b, sim)
                fusion.record_fusion(
                    source_ids=[src_a.get("id", ""), src_b.get("id", "")],
                    target_type=merged.get("knowledge_type", "fused"),
                    target_id="",
                    merged_fields=merged,
                    similarity=sim,
                )
                fused_count += 1

            logger.info("Fusion: %d candidates, %d fused", len(candidates), fused_count)
            return {"candidates": len(candidates), "fused": fused_count}
        except Exception as e:
            logger.warning("Fusion error: %s", e)
            return {"error": str(e)}

    async def _run_forgetting(self, ctx) -> Dict[str, Any]:
        try:
            from memory import get_episodic_memory, get_semantic_memory
            from memory.lifecycle import MemoryLifecycleConfig, MemoryLifecycleManager

            episodic = get_episodic_memory()
            semantic = get_semantic_memory()

            # D'-3: единый lifecycle-фреймворк (TTL + quota + importance eviction)
            # Безопасный конфиг для пиплайна: небольшие лимиты, чтобы забывание
            # не выжирало CPU в каждом 25-м диалоге.
            config = MemoryLifecycleConfig()
            config.max_items["episodic"] = 20000
            config.max_items["semantic"] = 10000

            manager = MemoryLifecycleManager(config)
            user_id = ctx.context.get("user_id") if ctx.context else None
            results = manager.run_maintenance(
                episodic=episodic,
                semantic=semantic,
                user_id=user_id,
            )

            totals = {"expired": 0, "evicted": 0, "protected": 0}
            for r in results.values():
                totals["expired"] += r.expired
                totals["evicted"] += r.evicted
                totals["protected"] += r.protected

            forgotten_count = totals["expired"] + totals["evicted"]

            logger.info(
                "Forgetting: %d items forgotten (expired=%d, evicted=%d, protected=%d)",
                forgotten_count, totals["expired"], totals["evicted"], totals["protected"],
            )
            return {
                "forgotten": forgotten_count,
                "expired": totals["expired"],
                "evicted": totals["evicted"],
                "protected": totals["protected"],
                "by_component": {k: v.to_dict() for k, v in results.items()},
            }
        except Exception as e:
            logger.warning("Forgetting error: %s", e, exc_info=True)
            return {"error": str(e)}
