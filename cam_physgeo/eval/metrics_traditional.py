from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np

_LPIPS_MODEL_CACHE: dict[tuple[str, str], Any] = {}


@dataclass(frozen=True)
class BackendStatus:
    name: str
    status: str
    reason: str = ""
    attempted_fix: str = ""


def read_video_rgb(path: str | Path, max_frames: int | None = None) -> tuple[np.ndarray | None, dict[str, Any]]:
    path = Path(path)
    meta: dict[str, Any] = {"path": str(path), "status": "ok"}
    if not path.exists():
        meta.update(status="missing")
        return None, meta
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        meta.update(status="open_failed")
        return None, meta
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    frame_count_hint = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frames: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0)
        if max_frames and len(frames) >= max_frames:
            break
    cap.release()
    if not frames:
        meta.update(status="decode_failed", fps=fps, width=width, height=height, frame_count_hint=frame_count_hint)
        return None, meta
    meta.update(
        fps=fps,
        width=width,
        height=height,
        frame_count_hint=frame_count_hint,
        num_frames=len(frames),
        file_size_mb=path.stat().st_size / (1024.0 * 1024.0),
    )
    return np.stack(frames, axis=0), meta


def align_videos(reference: np.ndarray, prediction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = min(len(reference), len(prediction))
    ref = reference[:n]
    pred = prediction[:n]
    if ref.shape[1:3] != pred.shape[1:3]:
        h, w = ref.shape[1:3]
        pred = np.stack([cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA) for fr in pred], axis=0)
    return ref.astype(np.float32), pred.astype(np.float32)


def psnr_from_mse(mse: float) -> float:
    return 99.0 if mse <= 1e-12 else float(-10.0 * math.log10(mse))


def ssim_frame(x: np.ndarray, y: np.ndarray) -> float:
    xg = 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]
    yg = 0.299 * y[..., 0] + 0.587 * y[..., 1] + 0.114 * y[..., 2]
    mx = float(xg.mean())
    my = float(yg.mean())
    vx = float(((xg - mx) ** 2).mean())
    vy = float(((yg - my) ** 2).mean())
    cov = float(((xg - mx) * (yg - my)).mean())
    c1 = 0.01**2
    c2 = 0.03**2
    denom = (mx * mx + my * my + c1) * (vx + vy + c2)
    if denom <= 0:
        return 0.0
    return float(((2 * mx * my + c1) * (2 * cov + c2)) / denom)


def laplacian_sharpness(video: np.ndarray) -> dict[str, float]:
    vals = []
    for frame in video:
        gray = (0.299 * frame[..., 0] + 0.587 * frame[..., 1] + 0.114 * frame[..., 2])
        vals.append(float(cv2.Laplacian((gray * 255).astype(np.uint8), cv2.CV_64F).var()))
    arr = np.asarray(vals, dtype=np.float64)
    return {
        "mean_laplacian_sharpness": float(arr.mean()) if len(arr) else 0.0,
        "median_laplacian_sharpness": float(np.median(arr)) if len(arr) else 0.0,
    }


def temporal_blur_proxy(video: np.ndarray) -> float:
    if len(video) < 2:
        return 0.0
    diffs = np.mean(np.abs(video[1:] - video[:-1]), axis=(1, 2, 3))
    return float(np.mean(diffs))


def brightness_contrast(video: np.ndarray) -> dict[str, float]:
    gray = 0.299 * video[..., 0] + 0.587 * video[..., 1] + 0.114 * video[..., 2]
    return {"brightness_mean": float(gray.mean()), "contrast_std": float(gray.std())}


