from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from cam_physgeo.rewards.conditioned_sgc import evaluate_csgc_video
from cam_physgeo.rewards.epipolar import evaluate_epipolar_video
from cam_physgeo.utils.io import ensure_dir, read_jsonl, write_json

VIDEO_KEYS = ("candidate_video", "video_path", "target_video", "target_video_path", "video", "mp4")
POSE_KEYS = ("poses", "poses_path")
INTR_KEYS = ("intrinsics", "intrinsics_path")
MISSING_TRACKER_REASON = "missing_real_tracker_or_sim_object_state_backend"


def _first_path(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if value:
            return str(value)
    return ""


def _read_video(path: str | Path, *, max_frames: int = 81) -> tuple[np.ndarray | None, str]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return None, "open_failed"
    frames: list[np.ndarray] = []
    while len(frames) < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame.astype(np.float32) / 255.0)
    cap.release()
    if not frames:
        return None, "decode_failed"
    return np.stack(frames, axis=0), "ok"


def _align_videos(gt: np.ndarray, cand: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = min(len(gt), len(cand))
    gt = gt[:n]
    cand = cand[:n]
    if gt.shape[1:3] != cand.shape[1:3]:
        h, w = gt.shape[1:3]
        cand = np.stack([cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA) for fr in cand], axis=0)
    return gt, cand


def _global_ssim(x: np.ndarray, y: np.ndarray) -> float:
    xg = 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]
    yg = 0.299 * y[..., 0] + 0.587 * y[..., 1] + 0.114 * y[..., 2]
    mx = float(xg.mean()); my = float(yg.mean())
    vx = float(((xg - mx) ** 2).mean()); vy = float(((yg - my) ** 2).mean())
    cov = float(((xg - mx) * (yg - my)).mean())
    c1 = 0.01 ** 2; c2 = 0.03 ** 2
    return float(((2 * mx * my + c1) * (2 * cov + c2)) / ((mx * mx + my * my + c1) * (vx + vy + c2)))


def _basic_pair_metrics(gt: np.ndarray, cand: np.ndarray) -> dict[str, float]:
    gt, cand = _align_videos(gt, cand)
    diff = gt - cand
    mse = float(np.mean(diff ** 2))
    psnr = 99.0 if mse <= 1e-12 else float(-10.0 * math.log10(mse))
    ssim_vals = [_global_ssim(a, b) for a, b in zip(gt, cand)]
    return {
        "frame_count_aligned": float(len(gt)),
        "mse": mse,
        "psnr": psnr,
        "ssim": float(np.mean(ssim_vals)) if ssim_vals else float("nan"),
        "pixel_l1_proxy": float(np.mean(np.abs(diff))),
    }


def _quality_metrics(frames: np.ndarray) -> dict[str, float]:
    if len(frames) < 2:
        return {"freeze_rate": 1.0, "blur_laplacian": 0.0, "flicker_proxy": 0.0, "quality_proxy": 0.0}
    diffs = np.mean(np.abs(frames[1:] - frames[:-1]), axis=(1, 2, 3))
    freeze_rate = float(np.mean(diffs < 0.002))
    gray = [(0.299 * fr[..., 0] + 0.587 * fr[..., 1] + 0.114 * fr[..., 2]) for fr in frames]
    blur_vals = [float(cv2.Laplacian((g * 255).astype(np.uint8), cv2.CV_64F).var()) for g in gray]
    frame_means = np.array([float(g.mean()) for g in gray], dtype=np.float64)
    flicker = float(np.mean(np.abs(np.diff(frame_means, n=2)))) if len(frame_means) >= 3 else 0.0
    blur_score = float(np.clip(math.log1p(float(np.mean(blur_vals))) / math.log1p(800.0), 0.0, 1.0))
    quality = float(np.clip(0.55 * blur_score + 0.25 * (1.0 - freeze_rate) + 0.20 * math.exp(-20.0 * flicker), 0.0, 1.0))
    return {
        "freeze_rate": freeze_rate,
        "blur_laplacian": float(np.mean(blur_vals)),
        "flicker_proxy": flicker,
        "quality_proxy": quality,
    }


