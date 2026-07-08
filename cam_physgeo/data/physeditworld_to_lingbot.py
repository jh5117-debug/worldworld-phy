from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from pathlib import Path
from typing import Any

from cam_physgeo.data.lingbot_condition_schema import validate_condition_dir, write_json
from cam_physgeo.data.prompt_gravity import build_prompt_gravity, validate_prompt
from cam_physgeo.utils.io import read_jsonl, write_jsonl

try:
    import numpy as np
except Exception:  # pragma: no cover - conversion reports the missing backend at runtime.
    np = None


def _link_or_copy(src: str | Path, dst: Path) -> None:
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(str(src))
    if dst.exists() or dst.is_symlink():
        return
    try:
        os.symlink(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def frame_indices(num_frames: int | None, target_frames: int) -> list[int]:
    if not num_frames or num_frames <= 0:
        return list(range(target_frames))
    if num_frames <= target_frames:
        return list(range(num_frames))
    return [round(i * (num_frames - 1) / (target_frames - 1)) for i in range(target_frames)]


def _as_positive_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def intrinsics_scale_metadata(row: dict[str, Any], target_width: int, target_height: int) -> dict[str, Any]:
    source_width = _as_positive_float(row.get("width") or row.get("source_width"))
    source_height = _as_positive_float(row.get("height") or row.get("source_height"))
    target_width_f = _as_positive_float(target_width)
    target_height_f = _as_positive_float(target_height)
    meta: dict[str, Any] = {
        "source_width": source_width,
        "source_height": source_height,
        "target_width": target_width_f,
        "target_height": target_height_f,
        "scale_x": None,
        "scale_y": None,
        "status": "SOURCE_SIZE_MISSING",
    }
    if source_width is None or source_height is None:
        return meta
    if target_width_f is None or target_height_f is None:
        meta["status"] = "TARGET_SIZE_INVALID"
        return meta
    meta["scale_x"] = target_width_f / source_width
    meta["scale_y"] = target_height_f / source_height
    meta["status"] = "OK"
    return meta


def scale_intrinsics_array(array: Any, scale_x: float, scale_y: float) -> Any:
    if np is None:
        raise RuntimeError("numpy is required to scale PhysEditWorld intrinsics")
    scaled = np.array(array, copy=True)
    if scaled.shape[-2:] == (3, 3):
        scaled[..., 0, 0] *= scale_x
        scaled[..., 0, 2] *= scale_x
        scaled[..., 1, 1] *= scale_y
        scaled[..., 1, 2] *= scale_y
        return scaled
    if scaled.shape[-1:] == (4,):
        scaled[..., 0] *= scale_x
        scaled[..., 1] *= scale_y
        scaled[..., 2] *= scale_x
        scaled[..., 3] *= scale_y
        return scaled
    raise ValueError(f"unsupported intrinsics shape {scaled.shape}; expected (..., 3, 3) or (..., 4)")


def write_or_link_intrinsics(src: str | Path, dst: Path, scale_meta: dict[str, Any]) -> None:
    if scale_meta.get("status") != "OK":
        _link_or_copy(src, dst)
        return
    if np is None:
        raise RuntimeError("numpy is required when source and target image sizes require intrinsics scaling")
    array = np.load(src)
    scaled = scale_intrinsics_array(array, float(scale_meta["scale_x"]), float(scale_meta["scale_y"]))
    np.save(dst, scaled)


def write_sampled_npy(src: str | Path, dst: Path, indices: list[int], field_name: str) -> dict[str, Any]:
    src = Path(src)
    if np is None:
        raise RuntimeError(f"numpy is required to sample {field_name}")
    if src.suffix.lower() != ".npy":
        raise ValueError(f"{field_name} must be convertible to .npy, got {src}")
    array = np.load(src, allow_pickle=False)
    if array.ndim < 1:
        raise ValueError(f"{field_name} must have a time dimension, got shape {array.shape}")
    max_index = max(indices) if indices else -1
    if array.shape[0] >= max_index + 1:
        sampled = array[indices]
        status = "SAMPLED"
    elif array.shape[0] == len(indices):
        sampled = np.array(array, copy=True)
        status = "ALREADY_SAMPLED"
    else:
        raise ValueError(
            f"{field_name} length {array.shape[0]} cannot cover max frame index {max_index} "
            f"or requested output length {len(indices)}"
        )
    np.save(dst, sampled)
    return {
        "source_path": str(src),
        "source_length": int(array.shape[0]),
        "output_length": int(sampled.shape[0]),
        "indices_length": len(indices),
        "status": status,
    }


def write_sampled_video(src: str | Path, dst: Path, indices: list[int], fps: int, width: int, height: int) -> dict[str, Any]:
    try:
        import cv2
    except Exception as exc:  # pragma: no cover - depends on deployment image.
        raise RuntimeError(f"cv2 is required to sample PhysEditWorld target video: {exc}") from exc

    src = Path(src)
    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        raise ValueError(f"video_open_failed:{src}")
    source_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    source_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    source_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    source_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    max_index = max(indices) if indices else -1
    if source_frame_count and source_frame_count < max_index + 1:
        cap.release()
        raise ValueError(f"video length {source_frame_count} cannot cover max frame index {max_index}")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(dst), fourcc, float(fps), (int(width), int(height)))
    if not writer.isOpened():
        cap.release()
        raise ValueError(f"video_writer_open_failed:{dst}")
    wanted = set(indices)
    written = 0
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx in wanted:
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (int(width), int(height)), interpolation=cv2.INTER_AREA)
            writer.write(frame)
            written += 1
            if written >= len(wanted):
                break
        frame_idx += 1
    cap.release()
    writer.release()
    if written != len(wanted):
        raise ValueError(f"video_sample_incomplete:wrote={written}:expected={len(wanted)}:max_index={max_index}")
    return {
        "source_path": str(src),
        "source_frame_count": source_frame_count,
        "source_fps": source_fps,
        "source_width": source_width,
        "source_height": source_height,
        "output_frame_count": written,
        "output_fps": int(fps),
        "output_width": int(width),
        "output_height": int(height),
        "indices_length": len(indices),
        "status": "SAMPLED",
    }