def compute_psnr_ssim(reference: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    ref, pred = align_videos(reference, prediction)
    diff = ref - pred
    mse = float(np.mean(diff**2))
    return {
        "frame_count_aligned": float(len(ref)),
        "mse": mse,
        "psnr": psnr_from_mse(mse),
        "ssim": float(np.mean([ssim_frame(a, b) for a, b in zip(ref, pred)])),
        "pixel_l1": float(np.mean(np.abs(diff))),
    }


def lpips_backend_status() -> BackendStatus:
    try:
        import lpips  # noqa: F401
        import torch  # noqa: F401
    except Exception as exc:  # pragma: no cover - depends on env
        return BackendStatus("LPIPS", "BLOCKED_BY_ENV", str(exc), "pip install lpips was attempted")
    return BackendStatus("LPIPS", "AVAILABLE", "", "pip install lpips succeeded")


def compute_lpips(reference: np.ndarray, prediction: np.ndarray, max_frames: int = 16, device: str = "cpu") -> dict[str, Any]:
    status = lpips_backend_status()
    if status.status != "AVAILABLE":
        return {"lpips_status": status.status, "lpips_reason": status.reason}
    try:
        import lpips
        import torch

        ref, pred = align_videos(reference, prediction)
        if max_frames and len(ref) > max_frames:
            idx = np.linspace(0, len(ref) - 1, max_frames).round().astype(int)
            ref = ref[idx]
            pred = pred[idx]
        cache_key = ("alex", device)
        if cache_key not in _LPIPS_MODEL_CACHE:
            _LPIPS_MODEL_CACHE[cache_key] = lpips.LPIPS(net="alex", verbose=False).to(device).eval()
        loss_fn = _LPIPS_MODEL_CACHE[cache_key]
        vals = []
        with torch.no_grad():
            for a, b in zip(ref, pred):
                at = torch.from_numpy(a.transpose(2, 0, 1)).unsqueeze(0).to(device) * 2.0 - 1.0
                bt = torch.from_numpy(b.transpose(2, 0, 1)).unsqueeze(0).to(device) * 2.0 - 1.0
                vals.append(float(loss_fn(at, bt).item()))
        return {"lpips_status": "ok", "lpips": float(np.mean(vals)), "lpips_frames": len(vals)}
    except Exception as exc:  # pragma: no cover - dependency/runtime variability
        return {"lpips_status": "BLOCKED_BY_ENV", "lpips_reason": str(exc)}


def fvd_backend_status() -> BackendStatus:
    from cam_physgeo.eval.metrics_fvd import fvd_backend_status as _fvd_backend_status

    status = _fvd_backend_status()
    return BackendStatus("FVD", status.status, status.reason, status.attempted_fix)


def compute_video_pair_metrics(
    reference_video_path: str | Path,
    prediction_video_path: str | Path,
    *,
    compute_lpips_metric: bool = False,
    lpips_max_frames: int = 16,
    lpips_device: str = "cpu",
    decode_max_frames: int | None = None,
) -> dict[str, Any]:
    ref, ref_meta = read_video_rgb(reference_video_path, max_frames=decode_max_frames)
    pred, pred_meta = read_video_rgb(prediction_video_path, max_frames=decode_max_frames)
    row: dict[str, Any] = {
        "reference_video_path": str(reference_video_path),
        "prediction_video_path": str(prediction_video_path),
        "reference_status": ref_meta.get("status"),
        "prediction_status": pred_meta.get("status"),
        "reference_width": ref_meta.get("width"),
        "reference_height": ref_meta.get("height"),
        "prediction_width": pred_meta.get("width"),
        "prediction_height": pred_meta.get("height"),
        "prediction_fps": pred_meta.get("fps"),
        "prediction_num_frames": pred_meta.get("num_frames"),
        "prediction_file_size_mb": pred_meta.get("file_size_mb"),
    }
    if ref is None or pred is None:
        row.update(status="decode_failed")
        return row
    row.update(status="ok")
    row.update(compute_psnr_ssim(ref, pred))
    row.update(laplacian_sharpness(pred))
    row["temporal_blur_proxy"] = temporal_blur_proxy(pred)
    row.update(brightness_contrast(pred))
    if compute_lpips_metric:
        row.update(compute_lpips(ref, pred, max_frames=lpips_max_frames, device=lpips_device))
    else:
        status = lpips_backend_status()
        row.update(lpips_status="not_requested" if status.status == "AVAILABLE" else status.status, lpips_reason=status.reason)
    fvd = fvd_backend_status()
    row.update(fvd_status=fvd.status, fvd_reason=fvd.reason)
    return row


def write_csv(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    path = Path(path)
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for row in rows for k in row})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str | Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")



def _pair_video_path(pair: dict[str, Any], side: str) -> str:
    item = pair.get(side) or {}
    return str(item.get("future_video_path") or item.get("video_path") or item.get("full_video_path") or pair.get(f"{side}_video_path") or "")


