"""
P3 — Impulse Research Harness test.

Запускается только с @pytest.mark.impulse_research (НЕ в default CI).
Требует реальный API-ключ.

Использование:
    pytest tests/impulse_research.py -m impulse_research --api-key "client_id:secret"
"""

import pytest
import os


@pytest.mark.impulse_research
@pytest.mark.asyncio
async def test_research_harness_runs():
    """Проверяет, что research harness запускается и возвращает отчёт."""
    api_key = os.environ.get("RESEARCH_API_KEY") or os.environ.get("GIGACHAT_API_KEY")
    if not api_key:
        pytest.skip("Нет RESEARCH_API_KEY или GIGACHAT_API_KEY в окружении")

    from backend.impulse.research import run_research

    report = await run_research(
        api_key=api_key,
        provider="gigachat",
        model="GigaChat",
    )

    assert report is not None
    assert len(report.results) == 35  # 5 profiles × 7 questions
    assert report.provider == "gigachat"