def convert_row(row: dict[str, Any], output_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    sample_id = str(row.get("sample_id") or Path(str(row.get("video_path", "sample"))).stem)
    final_dir = output_root / sample_id
    tmp_dir = output_root / f".{sample_id}.tmp"
    if final_dir.exists():
        errors = validate_condition_dir(final_dir)
        return {"sample_id": sample_id, "sample_dir": str(final_dir), "status": "EXISTS_OK" if not errors else "EXISTS_INVALID", "error_reason": ";".join(errors)}
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    status = "OK"
    error = ""
    try:
        # v0 keeps prefix media as links; target/action/camera are sampled to the same 81-frame index view.
        prefix = row.get("prefix_video_path") or row.get("image_path") or row.get("video_path")
        prefix_name = "prefix.mp4" if str(prefix).lower().endswith(".mp4") else "image.jpg"
        _link_or_copy(prefix, tmp_dir / prefix_name)
        indices = frame_indices(row.get("num_frames"), args.num_frames)
        video_sampling = write_sampled_video(row["video_path"], tmp_dir / "target.mp4", indices, args.fps, args.width, args.height)
        action_sampling = write_sampled_npy(row["action_trace_path"], tmp_dir / "action.npy", indices, "action_trace")
        camera_sampling = write_sampled_npy(row["camera_trajectory_path"], tmp_dir / "poses.npy", indices, "camera_trajectory")
        intrinsics_scale = intrinsics_scale_metadata(row, args.width, args.height)
        write_or_link_intrinsics(row["intrinsics_path"], tmp_dir / "intrinsics.npy", intrinsics_scale)
        prompt = build_prompt_gravity(row.get("gravity_value"), args.gravity_prompt_style)
        prompt_errors = validate_prompt(prompt)
        if prompt_errors:
            raise ValueError(";".join(prompt_errors))
        (tmp_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
        gravity = {"gravity_value": row.get("gravity_value"), "gravity_label": row.get("gravity_label"), "gravity_condition_type": "prompt_only"}
        write_json(tmp_dir / "gravity.json", gravity)
        metadata = {
            "sample_id": sample_id,
            "use_action": True,
            "use_camera": True,
            "use_intrinsics": True,
            "gravity_condition_type": "prompt_only",
            "gravity_value": row.get("gravity_value"),
            "gravity_label": row.get("gravity_label"),
            "replay_group_id": row.get("replay_group_id"),
            "scene_id": row.get("scene_id"),
            "action_trace_id": row.get("action_trace_id"),
            "camera_policy_id": row.get("camera_policy_id"),
            "source_video_path": row.get("video_path"),
            "source_action_trace_path": row.get("action_trace_path"),
            "source_camera_trajectory_path": row.get("camera_trajectory_path"),
            "source_intrinsics_path": row.get("intrinsics_path"),
            "source_height": intrinsics_scale.get("source_height"),
            "source_width": intrinsics_scale.get("source_width"),
            "num_frames_requested": args.num_frames,
            "fps_requested": args.fps,
            "height_requested": args.height,
            "width_requested": args.width,
            "frame_indices": indices,
            "sampling_alignment": {
                "video_frame_indices": indices,
                "action_frame_indices": indices,
                "camera_frame_indices": indices,
                "same_indices_for_action_camera_video": True,
            },
            "video_sampling": video_sampling,
            "action_sampling": action_sampling,
            "camera_sampling": camera_sampling,
            "intrinsics_scale": intrinsics_scale,
        }
        write_json(tmp_dir / "metadata.json", metadata)
        errors = validate_condition_dir(tmp_dir)
        if errors:
            raise ValueError(";".join(errors))
        tmp_dir.rename(final_dir)
    except Exception as exc:
        status = "FAILED"
        error = repr(exc)
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
    return {"sample_id": sample_id, "sample_dir": str(final_dir), "status": status, "error_reason": error}


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for row in rows for k in row}) or ["sample_id", "status"]
    with path.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--num_frames", type=int, default=81)
    ap.add_argument("--fps", type=int, default=16)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--width", type=int, default=832)
    ap.add_argument("--gravity_prompt_style", default="physeditworld_v0")
    ap.add_argument("--report", required=True)
    ap.add_argument("--summary", required=True)
    args = ap.parse_args(argv)
    rows = list(read_jsonl(args.manifest))
    if args.limit is not None:
        rows = rows[: args.limit]
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    reports = [convert_row(row, output_root, args) for row in rows]
    write_csv(reports, Path(args.report))
    ok = sum(1 for row in reports if row.get("status") in {"OK", "EXISTS_OK"})
    failed = sum(1 for row in reports if row.get("status") not in {"OK", "EXISTS_OK"})
    converted_manifest = []
    for row in reports:
        if row.get("status") in {"OK", "EXISTS_OK"}:
            converted_manifest.append({"sample_id": row["sample_id"], "sample_dir": row["sample_dir"], "status": row["status"]})
    suffix = Path(args.manifest).stem.replace("physeditworld_50h_", "") or "all"
    manifest_out = Path("manifests") / f"physeditworld_50h_lingbot_{suffix}.jsonl"
    write_jsonl(converted_manifest, manifest_out)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(
        "# PhysEditWorld To LingBot Conversion Summary\n\n"
        f"- Input manifest: `{args.manifest}`\n"
        f"- Rows selected: {len(rows)}\n"
        f"- Converted OK: {ok}\n"
        f"- Failed: {failed}\n"
        f"- Output root: `{args.output_root}`\n"
        f"- Output manifest: `{manifest_out}`\n"
        "- Gravity condition type: `prompt_only`\n"
        "- No gravity MLP or embedding is introduced.\n"
    )
    print({"selected": len(rows), "ok": ok, "failed": failed, "manifest_out": str(manifest_out)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
