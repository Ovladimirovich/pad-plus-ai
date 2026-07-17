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
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("padplus.impulse.research")

# Ключевые слова для каждого измерения импульса (русский язык)
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

# Короткие метки для таблиц
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


def analyze_keywords(responses: List[ResearchResult]) -> dict:
    """Подсчитывает частоту ключевых слов по профилям и измерениям."""
    from collections import Counter
    profile_scores: dict[str, dict[str, float]] = {}

    for profile in set(r.profile for r in responses):
        profile_texts = [r.response.lower() for r in responses if r.profile == profile and r.success]
        full_text = " ".join(profile_texts)
        scores = {}
        for dim_key, dim_data in KEYWORD_DICTS.items():
            matches = sum(
                1 for w in dim_data["words"]
                if w in full_text
            )
            scores[dim_key] = matches
            scores[f"{dim_key}_label"] = dim_data["label"]
        profile_scores[profile] = scores

    return profile_scores


def compare_profiles(profile_scores: dict[str, dict]) -> list[dict]:
    """Сравнивает каждый профиль с baseline."""
    baseline = profile_scores.get("baseline", {})
    comparisons = []
    dimensions = [k for k in KEYWORD_DICTS.keys()]

    for profile, scores in profile_scores.items():
        if profile == "baseline":
            continue
        deltas = {}
        for dim in dimensions:
            base_val = baseline.get(dim, 0) or 0
            prof_val = scores.get(dim, 0) or 0
            delta = prof_val - base_val
            deltas[dim] = {
                "baseline": base_val,
                "profile": prof_val,
                "delta": delta,
                "direction": "+" if delta > 0 else ("-" if delta < 0 else "="),
            }
        comparisons.append({
            "profile": profile,
            "label": PROFILE_LABELS.get(profile, profile),
            "deltas": deltas,
        })
    return comparisons


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
        f"## Сырые результаты",
        f"",
        f"| Профиль | Вопрос | Успех | Длина ответа |",
        f"|---------|--------|-------|-------------|",
    ]
    for r in report.results:
        q_short = r.question[:50].replace("|", "/")
        status = "✅" if r.success else "❌"
        lines.append(f"| {PROFILE_LABELS.get(r.profile, r.profile)} | {q_short} | {status} | {len(r.response)} |")

    lines.extend([
        f"",
        f"## Сводка",
        f"",
        f"- Всего прогонов: {len(report.results)}",
        f"- Успешных: {sum(1 for r in report.results if r.success)}",
        f"- Ошибок: {sum(1 for r in report.results if not r.success)}",
    ])

    # Keyword frequency analysis
    profile_scores = analyze_keywords(report.results)
    comparisons = compare_profiles(profile_scores)

    lines.extend([
        f"",
        f"## Keyword Frequency Analysis",
        f"",
        f"Подсчёт вхождений ключевых слов из словарей каждого измерения.",
        f"",
    ])

    # Table: absolute scores per profile
    dimensions = list(KEYWORD_DICTS.keys())
    headers = ["Профиль"] + [KEYWORD_DICTS[d]["label"] for d in dimensions]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for profile in report.profiles_used:
        scores = profile_scores.get(profile, {})
        row = [PROFILE_LABELS.get(profile, profile)]
        for d in dimensions:
            row.append(str(scores.get(d, 0)))
        lines.append("| " + " | ".join(row) + " |")

    # Table: delta from baseline
    lines.extend([
        f"",
        f"### Delta от Baseline",
        f"",
        f"Разница в частоте ключевых слов относительно базового профиля.",
        f"",
    ])
    delta_headers = ["Профиль"] + [f"{KEYWORD_DICTS[d]['label']} (Δ)" for d in dimensions]
    lines.append("| " + " | ".join(delta_headers) + " |")
    lines.append("|" + "|".join("---" for _ in delta_headers) + "|")
    for comp in comparisons:
        row = [comp["label"]]
        for d in dimensions:
            delta = comp["deltas"].get(d, {})
            d_val = delta.get("delta", 0)
            sign = "+" if d_val > 0 else ""
            row.append(f"{sign}{d_val}")
        lines.append("| " + " | ".join(row) + " |")

    # Interpretation
    lines.extend([
        f"",
        f"### Интерпретация",
        f"",
    ])
    for comp in comparisons:
        strongest = max(comp["deltas"].items(), key=lambda x: x[1]["delta"])
        dim_name = KEYWORD_DICTS[strongest[0]]["label"]
        delta_val = strongest[1]["delta"]
        direction = "выше" if delta_val > 0 else "ниже"
        lines.append(
            f"- **{comp['label']}**: наибольший сдвиг в «{dim_name}» "
            f"({direction} на {abs(delta_val)} слов)"
        )

    lines.extend([
        f"",
        f"### Effect-size (суммарный |Δ|)",
        f"",
    ])
    es_rows = []
    for comp in comparisons:
        total_delta = sum(abs(d["delta"]) for d in comp["deltas"].values())
        es_rows.append((comp["label"], total_delta))
    es_rows.sort(key=lambda x: x[1], reverse=True)
    for label, total in es_rows:
        bars = "█" * min(total, 40)
        lines.append(f"- {label}: {total} {bars}")

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
