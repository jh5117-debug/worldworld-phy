from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from cam_physgeo.utils.io import read_jsonl, write_jsonl


CORRUPTIONS = [
    "background_drift",
    "nonrigid_background_warp",
    "object_deformation",
    "object_color_identity_change",
    "freeze_foreground",
    "freeze_camera",
    "global_freeze",
    "wrong_camera_motion",
    "camera_shuffle",
    "reobserve_mismatch",
    "remove_object",
    "create_object",
]


def make_corruption_records(
    sample: dict,
    *,
    out_dir: str | Path | None = None,
    dry_run: bool = True,
    types: Iterable[str] | None = None,
    preserve_prefix_frames: int = 1,
    seed: int = 0,
    strength: str = "medium",
) -> list[dict]:
    choices = [c for c in (types or CORRUPTIONS) if c in CORRUPTIONS]
    rows = []
    source_video = sample.get("video_path")
    if not source_video and out_dir and sample.get("hdf5_path") and not dry_run:
        source_video = export_hdf5_video(sample, Path(out_dir) / str(sample.get("sample_id")) / "clean_from_hdf5.mp4")
    for corruption in choices:
        flags = list(sample.get("quality_flags") or [])
        out_path = None
        metadata_path = None
        if out_dir:
            out_path = Path(out_dir) / str(sample.get("sample_id")) / f"{corruption}.mp4"
            metadata_path = out_path.with_suffix(".metadata.json")
        loser = f"corruption://{sample.get('sample_id')}/{corruption}"
        if out_path:
            loser = str(out_path)
            if not dry_run:
                ok, meta = write_corrupted_video(
                    source_video,
                    out_path,
                    corruption,
                    preserve_prefix_frames=preserve_prefix_frames,
                    seed=seed,
                    strength=strength,
                )
                if not ok:
                    flags.append(f"corruption_failed:{corruption}")
                meta.update(
                    {
                        "sample_id": sample.get("sample_id"),
                        "source_video": source_video,
                        "corruption_type": corruption,
                        "source": sample.get("source"),
                        "template": sample.get("template"),
                        "camera_motion": sample.get("camera_motion"),
                    }
                )
                if metadata_path:
                    metadata_path.parent.mkdir(parents=True, exist_ok=True)
                    metadata_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        rows.append(
            {
                "sample_id": sample.get("sample_id"),
                "corruption": corruption,
                "loser_video": loser,
                "source_video": source_video,
                "metadata_path": str(metadata_path) if metadata_path else None,
                "risk": "synthetic_negative",
                "quality_flags": flags,
                "requires_mask": corruption
                in {"object_deformation", "object_color_identity_change", "freeze_foreground", "remove_object"},
            }
        )
    return rows


def export_hdf5_video(sample: dict, out_path: Path, *, num_frames: int = 81, fps: int = 16) -> str | None:
    try:
        from cam_physgeo.data.physion_hdf5_reader import read_physion_sample
        from cam_physgeo.utils.video import write_video_frames

        payload = read_physion_sample(sample["hdf5_path"], limit_frames=int(sample.get("num_frames") or num_frames))
        rgb = payload.get("rgb")
        if rgb is None:
            return None
        ok = write_video_frames(rgb[:num_frames], out_path, fps=int(sample.get("fps") or fps))
        return str(out_path) if ok else None
    except Exception:
        return None


