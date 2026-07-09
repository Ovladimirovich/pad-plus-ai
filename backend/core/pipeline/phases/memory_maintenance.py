import logging
from typing import Dict, Any, Optional

from ..base import PipelinePhase
from ..models import PhaseResult

logger = logging.getLogger("padplus.pipeline.memory_maintenance")

FUSION_INTERVAL_DIALOGS = 10
FORGETTING_INTERVAL_DIALOGS = 25


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
            from memory.forgetting import PriorityForgetting
            from memory import get_episodic_memory, get_semantic_memory

            forgetting = PriorityForgetting()
            episodic = get_episodic_memory()
            semantic = get_semantic_memory()

            ep_items = episodic.get_all() if hasattr(episodic, "get_all") else []
            sem_items = semantic.get_all() if hasattr(semantic, "get_all") else []
            ep_list = [e.to_dict() if hasattr(e, "to_dict") else e for e in ep_items]
            sem_list = [s.to_dict() if hasattr(s, "to_dict") else s for s in sem_items]

            all_items = ep_list + sem_list
            records = forgetting.forget_lowest_ranked(all_items)
            forgotten_count = len(records)

            if records:
                delete_ids = {}
                for r in records:
                    store = "episodic" if r.item_type in ("episodic", "unknown") else "semantic"
                    delete_ids.setdefault(store, []).append(r.item_id)
                for store_name, ids in delete_ids.items():
                    store = episodic if store_name == "episodic" else semantic
                    for item_id in ids:
                        try:
                            if hasattr(store, "delete"):
                                store.delete(item_id)
                        except Exception:
                            pass

            logger.info("Forgetting: %d items forgotten", forgotten_count)
            return {"forgotten": forgotten_count, "records": len(records)}
        except Exception as e:
            logger.warning("Forgetting error: %s", e)
            return {"error": str(e)}
