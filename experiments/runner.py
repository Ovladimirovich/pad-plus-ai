#!/usr/bin/env python3
"""
Experiment Runner — запускает эксперименты по JSON-конфигу.

Использование:
    python -m experiments.runner config.json
    python -m experiments.runner config.json --output experiments/runs/my-run

Конфиг: templates/experiment_config.json
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger("padplus.experiments.runner")

# Добавляем backend в path для импорта
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR.parent))
sys.path.insert(0, str(BACKEND_DIR))


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_experiment(config: dict) -> "ExperimentReport":
    from experiments.analysis import ExperimentReport, ExperimentResult
    from core.pipeline import get_pipeline
    from core.impulse.manager import set_impulse

    use_pg = config.get("use_pg_storage", False)
    os.environ.setdefault("USE_PG_STORAGE", str(use_pg).lower())

    pipeline = get_pipeline()
    provider = config.get("provider", "gigachat")
    model = config.get("model")
    user_id = config.get("user_id", "research_harness")
    profiles = config.get("profiles", {})
    questions = config.get("questions", [])
    api_key = config.get("api_key") or os.getenv("API_KEY", "")

    report = ExperimentReport(
        name=config.get("name", "Безымянный эксперимент"),
        description=config.get("description", ""),
        timestamp=datetime.now().isoformat(),
        provider=provider,
        model=model or provider,
        profiles_used=list(profiles.keys()),
    )

    for profile_name, weights in profiles.items():
        logger.info("Профиль: %s (%s)", profile_name, weights)
        set_impulse(weights)
        await asyncio.sleep(0.01)

        for q in questions:
            qid = q.get("id", "?")
            question = q.get("text", "")
            logger.info("  Вопрос %s/%d", qid, len(questions))

            try:
                result = await pipeline.execute(
                    user_message=question,
                    context={"user_id": user_id},
                    api_key=api_key or None,
                    provider=provider,
                )
                if result.success and result.response:
                    resp_text = result.response
                else:
                    resp_text = result.response or "(empty)"
                    if not result.success:
                        logger.warning("Pipeline не успешен: %s", result.errors)

                report.results.append(ExperimentResult(
                    profile=profile_name,
                    question_id=qid,
                    question=question,
                    response=resp_text,
                    success=result.success,
                ))
            except Exception as e:
                logger.error("Ошибка: %s", e)
                report.results.append(ExperimentResult(
                    profile=profile_name,
                    question_id=qid,
                    question=question,
                    response="",
                    success=False,
                    error=str(e),
                ))

    return report


def save_results(report: "ExperimentReport", config: dict, output_dir: str):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    raw_path = out / "raw_responses.json"
    raw_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Сырые ответы: %s", raw_path)

    # Копируем конфиг для воспроизводимости
    config_path = out / "experiment_config.json"
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Конфиг сохранён: %s", config_path)

    # Генерируем отчёт
    from experiments.analysis import generate_report_md

    keyword_dicts = config.get("keyword_dicts", {})
    profile_labels = config.get("profile_labels", {})
    report_path = out / "REPORT.md"
    generate_report_md(report, str(report_path), keyword_dicts, profile_labels)
    logger.info("Отчёт: %s", report_path)

    return str(report_path)


def _compare(args):
    from backend.evals.comparator import compare_runs

    run_a = Path(args.compare[0])
    run_b = Path(args.compare[1])

    with open(run_a / "raw_responses.json", "r", encoding="utf-8") as f:
        data_a = json.load(f)
    with open(run_b / "raw_responses.json", "r", encoding="utf-8") as f:
        data_b = json.load(f)

    output_dir = f'experiments/reports/comparison-{datetime.now().strftime("%Y-%m-%d")}'
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    reports = []
    profiles_a = {r["profile"]: r for r in data_a.get("results", [])}
    profiles_b = {r["profile"]: r for r in data_b.get("results", [])}

    for profile in set(list(profiles_a.keys()) + list(profiles_b.keys())):
        if profile not in profiles_a or profile not in profiles_b:
            continue
        comp = compare_runs(
            baseline=profiles_a[profile],
            treatment=profiles_b[profile],
            baseline_name=run_a.name,
            treatment_name=run_b.name,
        )
        comp.timestamp = data_a.get("timestamp", datetime.now().isoformat())
        path = comp.save(f"{output_dir}/{profile}-comparison.md")
        reports.append(path)
        print(f"  {profile}: {path}")

    print(f"\nСравнение готово. Отчёты в {output_dir}/")


def main():
    parser = argparse.ArgumentParser(description="PAD+ Experiment Runner")
    parser.add_argument("config", nargs="?", help="Путь к JSON-конфигу эксперимента")
    parser.add_argument("--output", "-o", help="Директория для результатов")
    parser.add_argument("--api-key", help="API ключ провайдера (переопределяет конфиг)")
    parser.add_argument("--compare", nargs=2, metavar=("RUN_A", "RUN_B"),
                        help="Сравнить два completed run'а")
    args = parser.parse_args()

    if args.compare:
        _compare(args)
        return

    if not args.config:
        parser.print_help()
        return

    config = load_config(args.config)

    if args.api_key:
        config["api_key"] = args.api_key

    output_dir = args.output or config.get(
        "output_dir",
        f'experiments/runs/{datetime.now().strftime("%Y-%m-%d")}-{config.get("name", "run")[:20]}',
    )

    report = asyncio.run(run_experiment(config))
    report_path = save_results(report, config, output_dir)
    print(f"\nГотово. Отчёт: {report_path}")


if __name__ == "__main__":
    main()
