from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


def _float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def pairwise_ordering_accuracy(rows: Iterable[dict[str, Any]], value_key: str, gravity_key: str = "gravity_value", group_key: str = "replay_group_id", higher_gravity_lower_value: bool = True) -> dict[str, Any]:
    groups: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        g = _float(row.get(gravity_key))
        v = _float(row.get(value_key))
        if g is None or v is None:
            continue
        groups[str(row.get(group_key) or "__all__")].append((g, v))
    correct = 0
    total = 0
    for values in groups.values():
        values = sorted(values)
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                g1, v1 = values[i]
                g2, v2 = values[j]
                if g1 == g2:
                    continue
                total += 1
                if higher_gravity_lower_value:
                    correct += int((g2 > g1 and v2 <= v1) or (g1 > g2 and v1 <= v2))
                else:
                    correct += int((g2 > g1 and v2 >= v1) or (g1 > g2 and v1 >= v2))
    return {"metric": f"{value_key}_ordering", "correct": correct, "total": total, "accuracy": (correct / total if total else None)}


def summarize_scalar_error(rows: Iterable[dict[str, Any]], pred_key: str, target_key: str) -> dict[str, Any]:
    vals = []
    for row in rows:
        p = _float(row.get(pred_key))
        t = _float(row.get(target_key))
        if p is not None and t is not None:
            vals.append(abs(p - t))
    return {"metric": f"{pred_key}_abs_error", "count": len(vals), "mean_abs_error": (mean(vals) if vals else None)}


def compute_metric_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        pairwise_ordering_accuracy(rows, "airtime_sec", higher_gravity_lower_value=True),
        pairwise_ordering_accuracy(rows, "fall_speed", higher_gravity_lower_value=False),
        pairwise_ordering_accuracy(rows, "vertical_displacement", higher_gravity_lower_value=True),
        summarize_scalar_error(rows, "contact_time_pred", "contact_time_gt"),
        summarize_scalar_error(rows, "airtime_pred", "airtime_gt"),
    ]


def read_csv(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for row in rows for k in row}) or ["metric"]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_csv", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--summary", required=True)
    args = ap.parse_args(argv)
    rows = read_csv(args.input_csv)
    metrics = compute_metric_summary(rows)
    write_csv(metrics, args.output)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(
        "# Gravity Metrics Summary\n\n"
        f"- Input rows: {len(rows)}\n"
        f"- Output metrics: {len(metrics)}\n"
        "- Metrics are offline scalar summaries; visual audit remains required for any checkpoint gate.\n"
    )
    print({"input_rows": len(rows), "metrics": len(metrics), "output": args.output})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
