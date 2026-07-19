import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RunComparison:
    baseline_name: str
    treatment_name: str
    metrics: Dict[str, dict] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_metric(self, name: str, baseline: float, treatment: float) -> None:
        delta = treatment - baseline
        pct = (delta / baseline * 100) if baseline != 0 else float("inf")
        improvement = "better" if delta > 0 else ("worse" if delta < 0 else "same")
        self.metrics[name] = {
            "baseline": round(baseline, 3),
            "treatment": round(treatment, 3),
            "delta": round(delta, 3),
            "pct_change": round(pct, 1),
            "direction": improvement,
        }

    def to_dict(self) -> dict:
        return {
            "comparison": {
                "baseline": self.baseline_name,
                "treatment": self.treatment_name,
            },
            "metrics": self.metrics,
            "timestamp": self.timestamp,
        }

    def to_markdown(self) -> str:
        lines = [
            f"# Сравнение: {self.baseline_name} vs {self.treatment_name}",
            f"",
            f"**Дата:** {self.timestamp}",
            f"",
            f"| Метрика | Baseline | Treatment | Delta | Delta% |",
            f"|---------|----------|-----------|-------|--------|",
        ]
        for name, m in self.metrics.items():
            lines.append(
            f"| {name} | {m['baseline']} | {m['treatment']} | "
            f"{m['delta']:+.3f} | {m['pct_change']:+.1f}% |"
            )
        return "\n".join(lines)

    def save(self, path: str) -> str:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)

        with open(out, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())

        json_path = out.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        return str(out)


def compare_runs(
    baseline: dict,
    treatment: dict,
    baseline_name: str = "baseline",
    treatment_name: str = "treatment",
    output_dir: Optional[str] = None,
) -> RunComparison:
    comp = RunComparison(
        baseline_name=baseline_name,
        treatment_name=treatment_name,
    )

    for key in ("total_ms", "execution_time_ms"):
        b = baseline.get(key, baseline.get("total_ms", 0))
        t = treatment.get(key, treatment.get("total_ms", 0))
        comp.add_metric("latency_ms", float(b or 0), float(t or 0))
        break

    for key in ("confidence", "truth_confidence"):
        b = baseline.get(key, 0)
        t = treatment.get(key, 0)
        comp.add_metric(key, float(b or 0), float(t or 0))

    b_success = 1 if baseline.get("success", False) else 0
    t_success = 1 if treatment.get("success", False) else 0
    comp.add_metric("success", b_success, t_success)

    b_len = len(baseline.get("response", ""))
    t_len = len(treatment.get("response", ""))
    comp.add_metric("response_length", float(b_len), float(t_len))

    if output_dir:
        comp.save(output_dir)

    return comp