def _load_candidate_spec(spec: str, conditions: list[dict[str, Any]]) -> tuple[str, dict[str, str]]:
    if "=" not in spec:
        raise ValueError(f"Candidate must be LABEL=PATH_OR_GT, got {spec!r}")
    label, value = spec.split("=", 1)
    label = label.strip(); value = value.strip()
    mapping: dict[str, str] = {}
    if value.lower() in {"gt", "clean_gt", "target"}:
        for row in conditions:
            mapping[str(row.get("sample_id"))] = _first_path(row, VIDEO_KEYS)
        return label, mapping
    path = Path(value)
    if path.is_file():
        for row in read_jsonl(path):
            sid = str(row.get("sample_id") or row.get("condition_id") or "")
            video = _first_path(row, VIDEO_KEYS)
            if sid and video:
                mapping[sid] = video
        return label, mapping
    if path.is_dir():
        mp4s = list(path.rglob("*.mp4"))
        by_name = {p.stem: str(p) for p in mp4s}
        for row in conditions:
            sid = str(row.get("sample_id"))
            direct = path / sid / "video.mp4"
            if direct.exists():
                mapping[sid] = str(direct)
                continue
            matches = [str(p) for p in mp4s if sid in p.name or sid in str(p.parent)]
            if matches:
                mapping[sid] = sorted(matches)[0]
        return label, mapping
    raise FileNotFoundError(f"Candidate path not found: {value}")


def _safe_load_npy(path: str) -> np.ndarray | None:
    if not path or not Path(path).exists():
        return None
    arr = np.load(path)
    return arr if np.isfinite(arr).all() else None


def _geometry_metrics(video_path: str, row: dict[str, Any], out_dir: Path, model: str, sid: str, *, skip: bool) -> dict[str, Any]:
    if skip:
        return {"epipolar_status": "skipped", "csgc_status": "skipped"}
    poses = _safe_load_npy(_first_path(row, POSE_KEYS))
    intr = _safe_load_npy(_first_path(row, INTR_KEYS))
    if poses is None or intr is None:
        return {"epipolar_status": "missing_camera", "csgc_status": "missing_camera"}
    vis_dir = out_dir / "geometry_visualizations" / model
    epi = evaluate_epipolar_video(video_path, poses, intr, frame_i=0, frame_j=min(40, len(poses) - 1), visualization_path=vis_dir / f"{sid}_epipolar.jpg")
    csgc = evaluate_csgc_video(video_path, poses, intr, frame_i=0, frame_j=min(40, len(poses) - 1), visualization_path=vis_dir / f"{sid}_csgc.jpg")
    d: dict[str, Any] = {}
    for k, v in epi.to_dict().items():
        d[f"epipolar_{k}"] = v
    for k, v in csgc.to_dict().items():
        d[f"csgc_{k}"] = v
    return d


def _missing_physics_fields() -> dict[str, Any]:
    keys = [
        "ade", "dtw_trajectory", "endpoint_error", "event_timing_error",
        "mask_iou", "st_iou", "object_area_drift", "bbox_aspect_ratio_drift", "contour_deformation",
        "fg_id", "vjepa_temporal_similarity", "object_persistence_rate", "disappearance_rate", "duplication_rate",
        "pes", "rcs",
    ]
    out: dict[str, Any] = {k: "" for k in keys}
    out["object_tracker_backend"] = "missing"
    out["object_tracker_reason"] = MISSING_TRACKER_REASON
    return out


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    ensure_dir(path.parent)
    keys: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key); keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader(); writer.writerows(rows)


def _numeric(value: Any) -> float | None:
    if value == "" or value is None:
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _summarize(rows: list[dict[str, Any]], group_keys: tuple[str, ...], metrics: tuple[str, ...]) -> list[dict[str, Any]]:
    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[tuple(row.get(k, "") for k in group_keys)].append(row)
    out: list[dict[str, Any]] = []
    for group, vals in sorted(buckets.items()):
        base = {k: v for k, v in zip(group_keys, group)}
        base["count"] = len(vals)
        for metric in metrics:
            xs = [_numeric(v.get(metric)) for v in vals]
            xs = [x for x in xs if x is not None]
            if xs:
                arr = np.asarray(xs, dtype=np.float64)
                base[f"{metric}_mean"] = float(arr.mean())
                base[f"{metric}_median"] = float(np.median(arr))
                base[f"{metric}_std"] = float(arr.std(ddof=0))
            else:
                base[f"{metric}_mean"] = "missing"
                base[f"{metric}_median"] = "missing"
                base[f"{metric}_std"] = "missing"
        out.append(base)
    return out


