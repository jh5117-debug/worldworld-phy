from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from cam_physgeo.data.physeditworld_schema import normalize_sample, status_from_errors, validate_sample
from cam_physgeo.data.physeditworld_split import main as split_main
from cam_physgeo.utils.io import write_jsonl

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}
ACTION_HINTS = ("action", "actions", "trace", "control")
CAMERA_HINTS = ("camera", "pose", "trajectory", "traj", "extrinsic")
INTRINSIC_HINTS = ("intrinsic", "intrinsics", "calib", "camera_matrix")
GRAVITY_RE = re.compile(r"(?:gravity|grav|g)[_=-]?([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
PHYS_HINTS = ("physedit", "gravity", "replay", "action", "engine_state")


def bounded_walk(roots: list[Path], max_depth: int = 7):
    for root in roots:
        if not root.exists():
            continue
        root = root.resolve()
        for dirpath, dirnames, filenames in os.walk(root):
            p = Path(dirpath)
            depth = len(p.relative_to(root).parts)
            if depth >= max_depth:
                dirnames[:] = []
            yield p, [p / name for name in filenames]


def infer_gravity(path: Path) -> tuple[float | None, str | None]:
    text = str(path).lower()
    m = GRAVITY_RE.search(text)
    if not m:
        return None, None
    val = float(m.group(1))
    return val, f"{val:g}g"


def first_matching(files: list[Path], hints: tuple[str, ...], exts: tuple[str, ...] = (".json", ".jsonl", ".npy", ".npz", ".txt", ".csv")) -> str | None:
    for file in files:
        low = file.name.lower()
        if file.suffix.lower() in exts and any(h in low for h in hints):
            return str(file)
    return None


def load_metadata(files: list[Path]) -> dict[str, Any]:
    for file in files:
        if file.suffix.lower() != ".json":
            continue
        low = file.name.lower()
        if not any(k in low for k in ["metadata", "meta", "gravity", "replay", "scene"]):
            continue
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            return data
    return {}


def probe_video(path: Path) -> dict[str, Any]:
    info = {"num_frames": None, "fps": None, "height": None, "width": None, "duration_sec": None, "video_decodable": False}
    if os.environ.get("PHYS_EDIT_WORLD_SKIP_VIDEO_PROBE") == "1":
        return info
    try:
        import cv2  # type: ignore
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return info
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        cap.release()
        info.update({"num_frames": frames or None, "fps": fps or None, "width": width or None, "height": height or None, "duration_sec": (frames / fps if frames and fps else None), "video_decodable": bool(frames and fps)})
    except Exception:
        pass
    return info


def make_sample(video: Path, files: list[Path], source_root: Path) -> dict[str, Any]:
    meta = load_metadata(files)
    g_value = meta.get("gravity_value") or meta.get("gravity") or meta.get("gravity_g")
    g_label = meta.get("gravity_label")
    if g_value is None and g_label is None:
        g_value, g_label = infer_gravity(video)
    scene = str(meta.get("scene_id") or meta.get("scene") or video.parent.name)
    initial = str(meta.get("initial_state_id") or meta.get("initial_state") or "unknown_initial_state")
    action = str(meta.get("action_trace_id") or meta.get("action_id") or "unknown_action")
    camera = str(meta.get("camera_policy_id") or meta.get("camera_id") or "unknown_camera")
    sample = {
        "sample_id": meta.get("sample_id"),
        "replay_group_id": meta.get("replay_group_id"),
        "scene_id": scene,
        "initial_state_id": initial,
        "action_trace_id": action,
        "camera_policy_id": camera,
        "gravity_value": g_value,
        "gravity_label": g_label,
        "video_path": str(video),
        "prefix_video_path": meta.get("prefix_video_path"),
        "image_path": meta.get("image_path"),
        "action_trace_path": meta.get("action_trace_path") or first_matching(files, ACTION_HINTS),
        "camera_trajectory_path": meta.get("camera_trajectory_path") or first_matching(files, CAMERA_HINTS),
        "intrinsics_path": meta.get("intrinsics_path") or first_matching(files, INTRINSIC_HINTS),
        "engine_state_path": meta.get("engine_state_path") or first_matching(files, ("engine", "state")),
        "semantic_annotation_path": meta.get("semantic_annotation_path") or first_matching(files, ("semantic", "annotation", "seg")),
        "depth_path": meta.get("depth_path") or first_matching(files, ("depth",)),
        "normal_path": meta.get("normal_path") or first_matching(files, ("normal",)),
        "prompt": meta.get("prompt"),
        "source_root": str(source_root),
    }
    sample.update(probe_video(video))
    sample = normalize_sample(sample)
    errors = validate_sample(sample, check_paths=True)
    video_text = str(video).lower()
    if "physinone" in video_text and "physedit" not in video_text:
        errors.append("not_physeditworld_source")
    if str(sample.get("action_trace_id")) == "unknown_action":
        errors.append("missing_matched_action_trace_id")
    if str(sample.get("camera_policy_id")) == "unknown_camera":
        errors.append("missing_matched_camera_policy_id")
    gravity_value = sample.get("gravity_value")
    if gravity_value is not None:
        try:
            if float(gravity_value) <= 0 or float(gravity_value) > 10:
                errors.append("invalid_gravity_value_for_prompt_condition")
        except Exception:
            errors.append("invalid_gravity_value_for_prompt_condition")
    if not sample.get("video_decodable"):
        errors.append("video_not_decodable_or_unprobed")
    status, reason = status_from_errors(errors)
    if status == "OK" and not sample.get("video_decodable"):
        status, reason = "VIDEO_DECODE_UNVERIFIED", "video_not_decodable_or_unprobed"
    sample["status"] = status
    sample["error_reason"] = reason
    return sample


def discover_samples(roots: list[Path], target_hours: float, max_depth: int = 7) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_sec = 0.0
    for dirpath, files in bounded_walk(roots, max_depth=max_depth):
        dir_text = str(dirpath).lower()
        file_text = " ".join(file.name.lower() for file in files)
        if not any(h in dir_text or h in file_text for h in PHYS_HINTS):
            continue
        videos = [file for file in files if file.suffix.lower() in VIDEO_EXTS]
        if not videos:
            continue
        for video in sorted(videos):
            if str(video) in seen:
                continue
            seen.add(str(video))
            row = make_sample(video, files, source_root=next((root for root in roots if str(video).startswith(str(root.resolve()))), roots[0]))
            rows.append(row)
            if row.get("status") == "OK" and row.get("duration_sec"):
                total_sec += float(row["duration_sec"])
                if total_sec >= target_hours * 3600:
                    return rows
    return rows



def discover_samples_from_candidates(candidate_file: Path, target_hours: float, max_candidates: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_videos: set[str] = set()
    total_sec = 0.0
    lines = [Path(line.strip()) for line in candidate_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if max_candidates is not None:
        lines = lines[:max_candidates]
    for item in lines:
        dirs: list[Path] = []
        if item.is_dir():
            dirs.append(item)
        elif item.exists():
            dirs.append(item.parent)
        else:
            continue
        for directory in dirs:
            try:
                files = [p for p in directory.iterdir() if p.is_file()]
            except Exception:
                continue
            videos = [file for file in files if file.suffix.lower() in VIDEO_EXTS]
            for video in videos:
                key = str(video.resolve())
                if key in seen_videos:
                    continue
                seen_videos.add(key)
                row = make_sample(video, files, source_root=directory)
                rows.append(row)
                if row.get("status") == "OK" and row.get("duration_sec"):
                    total_sec += float(row["duration_sec"])
                    if total_sec >= target_hours * 3600:
                        return rows
    return rows

def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for row in rows for k in row})
    with path.open("w", encoding="utf-8") as f:
        f.write(",".join(keys) + "\n")
        for row in rows:
            f.write(",".join(str(row.get(k, "")).replace("\n", " ").replace(",", ";") for k in keys) + "\n")


def write_summary(rows: list[dict[str, Any]], path: str | Path, target_hours: float) -> None:
    status_counts = Counter(str(row.get("status")) for row in rows)
    gravity_counts = Counter(str(row.get("gravity_label") or "missing") for row in rows)
    ok_rows = [row for row in rows if row.get("status") == "OK"]
    ok_hours = sum(float(row.get("duration_sec") or 0.0) for row in ok_rows) / 3600.0
    decision = "PHYS_EDIT_WORLD_DATA_READY_FOR_SPLIT" if ok_rows else "PHYS_EDIT_WORLD_DATA_NOT_FOUND"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        "# PhysEditWorld 50h Data Audit Summary\n\n"
        f"Decision: `{decision}`\n\n"
        f"- Candidate rows: {len(rows)}\n"
        f"- OK rows: {len(ok_rows)}\n"
        f"- OK duration hours: {ok_hours:.3f}\n"
        f"- Target hours: {target_hours}\n"
        f"- Replay groups: {len(set(str(row.get('replay_group_id')) for row in rows))}\n\n"
        "## Status Counts\n\n"
        + "\n".join(f"- `{k}`: {v}" for k, v in sorted(status_counts.items()))
        + "\n\n## Gravity Distribution\n\n"
        + "\n".join(f"- `{k}`: {v}" for k, v in sorted(gravity_counts.items()))
        + "\n"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", default=[])
    ap.add_argument("--candidate_file", default=None)
    ap.add_argument("--target_hours", type=float, default=50.0)
    ap.add_argument("--output", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--max-depth", type=int, default=7)
    ap.add_argument("--max_candidates", type=int, default=None)
    ap.add_argument("--skip_video_probe", action="store_true")
    args = ap.parse_args(argv)
    roots = [Path(root) for root in args.roots]
    if args.skip_video_probe:
        os.environ["PHYS_EDIT_WORLD_SKIP_VIDEO_PROBE"] = "1"
    if args.candidate_file:
        rows = discover_samples_from_candidates(Path(args.candidate_file), args.target_hours, max_candidates=args.max_candidates)
    else:
        if not roots:
            raise SystemExit("--roots is required unless --candidate_file is provided")
        rows = discover_samples(roots, args.target_hours, max_depth=args.max_depth)
    ok_rows = [row for row in rows if row.get("status") == "OK"]
    write_jsonl(ok_rows, args.output)
    write_csv(rows, args.report)
    write_summary(rows, args.summary, args.target_hours)
    # Always write split artifacts, even if empty, so downstream gates are explicit.
    split_main(["--manifest", args.output, "--out_dir", "manifests", "--prefix", "physeditworld_50h", "--report_dir", "reports/physeditworld_50h"])
    print({"candidates": len(rows), "ok": len(ok_rows), "output": args.output})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
