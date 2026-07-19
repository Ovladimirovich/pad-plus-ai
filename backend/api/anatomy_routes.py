"""
Роуты Living Anatomy — живая визуализация когнитивной архитектуры.
"""

from fastapi import APIRouter, HTTPException

from backend.core.anatomy import get_module_detail, get_module_status

router = APIRouter(prefix="/api/v1/anatomy", tags=["anatomy"])


@router.get("")
async def get_anatomy():
    """Полное дерево живой анатомии когнитивной архитектуры."""
    return get_module_status()


@router.get("/{module_id}")
async def get_anatomy_module(module_id: str):
    """Детальный статус конкретного модуля (brain, memory, emotion, ...)."""
    detail = get_module_detail(module_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found")
    return detail
