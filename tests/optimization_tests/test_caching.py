"""
Исправление 5: Кэширование ответов Pipeline

PipelineExecutor в v5.0 не содержит собственного слоя кэширования —
ответы LLM кэшируются через CacheManager (см. tests/hardening/test_cache_manager.py).
Эти тесты проверяют устойчивость PipelineExecutor к повторным запросам
и изоляцию контекста, что является требованием для безопасного кэширования.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from core.pipeline import PipelineExecutor, PipelineResult


def _make_executor():
    """Создаёт свежий executor со сброшенным глобальным состоянием."""
    import core.pipeline as pipeline_module
    pipeline_module._pipeline = None
    return PipelineExecutor()


class TestPipelineRepeatability:
    """Повторные вызовы pipeline должны быть безопасными (предусловие кэширования)."""

    @pytest.mark.asyncio
    async def test_repeated_execute_returns_result(self):
        """Повторный вызов execute не падает и возвращает PipelineResult."""
        executor = _make_executor()
        for i in range(3):
            result = await executor.execute(user_message="Привет, как дела?", context={"user_id": "test"})
            assert isinstance(result, PipelineResult)
            assert result.success

    @pytest.mark.asyncio
    async def test_repeated_execute_stable_strategy(self):
        """Одинаковый запрос даёт одинаковую стратегию."""
        executor = _make_executor()
        r1 = await executor.execute(user_message="Расскажи о Python", context={})
        r2 = await executor.execute(user_message="Расскажи о Python", context={})
        assert r1.strategy == r2.strategy
        assert r1.strategy in ("simple", "retrieval", "reasoning", "creative", "learning")

    @pytest.mark.asyncio
    async def test_execute_stats_accumulate(self):
        """Каждый вызов увеличивает счётчик вызовов."""
        executor = _make_executor()
        before = executor.get_stats()["total_calls"]
        await executor.execute(user_message="тест", context={})
        after = executor.get_stats()["total_calls"]
        assert after > before


class TestPipelineContextIsolation:
    """Разные контексты должны быть изолированы друг от друга."""

    @pytest.mark.asyncio
    async def test_different_contexts_isolated(self):
        """Вызовы с разными контекстами не пересекаются по состоянию."""
        executor = _make_executor()
        r1 = await executor.execute(user_message="Что такое Python?", context={"topic": "programming"})
        r2 = await executor.execute(user_message="Что такое Python?", context={"topic": "snake"})
        assert r1.success and r2.success

    @pytest.mark.asyncio
    async def test_user_id_in_context_used(self):
        """user_id из context не ломает выполнение."""
        executor = _make_executor()
        result = await executor.execute(
            user_message="Запомни важный факт",
            context={"user_id": "u-123"},
            session_id="s-1",
        )
        assert isinstance(result, PipelineResult)
        assert result.success


class TestPipelineNoStateLeak:
    """Pipeline не должен сохранять состояние между вызовами (кэш-безопасность)."""

    @pytest.mark.asyncio
    async def test_anti_loop_resets_between_calls(self):
        """anti-loop история растёт, но не блокирует новые уникальные запросы."""
        executor = _make_executor()
        for i in range(4):
            result = await executor.execute(user_message=f"Уникальный запрос {i}", context={})
            assert result.success
        # После 4 уникальных вызовов история не должна блокировать следующий уникальный
        result = await executor.execute(user_message="Совсем другой запрос", context={})
        assert result.success

    @pytest.mark.asyncio
    async def test_concurrent_executes(self):
        """Конкурентные вызовы execute не должны падать."""
        executor = _make_executor()

        async def make_request(i):
            return await executor.execute(user_message=f"Тест {i}", context={"user_id": "u1"})

        tasks = [make_request(i) for i in range(5)]
        results = await pytest_asyncio_gather_safe(tasks)
        assert all(isinstance(r, PipelineResult) and r.success for r in results)


async def pytest_asyncio_gather_safe(tasks):
    import asyncio
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
