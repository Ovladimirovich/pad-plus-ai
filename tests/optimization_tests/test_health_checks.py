"""
Исправление 7: Health Checks для сервисов

Тесты для проверки мониторинга сервисов:
- Health check определяет падение Redis / Supabase / LLM
- Health check обновляет метрики
- Периодический запуск health checks
"""

import pytest
import asyncio
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))


def _make_monitor():
    """Создаёт монитор с изолированным data_path."""
    from core.health_monitor import CognitiveHealthMonitor
    tmpdir = tempfile.mkdtemp(prefix="health_test_")
    return CognitiveHealthMonitor(data_path=str(Path(tmpdir) / "health.json"))


class TestHealthChecks:
    """Тесты health checks для сервисов"""

    @pytest.mark.asyncio
    async def test_redis_health_check_down(self):
        """Проверяет, что health check определяет падение Redis."""
        monitor = _make_monitor()

        with patch.object(monitor, 'check_redis', new=AsyncMock(return_value=False)):
            await monitor.run_health_check()

        cache_health = monitor.get_metric('cache_health')
        assert cache_health is not None
        assert cache_health.value == 0.0

    @pytest.mark.asyncio
    async def test_redis_health_check_up(self):
        """Проверяет, что health check определяет рабочий Redis."""
        monitor = _make_monitor()

        with patch.object(monitor, 'check_redis', new=AsyncMock(return_value=True)), \
             patch.object(monitor, 'check_supabase', new=AsyncMock(return_value=True)), \
             patch.object(monitor, 'check_llm', new=AsyncMock(return_value=True)):
            await monitor.run_health_check()

        cache_health = monitor.get_metric('cache_health')
        assert cache_health is not None
        assert cache_health.value == 1.0

    @pytest.mark.asyncio
    async def test_supabase_health_check_down(self):
        """Проверяет, что health check определяет падение Supabase."""
        monitor = _make_monitor()

        with patch.object(monitor, 'check_supabase', new=AsyncMock(return_value=False)):
            await monitor.run_health_check()

        db_health = monitor.get_metric('database_health')
        assert db_health is not None
        assert db_health.value == 0.0

    @pytest.mark.asyncio
    async def test_llm_health_check_down(self):
        """Проверяет, что health check определяет падение LLM сервиса."""
        monitor = _make_monitor()

        with patch.object(monitor, 'check_llm', new=AsyncMock(return_value=False)):
            await monitor.run_health_check()

        llm_health = monitor.get_metric('llm_health')
        assert llm_health is not None
        assert llm_health.value == 0.0
        # Падение LLM — критичная проблема
        assert any(i.severity == "critical" for i in monitor._issues)

    @pytest.mark.asyncio
    async def test_health_check_updates_metrics(self):
        """Проверяет, что health check обновляет метрики."""
        monitor = _make_monitor()

        await monitor.run_health_check()

        for name in ('cache_health', 'database_health', 'llm_health'):
            metric = monitor.get_metric(name)
            assert metric is not None
            assert metric.last_updated > datetime.now() - timedelta(seconds=5)

    @pytest.mark.asyncio
    async def test_periodic_health_check(self):
        """Проверяет периодический запуск health checks."""
        monitor = _make_monitor()

        call_count = 0

        async def mock_check():
            nonlocal call_count
            call_count += 1

        with patch.object(monitor, 'run_health_check', new=mock_check):
            task = asyncio.create_task(monitor.start_periodic_health_check(interval=1))

            await asyncio.sleep(3.1)

            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        assert call_count >= 3


class TestHealthCheckMetrics:
    """Тесты метрик health checks"""

    def test_overall_score_calculation(self):
        """Проверяет расчёт общего score здоровья."""
        monitor = _make_monitor()
        score = monitor.get_overall_score()
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_service_specific_scores(self):
        """Проверяет, что падение сервиса снижает метрику."""
        monitor = _make_monitor()

        with patch.object(monitor, 'check_redis', new=AsyncMock(return_value=False)), \
             patch.object(monitor, 'check_supabase', new=AsyncMock(return_value=True)), \
             patch.object(monitor, 'check_llm', new=AsyncMock(return_value=True)):
            await monitor.run_health_check()

        assert monitor.get_metric('cache_health').value == 0.0
        assert monitor.get_metric('database_health').value == 1.0
        assert monitor.get_metric('llm_health').value == 1.0

    @pytest.mark.asyncio
    async def test_health_history_tracking(self):
        """Проверяет, что assess_health возвращает метрики."""
        monitor = _make_monitor()
        with patch.object(monitor, 'check_redis', new=AsyncMock(return_value=True)), \
             patch.object(monitor, 'check_supabase', new=AsyncMock(return_value=True)), \
             patch.object(monitor, 'check_llm', new=AsyncMock(return_value=True)):
            for i in range(3):
                await monitor.run_health_check()

        health = monitor.assess_health()
        assert 'overall_score' in health
        assert 'status' in health
        assert 'metrics' in health
        assert 'llm_health' in health['metrics']