def run(args: argparse.Namespace) -> int:
    conditions = list(read_jsonl(args.conditions))
    if args.max_samples:
        conditions = conditions[: args.max_samples]
    out_dir = ensure_dir(args.out_dir)
    candidate_specs = args.candidate or ["GT=gt"]
    candidates = [_load_candidate_spec(spec, conditions) for spec in candidate_specs]
    rows: list[dict[str, Any]] = []
    failure_counts: Counter[str] = Counter()
    for label, mapping in candidates:
        for cond in conditions:
            sid = str(cond.get("sample_id"))
            gt_path = _first_path(cond, VIDEO_KEYS)
            cand_path = mapping.get(sid, "")
            base = {
                "sample_id": sid,
                "model": label,
                "template": cond.get("template") or cond.get("benchmark_template") or "",
                "camera_variant": cond.get("camera_variant", ""),
                "benchmark_split": cond.get("benchmark_split", ""),
                "source_split": cond.get("source_split", ""),
                "gt_video": gt_path,
                "candidate_video": cand_path,
            }
            if not cand_path:
                failure_counts[f"{label}:missing_candidate"] += 1
                rows.append({**base, "decode_status": "missing_candidate", **_missing_physics_fields()})
                continue
            gt, gt_status = _read_video(gt_path, max_frames=args.frame_count)
            cand, cand_status = _read_video(cand_path, max_frames=args.frame_count)
            if gt is None or cand is None:
                failure_counts[f"{label}:decode_failed"] += 1
                rows.append({**base, "decode_status": f"gt={gt_status};candidate={cand_status}", **_missing_physics_fields()})
                continue
            pair = _basic_pair_metrics(gt, cand)
            quality = _quality_metrics(cand)
            geom = _geometry_metrics(cand_path, cond, out_dir, label, sid, skip=args.skip_geometry)
            rows.append({**base, "decode_status": "ok", **pair, **quality, **geom, **_missing_physics_fields()})
    _write_csv(rows, out_dir / "per_sample_metrics.csv")
    metrics = ("psnr", "ssim", "pixel_l1_proxy", "freeze_rate", "blur_laplacian", "flicker_proxy", "quality_proxy", "epipolar_median_sampson", "csgc_score")
    _write_csv(_summarize(rows, ("model",), metrics), out_dir / "model_summary.csv")
    _write_csv(_summarize(rows, ("model", "template"), metrics), out_dir / "template_breakdown.csv")
    _write_csv(_summarize(rows, ("model", "camera_variant"), metrics), out_dir / "camera_breakdown.csv")
    failure_rows = [{"failure": k, "count": v} for k, v in sorted(failure_counts.items())]
    _write_csv(failure_rows, out_dir / "failure_counts.csv")
    write_json({
        "conditions": len(conditions),
        "candidates": [label for label, _ in candidates],
        "rows": len(rows),
        "metrics_with_real_backend": ["psnr", "ssim", "freeze_rate", "blur_laplacian", "flicker_proxy", "epipolar", "csgc"],
        "metrics_missing_backend": ["ADE", "DTW", "Mask IoU", "FG-ID", "PES", "RCS"],
        "missing_backend_reason": MISSING_TRACKER_REASON,
    }, out_dir / "summary.json")
    print({"rows": len(rows), "out_dir": str(out_dir), "failures": dict(failure_counts)})
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Evaluate fixed Quant Benchmark v1 candidates without faking unavailable backends.")
    ap.add_argument("--conditions", required=True)
    ap.add_argument("--candidate", action="append", help="LABEL=gt, LABEL=manifest.jsonl, or LABEL=directory")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--frame_count", type=int, default=81)
    ap.add_argument("--max_samples", type=int, default=0)
    ap.add_argument("--skip_geometry", action="store_true")
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