def _gt_future_path(pair: dict[str, Any]) -> str:
    cond = pair.get("condition") or {}
    return str(cond.get("gt_future_video_path") or cond.get("future_video_path") or cond.get("gt_video_path") or "")


def _source_for_metric(pair: dict[str, Any]) -> str:
    ptype = pair.get("pair_type")
    if ptype == "GT_C" or "rollout" in str(pair.get("_manifest_source", "")):
        return "rollout_derived"
    if ptype == "TypeA_plus":
        return "TypeA_plus"
    return "synthetic_controlled"


def _select_metric_pairs(pairs: list[dict[str, Any]], num_pairs: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    quotas = [("synthetic_controlled", 5), ("rollout_derived", 3)]
    for source, quota in quotas:
        for pair in pairs:
            pid = str(pair.get("pair_id"))
            if pid not in used and _source_for_metric(pair) == source:
                selected.append(pair); used.add(pid)
                if sum(1 for p in selected if _source_for_metric(p) == source) >= quota:
                    break
    for pair in pairs:
        pid = str(pair.get("pair_id"))
        if pid not in used:
            selected.append(pair); used.add(pid)
        if len(selected) >= num_pairs:
            break
    return selected[:num_pairs]


def _read_pair_manifest(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    import argparse
    from collections import Counter

    ap = argparse.ArgumentParser(description="Traditional pair metrics smoke for DPO pair manifests")
    ap.add_argument("--pair_manifest", required=True)
    ap.add_argument("--num_pairs", type=int, default=10)
    ap.add_argument("--metrics", default="psnr,ssim")
    ap.add_argument("--output", required=True)
    ap.add_argument("--lpips_max_frames", type=int, default=8)
    ap.add_argument("--lpips_device", default="cpu")
    ap.add_argument("--decode_max_frames", type=int, default=4)
    args = ap.parse_args()

    pairs = _select_metric_pairs(_read_pair_manifest(Path(args.pair_manifest)), args.num_pairs)
    compute_lpips_metric = "lpips" in {m.strip().lower() for m in args.metrics.split(",")}
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        pid = str(pair.get("pair_id"))
        winner = _pair_video_path(pair, "winner")
        loser = _pair_video_path(pair, "loser")
        gt = _gt_future_path(pair)
        comparisons = [("winner_vs_loser", winner, loser)]
        if gt:
            comparisons.append(("winner_vs_gt", gt, winner))
            comparisons.append(("loser_vs_gt", gt, loser))
        for comparison, ref, pred in comparisons:
            row = compute_video_pair_metrics(ref, pred, compute_lpips_metric=compute_lpips_metric, lpips_max_frames=args.lpips_max_frames, lpips_device=args.lpips_device, decode_max_frames=args.decode_max_frames)
            row.update({
                "pair_id": pid,
                "comparison": comparison,
                "pair_type": pair.get("pair_type", ""),
                "source": _source_for_metric(pair),
                "failure_type": pair.get("failure_tag") or ((pair.get("loser") or {}).get("failure_type")) or "",
            })
            rows.append(row)
    write_csv(args.output, rows)
    ok_lpips = [float(r.get("lpips", 0.0)) for r in rows if r.get("lpips_status") == "ok" and r.get("comparison") == "winner_vs_loser"]
    status = "PASS" if len(ok_lpips) == len(pairs) else "MIXED"
    summary = [
        f"Current Status: {status}",
        "",
        "# LPIPS Real Smoke Summary",
        "",
        f"- Pair manifest: `{args.pair_manifest}`",
        f"- Selected pairs: {len(pairs)}",
        f"- Rows written: {len(rows)}",
        f"- LPIPS winner_vs_loser rows: {len(ok_lpips)}",
        f"- Mean LPIPS winner_vs_loser: {sum(ok_lpips)/len(ok_lpips) if ok_lpips else 'NA'}",
        f"- Source counts: `{dict(Counter(_source_for_metric(p) for p in pairs))}`",
        f"- Output CSV: `{args.output}`",
    ]
    Path(args.output).with_name(Path(args.output).stem + "_summary.md").write_text("\n".join(summary) + "\n")
    print(json.dumps({"status": status, "pairs": len(pairs), "rows": len(rows), "lpips_rows": len(ok_lpips), "mean_lpips": (sum(ok_lpips)/len(ok_lpips) if ok_lpips else None)}, indent=2))


if __name__ == "__main__":
    main()
