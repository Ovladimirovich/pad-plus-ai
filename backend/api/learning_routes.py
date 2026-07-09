from fastapi import APIRouter, Query
from typing import Optional
import logging

logger = logging.getLogger("padplus.api.learning")

router = APIRouter(prefix="/api/v1/learning", tags=["Learning"])


@router.get("/stats")
async def get_learning_stats():
    from learning.evaluator import get_evaluator
    from learning.collector import get_collector
    from learning.experience import get_experience_learner
    from learning.active import get_active_policy
    evaluator = get_evaluator()
    collector = get_collector()
    learner = get_experience_learner()
    policy = get_active_policy()
    return {
        "evaluator": {
            "recent_count": evaluator.get_recent_count(),
        },
        "collector": collector.get_all_stats(),
        "experience_learner": learner.get_stats(),
        "active_policy": policy.get_policy_state(),
    }


@router.get("/evaluation/recent")
async def get_recent_evaluations(limit: int = Query(20, ge=1, le=200)):
    from learning.collector import get_collector
    collector = get_collector()
    records = collector.export_dataset("dialogs", limit=limit)
    return {
        "total": len(records),
        "records": records,
    }


@router.get("/experience/stats")
async def get_experience_stats():
    from learning.experience import get_experience_learner
    learner = get_experience_learner()
    return learner.get_stats()


@router.get("/experience/recent")
async def get_recent_experiences(limit: int = Query(20, ge=1, le=100)):
    from learning.experience import get_experience_learner
    learner = get_experience_learner()
    return {
        "total": len(learner.get_recent_interactions(limit=10000)),
        "records": learner.get_recent_interactions(limit=limit),
    }


@router.get("/active/policy")
async def get_active_policy():
    from learning.active import get_active_policy
    policy = get_active_policy()
    return policy.get_policy_state()


@router.post("/active/reset")
async def reset_active_policy():
    from learning.active import reset_active_policy
    reset_active_policy()
    return {"success": True}
