"""
Интеграционный слой для подключения Composite Cognitive Workspace к текущему пайплайну (D'-5).
"""

import logging
from typing import Optional, Any
from .schemas import TurnWorkspace, ConversationWorkspace, ConversationCore, PhaseName
from .checkpointer import SQLiteCheckpointer
from .reflection import ReflectionEngine

logger = logging.getLogger("padplus.workspace.integration")


class WorkspaceOrchestrator:
    """Оркестратор воркспейса для интеграции в PipelineExecutor."""

    def __init__(self, checkpointer: Optional[SQLiteCheckpointer] = None):
        # По умолчанию используем локальный SQLite для воркспейса
        self.checkpointer = checkpointer or SQLiteCheckpointer("data/workspace.db")

    def init_turn(self, session_id: str, turn_id: int, user_message: str) -> TurnWorkspace:
        """Инициализирует воркспейс для нового хода."""
        workspace = TurnWorkspace(
            session_id=session_id,
            turn_id=turn_id,
            user_message=user_message
        )
        return workspace

    def checkpoint_phase(self, workspace: TurnWorkspace, phase_str: str, output: Any) -> None:
        """Обновляет состояние фазы и сохраняет чекпоинт."""
        try:
            phase_enum = PhaseName(phase_str)
        except ValueError:
            # Если фаза кастомная/не входит в базовый enum
            return

        workspace.update_phase(phase_enum, output)
        self.checkpointer.save_after_phase(workspace, phase_enum)

    def run_reflection(self, workspace: TurnWorkspace) -> dict:
        """Запускает движок рефлексии."""
        result = ReflectionEngine.reflect_on_turn(workspace)
        self.checkpointer.save_after_phase(workspace, PhaseName.REFLECTION)
        return result

    def get_or_create_conversation(self, session_id: str, dialog_id: str = "default") -> ConversationWorkspace:
        """Загружает или создаёт сессионный воркспейс (ConversationWorkspace)."""
        conv = self.checkpointer.load_conversation(session_id)
        if not conv:
            conv = ConversationWorkspace(
                core=ConversationCore(session_id=session_id, dialog_id=dialog_id)
            )
            self.checkpointer.save_conversation(conv)
        return conv

    def save_conversation(self, conv: ConversationWorkspace) -> None:
        """Сохраняет сессионный воркспейс."""
        self.checkpointer.save_conversation(conv)
