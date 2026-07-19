"""
⚠️ DEPRECATED — Используйте experiments/runner.py вместо этого модуля.

    python -m experiments.runner experiments/runs/my-config.json

Оставлен для обратной совместимости со старыми запусками.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.analysis import (
    analyze_keywords,
    compare_profiles,
    generate_report_md,
    ExperimentResult,
    ExperimentReport,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("padplus.impulse.research")

KEYWORD_DICTS = {
    "understand": {
        "words": [
            "понима", "анализ", "систем", "взаимосвяз", "причин", "суть",
            "фундаментальн", "структур", "глубин", "осознан", "смысл",
            "закономерност", "концепци", "парадигм", "теоретическ",
            "методологи", "рационал", "логик", "рефлекси", "познан",
        ],
        "label": "Понять",
    },
    "improve": {
        "words": [
            "улучш", "оптимизаци", "эффективн", "реформ", "прогресс",
            "инноваци", "решен", "практическ", "прикладн", "инструмент",
            "технологи", "модернизаци", "рационализаци", "усовершенствован",
            "внедрен", "алгоритм", "автоматизаци", "стандартизаци",
        ],
        "label": "Улучшить",
    },
    "protect": {
        "words": [
            "защит", "безопасн", "риск", "угроз", "предотврат", "стабильн",
            "границ", "контрол", "предосторож", "кризис", "катастроф",
            "хрупк", "уязвим", "необратим", "регулирован", "моратор",
            "сдержк", "ограничен", "консервативн",
        ],
        "label": "Защитить",
    },
    "create": {
        "words": [
            "созда", "нов", "возможн", "потенциал", "генерирова", "воображен",
            "будущ", "горизонт", "перспектив", "прорыв", "открыт",
            "творческ", "фантази", "эксперимент", "синтез", "эмерджент",
            "целостн", "интеграци", "трансформаци", "революци",
        ],
        "label": "Создать",
    },
}

PROFILE_LABELS = {
    "baseline": "Базовый",
    "understand": "Понять",
    "improve": "Улучшить",
    "protect": "Защитить",
    "create": "Создать",
}

Q1 = "Что сейчас является самой важной проблемой человечества?"
Q2 = "Какое направление исследований наиболее перспективно?"
Q3 = "Что такое сознание?"
Q4 = "Как принимать правильные решения в неопределённости?"
Q5 = "Если бы у тебя был один вопрос для исследования?"
Q6 = "Что важнее: понимать / изменять / защищать / создавать?"
Q7 = "Что человечество чаще всего упускает из виду?"

QUESTIONS = [Q1, Q2, Q3, Q4, Q5, Q6, Q7]

PROFILES = {
    "baseline": {"understand": 0, "improve": 0, "protect": 0, "create": 0},
    "understand": {"understand": 1, "improve": 0, "protect": 0, "create": 0},
    "improve": {"understand": 0, "improve": 1, "protect": 0, "create": 0},
    "protect": {"understand": 0, "improve": 0, "protect": 1, "create": 0},
    "create": {"understand": 0, "improve": 0, "protect": 0, "create": 1},
}


async def run_research(
    api_key: str,
    provider: str = "gigachat",
    model: Optional[str] = None,
    user_id: str = "research_harness",
) -> ExperimentReport:
    from core.pipeline import get_pipeline
    from core.impulse.manager import set_impulse

    os.environ.setdefault("USE_PG_STORAGE", "false")

    pipeline = get_pipeline()
    report = ExperimentReport(
        name="I-010: Impulse Research Report",
        description="Автоматический прогон 5 профилей × 7 вопросов",
        timestamp=datetime.now().isoformat(),
        provider=provider,
        model=model or provider,
        profiles_used=list(PROFILES.keys()),
    )

    for profile_name, weights in PROFILES.items():
        logger.info("Профиль: %s (%s)", profile_name, weights)
        set_impulse(weights)
        await asyncio.sleep(0.01)

        for i, question in enumerate(QUESTIONS, 1):
            logger.info("  Вопрос Q%d/%d", i, len(QUESTIONS))

            try:
                result = await pipeline.execute(
                    user_message=question,
                    context={"user_id": user_id},
                    api_key=api_key,
                    provider=provider,
                )
                resp_text = result.response if result.success and result.response else (result.response or "(empty)")
                if not result.success:
                    logger.warning("Pipeline не успешен: %s", result.errors)

                report.results.append(ExperimentResult(
                    profile=profile_name,
                    question_id=f"Q{i}",
                    question=question,
                    response=resp_text,
                    success=result.success,
                ))
            except Exception as e:
                logger.error("Ошибка: %s", e)
                report.results.append(ExperimentResult(
                    profile=profile_name,
                    question_id=f"Q{i}",
                    question=question,
                    response="",
                    success=False,
                    error=str(e),
                ))

    return report


def save_report(report: ExperimentReport, output_dir: str = "experiments/I-010") -> str:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    raw_path = out / "raw_responses.json"
    raw_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Сырые ответы: %s", raw_path)

    report_path = out / "REPORT.md"
    generate_report_md(report, str(report_path), KEYWORD_DICTS, PROFILE_LABELS)
    logger.info("Отчёт: %s", report_path)
    return str(report_path)


def main():
    parser = argparse.ArgumentParser(description="Impulse Research Harness")
    parser.add_argument("--api-key", required=True, help="API ключ провайдера")
    parser.add_argument("--provider", default="gigachat", choices=["gigachat", "openrouter"])
    parser.add_argument("--model", default=None, help="Модель (опционально)")
    parser.add_argument("--output", default="experiments/I-010")
    args = parser.parse_args()

    report = asyncio.run(run_research(
        api_key=args.api_key,
        provider=args.provider,
        model=args.model,
    ))
    save_report(report, args.output)
    print(f"\nГотово. Отчёт: {args.output}/REPORT.md")


if __name__ == "__main__":
    main()
