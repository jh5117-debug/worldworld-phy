from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


BIN_RANGES: dict[str, tuple[float, float]] = {
    "low": (0.05, 0.20),
    "mid": (0.25, 0.55),
    "high": (0.70, 0.95),
}


@dataclass(frozen=True)
class SigmaPoint:
    index: int
    timestep: float
    sigma: float


def default_sigma_schedule(num_train_timesteps: int = 1000) -> list[SigmaPoint]:
    if num_train_timesteps < 2:
        raise ValueError("num_train_timesteps must be >= 2")
    points: list[SigmaPoint] = []
    denom = float(num_train_timesteps - 1)
    for idx in range(num_train_timesteps):
        # Wan/LingBot helper exposes a monotonically sampled sigma table; this
        # fallback is intentionally schedule-only and does not load DiT/VAE.
        sigma = 1.0 - float(idx) / denom
        timestep = float(num_train_timesteps - 1 - idx)
        points.append(SigmaPoint(index=idx, timestep=timestep, sigma=sigma))
    return points


def load_sigma_schedule(path: str | Path | None, *, num_train_timesteps: int = 1000) -> list[SigmaPoint]:
    if path is None or str(path) == "":
        return default_sigma_schedule(num_train_timesteps)
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    values: list[float] = []
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        raw = data.get("sigmas", data) if isinstance(data, dict) else data
        values = [float(x) for x in raw]
    else:
        with p.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and "sigma" in reader.fieldnames:
                values = [float(row["sigma"]) for row in reader]
            else:
                f.seek(0)
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        values.append(float(stripped.split(",")[0]))
    if not values:
        raise ValueError(f"empty sigma schedule: {p}")
    denom = float(max(len(values) - 1, 1))
    return [SigmaPoint(index=i, timestep=float(len(values) - 1 - i), sigma=float(s)) for i, s in enumerate(values)]


def parse_bins(value: str) -> list[str]:
    bins = [part.strip() for part in value.split(",") if part.strip()]
    unknown = [b for b in bins if b not in BIN_RANGES]
    if unknown:
        raise ValueError(f"unknown sigma bins: {unknown}; known={sorted(BIN_RANGES)}")
    return bins


def _nearest(points: list[SigmaPoint], target_sigma: float) -> SigmaPoint:
    return min(points, key=lambda p: abs(float(p.sigma) - float(target_sigma)))


def sample_targets(bin_name: str, count: int) -> list[float]:
    lo, hi = BIN_RANGES[bin_name]
    if count <= 1:
        return [(lo + hi) / 2.0]
    return [lo + (hi - lo) * (i + 0.5) / float(count) for i in range(count)]


def sigma_status_by_bin(rows: Iterable[dict[str, object]]) -> dict[str, str]:
    grouped: dict[str, list[float]] = {}
    for row in rows:
        grouped.setdefault(str(row["requested_bin"]), []).append(float(row["actual_sigma"]))
    status: dict[str, str] = {}
    for bin_name, values in grouped.items():
        lo, hi = BIN_RANGES[bin_name]
        if not values:
            status[bin_name] = "EMPTY"
        elif min(values) >= lo - 1e-6 and max(values) <= hi + 1e-6:
            status[bin_name] = "PASS"
        else:
            status[bin_name] = "OUT_OF_RANGE"
    return status


def distributions_are_separated(rows: list[dict[str, object]], bins: list[str]) -> bool:
    grouped: dict[str, list[float]] = {b: [] for b in bins}
    for row in rows:
        grouped[str(row["requested_bin"])].append(float(row["actual_sigma"]))
    if any(not grouped[b] for b in bins):
        return False
    centers = {b: sum(grouped[b]) / len(grouped[b]) for b in bins}
    ordered = [centers[b] for b in bins]
    return len({round(v, 6) for v in ordered}) == len(ordered) and ordered == sorted(ordered)


