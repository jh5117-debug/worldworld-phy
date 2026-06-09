from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def _probe_video_cv2(path: Path, reason: str) -> dict[str, Any]:
    try:
        import cv2  # type: ignore
    except Exception as exc:
        return {"exists": True, "ok": False, "error": f"{reason}; cv2_unavailable:{exc!r}"}

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"exists": True, "ok": False, "error": f"{reason}; cv2_open_failed"}
    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        ok = width > 0 and height > 0 and frame_count > 0
        return {
            "exists": True,
            "ok": ok,
            "probe_backend": "cv2",
            "width": width,
            "height": height,
            "avg_frame_rate": fps,
            "nb_frames": frame_count,
            "error": None if ok else f"{reason}; cv2_invalid_stream",
        }
    finally:
        cap.release()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _read_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _probe_video(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "missing"}
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate,nb_frames,duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
        payload = json.loads(proc.stdout)
        stream = (payload.get("streams") or [{}])[0]
        return {"exists": True, "ok": True, "probe_backend": "ffprobe", **stream}
    except FileNotFoundError as exc:
        return _probe_video_cv2(path, f"ffprobe_missing:{exc!r}")
    except Exception as exc:
        fallback = _probe_video_cv2(path, f"ffprobe_failed:{exc!r}")
        if fallback.get("ok"):
            return fallback
        return {"exists": True, "ok": False, "error": fallback.get("error") or repr(exc)}


def _shape(path: str | Path) -> list[int] | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return list(np.load(p).shape)
    except Exception:
        return None


def _norm(path: str | Path) -> float | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return float(np.linalg.norm(np.load(p)))
    except Exception:
        return None


def _image_size(path: str | Path) -> list[int] | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        with Image.open(p) as img:
            return [img.width, img.height]
    except Exception:
        return None


def audit(args: argparse.Namespace) -> dict[str, Any]:
    rows = _load_jsonl(Path(args.manifest))[: args.max_samples or None]
    invalid: list[dict[str, Any]] = []
    video_pass = 0
    duplicate_ids = [sample_id for sample_id, n in Counter(r.get("sample_id") for r in rows).items() if n > 1]
    shape_counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        reasons: list[str] = []
        sample_id = row.get("sample_id")
        sample_dir = Path(row.get("sample_dir", ""))
        for key in ["target_video_path", "image_path", "poses_path", "intrinsics_path", "action_path", "prompt_path", "metadata_path"]:
            if not Path(row.get(key) or "").exists():
                reasons.append(f"missing:{key}")
        if args.probe_videos:
            probe = _probe_video(Path(row.get("target_video_path") or ""))
            row["video_probe"] = probe
            if probe.get("ok"):
                video_pass += 1
            else:
                reasons.append(f"video_probe:{probe.get('error')}")
        if args.check_numpy_shapes:
            for key in ["poses_path", "intrinsics_path", "action_path"]:
                shape = _shape(row.get(key) or "")
                row[key.replace("_path", "_shape")] = shape
                shape_counts[key][str(shape)] += 1
                if shape is None:
                    reasons.append(f"bad_shape:{key}")
            action_norm = _norm(row.get("action_path") or "")
            row["computed_action_norm"] = action_norm
            if action_norm is None or abs(action_norm) > 1e-7:
                reasons.append("action_not_zero")
        if args.check_metadata:
            meta = _read_json(row.get("metadata_path") or "")
            row["metadata_use_action"] = meta.get("use_action")
            if meta.get("use_action") is not False:
                reasons.append("metadata_use_action_not_false")
        if args.check_prompts:
            prompt = Path(row.get("prompt_path") or "").read_text(encoding="utf-8", errors="ignore").strip() if Path(row.get("prompt_path") or "").exists() else ""
            if not prompt:
                reasons.append("empty_prompt")
            row["prompt_preview"] = prompt[:120]
        row["image_size"] = _image_size(row.get("image_path") or "")
        if row["image_size"] is None:
            reasons.append("bad_image")
        if sample_id in duplicate_ids:
            reasons.append("duplicate_sample_id")
        if sample_dir.is_symlink() and not sample_dir.exists():
            reasons.append("broken_sample_dir_symlink")
        if reasons:
            invalid.append({"sample_id": sample_id, "reasons": reasons})
    valid_count = len(rows) - len(invalid)
    return {
        "manifest": args.manifest,
        "total_samples": len(rows),
        "valid_samples": valid_count,
        "invalid_samples": len(invalid),
        "invalid": invalid[:100],
        "video_probe_pass": video_pass,
        "duplicate_sample_ids": duplicate_ids,
        "template_distribution": dict(Counter(r.get("template") for r in rows)),
        "camera_distribution": dict(Counter(r.get("camera_variant") for r in rows)),
        "numpy_shape_summary": {key: dict(counter) for key, counter in shape_counts.items()},
        "ready_for_dataloader": valid_count == len(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--probe_videos", action="store_true")
    parser.add_argument("--check_numpy_shapes", action="store_true")
    parser.add_argument("--check_metadata", action="store_true")
    parser.add_argument("--check_prompts", action="store_true")
    parser.add_argument("--max_samples", type=int, default=0)
    args = parser.parse_args()
    result = audit(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ready_for_dataloader"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
