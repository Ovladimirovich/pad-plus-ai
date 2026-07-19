from typing import Dict, List
from dataclasses import dataclass, field


@dataclass
class ExperimentResult:
    profile: str
    question_id: str
    question: str
    response: str
    success: bool
    error: str = ""


@dataclass
class ExperimentReport:
    name: str
    description: str
    timestamp: str
    provider: str
    model: str
    profiles_used: List[str]
    results: List[ExperimentResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model": self.model,
            "profiles_used": self.profiles_used,
            "results": [
                {
                    "profile": r.profile,
                    "question_id": r.question_id,
                    "question": r.question[:60],
                    "response": r.response,
                    "success": r.success,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


def analyze_keywords(
    results: List[ExperimentResult],
    keyword_dicts: Dict[str, dict],
) -> Dict[str, dict]:
    profile_scores: dict[str, dict[str, float]] = {}
    for profile in set(r.profile for r in results):
        profile_texts = [
            r.response.lower()
            for r in results
            if r.profile == profile and r.success
        ]
        full_text = " ".join(profile_texts)
        scores = {}
        for dim_key, dim_data in keyword_dicts.items():
            matches = sum(1 for w in dim_data["words"] if w in full_text)
            scores[dim_key] = matches
            scores[f"{dim_key}_label"] = dim_data["label"]
        profile_scores[profile] = scores
    return profile_scores


def compare_profiles(
    profile_scores: Dict[str, dict],
    profile_labels: Dict[str, str],
    keyword_dicts: Dict[str, dict],
) -> List[dict]:
    baseline = profile_scores.get("baseline", {})
    comparisons = []
    dimensions = [k for k in keyword_dicts.keys()]

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
            "label": profile_labels.get(profile, profile),
            "deltas": deltas,
        })
    return comparisons


def generate_report_md(
    report: ExperimentReport,
    output_path: str,
    keyword_dicts: Dict[str, dict],
    profile_labels: Dict[str, str],
) -> str:
    profile_scores = analyze_keywords(report.results, keyword_dicts)
    comparisons = compare_profiles(profile_scores, profile_labels, keyword_dicts)
    dimensions = list(keyword_dicts.keys())

    lines = [
        f"# {report.name}",
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
        lines.append(
            f"| {profile_labels.get(r.profile, r.profile)} | "
            f"{q_short} | {status} | {len(r.response)} |"
        )

    lines.extend([
        f"",
        f"## Сводка",
        f"",
        f"- Всего прогонов: {len(report.results)}",
        f"- Успешных: {sum(1 for r in report.results if r.success)}",
        f"- Ошибок: {sum(1 for r in report.results if not r.success)}",
        f"",
        f"## Keyword Frequency Analysis",
        f"",
        f"Подсчёт вхождений ключевых слов из словарей каждого измерения.",
        f"",
    ])

    headers = ["Профиль"] + [keyword_dicts[d]["label"] for d in dimensions]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for profile in report.profiles_used:
        scores = profile_scores.get(profile, {})
        row = [profile_labels.get(profile, profile)]
        for d in dimensions:
            row.append(str(scores.get(d, 0)))
        lines.append("| " + " | ".join(row) + " |")

    lines.extend([
        f"",
        f"### Delta от Baseline",
        f"",
        f"Разница в частоте ключевых слов относительно базового профиля.",
        f"",
    ])
    delta_headers = ["Профиль"] + [
        f"{keyword_dicts[d]['label']} (Δ)" for d in dimensions
    ]
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

    lines.extend([
        f"",
        f"### Интерпретация",
        f"",
    ])
    for comp in comparisons:
        strongest = max(comp["deltas"].items(), key=lambda x: x[1]["delta"])
        dim_name = keyword_dicts[strongest[0]]["label"]
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

    text = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return text