def build_rows(
    *,
    bins: list[str],
    num_samples_per_bin: int,
    schedule: list[SigmaPoint],
    scheduler_name: str,
) -> list[dict[str, object]]:
    sigmas = [p.sigma for p in schedule]
    sigma_min = min(sigmas)
    sigma_max = max(sigmas)
    rows: list[dict[str, object]] = []
    for bin_name in bins:
        lo, hi = BIN_RANGES[bin_name]
        for sample_idx, target in enumerate(sample_targets(bin_name, num_samples_per_bin)):
            point = _nearest(schedule, target)
            status = "PASS" if lo - 1e-6 <= point.sigma <= hi + 1e-6 else "OUT_OF_RANGE"
            rows.append(
                {
                    "requested_bin": bin_name,
                    "sample_idx": sample_idx,
                    "target_sigma": round(float(target), 8),
                    "timestep_index": int(point.index),
                    "timestep": float(point.timestep),
                    "actual_sigma": float(point.sigma),
                    "scheduler_name": scheduler_name,
                    "sigma_min": float(sigma_min),
                    "sigma_max": float(sigma_max),
                    "bin_low": float(lo),
                    "bin_high": float(hi),
                    "status": status,
                }
            )
    return rows


def write_csv(path: str | Path, rows: list[dict[str, object]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: str | Path, *, rows: list[dict[str, object]], bins: list[str], scheduler_name: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    by_bin = sigma_status_by_bin(rows)
    separated = distributions_are_separated(rows, bins)
    overall = "SIGMA_SAMPLER_ONLY_PASS" if separated and all(by_bin.get(b) == "PASS" for b in bins) else "SIGMA_MAPPING_BROKEN"
    lines = [
        "Current Status:",
        "PASS" if overall == "SIGMA_SAMPLER_ONLY_PASS" else "BLOCKED",
        "",
        "# Sigma Sampler-Only Check v8b",
        "",
        f"Decision: `{overall}`",
        "",
        f"Scheduler: `{scheduler_name}`",
        f"Rows: {len(rows)}",
        f"Bins: {', '.join(bins)}",
        f"Separated distributions: {separated}",
        "",
        "## Bin Status",
    ]
    for b in bins:
        vals = [float(r["actual_sigma"]) for r in rows if r["requested_bin"] == b]
        lines.append(f"- {b}: {by_bin.get(b)}; min={min(vals):.6f}; max={max(vals):.6f}; mean={sum(vals)/len(vals):.6f}")
    lines.append("")
    lines.append("This is a schedule-only diagnostic. It does not replace real LingBot-Fast energy evaluation.")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return overall


def run(args: argparse.Namespace) -> str:
    bins = parse_bins(args.bins)
    schedule = load_sigma_schedule(args.sigma_schedule, num_train_timesteps=int(args.num_train_timesteps))
    rows = build_rows(
        bins=bins,
        num_samples_per_bin=int(args.num_samples_per_bin),
        schedule=schedule,
        scheduler_name=str(args.scheduler_name),
    )
    write_csv(args.output, rows)
    summary_path = args.summary or str(Path(args.output).with_name(Path(args.output).stem + "_summary.md"))
    decision = write_summary(summary_path, rows=rows, bins=bins, scheduler_name=str(args.scheduler_name))
    print(json.dumps({"decision": decision, "rows": len(rows), "output": str(args.output), "summary": str(summary_path)}, sort_keys=True))
    return decision


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded sampler-only sigma/timestep debug check")
    parser.add_argument("--bins", default="low,mid,high")
    parser.add_argument("--num_samples_per_bin", type=int, default=20)
    parser.add_argument("--output", default="reports/dpo_objective_diagnosis_v8b/sigma_sampler_only.csv")
    parser.add_argument("--summary", default="")
    parser.add_argument("--sigma_schedule", default="")
    parser.add_argument("--num_train_timesteps", type=int, default=1000)
    parser.add_argument("--scheduler_name", default="fallback_linear_sigma_1_to_0")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)
    decision = run(args)
    return 0 if decision == "SIGMA_SAMPLER_ONLY_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
