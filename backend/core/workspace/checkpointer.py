"""
Checkpointer для сохранения фазовых чекпоинтов воркспейса (D'-1).
Поддерживает SQLite (для тестов и локальной разработки) и PostgreSQL/AsyncPG (для прода).
"""

from __future__ import annotations
import logging
import sqlite3
from datetime import datetime
from typing import Any, Optional

from .schemas import TurnWorkspace, PhaseName, ConversationWorkspace

logger = logging.getLogger("padplus.workspace.checkpointer")


class SQLiteCheckpointer:
    """Фазово-ориентированный чекер на базе SQLite для локальной разработки и тестов."""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._mem_conn = sqlite3.connect(db_path, check_same_thread=False) if db_path == ":memory:" else None
        if self._mem_conn:
            self._mem_conn.row_factory = sqlite3.Row
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if self._mem_conn:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS turn_workspaces (
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    workspace_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (session_id, turn_id, phase)
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_turn_workspaces_session_turn 
                ON turn_workspaces (session_id, turn_id);
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_workspaces (
                    session_id TEXT PRIMARY KEY,
                    workspace_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def save_after_phase(self, workspace: TurnWorkspace, phase: PhaseName) -> None:
        """Сохраняет чекпоинт после завершения фазы."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO turn_workspaces (session_id, turn_id, phase, workspace_json, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (workspace.session_id, workspace.turn_id, phase.value, workspace.to_checkpoint_json()))
            conn.commit()

    def save_conversation(self, workspace: ConversationWorkspace) -> None:
        """Сохраняет воркспейс сессии (разговор/цели)."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO conversation_workspaces (session_id, workspace_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (workspace.core.session_id, workspace.model_dump_json()))
            conn.commit()

    def load_conversation(self, session_id: str) -> Optional[ConversationWorkspace]:
        """Загружает воркспейс сессии."""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT workspace_json FROM conversation_workspaces WHERE session_id = ?
            """, (session_id,)).fetchone()
            if row:
                return ConversationWorkspace.model_validate_json(row["workspace_json"])
        return None

    def load_latest(self, session_id: str, turn_id: int) -> Optional[TurnWorkspace]:
        """Загружает последний чекпоинт для хода (после последней завершённой фазы)."""
        phase_priority = {
            PhaseName.SAVE_EPISODE.value: 16,
            PhaseName.EVALUATION.value: 15,
            PhaseName.REFLECTION.value: 14,
            PhaseName.TRUTH_LOOP.value: 13,
            PhaseName.GENERATE.value: 12,
            PhaseName.IDENTITY.value: 11,
            PhaseName.ROOTS.value: 10,
            PhaseName.PERSONA.value: 9,
            PhaseName.IMPULSE.value: 8,
            PhaseName.EMOTION.value: 7,
            PhaseName.SEMANTIC.value: 6,
            PhaseName.EPISODIC.value: 5,
            PhaseName.KNOWLEDGE_GRAPH.value: 4,
            PhaseName.RAG.value: 3,
            PhaseName.INTENT.value: 2,
            PhaseName.SAFETY.value: 1,
        }
        
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT phase, workspace_json FROM turn_workspaces
                WHERE session_id = ? AND turn_id = ?
            """, (session_id, turn_id)).fetchall()
            
            if not rows:
                return None
            
            # Находим фазу с наивысшим приоритетом
            best_row = max(rows, key=lambda r: phase_priority.get(r["phase"], 0))
            return TurnWorkspace.from_checkpoint_json(best_row["workspace_json"])

    def load_at_phase(self, session_id: str, turn_id: int, phase: PhaseName) -> Optional[TurnWorkspace]:
        """Time-travel: загрузка состояния ПОСЛЕ конкретной фазы."""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT workspace_json FROM turn_workspaces
                WHERE session_id = ? AND turn_id = ? AND phase = ?
            """, (session_id, turn_id, phase.value)).fetchone()
            
            if row:
                return TurnWorkspace.from_checkpoint_json(row["workspace_json"])
        return None

    def branch(self, session_id: str, turn_id: int, from_phase: PhaseName, new_turn_id: int) -> TurnWorkspace:
        """Ветвление состояния для what-if анализа."""
        workspace = self.load_at_phase(session_id, turn_id, from_phase)
        if not workspace:
            raise ValueError(f"Нет чекпоинта на фазе {from_phase.value}")
        
        workspace.turn_id = new_turn_id
        workspace.created_at = datetime.now()
        workspace.updated_at = datetime.now()
        workspace.current_phase = None
        
        self.save_after_phase(workspace, PhaseName.SAFETY)
        return workspace


class PostgresCheckpointer:
    """Фазово-ориентированный чекер на базе PostgreSQL (asyncpg) для продакшена."""

    def __init__(self, pool: Any):
        self.pool = pool

    @classmethod
    async def create(cls, dsn: str, min_size: int = 2, max_size: int = 10) -> "PostgresCheckpointer":
        import asyncpg
        pool = await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)
        await cls._init_schema(pool)
        return cls(pool)

    @staticmethod
    async def _init_schema(pool: Any) -> None:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS turn_workspaces (
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    workspace_json JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (session_id, turn_id, phase)
                );
                CREATE INDEX IF NOT EXISTS idx_turn_workspaces_session_turn 
                ON turn_workspaces (session_id, turn_id);

                CREATE TABLE IF NOT EXISTS conversation_workspaces (
                    session_id TEXT PRIMARY KEY,
                    workspace_json JSONB NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

    async def save_after_phase(self, workspace: TurnWorkspace, phase: PhaseName) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO turn_workspaces (session_id, turn_id, phase, workspace_json)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (session_id, turn_id, phase) DO UPDATE
                SET workspace_json = EXCLUDED.workspace_json, created_at = NOW()
            """, workspace.session_id, workspace.turn_id, phase.value, workspace.to_checkpoint_json())

    async def load_latest(self, session_id: str, turn_id: int) -> Optional[TurnWorkspace]:
        phase_priority = {
            PhaseName.SAVE_EPISODE.value: 16,
            PhaseName.EVALUATION.value: 15,
            PhaseName.REFLECTION.value: 14,
            PhaseName.TRUTH_LOOP.value: 13,
            PhaseName.GENERATE.value: 12,
            PhaseName.IDENTITY.value: 11,
            PhaseName.ROOTS.value: 10,
            PhaseName.PERSONA.value: 9,
            PhaseName.IMPULSE.value: 8,
            PhaseName.EMOTION.value: 7,
            PhaseName.SEMANTIC.value: 6,
            PhaseName.EPISODIC.value: 5,
            PhaseName.KNOWLEDGE_GRAPH.value: 4,
            PhaseName.RAG.value: 3,
            PhaseName.INTENT.value: 2,
            PhaseName.SAFETY.value: 1,
        }
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT phase, workspace_json FROM turn_workspaces
                WHERE session_id = $1 AND turn_id = $2
            """, session_id, turn_id)

            if not rows:
                return None

            best_row = max(rows, key=lambda r: phase_priority.get(r["phase"], 0))
            return TurnWorkspace.from_checkpoint_json(best_row["workspace_json"])

    async def load_at_phase(self, session_id: str, turn_id: int, phase: PhaseName) -> Optional[TurnWorkspace]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT workspace_json FROM turn_workspaces
                WHERE session_id = $1 AND turn_id = $2 AND phase = $3
            """, session_id, turn_id, phase.value)

            if row:
                return TurnWorkspace.from_checkpoint_json(row["workspace_json"])
        return None

    async def branch(self, session_id: str, turn_id: int, from_phase: PhaseName, new_turn_id: int) -> TurnWorkspace:
        workspace = await self.load_at_phase(session_id, turn_id, from_phase)
        if not workspace:
            raise ValueError(f"Нет чекпоинта на фазе {from_phase.value}")

        workspace.turn_id = new_turn_id
        workspace.created_at = datetime.now()
        workspace.updated_at = datetime.now()
        workspace.current_phase = None

        await self.save_after_phase(workspace, PhaseName.SAFETY)
        return workspace

    async def save_conversation(self, workspace: ConversationWorkspace) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversation_workspaces (session_id, workspace_json, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (session_id) DO UPDATE
                SET workspace_json = EXCLUDED.workspace_json, updated_at = NOW()
            """, workspace.core.session_id, workspace.model_dump_json())

    async def load_conversation(self, session_id: str) -> Optional[ConversationWorkspace]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT workspace_json FROM conversation_workspaces WHERE session_id = $1
            """, session_id)
            if row:
                return ConversationWorkspace.model_validate_json(row["workspace_json"])
        return None
