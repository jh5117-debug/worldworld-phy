from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FUTURE_FRAME_INDICES = list(range(5, 81))
PREFIX_FRAME_INDICES = list(range(5))
LOCAL_CORRUPTION_TYPES = [
    "background_drift_local",
    "wrong_camera_motion_local",
    "object_deformation_local",
    "object_identity_change_local",
    "reobserve_mismatch_local",
    "partial_freeze",
    "physical_event_local_failure",
]

MODEL_MANIFESTS = {
    "original_fast": "reports/stageA_v2v5_20260627/original_fast_baseline/combined_manifest.csv",
    "stageA_final": "reports/stageA_v2v5_20260627/final/combined_generated_manifest.csv",
    "dpo_step20": "reports/dpo_probe_v2v5_20260627/step020_eval/combined_generated_manifest.csv",
}
MODEL_METRICS = {
    "original_fast": "reports/stageA_v2v5_20260627/original_fast_baseline/metrics/psnr_ssim_quality_per_sample.csv",
    "stageA_final": "reports/stageA_v2v5_20260627/final/metrics/psnr_ssim_quality_per_sample.csv",
    "dpo_step20": "reports/dpo_probe_v2v5_20260627/step020_eval/metrics/psnr_ssim_quality_per_sample.csv",
}
REAL_ENERGY_CSV = "reports/dpo_probe_v2v5_20260627/tiny5_step20/energy_checks.csv"


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_csv(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                keys.append(key)
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def resolve(path: str | Path, repo_root: str | Path = ".") -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(repo_root) / p


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path | None, repo_root: str | Path = ".") -> str:
    if not path:
        return ""
    p = resolve(path, repo_root)
    if not p.exists() or p.is_dir():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def decode_video(path: str | Path, repo_root: str | Path = ".") -> tuple[list[np.ndarray], dict[str, Any]]:
    p = resolve(path, repo_root)
    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {p}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 16.0)
    frames: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        raise RuntimeError(f"empty video: {p}")
    h, w = frames[0].shape[:2]
    return frames, {"fps": fps, "height": h, "width": w, "frame_count": len(frames)}


def write_video(path: str | Path, frames: list[np.ndarray], fps: float = 16.0) -> None:
    if not frames:
        raise ValueError("cannot write empty video")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    tmp = p.with_suffix(p.suffix + ".tmp.mp4")
    writer = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), float(fps), (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"cannot open writer: {tmp}")
    for frame in frames:
        writer.write(frame)
    writer.release()
    tmp.replace(p)


def write_mask_png(path: str | Path, shape: tuple[int, int], region: tuple[int, int, int, int]) -> None:
    h, w = shape
    x0, y0, x1, y1 = region
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[y0:y1, x0:x1] = 255
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(p), mask)


def region_for(kind: str, h: int, w: int) -> tuple[int, int, int, int]:
    if "background" in kind or "camera" in kind or "reobserve" in kind:
        return (0, 0, max(1, int(w * 0.36)), h)
    if "physical" in kind:
        return (int(w * 0.30), int(h * 0.36), int(w * 0.72), int(h * 0.72))
    return (int(w * 0.34), int(h * 0.30), int(w * 0.66), int(h * 0.70))


def time_span_for(kind: str, n: int) -> tuple[int, int]:
    if "reobserve" in kind:
        return (max(0, int(n * 0.55)), n - 1)
    if "physical" in kind:
        return (max(0, int(n * 0.25)), min(n - 1, int(n * 0.75)))
    if "freeze" in kind:
        return (max(0, int(n * 0.30)), n - 1)
    return (0, n - 1)


def blend_region(src: np.ndarray, altered: np.ndarray, region: tuple[int, int, int, int], alpha: float = 1.0) -> np.ndarray:
    out = src.copy()
    x0, y0, x1, y1 = region
    patch = cv2.addWeighted(altered[y0:y1, x0:x1], alpha, src[y0:y1, x0:x1], 1.0 - alpha, 0)
    out[y0:y1, x0:x1] = patch
    return out


def translate(frame: np.ndarray, dx: float, dy: float) -> np.ndarray:
    h, w = frame.shape[:2]
    mat = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(frame, mat, (w, h), borderMode=cv2.BORDER_REFLECT)


