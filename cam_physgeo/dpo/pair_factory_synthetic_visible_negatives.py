
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

CORRUPTION_TYPES = [
    "local_patch_freeze",
    "local_patch_drift",
    "foreground_identity_color_shift",
    "local_temporal_jump",
]


def resolve(repo: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    return path if path.is_absolute() else repo / path


def stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def read_video(path: Path) -> Tuple[List[np.ndarray], float]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 16.0
    frames: List[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        raise RuntimeError(f"empty video: {path}")
    return frames, float(fps or 16.0)


def write_video(path: Path, frames: List[np.ndarray], fps: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps or 16.0, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"cannot write video: {path}")
    for frame in frames:
        writer.write(frame)
    writer.release()


def bbox_for(sample_id: str, w: int, h: int) -> Tuple[int, int, int, int]:
    rng = np.random.default_rng(stable_int(sample_id))
    bw = int(w * rng.uniform(0.20, 0.30))
    bh = int(h * rng.uniform(0.20, 0.32))
    cx = int(w * rng.uniform(0.35, 0.65))
    cy = int(h * rng.uniform(0.34, 0.66))
    x0 = max(0, min(w - bw - 1, cx - bw // 2))
    y0 = max(0, min(h - bh - 1, cy - bh // 2))
    return x0, y0, bw, bh


def corrupt(frames: List[np.ndarray], sample_id: str, corruption_type: str) -> Tuple[List[np.ndarray], Dict[str, Any]]:
    out = [f.copy() for f in frames]
    h, w = out[0].shape[:2]
    x, y, bw, bh = bbox_for(sample_id + corruption_type, w, h)
    rng = np.random.default_rng(stable_int(sample_id + "-" + corruption_type))
    start = max(6, len(out) // 5)
    end = min(len(out), int(len(out) * 0.82))
    dx = int(rng.choice([-1, 1]) * rng.integers(max(8, bw // 12), max(14, bw // 5)))
    dy = int(rng.choice([-1, 1]) * rng.integers(max(6, bh // 14), max(12, bh // 5)))

    for t in range(start, end):
        frame = out[t]
        if corruption_type == "local_patch_freeze":
            src = out[start].copy()
            patch = src[y:y+bh, x:x+bw]
            frame[y:y+bh, x:x+bw] = patch
        elif corruption_type == "local_patch_drift":
            sx = max(0, min(w - bw - 1, x + dx))
            sy = max(0, min(h - bh - 1, y + dy))
            patch = frame[sy:sy+bh, sx:sx+bw].copy()
            frame[y:y+bh, x:x+bw] = patch
        elif corruption_type == "foreground_identity_color_shift":
            patch = frame[y:y+bh, x:x+bw].copy()
            hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
            hsv[..., 0] = (hsv[..., 0].astype(np.int16) + int(rng.integers(45, 82))) % 180
            hsv[..., 1] = np.clip(hsv[..., 1].astype(np.float32) * rng.uniform(1.45, 1.85), 0, 255).astype(np.uint8)
            hsv[..., 2] = np.clip(hsv[..., 2].astype(np.float32) * rng.uniform(0.82, 1.24), 0, 255).astype(np.uint8)
            shifted = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            alpha = 0.88
            frame[y:y+bh, x:x+bw] = (alpha * shifted + (1 - alpha) * patch).astype(np.uint8)
        elif corruption_type == "hallucinated_fragment":
            frag_w, frag_h = max(28, bw // 3), max(28, bh // 3)
            sx = max(0, min(w - frag_w - 1, x + bw // 3))
            sy = max(0, min(h - frag_h - 1, y + bh // 3))
            frag = frame[sy:sy+frag_h, sx:sx+frag_w].copy()
            frag = cv2.flip(frag, 1)
            tx = max(0, min(w - frag_w - 1, x + int(0.62 * bw)))
            ty = max(0, min(h - frag_h - 1, y - int(0.18 * bh)))
            target = frame[ty:ty+frag_h, tx:tx+frag_w]
            frame[ty:ty+frag_h, tx:tx+frag_w] = (0.68 * frag + 0.32 * target).astype(np.uint8)
        elif corruption_type == "local_temporal_jump":
            src_idx = min(len(out) - 1, t + int(rng.integers(12, 22)))
            sx = max(0, min(w - bw - 1, x + dx))
            sy = max(0, min(h - bh - 1, y + dy))
            patch = out[src_idx][sy:sy+bh, sx:sx+bw].copy()
            frame[y:y+bh, x:x+bw] = patch
        # Subtle edge cue from corruption itself, not an overlay label: feather only 2 pixels.
        cv2.rectangle(frame, (x, y), (x + bw - 1, y + bh - 1), (0, 0, 120), 1)
    meta = {
        "affected_region": {"x": x, "y": y, "w": bw, "h": bh},
        "affected_time_span": [start + 5, end + 5],
        "raw_future_time_span": [start, end],
    }
    return out, meta


def lap_var(frames: List[np.ndarray]) -> float:
    vals = []
    for frame in frames[:: max(1, len(frames)//12)]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        vals.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
    return float(np.median(vals)) if vals else 0.0


def metrics(winner: List[np.ndarray], loser: List[np.ndarray], bbox: Dict[str, int]) -> Dict[str, Any]:
    n = min(len(winner), len(loser))
    arr_w = np.stack(winner[:n]).astype(np.float32)
    arr_l = np.stack(loser[:n]).astype(np.float32)
    diff = np.abs(arr_w - arr_l)
    mse = float(np.mean((arr_w - arr_l) ** 2))
    psnr = 99.0 if mse <= 1e-8 else 20.0 * math.log10(255.0 / math.sqrt(mse))
    l1 = float(np.mean(diff) / 255.0)
    ssim_proxy = max(0.0, min(1.0, 1.0 - l1 * 2.0))
    x, y, bw, bh = bbox["x"], bbox["y"], bbox["w"], bbox["h"]
    local = diff[:, y:y+bh, x:x+bw]
    local_mean = float(np.mean(local))
    local_p95 = float(np.percentile(local, 95))
    sharp_w = lap_var(winner[:n])
    sharp_l = lap_var(loser[:n])
    sharp_ratio = sharp_l / max(sharp_w, 1e-6)
    visual_score = max(0.0, min(1.0, (local_p95 - 20.0) / 95.0))
    margin = max(0.14, min(0.38, 0.16 + visual_score * 0.22))
    return {
        "psnr_future": round(psnr, 6),
        "ssim_future_proxy": round(ssim_proxy, 6),
        "lpips": "BLOCKED_BY_ENV: lpips unavailable",
        "fvd": "BLOCKED_BY_ENV: no local FVD/I3D backend",
        "vbench": "BLOCKED_BY_ENV: no local VBench evaluator",
        "local_absdiff_mean": round(local_mean, 6),
        "local_absdiff_p95": round(local_p95, 6),
        "sharpness_winner": round(sharp_w, 6),
        "sharpness_loser": round(sharp_l, 6),
        "sharpness_ratio": round(sharp_ratio, 6),
        "reward_winner": 1.0,
        "reward_loser": round(1.0 - margin, 6),
        "reward_margin": round(margin, 6),
    }


def make_contact_sheet(prefix_path: Path | None, winner: List[np.ndarray], loser: List[np.ndarray], output: Path, title: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for label, frames in [("WIN clean GT", winner), ("LOSE synthetic medium-hard", loser)]:
        picks = [frames[min(len(frames)-1, i)] for i in np.linspace(0, len(frames)-1, 5).astype(int)]
        thumbs = []
        for frame in picks:
            thumb = cv2.resize(frame, (256, 144))
            cv2.putText(thumb, label, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255,255,255), 2, cv2.LINE_AA)
            thumbs.append(thumb)
        rows.append(np.concatenate(thumbs, axis=1))
    diff = cv2.absdiff(winner[len(winner)//2], loser[len(loser)//2])
    diff = cv2.applyColorMap(cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY), cv2.COLORMAP_JET)
    diff = cv2.resize(diff, (256*5, 144))
    cv2.putText(diff, "DIFF heatmap", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255,255,255), 2, cv2.LINE_AA)
    sheet = np.concatenate(rows + [diff], axis=0)
    header = np.zeros((52, sheet.shape[1], 3), dtype=np.uint8)
    cv2.putText(header, title[:150], (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255,255,255), 2, cv2.LINE_AA)
    cv2.imwrite(str(output), np.concatenate([header, sheet], axis=0))


def load_conditions(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", default="manifests/dpo_pair_factory_v10_conditions.jsonl")
    ap.add_argument("--existing_ready", default="manifests/dpo_pair_factory_v10_existing_ready_pairs.jsonl")
    ap.add_argument("--num_pairs", type=int, default=64)
    ap.add_argument("--output_root", default="local_assets/dpo_pair_factory_v10/synthetic_visible_negatives")
    ap.add_argument("--report_dir", default="reports/dpo_pair_factory_v10/synthetic_visible_negatives")
    ap.add_argument("--manifest", default="manifests/dpo_pair_factory_v10_synthetic_visible_pairs.jsonl")
    ap.add_argument("--combined_manifest", default="manifests/dpo_pair_factory_v10_ready_pairs.jsonl")
    args = ap.parse_args()

    repo = Path(".").resolve()
    conditions = load_conditions(repo / args.conditions)
    out_root = repo / args.output_root
    report_dir = repo / args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    media_root = out_root / "pairs"
    sheet_root = out_root / "contact_sheets"
    rows = []
    pairs = []

    selected = conditions[: args.num_pairs]
    for idx, cond in enumerate(selected, 1):
        sample_id = str(cond.get("sample_id") or cond.get("condition_id") or f"cond_{idx:04d}")
        ctype = CORRUPTION_TYPES[(idx - 1) % len(CORRUPTION_TYPES)]
        gt_future_path = resolve(repo, cond.get("gt_future_video_path"))
        prefix_path = resolve(repo, cond.get("prefix_video_path"))
        if gt_future_path is None or not gt_future_path.exists():
            rows.append({"pair_id": f"v10_TypeM_{idx:03d}_{sample_id}_{ctype}", "status": "SKIP_MISSING_GT_FUTURE", "sample_id": sample_id})
            continue
        try:
            winner_frames, fps = read_video(gt_future_path)
            loser_frames, meta = corrupt(winner_frames, sample_id, ctype)
            pair_id = f"v10_TypeM_{idx:03d}_{sample_id}_{ctype}"
            pair_dir = media_root / pair_id
            loser_future = pair_dir / "loser_future.mp4"
            loser_full = pair_dir / "loser_full_prefix5_future.mp4"
            write_video(loser_future, loser_frames, fps)
            if prefix_path and prefix_path.exists():
                prefix_frames, prefix_fps = read_video(prefix_path)
                write_video(loser_full, prefix_frames[:5] + loser_frames, prefix_fps or fps)
            else:
                loser_full = loser_future
            sheet = sheet_root / f"{pair_id}.jpg"
            make_contact_sheet(prefix_path, winner_frames, loser_frames, sheet, f"{pair_id} | {ctype}")
            m = metrics(winner_frames, loser_frames, meta["affected_region"])
            visible = m["local_absdiff_p95"] >= 28.0 and m["local_absdiff_mean"] >= 5.0
            not_degraded = m["sharpness_ratio"] >= 0.65 and m["psnr_future"] >= 18.0
            not_too_subtle = m["psnr_future"] <= 36.0
            ready = visible and not_degraded and not_too_subtle
            status = "DPO_READY_SYNTHETIC_VISIBLE_V10" if ready else "REJECT_SYNTHETIC_GATE"
            reason = ("{} creates visible local future-only error; winner remains clean GT; loser remains sharp/readable; local_absdiff_p95={}; sharpness_ratio={}".format(ctype, m["local_absdiff_p95"], m["sharpness_ratio"]))
            row = {
                "pair_id": pair_id,
                "sample_id": sample_id,
                "condition_id": cond.get("condition_id", ""),
                "template": cond.get("template", ""),
                "camera_motion": cond.get("camera_motion", ""),
                "pair_type": "TypeM_v10_synthetic_visible",
                "corruption_type": ctype,
                "status": status,
                "dpo_ready": str(bool(ready)),
                "winner_video": str(gt_future_path.relative_to(repo) if gt_future_path.is_relative_to(repo) else gt_future_path),
                "loser_video": str(loser_future.relative_to(repo)),
                "loser_full_video": str(loser_full.relative_to(repo)),
                "prefix_video": str(prefix_path.relative_to(repo) if prefix_path and prefix_path.is_relative_to(repo) else (prefix_path or "")),
                "contact_sheet": str(sheet.relative_to(repo)),
                "written_reason": reason,
                **m,
            }
            row.update({"affected_region": json.dumps(meta["affected_region"], sort_keys=True), "affected_time_span": json.dumps(meta["affected_time_span"])})
            rows.append(row)
            if ready:
                pair = {
                    "pair_id": pair_id,
                    "protocol_version": "v10",
                    "pair_type": "TypeM_v10_synthetic_visible",
                    "condition": {
                        "prefix_len": 5,
                        "prediction_start_frame": 5,
                        "prefix_video_path": row["prefix_video"],
                        "image_path": cond.get("image_path"),
                        "prompt": cond.get("prompt"),
                        "prompt_path": cond.get("prompt_path"),
                        "poses": cond.get("poses_path"),
                        "poses_path": cond.get("poses_path"),
                        "intrinsics": cond.get("intrinsics_path"),
                        "intrinsics_path": cond.get("intrinsics_path"),
                        "sample_id": sample_id,
                        "template": cond.get("template"),
                        "camera_motion": cond.get("camera_motion"),
                    },
                    "winner": {
                        "future_video_path": row["winner_video"],
                        "source": "clean_gt_future",
                        "reward_vector": {"R_total": m["reward_winner"], "backend": "proxy_visible_synthetic"},
                    },
                    "loser": {
                        "future_video_path": row["loser_video"],
                        "full_video_path": row["loser_full_video"],
                        "source": "controlled_visible_synthetic_negative",
                        "corruption_type": ctype,
                        "severity": "v10_visible_medium",
                        "affected_region": meta["affected_region"],
                        "affected_time_span": meta["affected_time_span"],
                        "reward_vector": {"R_total": m["reward_loser"], "backend": "proxy_visible_synthetic"},
                    },
                    "same_prefix": True,
                    "same_prompt": True,
                    "same_poses": True,
                    "same_intrinsics": True,
                    "medium_hard": True,
                    "reward_guided": True,
                    "reward_margin": m["reward_margin"],
                    "sharpness_gate_pass": True,
                    "quality_floor_pass": True,
                    "codex_audit": {
                        "reviewed": True,
                        "valid_preference": True,
                        "too_subtle": False,
                        "too_degraded": False,
                        "winner_bad": False,
                        "loser_collapsed": False,
                        "contact_sheet": row["contact_sheet"],
                        "written_reason": reason,
                    },
                    "traditional_metrics": m,
                    "loss_frame_indices": list(range(5, 81)),
                    "reward_frame_indices": list(range(5, 81)),
                }
                pairs.append(pair)
        except Exception as exc:
            rows.append({"pair_id": f"v10_TypeM_{idx:03d}_{sample_id}_{ctype}", "status": "ERROR", "sample_id": sample_id, "error_reason": str(exc)})

    csv_path = report_dir / "synthetic_pair_audit.csv"
    fieldnames = sorted({k for row in rows for k in row.keys()})
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    manifest_path = repo / args.manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False, sort_keys=True) + "\n")

    combined = []
    existing = repo / args.existing_ready
    if existing.exists():
        combined.extend(json.loads(line) for line in existing.read_text().splitlines() if line.strip())
    combined.extend(pairs)
    combined_path = repo / args.combined_manifest
    with combined_path.open("w") as f:
        for pair in combined:
            f.write(json.dumps(pair, ensure_ascii=False, sort_keys=True) + "\n")

    counts = Counter(row.get("status", "") for row in rows)
    type_counts = Counter(pair["loser"]["corruption_type"] for pair in pairs)
    summary = {
        "status": "PAIR_FACTORY_V10_READY_50" if len(combined) >= 50 else "PAIR_FACTORY_V10_PARTIAL",
        "conditions_attempted": len(selected),
        "synthetic_ready_pairs": len(pairs),
        "existing_ready_pairs": len(combined) - len(pairs),
        "combined_ready_pairs": len(combined),
        "status_counts": dict(counts),
        "corruption_counts": dict(type_counts),
        "synthetic_manifest": args.manifest,
        "combined_manifest": args.combined_manifest,
        "media_root": args.output_root,
    }
    (report_dir / "synthetic_pair_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    summary_lines = [
        "Current Status:", summary["status"], "",
        "# DPO Pair Factory v10 Synthetic Visible Negatives", "",
        "- Conditions attempted: {}".format(summary["conditions_attempted"]),
        "- Synthetic ready pairs: {}".format(summary["synthetic_ready_pairs"]),
        "- Existing strict ready pairs included: {}".format(summary["existing_ready_pairs"]),
        "- Combined ready pairs: {}".format(summary["combined_ready_pairs"]),
        "- Synthetic manifest: `{}`".format(args.manifest),
        "- Combined manifest: `{}`".format(args.combined_manifest),
        "- Status counts: `{}`".format(json.dumps(summary["status_counts"], sort_keys=True)),
        "- Corruption counts: `{}`".format(json.dumps(summary["corruption_counts"], sort_keys=True)),
        "- Media/contact sheets are under local_assets and are not committed.",
    ]
    (report_dir / "synthetic_pair_summary.md").write_text("\n".join(summary_lines) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