def write_corrupted_video(
    video_path: str | None,
    out_path: Path,
    corruption: str,
    *,
    preserve_prefix_frames: int = 1,
    seed: int = 0,
    strength: str = "medium",
) -> tuple[bool, dict]:
    if not video_path or not Path(str(video_path)).exists():
        return False, {"error": "missing_source_video"}
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        rng = np.random.default_rng(seed)
        cap = cv2.VideoCapture(str(video_path))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 16)
        frames = []
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(frame)
        cap.release()
        if not frames:
            return False, {"error": "empty_source_video"}
        h, w = frames[0].shape[:2]
        first_mutable = max(0, int(preserve_prefix_frames))
        affected = list(range(first_mutable, len(frames)))
        frames_out = [f.copy() for f in frames]
        s = {"low": 0.55, "medium": 1.0, "high": 1.55}.get(str(strength).lower(), 1.0)

        if corruption in {"freeze_camera", "global_freeze"}:
            base = frames[first_mutable if first_mutable < len(frames) else 0].copy()
            for i in affected:
                frames_out[i] = base.copy()
        elif corruption in {"camera_shuffle", "wrong_camera_motion"}:
            tail = list(reversed(frames_out[first_mutable:]))
            frames_out = frames_out[:first_mutable] + tail
        elif corruption == "background_drift":
            for i in affected:
                dx = int(round((i - first_mutable + 1) * w / max(len(affected), 1) * 0.10 * s))
                mat = np.float32([[1, 0, dx], [0, 1, 0]])
                frames_out[i] = cv2.warpAffine(frames_out[i], mat, (w, h), borderMode=cv2.BORDER_REFLECT)
        elif corruption == "nonrigid_background_warp":
            for i in affected:
                xmap, ymap = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
                xmap = xmap + (8.0 * s) * np.sin((ymap / max(8.0, 24.0 / s)) + i * 0.25)
                frames_out[i] = cv2.remap(frames_out[i], xmap, ymap, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        elif corruption in {"object_deformation", "object_color_identity_change", "freeze_foreground", "remove_object", "create_object"}:
            x0, y0, x1, y1 = int(w * 0.35), int(h * 0.28), int(w * 0.65), int(h * 0.70)
            frozen = frames_out[first_mutable][y0:y1, x0:x1].copy() if first_mutable < len(frames_out) else None
            for i in affected:
                patch = frames_out[i][y0:y1, x0:x1].copy()
                if corruption == "object_deformation":
                    patch = cv2.resize(patch, (max(1, x1 - x0 + int(28 * s)), max(1, y1 - y0 - int(24 * s))))
                    patch = cv2.resize(patch, (x1 - x0, y1 - y0))
                elif corruption == "object_color_identity_change":
                    patch[..., 1] = np.clip(patch[..., 1].astype(np.float32) * max(0.1, 0.5 / s) + 95 * s, 0, 255).astype(np.uint8)
                elif corruption == "freeze_foreground" and frozen is not None:
                    patch = frozen.copy()
                elif corruption == "remove_object":
                    patch[:] = np.mean(frames_out[i], axis=(0, 1), keepdims=True).astype(np.uint8)
                elif corruption == "create_object":
                    color = rng.integers(30, 230, size=(3,), dtype=np.uint8).tolist()
                    cv2.circle(patch, (patch.shape[1] // 2, patch.shape[0] // 2), max(8, int(min(w, h) // 18 * s)), color, -1)
                frames_out[i][y0:y1, x0:x1] = patch
        elif corruption == "reobserve_mismatch":
            if len(frames_out) > first_mutable + 4:
                ref = frames_out[first_mutable].copy()
                for i in affected[len(affected) // 2 :]:
                    alpha = max(0.15, 0.40 / s)
                    frames_out[i] = cv2.addWeighted(frames_out[i], alpha, ref, 1.0 - alpha, 0)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        for frame in frames_out:
            writer.write(frame)
        writer.release()
        meta = {
            "affected_frames": affected,
            "affected_object_id": None,
            "mask_ratio": round(((x1 - x0) * (y1 - y0)) / float(w * h), 6) if "x0" in locals() else None,
            "params": {"preserve_prefix_frames": preserve_prefix_frames, "seed": seed, "strength": strength, "strength_scale": s, "fallback_region": "center_crop"},
            "preserves_first_frame": first_mutable >= 1,
            "mask_source": "physion_id_mask_when_available_else_center_crop",
        }
        return out_path.exists(), meta
    except Exception as exc:
        return False, {"error": repr(exc)}


def make_contact_sheet(video_paths: list[str], out_path: Path) -> bool:
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        thumbs = []
        for path in video_paths:
            cap = cv2.VideoCapture(str(path))
            ok, frame = cap.read()
            cap.release()
            if ok:
                thumbs.append(cv2.resize(frame, (160, 96)))
        if not thumbs:
            return False
        sheet = np.concatenate(thumbs, axis=1)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        return bool(cv2.imwrite(str(out_path), sheet))
    except Exception:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--source", default="", choices=["", "physion_official", "physion_movingcam"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--types", nargs="+", default=["background_drift", "global_freeze"])
    ap.add_argument("--make_contact_sheet", action="store_true")
    ap.add_argument("--strength", default="medium", choices=["low", "medium", "high"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--preserve_prefix_frames", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    rows = []
    videos = []
    count = 0
    for sample in read_jsonl(args.manifest):
        if args.source and sample.get("source") != args.source:
            continue
        if args.limit and count >= args.limit:
            break
        recs = make_corruption_records(
            sample,
            out_dir=args.out,
            dry_run=args.dry_run,
            types=args.types,
            preserve_prefix_frames=args.preserve_prefix_frames,
            seed=args.seed + count,
            strength=args.strength,
        )
        rows.extend(recs)
        videos.extend([r["loser_video"] for r in recs if r.get("loser_video") and not str(r["loser_video"]).startswith("corruption://")])
        count += 1
    manifest_out = Path(args.out) / "corruptions_manifest.jsonl"
    if not args.dry_run:
        write_jsonl(rows, manifest_out)
        if args.make_contact_sheet:
            make_contact_sheet(videos[:12], Path(args.out) / "contact_sheet.jpg")
    print({"samples": count, "corruptions": len(rows), "out": args.out, "dry_run": args.dry_run})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
