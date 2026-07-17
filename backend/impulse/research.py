"""
P3 — Research harness for Impulse validation.

Запускает PipelineExecutor с 5 профилями импульсов на 7 стандартных вопросах,
собирает ответы и сравнивает effect-size между профилями.

Использование:
    python -m backend.impulse.research --api-key "client_id:secret" --provider gigachat
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

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("padplus.impulse.research")


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


@dataclass
class ResearchResult:
    """Результат одного прогона (профиль + вопрос)"""
    profile: str
    question: str
    response: str
    success: bool
    error: Optional[str] = None


@dataclass
class ResearchReport:
    """Полный отчёт исследования"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    provider: str = ""
    model: str = ""
    results: List[ResearchResult] = field(default_factory=list)
    profiles_used: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model": self.model,
            "profiles_used": self.profiles_used,
            "results": [
                {
                    "profile": r.profile,
                    "question": r.question[:60],
                    "response": r.response,
                    "success": r.success,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


async def run_research(
    api_key: str,
    provider: str = "gigachat",
    model: Optional[str] = None,
    user_id: str = "research_harness",
) -> ResearchReport:
    """Запускает исследование: все профили × все вопросы."""
    from core.pipeline import get_pipeline
    from core.impulse.manager import set_impulse, set_impulse_by_question

    os.environ.setdefault("USE_PG_STORAGE", "false")

    pipeline = get_pipeline()
    report = ResearchReport(provider=provider, model=model or provider)
    report.profiles_used = list(PROFILES.keys())

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
                if result.success and result.response:
                    resp_text = result.response
                else:
                    resp_text = result.response or "(empty)"
                    if not result.success:
                        logger.warning("Pipeline не успешен: %s", result.errors)

                report.results.append(ResearchResult(
                    profile=profile_name,
                    question=question,
                    response=resp_text,
                    success=result.success,
                ))
            except Exception as e:
                logger.error("Ошибка: %s", e)
                report.results.append(ResearchResult(
                    profile=profile_name,
                    question=question,
                    response="",
                    success=False,
                    error=str(e),
                ))

    return report


def save_report(report: ResearchReport, output_dir: str = "experiments/I-010") -> str:
    """Сохраняет сырые ответы и генерирует отчёт."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    raw_path = out / "raw_responses.json"
    raw_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Сырые ответы: %s", raw_path)

    report_path = out / "REPORT.md"
    lines = [
        f"# I-010: Impulse Research Report",
        f"",
        f"**Дата:** {report.timestamp}",
        f"**Провайдер:** {report.provider}",
        f"**Модель:** {report.model}",
        f"**Профили:** {', '.join(report.profiles_used)}",
        f"",
        f"## Результаты",
        f"",
        f"| Профиль | Вопрос | Успех | Длина ответа |",
        f"|---------|--------|-------|-------------|",
    ]
    for r in report.results:
        q_short = r.question[:50].replace("|", "/")
        status = "✅" if r.success else "❌"
        lines.append(f"| {r.profile} | {q_short} | {status} | {len(r.response)} |")

    lines.extend([
        f"",
        f"## Сводка",
        f"",
        f"- Всего прогонов: {len(report.results)}",
        f"- Успешных: {sum(1 for r in report.results if r.success)}",
        f"- Ошибок: {sum(1 for r in report.results if not r.success)}",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
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
