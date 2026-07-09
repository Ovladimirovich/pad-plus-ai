"""
Legacy API Routes — заглушки для старых frontend компонентов

Временные заглушки для API endpoints которые были удалены из новой разработки,
но все еще используются в frontend.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

logger = logging.getLogger("padplus.legacy")

router = APIRouter(prefix="/api/v1", tags=["Legacy Stubs"])


# === PROVIDERS STUBS ===
@router.get("/providers")
async def get_providers_stub():
    """Заглушка для списка провайдеров"""
    return {"providers": [], "message": "Providers API temporarily disabled"}


@router.get("/providers/{provider_id}/models")
async def get_provider_models_stub(provider_id: str):
    """Заглушка для моделей провайдера"""
    return {"models": [], "message": "Provider models API temporarily disabled"}


# === KEYS STUBS ===
@router.get("/keys")
async def get_keys_stub(offset: int = 0, limit: int = 100):
    """Заглушка для списка API ключей"""
    return {"keys": [], "total": 0, "offset": offset, "limit": limit, "message": "Keys API temporarily disabled"}


@router.post("/keys")
async def create_key_stub(body: Dict[str, Any]):
    """Заглушка для создания API ключа"""
    raise HTTPException(status_code=503, detail="Keys API temporarily disabled")


@router.patch("/keys/{key_id}")
async def update_key_stub(key_id: str, body: Dict[str, Any]):
    """Заглушка для обновления API ключа"""
    raise HTTPException(status_code=503, detail="Keys API temporarily disabled")


@router.delete("/keys/{key_id}")
async def delete_key_stub(key_id: str):
    """Заглушка для удаления API ключа"""
    raise HTTPException(status_code=503, detail="Keys API temporarily disabled")


@router.post("/keys/{key_id}/set-default")
async def set_default_key_stub(key_id: str):
    """Заглушка для установки ключа по умолчанию"""
    raise HTTPException(status_code=503, detail="Keys API temporarily disabled")


# === AUTH STUBS ===
@router.post("/auth/login")
async def login_stub(body: Dict[str, Any]):
    """Заглушка для логина"""
    raise HTTPException(status_code=503, detail="Auth API temporarily disabled. Use Supabase auth directly.")


@router.post("/auth/refresh")
async def refresh_stub():
    """Заглушка для refresh токена"""
    raise HTTPException(status_code=503, detail="Auth API temporarily disabled. Use Supabase auth directly.")


@router.post("/auth/logout")
async def logout_stub():
    """Заглушка для логаута"""
    raise HTTPException(status_code=503, detail="Auth API temporarily disabled. Use Supabase auth directly.")