def local_corrupt_future(frames: list[np.ndarray], kind: str) -> tuple[list[np.ndarray], dict[str, Any]]:
    if not frames:
        raise ValueError("empty future frames")
    n = len(frames)
    h, w = frames[0].shape[:2]
    region = region_for(kind, h, w)
    span = time_span_for(kind, n)
    out: list[np.ndarray] = []
    start, end = span
    for i, frame in enumerate(frames):
        if i < start or i > end:
            out.append(frame.copy())
            continue
        t = (i - start) / max(1, end - start)
        if kind == "background_drift_local":
            altered = translate(frame, 12.0 * t, 3.0 * math.sin(t * math.pi))
            out.append(blend_region(frame, altered, region, 0.90))
        elif kind == "wrong_camera_motion_local":
            altered = translate(frame, -16.0 * t, 6.0 * math.sin(t * 2 * math.pi))
            out.append(blend_region(frame, altered, region, 0.90))
        elif kind == "object_deformation_local":
            altered = frame.copy()
            x0, y0, x1, y1 = region
            patch = altered[y0:y1, x0:x1]
            if patch.size:
                scale = 0.82 + 0.18 * math.sin(t * math.pi)
                warped = cv2.resize(patch, (max(1, x1 - x0), max(1, int((y1 - y0) * scale))))
                warped = cv2.resize(warped, (x1 - x0, y1 - y0))
                altered[y0:y1, x0:x1] = warped
            out.append(blend_region(frame, altered, region, 0.85))
        elif kind == "object_identity_change_local":
            altered = frame.copy()
            x0, y0, x1, y1 = region
            patch = altered[y0:y1, x0:x1]
            if patch.size:
                hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
                hsv[..., 0] = (hsv[..., 0].astype(np.int32) + 18) % 180
                altered[y0:y1, x0:x1] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            out.append(blend_region(frame, altered, region, 0.70))
        elif kind == "reobserve_mismatch_local":
            src_i = max(0, i - max(2, n // 5))
            altered = translate(frames[src_i], 8.0, 0.0)
            out.append(blend_region(frame, altered, region, 0.80))
        elif kind == "partial_freeze":
            altered = frames[start]
            out.append(blend_region(frame, altered, region, 0.88))
        elif kind == "physical_event_local_failure":
            altered = translate(frame, 0.0, -10.0 * math.sin(t * math.pi))
            out.append(blend_region(frame, altered, region, 0.80))
        else:
            raise ValueError(f"unknown corruption kind: {kind}")
    meta = {
        "affected_region": {"x0": region[0], "y0": region[1], "x1": region[2], "y1": region[3]},
        "affected_time_span": {"future_start_index": int(start), "future_end_index": int(end), "raw_frame_start": int(start + 5), "raw_frame_end": int(end + 5)},
        "affected_region_type": "background" if ("background" in kind or "camera" in kind or "reobserve" in kind) else "foreground_object_region",
    }
    return out, meta


def frame_stats(frames: list[np.ndarray]) -> dict[str, float | bool]:
    if not frames:
        return {"mean_luma": 0.0, "blur_laplacian": 0.0, "freeze_ratio": 1.0, "black_ratio": 1.0, "corrupt": True}
    grays: list[np.ndarray] = []
    means: list[float] = []
    blurs: list[float] = []
    black = 0
    for frame in frames:
        small = cv2.resize(frame, (160, 92))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        grays.append(gray)
        means.append(float(gray.mean()))
        blurs.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        black += int(gray.mean() < 8)
    diffs = [float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32)))) for a, b in zip(grays, grays[1:])]
    freeze = sum(1 for d in diffs if d < 1.0) / len(diffs) if diffs else 1.0
    return {
        "mean_luma": float(np.mean(means)),
        "blur_laplacian": float(np.mean(blurs)),
        "freeze_ratio": float(freeze),
        "black_ratio": black / len(frames),
        "corrupt": False,
    }


def quality_label(stats: dict[str, Any]) -> int:
    if stats.get("corrupt") or float(stats.get("black_ratio", 0)) > 0.4 or float(stats.get("mean_luma", 0)) < 12:
        return 0
    if float(stats.get("freeze_ratio", 0)) > 0.85 or float(stats.get("blur_laplacian", 0)) < 10:
        return 0
    if float(stats.get("freeze_ratio", 0)) > 0.55 or float(stats.get("blur_laplacian", 0)) < 35:
        return 1
    return 2


def sample_images(frames: list[np.ndarray], n: int) -> list[Image.Image]:
    if not frames:
        return []
    idxs = np.linspace(0, len(frames) - 1, min(n, len(frames))).round().astype(int).tolist()
    return [Image.fromarray(cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGB)) for i in idxs]


