"""
Тесты для ConversationWorkspace и стека целей (Phase D'-2).
"""

import pytest
from backend.core.workspace.schemas import ConversationWorkspace, ConversationCore
from backend.core.workspace.checkpointer import SQLiteCheckpointer


def test_conversation_goals_stack():
    conv = ConversationWorkspace(
        core=ConversationCore(session_id="sess-1", dialog_id="diag-1")
    )
    
    # Добавление хода
    conv.add_turn(1, "Расскажи про квантовую физику", "physics")
    assert conv.core.turn_count == 1
    assert conv.core.current_topic == "physics"
    assert len(conv.core.topic_stack) == 1

    # Добавление цели
    goal = conv.push_goal("Объяснить суперпозицию", turn_id=1)
    assert len(conv.core.active_goals) == 1
    assert goal.status == "active"

    # Приостановка цели (suspend)
    assert conv.suspend_goal(goal.id, turn_id=2) is True
    assert len(conv.core.active_goals) == 0
    assert len(conv.core.suspended_goals) == 1
    assert conv.core.suspended_goals[0].status == "suspended"

    # Возобновление цели (resume)
    assert conv.resume_goal(goal.id) is True
    assert len(conv.core.active_goals) == 1
    assert len(conv.core.suspended_goals) == 0
    assert conv.core.active_goals[0].status == "active"


def test_conversation_persistence_sqlite():
    cp = SQLiteCheckpointer(":memory:")
    
    conv = ConversationWorkspace(
        core=ConversationCore(
            session_id="persist-sess",
            dialog_id="diag-persist",
            entities={"Python": "Язык программирования"}
        )
    )
    # Добавление цели
    goal = conv.push_goal("Изучить FastAPI", turn_id=1)
    conv.add_fact("FastAPI быстрый")

    # Сохранение
    cp.save_conversation(conv)

    # Загрузка
    loaded = cp.load_conversation("persist-sess")
    assert loaded is not None
    assert loaded.core.dialog_id == "diag-persist"
    assert "Python" in loaded.core.entities
    assert "FastAPI быстрый" in loaded.core.key_facts
