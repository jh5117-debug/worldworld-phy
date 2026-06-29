from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from cam_physgeo.eval.metrics_traditional import (
    compute_video_pair_metrics,
    fvd_backend_status,
    lpips_backend_status,
    write_csv,
    write_json,
)
from cam_physgeo.eval.metrics_fvd import compute_fvd_if_available
from cam_physgeo.eval.metrics_vbench import compute_vbench_if_available, vbench_backend_status


def read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pick(row: dict[str, Any], names: list[str]) -> str:
    for name in names:
        value = row.get(name)
        if value:
            return str(value)
    return ""


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [r for r in rows if r.get("status") == "ok"]
    summary: dict[str, Any] = {"rows": len(rows), "ok_rows": len(ok), "metric_scope": "future_frames_5_80"}
    for key in ["psnr", "ssim", "mse", "pixel_l1", "mean_laplacian_sharpness", "temporal_blur_proxy"]:
        vals = [float(r[key]) for r in ok if r.get(key) not in (None, "")]
        summary[f"{key}_mean"] = float(np.mean(vals)) if vals else "missing"
        summary[f"{key}_median"] = float(np.median(vals)) if vals else "missing"
    lp = lpips_backend_status()
    fv = fvd_backend_status()
    vb = vbench_backend_status()
    summary.update(
        lpips_status=lp.status,
        lpips_reason=lp.reason,
        fvd_status=fv.status,
        fvd_reason=fv.reason,
        vbench_status=vb.status,
        vbench_reason=vb.reason,
    )
    return summary


def run(args: argparse.Namespace) -> int:
    manifest = Path(args.manifest)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_rows(manifest)
    if args.max_samples:
        rows = rows[: args.max_samples]
    results = []
    for row in rows:
        gt = pick(row, ["gt_future_video_path", "winner_future_video_path", "gt_video", "target_video", "reference_video_path"])
        pred = pick(row, ["generated_future_video_path", "loser_future_video_path", "prediction_video_path", "generated_video"])
        base = {
            "sample_id": row.get("sample_id") or row.get("pair_id") or "",
            "model": row.get("model") or row.get("model_name") or row.get("loser_source") or "",
            "template": row.get("template", ""),
        }
        if not gt or not pred:
            results.append({**base, "status": "missing_video_path", "reference_video_path": gt, "prediction_video_path": pred})
            continue
        result = compute_video_pair_metrics(
            gt,
            pred,
            compute_lpips_metric=args.compute_lpips,
            lpips_max_frames=args.lpips_max_frames,
            lpips_device=args.lpips_device,
        )
        result.update(compute_fvd_if_available(gt, pred))
        result.update(compute_vbench_if_available(gt, pred))
        results.append({**base, **result})
    write_csv(out_dir / "per_sample_metrics.csv", results)
    summary = summarize(results)
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--max_samples", type=int, default=0)
    parser.add_argument("--compute_lpips", action="store_true")
    parser.add_argument("--lpips_max_frames", type=int, default=8)
    parser.add_argument("--lpips_device", default="cpu")
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
