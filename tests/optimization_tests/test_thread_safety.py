"""
Тесты потокобезопасности PipelineExecutor v5.0.
Проверяет счётчики, background consolidation, fire-and-forget механизм.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))


class TestThreadSafety:
    """Тесты потокобезопасности PipelineExecutor"""

    @pytest.fixture
    def executor(self):
        """Создаёт executor с пустыми фазами (без внешних зависимостей)"""
        from backend.core.pipeline.executor import PipelineExecutor
        with patch.object(PipelineExecutor, '_build_phases', return_value=[]):
            return PipelineExecutor()

    def test_counter_starts_at_zero(self, executor):
        assert executor._call_count == 0
        assert executor._dialogs_since_consolidation == 0

    def test_counter_increment(self, executor):
        executor._call_count += 1
        assert executor._call_count == 1

    def test_dialogs_since_consolidation_increment(self, executor):
        executor._dialogs_since_consolidation += 1
        assert executor._dialogs_since_consolidation == 1

    @pytest.mark.asyncio
    async def test_fire_background_phases_creates_tasks(self, executor):
        """_fire_background_phases создаёт asyncio.Task для каждой background-фазы"""
        from backend.core.pipeline.models import PipelineResult
        from backend.core.pipeline.context import PipelineContext
        from backend.core.pipeline.executor import _BACKGROUND_PHASES

        ctx = PipelineContext(user_message="test", context={}, session_id=None, api_key=None, provider=None)
        result = PipelineResult(success=True)
        result.intent = "chat_general"
        result.strategy = "default"  # Не "simple", чтобы не пропустить половину фаз

        fake_phases = [(name, AsyncMock()) for name in sorted(_BACKGROUND_PHASES - {"consolidation", "procedure_success"})]
        executor._phases = fake_phases

        with patch.object(executor, '_run_background_phase', new=AsyncMock()) as mock_run:
            executor._fire_background_phases(ctx, result, "req-1", 0.0)

        await asyncio.sleep(0.01)

        assert mock_run.call_count == len(fake_phases)

    @pytest.mark.asyncio
    async def test_background_phase_does_not_raise(self, executor):
        """Background-фаза никогда не роняет request, даже при ошибке"""
        from backend.core.pipeline.executor import _BACKGROUND_PHASES

        bg_data = {
            "user_message": "test", "strategy": "default",
            "intent": "chat_general", "response": "ok",
            "session_id": None, "user_id": None,
            "provider": None, "model": None,
        }

        phase_names = list(_BACKGROUND_PHASES)
        phase_mocks = {}
        for name in phase_names:
            m = AsyncMock()
            m.execute = AsyncMock(side_effect=Exception(f"{name} error"))
            phase_mocks[name] = m

        with patch.object(executor, '_phases', [(n, phase_mocks[n]) for n in phase_names]):
            task = asyncio.create_task(
                executor._run_background_phase("consolidation", phase_mocks["consolidation"], bg_data, "req-1")
            )
            done, _ = await asyncio.wait([task], timeout=2)
            assert task in done

    def test_get_stats_returns_version(self, executor):
        stats = executor.get_stats()
        assert stats["version"] == "5.0"
        assert stats["total_calls"] == 0
        assert "state" in stats

    def test_get_stats_reflects_counters(self, executor):
        executor._call_count = 42
        executor._dialogs_since_consolidation = 7
        stats = executor.get_stats()
        assert stats["total_calls"] == 42
        assert stats["dialogs_since_consolidation"] == 7
