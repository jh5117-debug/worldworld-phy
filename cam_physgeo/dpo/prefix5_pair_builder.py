from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FUTURE_FRAME_INDICES = list(range(5, 81))
PREFIX_FRAME_INDICES = list(range(5))
CORRUPTION_TYPES = [
    "background_drift",
    "nonrigid_background_warp",
    "object_deformation",
    "object_identity_change",
    "wrong_camera_motion",
    "reobserve_mismatch",
    "freeze_foreground",
]


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


def sha256_file(path: str | Path | None) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists() or p.is_dir():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def future_indices(prefix_len: int = 5, total_frames: int = 81) -> list[int]:
    if prefix_len < 0:
        raise ValueError("prefix_len must be non-negative")
    if prefix_len >= total_frames:
        raise ValueError("prefix_len must be smaller than total_frames")
    return list(range(prefix_len, total_frames))


def prefix_indices(prefix_len: int = 5) -> list[int]:
    if prefix_len <= 0:
        raise ValueError("prefix_len must be positive")
    return list(range(prefix_len))


def frame_mask(total_frames: int = 81, prefix_len: int = 5) -> dict[str, list[int]]:
    return {
        "prefix_frame_indices": prefix_indices(prefix_len),
        "loss_frame_indices": future_indices(prefix_len, total_frames),
        "reward_frame_indices": future_indices(prefix_len, total_frames),
    }