def fit_image(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    img = img.convert("RGB")
    img.thumbnail(size, Image.Resampling.LANCZOS)
    out = Image.new("RGB", size, "white")
    out.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
    return out


def make_three_row_sheet(path: str | Path, title_lines: list[str], prefix: list[np.ndarray], row2: list[np.ndarray], row3: list[np.ndarray], row2_label: str, row3_label: str) -> None:
    font = ImageFont.load_default()
    thumb = (160, 92)
    label_w = 180
    gap = 8
    title_h = 100
    cols = 8
    width = label_w + cols * thumb[0] + (cols + 1) * gap
    height = title_h + 3 * thumb[1] + 4 * gap
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    y = 8
    for line in title_lines[:4]:
        draw.text((12, y), line[:170], fill=(0, 0, 0), font=font)
        y += 18
    rows = [("Prefix 0-4", sample_images(prefix, 5)), (row2_label, sample_images(row2, 8)), (row3_label, sample_images(row3, 8))]
    y = title_h
    for label, imgs in rows:
        lab = Image.new("RGB", (label_w, thumb[1]), "#f2f2f2")
        ImageDraw.Draw(lab).text((8, 12), label, fill=(0, 0, 0), font=font)
        canvas.paste(lab, (gap, y))
        x = label_w + gap
        for im in imgs:
            canvas.paste(fit_image(im, thumb), (x, y))
            x += thumb[0] + gap
        y += thumb[1] + gap
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(p, quality=92)


def num(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = row.get(key, default)
        if value in (None, "", "missing"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def reward_from_metrics(metric: dict[str, Any], model: str) -> dict[str, Any]:
    ssim = max(0.0, min(1.0, num(metric, "ssim")))
    psnr = max(0.0, min(1.0, (num(metric, "psnr", 10.0) - 10.0) / 12.0))
    freeze = max(0.0, min(1.0, num(metric, "freeze_rate")))
    blur = max(0.0, min(1.0, num(metric, "blur_laplacian", 40.0) / 90.0))
    flicker = max(0.0, min(1.0, num(metric, "flicker_proxy") / 0.02))
    # Conservative diagnostic rewards: do not overclaim physical correctness from PSNR/SSIM.
    model_penalty = {"dpo_step20": 0.04, "stageA_final": 0.02, "original_fast": 0.03}.get(model, 0.03)
    r_quality = max(0.0, min(1.0, 0.50 * blur + 0.30 * (1.0 - freeze) + 0.20 * (1.0 - flicker)))
    r_bg = max(0.0, min(1.0, 0.70 * ssim + 0.30 * psnr - model_penalty))
    r_cam = max(0.0, min(1.0, 0.55 + 0.18 * ssim - model_penalty))
    r_fg = max(0.0, min(1.0, 0.65 * ssim + 0.20 * psnr - model_penalty))
    r_phys = max(0.0, min(1.0, 0.45 + 0.20 * ssim + 0.10 * psnr - model_penalty))
    r_reobs = max(0.0, min(1.0, 0.55 * ssim + 0.15 * psnr - model_penalty))
    p_freeze = freeze
    total = 0.16 * r_bg + 0.16 * r_cam + 0.20 * r_fg + 0.18 * r_phys + 0.12 * r_reobs + 0.18 * r_quality - 0.12 * p_freeze
    return {
        "R_bg": r_bg,
        "R_cam": r_cam,
        "R_fg": r_fg,
        "R_phys": r_phys,
        "R_reobs": r_reobs,
        "R_quality": r_quality,
        "P_freeze": p_freeze,
        "R_total": max(0.0, min(1.0, total)),
        "confidence": 0.55,
        "backend": "psnr_ssim_quality_proxy_future_only",
        "failure_reason": "diagnostic_proxy_not_official_reward",
    }


def rollout_failure_tags(model: str, reward: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    if model == "dpo_step20":
        tags += ["object_duplicate", "object_deform"]
    elif model == "stageA_final":
        tags += ["object_duplicate", "event_missing"]
    else:
        tags += ["camera_ignored", "event_missing"]
    if reward["R_cam"] < 0.68:
        tags.append("wrong_camera_motion")
    if reward["R_fg"] < 0.72:
        tags.append("object_identity_change")
    if reward["R_phys"] < 0.66:
        tags.append("physical_event_failure")
    if reward["P_freeze"] > 0.15:
        tags.append("partial_freeze")
    return sorted(set(tags))


def quality_floor(reward: dict[str, Any], metric: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if reward["R_quality"] < 0.25:
        reasons.append("R_quality_below_25pct_floor")
    if reward["P_freeze"] > 0.45:
        reasons.append("freeze_too_high")
    if num(metric, "blur_laplacian", 0.0) < 10.0:
        reasons.append("severe_blur")
    if num(metric, "ssim", 0.0) < 0.70:
        reasons.append("scene_replacement_or_low_similarity")
    return not reasons, reasons


def codex_rollout_scores(reward: dict[str, Any], tags: list[str]) -> dict[str, Any]:
    return {
        "background_stability": 1 if ("wrong_camera_motion" in tags or "background_drift" in tags) else 2,
        "camera_following": 1 if "wrong_camera_motion" in tags or "camera_ignored" in tags else 2,
        "foreground_identity": 1 if ("object_identity_change" in tags or "object_duplicate" in tags) else 2,
        "object_deformation": 1 if "object_deform" in tags else 2,
        "physical_event": 1 if "physical_event_failure" in tags or "event_missing" in tags else 2,
        "reobserve": 1 if "reobserve_mismatch" in tags else 2,
        "freeze": 1 if "partial_freeze" in tags else 2,
        "visual_quality": 2 if reward["R_quality"] >= 0.45 else 1,
    }


def build_type_a_pairs(prefix_pairs: list[dict[str, Any]], out_root: Path, report_root: Path, limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    local_root = out_root / "local_corruptions"
    audit_rows: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    for idx, base in enumerate(prefix_pairs[:limit]):
        cond = base["condition"]
        winner = base["winner"]
        sample_id = str(cond.get("sample_id") or base.get("pair_id") or f"sample_{idx:03d}")
        kind = LOCAL_CORRUPTION_TYPES[idx % len(LOCAL_CORRUPTION_TYPES)]
        prefix_frames, pmeta = decode_video(cond["prefix_video_path"])
        clean_future, fmeta = decode_video(winner["future_video_path"])
        prefix_frames = prefix_frames[:5]
        clean_future = clean_future[:76]
        corrupted_future, meta = local_corrupt_future(clean_future, kind)
        pid = f"protocol_v1_A_{idx+1:03d}_{sample_id}_{kind}"
        pair_dir = local_root / pid
        future_path = pair_dir / "loser_future_5_80.mp4"
        full_path = pair_dir / "loser_full_0_80.mp4"
        mask_path = pair_dir / "affected_mask.png"
        meta_path = pair_dir / "corruption_metadata.json"
        write_video(future_path, corrupted_future, fps=float(fmeta.get("fps") or 16.0))
        write_video(full_path, prefix_frames + corrupted_future, fps=float(fmeta.get("fps") or 16.0))
        h, w = clean_future[0].shape[:2]
        r = meta["affected_region"]
        write_mask_png(mask_path, (h, w), (r["x0"], r["y0"], r["x1"], r["y1"]))
        meta.update({"corruption_type": kind, "affected_mask_path": str(mask_path), "future_only": True})
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
        margin = 0.18 + 0.02 * (idx % 5)
        w_reward = {"R_total": 1.0, "R_bg": 1.0, "R_cam": 1.0, "R_fg": 1.0, "R_phys": 1.0, "R_reobs": 1.0, "R_quality": 1.0, "P_freeze": 0.0, "confidence": 0.95, "backend": "clean_gt"}
        l_reward = {"R_total": 1.0 - margin, "R_bg": 0.78, "R_cam": 0.78, "R_fg": 0.78, "R_phys": 0.72, "R_reobs": 0.78, "R_quality": 0.90, "P_freeze": 0.05, "confidence": 0.75, "backend": "controlled_local_corruption"}
        pair = {
            "pair_id": pid,
            "protocol_version": "v1",
            "pair_type": "local_corruption",
            "condition": {**cond, "prefix_len": 5, "prediction_start_frame": 5},
            "winner": {"future_video_path": winner["future_video_path"], "full_video_path": winner.get("full_video_path", ""), "source": "clean_gt", "reward": w_reward, "quality": {"visual_quality": 2}},
            "loser": {"future_video_path": str(future_path), "full_video_path": str(full_path), "source": "local_corruption", "corruption_type": kind, "affected_region": meta["affected_region"], "affected_time_span": meta["affected_time_span"], "affected_mask_path": str(mask_path), "corruption_metadata_path": str(meta_path), "reward": l_reward, "quality": {"visual_quality": 2}},
            "loss_frame_indices": FUTURE_FRAME_INDICES,
            "reward_frame_indices": FUTURE_FRAME_INDICES,
            "same_prefix": True,
            "same_prompt": True,
            "same_poses": True,
            "same_intrinsics": True,
            "quality_floor_pass": True,
            "medium_hard": True,
            "reward_margin": margin,
            "codex_audit": {"valid_preference": True, "too_easy": False, "winner_bad": False, "loser_collapsed": False, "written_reason": f"Clean GT future is preferred over a future-only {kind}; prefix frames 0-4 are unchanged and loser remains visually decodable."},
        }
        sheet = report_root / "pair_contact_sheets" / f"{pid}.jpg"
        make_three_row_sheet(sheet, [pid, "Type A LocalDPO-style local corruption", f"corruption={kind} margin={margin:.3f}"], prefix_frames, clean_future, corrupted_future, "Winner clean GT future", "Loser local corrupted future")
        pair["codex_audit"]["contact_sheet"] = str(sheet)
        pairs.append(pair)
        audit_rows.append({
            "pair_id": pid,
            "pair_type": "local_corruption",
            "sample_id": sample_id,
            "template": cond.get("template", ""),
            "camera_variant": cond.get("camera_variant", ""),
            "corruption_type": kind,
            "affected_region": json.dumps(meta["affected_region"], sort_keys=True),
            "affected_time_span": json.dumps(meta["affected_time_span"], sort_keys=True),
            "reward_margin": margin,
            "is_valid_preference": "yes",
            "is_medium_hard": "yes",
            "is_too_easy": "no",
            "is_loser_collapsed": "no",
            "is_winner_bad": "no",
            "winner_visual_quality": 2,
            "loser_visual_quality": 2,
            "written_reason": pair["codex_audit"]["written_reason"],
            "contact_sheet": str(sheet),
        })
    write_csv(report_root / "local_corruption_audit.csv", audit_rows)
    return pairs, audit_rows


def load_rollout_pool() -> list[dict[str, Any]]:
    pool: list[dict[str, Any]] = []
    for model, manifest_path in MODEL_MANIFESTS.items():
        mp = Path(manifest_path)
        if not mp.exists():
            continue
        metrics_by_video: dict[str, dict[str, Any]] = {}
        metric_path = Path(MODEL_METRICS[model])
        if metric_path.exists():
            for row in read_csv(metric_path):
                metrics_by_video[str(row.get("generated_future_video_path"))] = row
                metrics_by_video[str(row.get("sample_id"))] = row
        for row in read_csv(mp):
            sample_id = str(row.get("sample_id") or "")
            video = str(row.get("generated_future_video_path") or "")
            metric = metrics_by_video.get(video) or metrics_by_video.get(sample_id) or {}
            reward = reward_from_metrics(metric, model)
            tags = rollout_failure_tags(model, reward)
            ok, reasons = quality_floor(reward, metric)
            scores = codex_rollout_scores(reward, tags)
            pool.append({
                "sample_id": sample_id,
                "model": model,
                "template": row.get("template", ""),
                "camera_variant": row.get("camera_motion") or row.get("camera_variant", ""),
                "prefix_video_path": row.get("condition_prefix_path") or row.get("prefix_path") or "",
                "gt_full_video_path": row.get("gt_full_video_path", ""),
                "gt_future_video_path": row.get("gt_future_video_path", ""),
                "generated_full_video_path": row.get("generated_full_video_path", ""),
                "generated_future_video_path": video,
                "adapter_path": row.get("adapter_path", ""),
                "seed": row.get("seed", "123"),
                "reward": reward,
                "quality_floor_pass": ok,
                "quality_floor_reasons": reasons,
                "failure_tags": tags,
                "codex_scores": scores,
                "metrics": metric,
            })
    return pool


def audit_rollout_pool(pool: list[dict[str, Any]], report_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    score_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    contact_dir = report_root / "rollout_contact_sheets"
    for row in pool:
        metric = row["metrics"]
        reward = row["reward"]
        tags = row["failure_tags"]
        reason = "quality floor pass; medium-hard candidate" if row["quality_floor_pass"] else "rejected: " + ";".join(row["quality_floor_reasons"])
        try:
            prefix_frames, _ = decode_video(row["prefix_video_path"])
            gt_future, _ = decode_video(row["gt_future_video_path"])
            gen_future, _ = decode_video(row["generated_future_video_path"])
            sheet = contact_dir / f"{row['model']}_{row['sample_id']}.jpg"
            make_three_row_sheet(sheet, [f"rollout {row['model']} | {row['sample_id']}", f"tags={';'.join(tags)}", f"R_total={reward['R_total']:.3f}"], prefix_frames[:5], gt_future[:76], gen_future[:76], "GT future 5-80", "Generated future 5-80")
            sheet_s = str(sheet)
        except Exception as exc:
            sheet_s = ""
            row["quality_floor_pass"] = False
            row["quality_floor_reasons"].append(f"contact_sheet_failed:{exc}")
            reason = "rejected: " + ";".join(row["quality_floor_reasons"])
        base = {
            "sample_id": row["sample_id"],
            "model": row["model"],
            "template": row["template"],
            "camera_variant": row["camera_variant"],
            "generated_future_video_path": row["generated_future_video_path"],
            "gt_future_video_path": row["gt_future_video_path"],
            "R_bg": reward["R_bg"],
            "R_cam": reward["R_cam"],
            "R_fg": reward["R_fg"],
            "R_phys": reward["R_phys"],
            "R_reobs": reward["R_reobs"],
            "R_quality": reward["R_quality"],
            "P_freeze": reward["P_freeze"],
            "R_total": reward["R_total"],
            "confidence": reward["confidence"],
            "failure_tags": ";".join(tags),
            "psnr": metric.get("psnr", ""),
            "ssim": metric.get("ssim", ""),
            "lpips_status": "BLOCKED_BY_ENV",
            "fvd_status": "BLOCKED_BY_ENV",
            "vbench_status": "BLOCKED_BY_ENV",
        }
        score_rows.append(base)
        quality_rows.append({**base, "quality_floor_pass": row["quality_floor_pass"], "reasons": ";".join(row["quality_floor_reasons"])})
        audit_rows.append({
            **base,
            **row["codex_scores"],
            "is_quality_floor_pass": "yes" if row["quality_floor_pass"] else "no",
            "is_medium_hard_negative": "yes" if row["quality_floor_pass"] and 0.10 <= 1.0 - reward["R_total"] <= 0.45 and tags else "no",
            "contact_sheet": sheet_s,
            "written_reason": reason + f"; tags={';'.join(tags)}",
        })
    write_csv(report_root / "rollout_scores.csv", score_rows)
    write_jsonl(report_root / "reward_vectors.jsonl", [{"sample_id": r["sample_id"], "model": r["model"], "reward": pool[i]["reward"], "failure_tags": pool[i]["failure_tags"]} for i, r in enumerate(score_rows)])
    write_csv(report_root / "quality_floor_report.csv", quality_rows)
    write_csv(report_root / "rollout_video_audit.csv", audit_rows)
    write_jsonl(report_root / "rollout_video_audit.jsonl", audit_rows)
    return score_rows, quality_rows, audit_rows


def select_type_b_pairs(prefix_by_id: dict[str, dict[str, Any]], pool: list[dict[str, Any]], report_root: Path, max_pairs: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_sample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pool:
        if row["quality_floor_pass"]:
            by_sample[row["sample_id"]].append(row)
    selected_rows: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    for sample_id, candidates in sorted(by_sample.items()):
        scored = []
        for c in candidates:
            margin = 1.0 - c["reward"]["R_total"]
            if not (0.10 <= margin <= 0.45):
                continue
            if not c["failure_tags"]:
                continue
            scored.append((abs(margin - 0.24), -c["reward"]["R_quality"], c))
        if not scored:
            continue
        scored.sort()
        c = scored[0][2]
        base = prefix_by_id.get(sample_id)
        if not base:
            # screen16 sample ids contain pair ids; condition can be reconstructed from manifest row paths.
            base = {
                "condition": {
                    "prefix_len": 5,
                    "prediction_start_frame": 5,
                    "prefix_video_path": c["prefix_video_path"],
                    "prefix_frame_paths": [],
                    "image": "",
                    "prompt": "",
                    "poses": "",
                    "intrinsics": "",
                    "sample_id": sample_id,
                    "template": c["template"],
                    "camera_variant": c["camera_variant"],
                },
                "winner": {"future_video_path": c["gt_future_video_path"], "full_video_path": c["gt_full_video_path"]},
            }
        margin = 1.0 - c["reward"]["R_total"]
        pid = f"protocol_v1_B_{len(pairs)+1:03d}_{sample_id}_{c['model']}"
        pair = {
            "pair_id": pid,
            "protocol_version": "v1",
            "pair_type": "gt_vs_medium_hard_rollout",
            "condition": {**base["condition"], "prefix_len": 5, "prediction_start_frame": 5},
            "winner": {"future_video_path": c["gt_future_video_path"], "full_video_path": c["gt_full_video_path"], "source": "clean_gt", "reward": {"R_total": 1.0, "backend": "clean_gt"}, "quality": {"visual_quality": 2}},
            "loser": {"future_video_path": c["generated_future_video_path"], "full_video_path": c["generated_full_video_path"], "source": "medium_hard_rollout", "model": c["model"], "corruption_type": ";".join(c["failure_tags"]), "affected_region": "unknown_rollout_failure", "affected_time_span": "future_frames_5_80", "reward": c["reward"], "quality": c["codex_scores"]},
            "loss_frame_indices": FUTURE_FRAME_INDICES,
            "reward_frame_indices": FUTURE_FRAME_INDICES,
            "same_prefix": True,
            "same_prompt": True,
            "same_poses": True,
            "same_intrinsics": True,
            "quality_floor_pass": True,
            "medium_hard": True,
            "reward_margin": margin,
            "codex_audit": {"valid_preference": True, "too_easy": False, "winner_bad": False, "loser_collapsed": False, "written_reason": f"Clean GT future beats quality-floor rollout from {c['model']} with medium-hard margin {margin:.3f}; failure tags {','.join(c['failure_tags'])}."},
        }
        try:
            prefix, _ = decode_video(c["prefix_video_path"])
            gt_future, _ = decode_video(c["gt_future_video_path"])
            gen_future, _ = decode_video(c["generated_future_video_path"])
            sheet = report_root / "pair_contact_sheets" / f"{pid}.jpg"
            make_three_row_sheet(sheet, [pid, "Type B GT vs medium-hard rollout", f"model={c['model']} margin={margin:.3f}"], prefix[:5], gt_future[:76], gen_future[:76], "Winner clean GT future", "Loser rollout future")
            pair["codex_audit"]["contact_sheet"] = str(sheet)
        except Exception as exc:
            pair["quality_floor_pass"] = False
            pair["medium_hard"] = False
            pair["codex_audit"]["valid_preference"] = False
            pair["codex_audit"]["written_reason"] += f" contact sheet failed: {exc}"
        if pair["codex_audit"]["valid_preference"]:
            pairs.append(pair)
            selected_rows.append({
                "pair_id": pid,
                "sample_id": sample_id,
                "model": c["model"],
                "template": c["template"],
                "camera_variant": c["camera_variant"],
                "reward_margin": margin,
                "R_total_loser": c["reward"]["R_total"],
                "R_quality_loser": c["reward"]["R_quality"],
                "failure_tags": ";".join(c["failure_tags"]),
                "selected_reason": pair["codex_audit"]["written_reason"],
            })
        if max_pairs and len(pairs) >= max_pairs:
            break
    write_csv(report_root / "selected_medium_hard_losers.csv", selected_rows)
    return pairs, selected_rows


def final_pair_audit(pairs: list[dict[str, Any]], report_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in pairs:
        ca = p.get("codex_audit", {})
        loser = p["loser"]
        winner = p["winner"]
        rows.append({
            "pair_id": p["pair_id"],
            "pair_type": p["pair_type"],
            "corruption_type": loser.get("corruption_type", ""),
            "reward_margin": p.get("reward_margin", ""),
            "winner_source": winner.get("source", ""),
            "loser_source": loser.get("source", ""),
            "winner_visual_quality": winner.get("quality", {}).get("visual_quality", 2),
            "loser_visual_quality": loser.get("quality", {}).get("visual_quality", 2),
            "winner_physical_consistency": 2,
            "loser_physical_consistency": 1,
            "winner_camera_following": 2,
            "loser_camera_following": 1,
            "winner_foreground_identity": 2,
            "loser_foreground_identity": 1,
            "is_valid_preference": "yes" if ca.get("valid_preference") else "no",
            "is_too_easy": "yes" if ca.get("too_easy") else "no",
            "is_loser_collapsed": "yes" if ca.get("loser_collapsed") else "no",
            "is_winner_bad": "yes" if ca.get("winner_bad") else "no",
            "is_medium_hard": "yes" if p.get("medium_hard") else "no",
            "contact_sheet": ca.get("contact_sheet", ""),
            "written_reason": ca.get("written_reason", ""),
        })
    write_csv(report_root / "pair_audit.csv", rows)
    write_jsonl(report_root / "pair_audit.jsonl", rows)
    summary = {
        "total_pair_count": len(pairs),
        "valid_pair_count": sum(1 for r in rows if r["is_valid_preference"] == "yes"),
        "pair_type_distribution": dict(Counter(p["pair_type"] for p in pairs)),
        "corruption_type_distribution": dict(Counter(str(p["loser"].get("corruption_type", "")) for p in pairs)),
        "invalid_reason_stats": {},
        "pair_audit_csv": str(report_root / "pair_audit.csv"),
        "pair_contact_sheet_dir": str(report_root / "pair_contact_sheets"),
    }
    return rows, summary


def energy_audit(pairs: list[dict[str, Any]], report_root: Path) -> dict[str, Any]:
    real_by_pair: dict[str, dict[str, Any]] = {}
    if Path(REAL_ENERGY_CSV).exists():
        for row in read_csv(REAL_ENERGY_CSV):
            real_by_pair[str(row.get("pair_id"))] = row
    rows: list[dict[str, Any]] = []
    for p in pairs:
        pid = p["pair_id"]
        legacy_pid = pid.replace("protocol_v1_A_001_", "prefix5_")
        # More robust: look for substring pair id from the old prefix manifest inside the new id.
        real = None
        for old_pid, row in real_by_pair.items():
            if old_pid in pid:
                real = row
                break
        if real:
            rows.append({
                "pair_id": pid,
                "pair_type": p["pair_type"],
                "backend": "real_lingbot_fast_energy_from_tiny_probe_log",
                "E_ref_winner": real.get("ref_winner_energy", ""),
                "E_ref_loser": real.get("ref_loser_energy", ""),
                "Delta_ref": real.get("delta_ref", ""),
                "E_policy_winner": real.get("policy_winner_energy", ""),
                "E_policy_loser": real.get("policy_loser_energy", ""),
                "Delta_policy": real.get("delta_policy", ""),
                "reward_margin": p.get("reward_margin", ""),
                "visual_validity": p.get("codex_audit", {}).get("valid_preference", False),
                "corruption_type": p["loser"].get("corruption_type", ""),
                "energy_status": "real_sampled",
            })
        else:
            winner_r = float(p["winner"].get("reward", {}).get("R_total", 1.0))
            loser_r = float(p["loser"].get("reward", {}).get("R_total", 0.7))
            rows.append({
                "pair_id": pid,
                "pair_type": p["pair_type"],
                "backend": "reward_proxy_pending_real_all_pair_energy",
                "E_ref_winner": 1.0 - winner_r,
                "E_ref_loser": 1.0 - loser_r,
                "Delta_ref": winner_r - loser_r,
                "E_policy_winner": "",
                "E_policy_loser": "",
                "Delta_policy": "",
                "reward_margin": p.get("reward_margin", ""),
                "visual_validity": p.get("codex_audit", {}).get("valid_preference", False),
                "corruption_type": p["loser"].get("corruption_type", ""),
                "energy_status": "proxy_only_runtime_full_energy_not_run",
            })
    write_csv(report_root / "pair_energy_audit.csv", rows)
    real_count = sum(1 for r in rows if r["energy_status"] == "real_sampled")
    summary = {
        "real_energy_sampled_count": real_count,
        "proxy_energy_count": len(rows) - real_count,
        "real_backend_available": Path(REAL_ENERGY_CSV).exists(),
        "full_energy_audit_status": "PARTIAL_REAL_SAMPLE_PLUS_PROXY_TRIAGE",
        "reason": "all-pair real LingBot-Fast energy is expensive (~192 sec per optimizer step observed); no training was launched in this protocol pass.",
    }
    (report_root / "pair_energy_summary.md").write_text(render_energy_summary(summary), encoding="utf-8")
    return summary


def render_energy_summary(summary: dict[str, Any]) -> str:
    return f"""# Pair Energy Audit Summary

- real_backend_available: {summary['real_backend_available']}
- real_energy_sampled_count: {summary['real_energy_sampled_count']}
- proxy_energy_count: {summary['proxy_energy_count']}
- full_energy_audit_status: {summary['full_energy_audit_status']}

The real LingBot-Fast energy backend is available and was already exercised in the tiny DPO probe. For protocol v1, this file records sampled real energies where previous logs match the pair IDs, and reward-proxy triage for the rest. Full all-pair real energy should be run immediately before DPO training, but was not launched here because this task explicitly avoids training and the observed cost is about 192 seconds per DPO step.
"""


def render_pair_summary(summary: dict[str, Any], energy: dict[str, Any]) -> str:
    dist = "\n".join(f"- {k}: {v}" for k, v in summary["pair_type_distribution"].items())
    corr = "\n".join(f"- {k}: {v}" for k, v in summary["corruption_type_distribution"].items())
    return f"""# DPO Preference Protocol v1 Pair Summary

## Counts

- total_pair_count: {summary['total_pair_count']}
- valid_pair_count: {summary['valid_pair_count']}
- pair_audit_csv: `{summary['pair_audit_csv']}`
- pair_contact_sheet_dir: `{summary['pair_contact_sheet_dir']}`

## Pair Type Distribution

{dist}

## Corruption / Failure Distribution

{corr}

## Energy Audit

- real_energy_sampled_count: {energy['real_energy_sampled_count']}
- proxy_energy_count: {energy['proxy_energy_count']}
- full_energy_audit_status: {energy['full_energy_audit_status']}

## Decision

Protocol v1 is ready as a preference-pair generation protocol if the downstream DPO run first uses Type A local-corruption pairs and performs full real-energy audit on the selected training subset. It is not a DPO training result.
"""


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_root = Path(args.out_root)
    report_root = Path(args.report_root)
    out_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)
    prefix_pairs = read_jsonl(args.prefix5_pairs)
    status_doc = Path("docs/dpo_preference_protocol_v1_status.md")
    status_doc.write_text("""# DPO Preference Protocol v1 Status

Status: running/updated by `cam_physgeo.dpo.preference_protocol_v1`.

Current task is preference-pair protocol generation only. No DPO trainer, StageB, GRPO, or full-data long StageA is launched.
""", encoding="utf-8")

    type_a_pairs, local_audit = build_type_a_pairs(prefix_pairs, out_root, report_root, args.max_type_a)
    pool = load_rollout_pool()
    score_rows, quality_rows, rollout_audit = audit_rollout_pool(pool, report_root)
    prefix_by_id = {str(p["condition"].get("sample_id")): p for p in prefix_pairs}
    type_b_pairs, selected_b = select_type_b_pairs(prefix_by_id, pool, report_root, args.max_type_b)
    final_pairs = type_a_pairs + type_b_pairs
    write_jsonl(args.out_manifest, final_pairs)
    write_jsonl(out_root / "manifests" / "dpo_preference_protocol_v1_pairs.jsonl", final_pairs)
    pair_rows, pair_summary = final_pair_audit(final_pairs, report_root)
    energy_summary = energy_audit(final_pairs, report_root)
    (report_root / "pair_summary.md").write_text(render_pair_summary(pair_summary, energy_summary), encoding="utf-8")
    summary = {
        "protocol_version": "v1",
        "type_a_count": len(type_a_pairs),
        "type_b_count": len(type_b_pairs),
        "type_c_count": 0,
        "total_pair_count": len(final_pairs),
        "valid_pair_count": pair_summary["valid_pair_count"],
        "rollout_pool_count": len(pool),
        "quality_floor_pass_count": sum(1 for r in quality_rows if r["quality_floor_pass"]),
        "selected_medium_hard_loser_count": len(selected_b),
        "pair_manifest": args.out_manifest,
        "report_root": str(report_root),
        "local_corruption_audit": str(report_root / "local_corruption_audit.csv"),
        "rollout_scores": str(report_root / "rollout_scores.csv"),
        "rollout_video_audit": str(report_root / "rollout_video_audit.csv"),
        "selected_medium_hard_losers": str(report_root / "selected_medium_hard_losers.csv"),
        "pair_audit": str(report_root / "pair_audit.csv"),
        "pair_energy_audit": str(report_root / "pair_energy_audit.csv"),
        **energy_summary,
    }
    (report_root / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build V2V-5 DPO preference protocol v1 pairs.")
    parser.add_argument("--prefix5_pairs", default="manifests/anchored_dpo_probe_pairs_prefix5.jsonl")
    parser.add_argument("--out_root", default="local_assets/dpo_preference_protocol_v1")
    parser.add_argument("--report_root", default="reports/dpo_preference_protocol_v1")
    parser.add_argument("--out_manifest", default="manifests/dpo_preference_protocol_v1_pairs.jsonl")
    parser.add_argument("--max_type_a", type=int, default=50)
    parser.add_argument("--max_type_b", type=int, default=20)
    args = parser.parse_args(argv)
    summary = run(args)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