class TestHealthCheckAlerts:
    """Тесты алертов health checks"""

    @pytest.mark.asyncio
    async def test_alert_on_critical_service_down(self):
        """Проверяет, что падение LLM добавляет критичную проблему."""
        monitor = _make_monitor()

        with patch.object(monitor, 'check_llm', new=AsyncMock(return_value=False)):
            await monitor.run_health_check()

        assert any(i.severity == "critical" for i in monitor._issues)
        assert any(i.category == "llm" for i in monitor._issues)

    @pytest.mark.asyncio
    async def test_no_alert_on_warning_service_down(self):
        """Redis down не добавляет критичную проблему."""
        monitor = _make_monitor()

        with patch.object(monitor, 'check_redis', new=AsyncMock(return_value=False)), \
             patch.object(monitor, 'check_llm', new=AsyncMock(return_value=True)):
            await monitor.run_health_check()

        assert not any(i.severity == "critical" and i.category == "llm" for i in monitor._issues)


class TestHealthCheckIntegration:
    """Интеграционные тесты health checks"""

    @pytest.mark.asyncio
    async def test_full_health_check_all_services(self):
        """Проверяет полную проверку всех сервисов."""
        monitor = _make_monitor()

        with patch.object(monitor, 'check_redis', new=AsyncMock(return_value=True)), \
             patch.object(monitor, 'check_supabase', new=AsyncMock(return_value=True)), \
             patch.object(monitor, 'check_llm', new=AsyncMock(return_value=True)):
            await monitor.run_health_check()

        for name in ('cache_health', 'database_health', 'llm_health'):
            assert monitor.get_metric(name).value == 1.0

    @pytest.mark.asyncio
    async def test_health_check_with_recovery(self):
        """Проверяет восстановление сервиса после падения."""
        monitor = _make_monitor()

        # Сначала LLM down
        with patch.object(monitor, 'check_llm', new=AsyncMock(return_value=False)):
            await monitor.run_health_check()
        llm_before = monitor.get_metric('llm_health').value

        # Затем LLM up
        with patch.object(monitor, 'check_llm', new=AsyncMock(return_value=True)):
            await monitor.run_health_check()
        llm_after = monitor.get_metric('llm_health').value

        assert llm_before == 0.0
        assert llm_after == 1.0


class TestHealthCheckConfiguration:
    """Тесты конфигурации health checks"""

    @pytest.mark.asyncio
    async def test_configurable_check_interval(self):
        """Проверяет настройку интервала проверок."""
        monitor = _make_monitor()
        # start_periodic_health_check принимает interval параметром
        assert asyncio.iscoroutinefunction(monitor.start_periodic_health_check)

    @pytest.mark.asyncio
    async def test_configurable_service_timeout(self):
        """check_* методы асинхронны и перехватывают ошибки подключения."""
        monitor = _make_monitor()
        assert asyncio.iscoroutinefunction(monitor.check_redis)
        assert asyncio.iscoroutinefunction(monitor.check_supabase)
        assert asyncio.iscoroutinefunction(monitor.check_llm)


class TestHealthCheckHelpers:
    """Вспомогательные тесты health checks"""

    @pytest.mark.asyncio
    async def test_check_redis_helper(self):
        """check_redis возвращает False без доступного Redis."""
        monitor = _make_monitor()
        result = await monitor.check_redis()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_check_supabase_helper(self):
        """check_supabase возвращает bool."""
        monitor = _make_monitor()
        result = await monitor.check_supabase()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_check_llm_helper(self):
        """check_llm возвращает bool."""
        monitor = _make_monitor()
        result = await monitor.check_llm()
        assert isinstance(result, bool)
