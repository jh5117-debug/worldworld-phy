from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from cam_physgeo.rewards.corruption import CORRUPTIONS, make_corruption_records
from cam_physgeo.utils.io import ensure_dir, read_jsonl, write_json


def _video_key(row: dict[str, Any]) -> str:
    for key in ("target_video", "video_path", "target_video_path", "video", "candidate_video"):
        if row.get(key):
            return str(row[key])
    return ""


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _num(row: dict[str, Any], key: str, default: float | None = None) -> float | None:
    try:
        value = row.get(key)
        if value in {None, "", "missing"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _higher_better(metric: str) -> bool:
    return metric not in {"pixel_l1_proxy", "freeze_rate", "flicker_proxy", "epipolar_median_sampson"}


def _clean_wins(clean: dict[str, Any], corrupt: dict[str, Any], metric: str) -> bool | None:
    a = _num(clean, metric); b = _num(corrupt, metric)
    if a is None or b is None:
        return None
    return a > b if _higher_better(metric) else a < b


def _run_quant_eval(conditions: Path, candidates: list[str], out_dir: Path, *, frame_count: int, max_samples: int, skip_geometry: bool) -> None:
    from cam_physgeo.eval.quant_benchmark_v1 import main as quant_main
    argv = ["--conditions", str(conditions), "--out_dir", str(out_dir), "--frame_count", str(frame_count)]
    for candidate in candidates:
        argv.extend(["--candidate", candidate])
    if max_samples:
        argv.extend(["--max_samples", str(max_samples)])
    if skip_geometry:
        argv.append("--skip_geometry")
    quant_main(argv)


def run(args: argparse.Namespace) -> int:
    out_dir = ensure_dir(args.out_dir)
    corrupt_dir = ensure_dir(out_dir / "corruptions")
    conditions: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    corruptions = [c for c in args.corruptions.split(",") if c in CORRUPTIONS]
    for i, row in enumerate(read_jsonl(args.manifest)):
        if args.limit and i >= args.limit:
            break
        sample = dict(row)
        sample_id = str(sample.get("sample_id") or f"sample_{i:05d}")
        video = _video_key(sample)
        if not video:
            continue
        sample["sample_id"] = sample_id
        sample["video_path"] = video
        sample["target_video"] = video
        conditions.append(sample)
        for corr in make_corruption_records(sample, out_dir=str(corrupt_dir), dry_run=False):
            if corr["corruption"] not in corruptions:
                continue
            candidate_rows.append({
                "sample_id": sample_id,
                "model": corr["corruption"],
                "candidate_video": corr["loser_video"],
                "template": sample.get("template", ""),
                "camera_variant": sample.get("camera_variant", sample.get("camera_motion", "")),
                "corruption": corr["corruption"],
                "quality_flags": ";".join(corr.get("quality_flags") or []),
            })
    cond_path = out_dir / "calibration_conditions.jsonl"
    cand_path = out_dir / "corrupted_candidates.jsonl"
    _write_jsonl(conditions, cond_path)
    _write_jsonl(candidate_rows, cand_path)
    eval_dir = out_dir / "metrics"
    _run_quant_eval(cond_path, ["clean_gt=gt", f"corrupted={cand_path}"], eval_dir, frame_count=args.frame_count, max_samples=0, skip_geometry=args.skip_geometry)
    rows = _read_csv(eval_dir / "per_sample_metrics.csv")
    by_sample: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_sample.setdefault(str(row.get("sample_id")), {})[str(row.get("model"))] = row
    metrics = ["psnr", "ssim", "pixel_l1_proxy", "freeze_rate", "quality_proxy", "epipolar_median_sampson", "csgc_score"]
    detail: list[dict[str, Any]] = []
    wins = {m: [0, 0] for m in metrics}
    for sid, model_rows in by_sample.items():
        clean = model_rows.get("clean_gt")
        corrupt = model_rows.get("corrupted")
        if not clean or not corrupt:
            continue
        row = {"sample_id": sid, "corruption": corrupt.get("corruption", "corrupted")}
        for metric in metrics:
            win = _clean_wins(clean, corrupt, metric)
            if win is not None:
                wins[metric][1] += 1
                wins[metric][0] += int(bool(win))
            row[f"{metric}_clean"] = clean.get(metric, "")
            row[f"{metric}_corrupted"] = corrupt.get(metric, "")
            row[f"{metric}_clean_wins"] = "" if win is None else int(bool(win))
        detail.append(row)
    detail_path = out_dir / "calibration_detail.csv"
    if detail:
        keys = list(detail[0].keys())
        with detail_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys); writer.writeheader(); writer.writerows(detail)
    summary = {
        "conditions": len(conditions),
        "corrupted_candidates": len(candidate_rows),
        "corruptions": corruptions,
        "metric_clean_win_rate": {m: (wins[m][0] / wins[m][1] if wins[m][1] else None) for m in metrics},
        "dpo_ready_gate": "PASS" if wins.get("quality_proxy", [0, 1])[1] and (wins["quality_proxy"][0] / max(1, wins["quality_proxy"][1])) >= args.min_clean_win_rate else "PRELIMINARY_OR_BLOCKED",
        "skip_geometry": args.skip_geometry,
    }
    write_json(summary, out_dir / "summary.json")
    lines = ["# Reward Calibration v2 Report", "", f"- conditions: {len(conditions)}", f"- corrupted candidates: {len(candidate_rows)}", f"- dpo_ready_gate: {summary['dpo_ready_gate']}", "", "## Clean > Corrupted Rates"]
    for metric, rate in summary["metric_clean_win_rate"].items():
        lines.append(f"- {metric}: {rate}")
    (out_dir / "reward_calibration_v2_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(summary)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Reward calibration v2 using real video corruptions and benchmark metrics.")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--frame_count", type=int, default=81)
    ap.add_argument("--corruptions", default="background_drift,wrong_camera_motion,freeze_camera,global_freeze")
    ap.add_argument("--skip_geometry", action="store_true")
    ap.add_argument("--min_clean_win_rate", type=float, default=0.85)
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
