from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from memory.user_persona import UserPersona
from core.supabase_client import get_supabase, get_supabase_service

logger = logging.getLogger("PAD+.user_persona_postgres")


class UserPersonaPostgresManager:
    """
    PostgreSQL-версия UserPersonaManager.

    Хранит UserPersona в таблице user_personas вместо JSON-файла.
    """

    def __init__(self):
        self._personas: Dict[str, UserPersona] = {}
        self._load_all()
        logger.info(f"UserPersonaPostgresManager инициализирован: {len(self._personas)} пользователей")

    def _load_all(self) -> None:
        try:
            client = get_supabase()
            if client is None:
                logger.warning("Supabase клиент недоступен, кэш пуст")
                return
            resp = client.table("user_personas").select("*").execute()
            for row in resp.data:
                persona = UserPersona.from_dict(row["data"])
                self._personas[persona.user_id] = persona
        except Exception as e:
            logger.warning(f"Не удалось загрузить UserPersona: {e}")

    def get_persona(self, user_id: str) -> UserPersona:
        if user_id not in self._personas:
            self._personas[user_id] = UserPersona(user_id=user_id)
            logger.info(f"Создана новая UserPersona для {user_id[:8]}...")
        return self._personas[user_id]

    def save_persona(self, persona: UserPersona) -> None:
        persona.updated_at = datetime.now().isoformat()
        self._personas[persona.user_id] = persona
        self._upsert_db(persona)

    def _upsert_db(self, persona: UserPersona) -> None:
        try:
            client = get_supabase_service() or get_supabase()
            if client is None:
                logger.warning("Supabase клиент недоступен, сохранение в кэш")
                return
            client.table("user_personas").upsert(
                {
                    "user_id": persona.user_id,
                    "data": persona.to_dict(),
                    "updated_at": datetime.now().isoformat(),
                },
                on_conflict="user_id",
            ).execute()
        except Exception as e:
            logger.error(f"Ошибка сохранения UserPersona в БД: {e}")

    def get_stats(self) -> Dict[str, Any]:
        if not self._personas:
            return {"total_users": 0}
        total_interactions = sum(p.total_interactions for p in self._personas.values())
        return {
            "total_users": len(self._personas),
            "total_interactions": total_interactions,
            "avg_interactions_per_user": round(total_interactions / len(self._personas), 1),
            "storage": "postgres",
        }


_user_persona_postgres: Optional[UserPersonaPostgresManager] = None


def get_user_persona_postgres_manager() -> UserPersonaPostgresManager:
    global _user_persona_postgres
    if _user_persona_postgres is None:
        _user_persona_postgres = UserPersonaPostgresManager()
    return _user_persona_postgres