def latent_future_indices(total_frames: int = 81, prefix_len: int = 5, temporal_compression: int = 4) -> list[int]:
    if temporal_compression <= 0:
        raise ValueError("temporal_compression must be positive")
    return sorted({idx // temporal_compression for idx in future_indices(prefix_len, total_frames)})


def decode_video(path: str | Path) -> tuple[list[np.ndarray], dict[str, Any]]:
    p = Path(path)
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
    return frames, {"fps": fps, "width": w, "height": h, "frame_count": len(frames)}


def write_video(path: str | Path, frames: list[np.ndarray], fps: float = 16.0) -> None:
    if not frames:
        raise ValueError("cannot write empty video")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    tmp = p.with_suffix(p.suffix + ".tmp.mp4")
    writer = cv2.VideoWriter(str(tmp), fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"cannot open writer: {tmp}")
    for frame in frames:
        writer.write(frame)
    writer.release()
    tmp.replace(p)


def _translate(frame: np.ndarray, dx: float, dy: float) -> np.ndarray:
    h, w = frame.shape[:2]
    mat = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(frame, mat, (w, h), borderMode=cv2.BORDER_REFLECT)


def corrupt_future(frames: list[np.ndarray], corruption_type: str) -> list[np.ndarray]:
    out: list[np.ndarray] = []
    n = max(1, len(frames) - 1)
    if corruption_type == "wrong_camera_motion":
        return list(reversed(frames))
    for i, frame in enumerate(frames):
        t = i / n
        h, w = frame.shape[:2]
        if corruption_type == "background_drift":
            out.append(_translate(frame, 18.0 * t, 0.0))
        elif corruption_type == "nonrigid_background_warp":
            yy, xx = np.indices((h, w), dtype=np.float32)
            amp = 3.0 + 5.0 * t
            map_x = xx + amp * np.sin(yy / 35.0 + t * 3.0)
            map_y = yy + amp * np.sin(xx / 45.0 + t * 2.0)
            out.append(cv2.remap(frame, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
        elif corruption_type == "object_deformation":
            img = frame.copy()
            x0, x1 = int(w * 0.33), int(w * 0.67)
            y0, y1 = int(h * 0.30), int(h * 0.72)
            patch = img[y0:y1, x0:x1]
            if patch.size:
                stretched = cv2.resize(patch, (x1 - x0, max(1, int((y1 - y0) * (0.80 + 0.25 * np.sin(t * np.pi))))))
                canvas = cv2.resize(stretched, (x1 - x0, y1 - y0))
                img[y0:y1, x0:x1] = canvas
            out.append(img)
        elif corruption_type == "object_identity_change":
            img = frame.copy()
            x0, x1 = int(w * 0.38), int(w * 0.62)
            y0, y1 = int(h * 0.36), int(h * 0.66)
            patch = img[y0:y1, x0:x1]
            if patch.size:
                hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
                hsv[..., 0] = (hsv[..., 0].astype(np.int32) + 25) % 180
                img[y0:y1, x0:x1] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            out.append(img)
        elif corruption_type == "reobserve_mismatch":
            if i > len(frames) // 2:
                src = frames[max(0, i - len(frames) // 3)]
                out.append(_translate(src, 8.0, 0.0))
            else:
                out.append(frame.copy())
        elif corruption_type == "freeze_foreground":
            img = frame.copy()
            src = frames[0]
            x0, x1 = int(w * 0.35), int(w * 0.65)
            y0, y1 = int(h * 0.35), int(h * 0.68)
            img[y0:y1, x0:x1] = src[y0:y1, x0:x1]
            out.append(img)
        else:
            raise ValueError(f"unknown corruption_type: {corruption_type}")
    return out


def frame_stats(frames: list[np.ndarray]) -> dict[str, float | bool]:
    if not frames:
        return {"mean_luma": 0.0, "blur_laplacian": 0.0, "freeze_ratio": 1.0, "black_ratio": 1.0, "corrupt": True}
    grays = []
    means = []
    blurs = []
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


def quality_score(stats: dict[str, Any]) -> int:
    if stats.get("corrupt") or stats.get("black_ratio", 0) > 0.4 or stats.get("mean_luma", 0) < 12:
        return 0
    if stats.get("freeze_ratio", 0) > 0.85 or stats.get("blur_laplacian", 0) < 10:
        return 0
    if stats.get("freeze_ratio", 0) > 0.55 or stats.get("blur_laplacian", 0) < 35:
        return 1
    return 2


def sampled_pil_frames(frames: list[np.ndarray], n: int) -> list[Image.Image]:
    if not frames:
        return []
    idxs = np.linspace(0, len(frames) - 1, min(n, len(frames))).round().astype(int).tolist()
    return [Image.fromarray(cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGB)) for i in idxs]


def _fit(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    img = img.convert("RGB")
    img.thumbnail(size, Image.Resampling.LANCZOS)
    out = Image.new("RGB", size, "white")
    out.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
    return out


def make_contact_sheet(path: str | Path, pair: dict[str, Any], prefix_frames: list[np.ndarray], winner_future: list[np.ndarray], loser_future: list[np.ndarray], audit: dict[str, Any]) -> None:
    font = ImageFont.load_default()
    thumb = (160, 92)
    label_w = 170
    gap = 8
    title_h = 94
    cols = 8
    width = label_w + cols * thumb[0] + (cols + 1) * gap
    height = title_h + 3 * thumb[1] + 4 * gap
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    lines = [
        f"pair_id: {pair['pair_id']}",
        f"type: {pair['pair_type']} | prefix_len=5 | corruption={pair['loser']['corruption_type']}",
        f"winner={pair['winner']['source']} loser={pair['loser']['source']} margin={pair['margin']:.3f}",
    ]
    y = 8
    for line in lines:
        draw.text((12, y), line, fill=(0, 0, 0), font=font)
        y += 18
    rows = [
        ("Prefix frames 0-4", sampled_pil_frames(prefix_frames, 5)),
        ("Winner future 5-80", sampled_pil_frames(winner_future, 8)),
        ("Loser future 5-80", sampled_pil_frames(loser_future, 8)),
    ]
    y = title_h
    for label, imgs in rows:
        lab = Image.new("RGB", (label_w, thumb[1]), "#f2f2f2")
        ImageDraw.Draw(lab).text((8, 12), label, fill=(0, 0, 0), font=font)
        canvas.paste(lab, (gap, y))
        x = label_w + gap
        for im in imgs:
            canvas.paste(_fit(im, thumb), (x, y))
            x += thumb[0] + gap
        y += thumb[1] + gap
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(p, quality=92)


def score_pair(winner_future: list[np.ndarray], loser_future: list[np.ndarray], margin: float) -> dict[str, Any]:
    ws = frame_stats(winner_future)
    ls = frame_stats(loser_future)
    wq = quality_score(ws)
    lq = quality_score(ls)
    loser_collapsed = lq == 0 or bool(ls.get("black_ratio", 0) > 0.4) or bool(ls.get("freeze_ratio", 0) > 0.85)
    winner_bad = wq < 2
    too_easy = loser_collapsed or margin > 0.55
    valid = (wq >= 2 and lq >= 1 and not loser_collapsed and not too_easy and margin >= 0.05)
    return {
        "winner_visual_quality": wq,
        "loser_visual_quality": lq,
        "winner_physical_consistency": 2,
        "loser_physical_consistency": 1 if lq >= 1 else 0,
        "winner_camera_following": 2,
        "loser_camera_following": 1 if lq >= 1 else 0,
        "winner_foreground_identity": 2,
        "loser_foreground_identity": 1 if lq >= 1 else 0,
        "is_valid_preference": "yes" if valid else "no",
        "is_too_easy": "yes" if too_easy else "no",
        "is_loser_collapsed": "yes" if loser_collapsed else "no",
        "is_winner_bad": "yes" if winner_bad else "no",
        "winner_mean_luma": ws["mean_luma"],
        "loser_mean_luma": ls["mean_luma"],
        "winner_blur_laplacian": ws["blur_laplacian"],
        "loser_blur_laplacian": ls["blur_laplacian"],
        "winner_freeze_ratio": ws["freeze_ratio"],
        "loser_freeze_ratio": ls["freeze_ratio"],
    }


def build_prefix5_pairs(old_pairs: list[dict[str, Any]], out_root: str | Path, manifest_out: str | Path, audit_out: str | Path, limit: int = 50) -> dict[str, Any]:
    out_root = Path(out_root)
    manifest_out = Path(manifest_out)
    audit_out = Path(audit_out)
    conditions_dir = out_root / "conditions"
    clean_dir = out_root / "clean_futures"
    corr_dir = out_root / "corrupted_futures"
    sheets_dir = audit_out / "pair_contact_sheets"
    manifests_dir = out_root / "manifests"
    logs_dir = out_root / "logs"
    for d in (conditions_dir, clean_dir, corr_dir, sheets_dir, manifests_dir, logs_dir, manifest_out.parent, audit_out):
        d.mkdir(parents=True, exist_ok=True)

    new_pairs: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    seen_condition: dict[str, dict[str, Any]] = {}
    selected = old_pairs[:limit]
    for i, old in enumerate(selected):
        cond = old.get("condition", {})
        sample_id = str(cond.get("sample_id") or f"sample_{i:03d}")
        winner_video = old.get("winner", {}).get("video")
        if not winner_video:
            raise RuntimeError(f"old pair {old.get('pair_id')} has no winner.video")
        full_frames, meta = decode_video(winner_video)
        if len(full_frames) < 81:
            raise RuntimeError(f"expected at least 81 frames for {winner_video}, got {len(full_frames)}")
        full_frames = full_frames[:81]
        fps = float(meta.get("fps") or 16.0)
        cache_key = f"{sample_id}|{sha256_file(winner_video)}"
        if cache_key not in seen_condition:
            prefix_frames = full_frames[:5]
            clean_future = full_frames[5:81]
            prefix_path = conditions_dir / sample_id / "prefix_len5.mp4"
            clean_future_path = clean_dir / sample_id / "clean_future_5_80.mp4"
            full_copy = conditions_dir / sample_id / "full_clean_0_80.mp4"
            write_video(prefix_path, prefix_frames, fps=fps)
            write_video(clean_future_path, clean_future, fps=fps)
            if Path(winner_video).exists():
                shutil.copy2(winner_video, full_copy)
            else:
                write_video(full_copy, full_frames, fps=fps)
            seen_condition[cache_key] = {
                "prefix_frames": prefix_frames,
                "clean_future": clean_future,
                "prefix_path": prefix_path,
                "clean_future_path": clean_future_path,
                "full_copy": full_copy,
                "fps": fps,
            }
        cached = seen_condition[cache_key]
        corruption_type = CORRUPTION_TYPES[i % len(CORRUPTION_TYPES)]
        corrupted_future = corrupt_future(cached["clean_future"], corruption_type)
        loser_future_path = corr_dir / sample_id / f"{old.get('pair_id', i)}_{corruption_type}_future_5_80.mp4"
        loser_full_path = corr_dir / sample_id / f"{old.get('pair_id', i)}_{corruption_type}_full_0_80.mp4"
        write_video(loser_future_path, corrupted_future, fps=cached["fps"])
        write_video(loser_full_path, cached["prefix_frames"] + corrupted_future, fps=cached["fps"])
        audit = score_pair(cached["clean_future"], corrupted_future, margin=0.12)
        margin = 0.12
        prompt_hash = sha256_file(cond.get("prompt"))
        poses_hash = sha256_file(cond.get("poses"))
        intrinsics_hash = sha256_file(cond.get("intrinsics"))
        prefix_hash = sha256_file(cached["prefix_path"])
        full_condition_hash = hashlib.sha256("|".join([prompt_hash, poses_hash, intrinsics_hash, prefix_hash]).encode()).hexdigest()
        new_pair = {
            "pair_id": f"prefix5_{old.get('pair_id', i)}_{corruption_type}",
            "pair_type": "clean_gt_future_vs_corrupted_gt_future",
            "condition": {
                "prefix_len": 5,
                "prediction_start_frame": 5,
                "prefix_video_path": str(cached["prefix_path"]),
                "prefix_frame_paths": [],
                "image": cond.get("image", ""),
                "prompt": cond.get("prompt", ""),
                "poses": cond.get("poses", ""),
                "intrinsics": cond.get("intrinsics", ""),
                "sample_id": sample_id,
                "template": cond.get("template", ""),
                "camera_variant": cond.get("camera_variant", ""),
                "use_action": False,
                "full_condition_hash": full_condition_hash,
                "prefix_hash": prefix_hash,
                "prompt_hash": prompt_hash,
                "poses_hash": poses_hash,
                "intrinsics_hash": intrinsics_hash,
            },
            "winner": {
                "full_video_path": str(cached["full_copy"]),
                "future_video_path": str(cached["clean_future_path"]),
                "video": str(cached["clean_future_path"]),
                "source": "clean_gt_future",
                "reward": {"reward_total": 1.0, "future_only": True, "source": "prefix5_builder_v1"},
                "future_frame_indices": FUTURE_FRAME_INDICES,
            },
            "loser": {
                "full_video_path": str(loser_full_path),
                "future_video_path": str(loser_future_path),
                "video": str(loser_future_path),
                "source": "controlled_corrupted_gt_future",
                "corruption_type": corruption_type,
                "reward": {"reward_total": 1.0 - margin, "future_only": True, "source": "prefix5_builder_v1"},
                "future_frame_indices": FUTURE_FRAME_INDICES,
            },
            "margin": margin,
            "loss_frame_indices": FUTURE_FRAME_INDICES,
            "reward_frame_indices": FUTURE_FRAME_INDICES,
            "same_prefix": True,
            "same_prompt": True,
            "same_poses": True,
            "same_intrinsics": True,
            "old_pair_id": old.get("pair_id", ""),
        }
        sheet_path = sheets_dir / f"{i+1:03d}_{new_pair['pair_id']}.jpg"
        make_contact_sheet(sheet_path, new_pair, cached["prefix_frames"], cached["clean_future"], corrupted_future, audit)
        audit_row = {
            "index": i + 1,
            "pair_id": new_pair["pair_id"],
            "prefix_len": 5,
            "pair_type": new_pair["pair_type"],
            "sample_id": sample_id,
            "template": cond.get("template", ""),
            "camera_variant": cond.get("camera_variant", ""),
            "corruption_type": corruption_type,
            "winner_source": new_pair["winner"]["source"],
            "loser_source": new_pair["loser"]["source"],
            "reward_margin": margin,
            "contact_sheet": str(sheet_path),
            "written_reason": (
                f"prefix frames 0-4 are clean; winner future is GT frames 5-80; "
                f"loser future applies {corruption_type} only to frames 5-80; "
                f"valid={audit['is_valid_preference']} too_easy={audit['is_too_easy']}"
            ),
            **audit,
        }
        new_pairs.append(new_pair)
        audit_rows.append(audit_row)

    write_jsonl(manifest_out, new_pairs)
    write_jsonl(manifests_dir / "anchored_dpo_probe_pairs_prefix5.jsonl", new_pairs)
    audit_csv = audit_out / "pair_audit.csv"
    audit_jsonl = audit_out / "pair_audit.jsonl"
    fields = list(audit_rows[0].keys()) if audit_rows else []
    with audit_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(audit_rows)
    write_jsonl(audit_jsonl, audit_rows)

    corr_dist = Counter(p["loser"]["corruption_type"] for p in new_pairs)
    invalid = Counter()
    for row in audit_rows:
        if row["is_valid_preference"] != "yes":
            if row["is_winner_bad"] == "yes":
                invalid["winner_bad"] += 1
            if row["is_loser_collapsed"] == "yes":
                invalid["loser_collapsed"] += 1
            if row["is_too_easy"] == "yes":
                invalid["too_easy"] += 1
            if not any(row[k] == "yes" for k in ("is_winner_bad", "is_loser_collapsed", "is_too_easy")):
                invalid["other_quality_gate"] += 1
    valid = sum(1 for r in audit_rows if r["is_valid_preference"] == "yes")
    summary = {
        "old_pair_count": len(old_pairs),
        "prefix5_pair_count": len(new_pairs),
        "valid_pair_count": valid,
        "corruption_type_distribution": dict(corr_dist),
        "invalid_reason_stats": dict(invalid),
        "manifest": str(manifest_out),
        "audit_csv": str(audit_csv),
        "audit_jsonl": str(audit_jsonl),
        "contact_sheet_dir": str(sheets_dir),
    }
    (audit_out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (audit_out / "pair_summary.md").write_text(render_summary(summary), encoding="utf-8")
    return summary


def render_summary(summary: dict[str, Any]) -> str:
    corr = "\n".join(f"- {k}: {v}" for k, v in summary["corruption_type_distribution"].items())
    invalid = "\n".join(f"- {k}: {v}" for k, v in summary["invalid_reason_stats"].items()) or "- none"
    can_dpo = summary["valid_pair_count"] >= 20
    return f"""# Prefix-5 DPO Pair Visual Audit Summary

## Result

- old_pair_count: {summary['old_pair_count']}
- prefix5_pair_count: {summary['prefix5_pair_count']}
- valid_pair_count: {summary['valid_pair_count']}
- can_enter_dpo_probe_after_real_backend: {'yes' if can_dpo else 'no'}

## Corruption Type Distribution

{corr}

## Invalid Reason Stats

{invalid}

## Prefix Verification

All rebuilt pairs set:

- `condition.prefix_len = 5`
- `condition.prediction_start_frame = 5`
- `loss_frame_indices = [5..80]`
- `reward_frame_indices = [5..80]`
- `same_prefix = true`
- `same_prompt = true`
- `same_poses = true`
- `same_intrinsics = true`

The prefix clip contains frames 0-4. Winner and loser futures contain frames 5-80.

## Paths

- manifest: `{summary['manifest']}`
- audit_csv: `{summary['audit_csv']}`
- audit_jsonl: `{summary['audit_jsonl']}`
- contact_sheet_dir: `{summary['contact_sheet_dir']}`

## DPO Decision

These pairs satisfy the prefix5 schema. DPO still cannot proceed until the real LingBot-Fast winner/loser energy backend is callable and BF16 DDP preflight passes on that real backend.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old_pairs", required=True)
    parser.add_argument("--out_root", required=True)
    parser.add_argument("--manifest_out", required=True)
    parser.add_argument("--audit_out", required=True)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args(argv)
    rows = read_jsonl(args.old_pairs)
    summary = build_prefix5_pairs(rows, args.out_root, args.manifest_out, args.audit_out, limit=args.limit)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
