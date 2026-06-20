from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np

try:
    import h5py  # type: ignore
except Exception:  # pragma: no cover - exercised in environment diagnostics.
    h5py = None

try:
    import imageio.v2 as imageio  # type: ignore
except Exception:  # pragma: no cover
    imageio = None

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    Image = None


TARGET_FRAMES = 81
TARGET_FPS = 16
SOURCE_FPS = 30
DEFAULT_RAW_SUBDIR = "v5_aggressive_2x_scaleup_4000_to_5000"


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return rows


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            line = json.dumps(row, ensure_ascii=False, sort_keys=True)
            handle.write(line + "\n")
            h.update(line.encode("utf-8"))
            h.update(b"\n")
    digest = h.hexdigest()
    path.with_suffix(path.suffix + ".sha256").write_text(digest + "\n", encoding="utf-8")
    return digest


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _trial_name(row: dict, fallback_index: int) -> str:
    for key in ("sample_id", "output_name", "trial_name", "name"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    sample_index = int(row.get("sample_index", row.get("trial_index", row.get("index", fallback_index))))
    template = str(row.get("template") or "unknown")
    camera = str(row.get("camera_variant") or row.get("camera_motion") or "camera")
    seed = int(row.get("seed", row.get("trial_seed", sample_index)))
    return f"{sample_index:05d}_{template}_{camera}_seed{seed}"


def _chunk_id_from_path(path: Path) -> str:
    return path.stem.replace("chunk_", "")


def _expected_hdf5(generated_root: Path, raw_subdir: str, row: dict, index: int) -> Path:
    for key in ("hdf5_path", "output_path", "path"):
        value = str(row.get(key) or "").strip()
        if value:
            p = Path(value)
            return p if p.is_absolute() else generated_root / p
    return generated_root / "raw_hdf5" / raw_subdir / _trial_name(row, index) / "0000.hdf5"


def _finite_array(value: np.ndarray) -> bool:
    try:
        arr = np.asarray(value)
        return bool(arr.size) and bool(np.isfinite(arr.astype("float64", copy=False)).all())
    except Exception:
        return False


def _frame_keys(handle) -> list[str]:
    if "frames" not in handle:
        return []
    keys = list(handle["frames"].keys())
    return sorted(keys, key=lambda x: int(x) if str(x).isdigit() else str(x))


def _decode_rgb(dataset) -> np.ndarray:
    if Image is None:
        raise RuntimeError("PIL unavailable")
    arr = np.asarray(dataset[()])
    if arr.ndim == 1:
        with Image.open(io.BytesIO(arr.tobytes())) as image:
            return np.asarray(image.convert("RGB"), dtype=np.uint8)
    if arr.ndim == 3:
        if arr.shape[-1] == 4:
            arr = arr[..., :3]
        if arr.shape[-1] == 1:
            arr = np.repeat(arr, 3, axis=-1)
        return arr.astype(np.uint8, copy=False)
    raise RuntimeError(f"unsupported rgb array shape {arr.shape}")


def _matrix4(dataset) -> np.ndarray:
    arr = np.asarray(dataset[()], dtype=np.float32)
    if arr.shape == (16,):
        return arr.reshape(4, 4)
    if arr.shape == (4, 4):
        return arr
    raise ValueError(f"expected 4x4/16 matrix, got {arr.shape}")


def _projection_matrix_to_lingbot_intrinsics(matrix: np.ndarray, *, width: int, height: int) -> np.ndarray:
    """Convert a TDW/OpenGL projection matrix to LingBot [fx, fy, cx, cy]."""

    mat = np.asarray(matrix, dtype=np.float32)
    if mat.shape != (4, 4):
        raise ValueError(f"expected projection matrix shape (4,4), got {mat.shape}")
    fx = abs(float(mat[0, 0])) * float(width) * 0.5
    fy = abs(float(mat[1, 1])) * float(height) * 0.5
    cx = (1.0 - float(mat[0, 2])) * float(width) * 0.5
    cy = (1.0 + float(mat[1, 2])) * float(height) * 0.5
    intr = np.asarray([fx, fy, cx, cy], dtype=np.float32)
    if not np.isfinite(intr).all() or fx <= 0.0 or fy <= 0.0:
        raise ValueError(f"invalid derived intrinsics {intr.tolist()}")
    return intr


def _sample_indices(num_source_frames: int, target_frames: int) -> list[int]:
    if num_source_frames <= 0:
        return []
    if target_frames <= 1:
        return [0]
    return [int(round(x)) for x in np.linspace(0, num_source_frames - 1, target_frames)]


def _prompt_for(row: dict, *, prompt_variant: str = "structured_prompt_v2") -> str:
    existing = str(row.get("prompt") or "").strip()
    if existing and prompt_variant != "structured_prompt_v2":
        return existing
    template = str(row.get("template") or "physical interaction").strip() or "physical interaction"
    camera = str(row.get("camera_variant") or row.get("camera_motion") or "moving camera").strip()
    event = {
        "drop": "a gravity-driven drop event",
        "collision": "a rigid-body collision event",
        "roll": "a rolling object event",
        "containment": "a containment interaction event",
    }.get(template, f"a {template} physical event")
    return (
        "Synthetic indoor physical scene. "
        f"The video shows {event} with initially visible foreground objects and a stable room, floor, and background. "
        "Preserve the foreground object count, colors, rigid shapes, and sizes throughout the clip. "
        f"The camera follows the externally supplied {camera} trajectory from the first frame, with visible background parallax. "
        "Do not add, remove, duplicate, recolor, melt, or morph objects. "
        "Use the provided camera poses and intrinsics as the only camera control."
    )


def raw_validate_hdf5(
    *,
    sample_id: str,
    hdf5_path: Path,
    chunk_complete: bool,
    min_source_frames: int,
    min_stable_seconds: int,
    raw_probe_stride: int,
) -> dict:
    reasons: list[str] = []
    now = time.time()
    record = {
        "sample_id": sample_id,
        "hdf5_path": str(hdf5_path),
        "raw_hdf5_valid": False,
        "conversion_candidate": False,
        "raw_blocked_reasons": reasons,
        "source_frame_count": 0,
        "source_height": None,
        "source_width": None,
        "source_file_size": None,
        "source_file_mtime": None,
        "source_age_seconds": None,
        "rgb_pass_probe_frames": [],
    }
    if h5py is None:
        reasons.append("h5py_unavailable")
        return record
    if Image is None:
        reasons.append("PIL_unavailable")
        return record
    if not hdf5_path.exists():
        reasons.append("missing_hdf5")
        return record
    stat = hdf5_path.stat()
    record["source_file_size"] = int(stat.st_size)
    record["source_file_mtime"] = int(stat.st_mtime)
    age = now - float(stat.st_mtime)
    record["source_age_seconds"] = round(age, 3)
    if stat.st_size <= 0:
        reasons.append("empty_hdf5")
    if not chunk_complete:
        reasons.append("active_or_incomplete_chunk")
        return record
    if min_stable_seconds > 0 and age < min_stable_seconds:
        reasons.append("file_too_recent")
        return record
    try:
        with h5py.File(hdf5_path, "r") as handle:
            keys = _frame_keys(handle)
            record["source_frame_count"] = len(keys)
            if len(keys) < min_source_frames:
                reasons.append("too_few_frames")
            if keys:
                ints = [int(k) for k in keys if str(k).isdigit()]
                if len(ints) != len(keys) or ints != list(range(ints[0], ints[0] + len(ints))):
                    reasons.append("non_contiguous_frame_keys")
            if "static" not in handle:
                reasons.append("missing_static_metadata")
            probe_keys = []
            check_keys = []
            if keys:
                stride = max(int(raw_probe_stride or 1), 1)
                check_keys = keys[::stride]
                for extra in (keys[0], keys[len(keys) // 2], keys[-1]):
                    if extra not in check_keys:
                        check_keys.append(extra)
                check_keys = sorted(set(check_keys), key=lambda x: int(x) if str(x).isdigit() else str(x))
                probe_keys = [keys[0], keys[len(keys) // 2], keys[-1]]
            record["raw_frames_checked"] = len(check_keys)
            record["raw_probe_stride"] = max(int(raw_probe_stride or 1), 1)
            seen_probe = []
            for frame_key in check_keys:
                frame = handle["frames"][frame_key]
                if "images" not in frame:
                    reasons.append(f"missing_images:{frame_key}")
                    break
                images = frame["images"]
                for pass_name in ("_img", "_depth", "_id"):
                    if pass_name not in images:
                        reasons.append(f"missing_{pass_name}:{frame_key}")
                        break
                    if np.asarray(images[pass_name]).size <= 0:
                        reasons.append(f"empty_{pass_name}:{frame_key}")
                        break
                if "labels" not in frame:
                    reasons.append(f"missing_labels:{frame_key}")
                    break
                labels = frame["labels"]
                for label_name in ("camera_pose", "camera_position", "camera_aim"):
                    if label_name not in labels:
                        reasons.append(f"missing_{label_name}:{frame_key}")
                        break
                    if not _finite_array(labels[label_name][()]):
                        reasons.append(f"nonfinite_{label_name}:{frame_key}")
                        break
                if "camera_matrices" not in frame:
                    reasons.append(f"missing_camera_matrices:{frame_key}")
                    break
                matrices = frame["camera_matrices"]
                if "projection_matrix" not in matrices and "camera_matrix" not in matrices:
                    reasons.append(f"missing_projection_or_camera_matrix:{frame_key}")
                    break
                for matrix_name in ("projection_matrix", "camera_matrix"):
                    if matrix_name in matrices and not _finite_array(matrices[matrix_name][()]):
                        reasons.append(f"nonfinite_{matrix_name}:{frame_key}")
                        break
                if "objects" not in frame or "positions" not in frame["objects"]:
                    reasons.append(f"missing_object_positions:{frame_key}")
                    break
                if not _finite_array(frame["objects"]["positions"][()]):
                    reasons.append(f"nonfinite_object_positions:{frame_key}")
                    break
                if frame_key in probe_keys:
                    depth_shape = tuple(np.asarray(images["_depth"]).shape)
                    if len(depth_shape) >= 2:
                        record["source_height"] = int(depth_shape[0])
                        record["source_width"] = int(depth_shape[1])
                    seen_probe.append(frame_key)
                if reasons and any(":" in r for r in reasons[-3:]):
                    break
            record["rgb_pass_probe_frames"] = seen_probe
    except Exception as exc:
        reasons.append("hdf5_open_or_parse_failed:" + repr(exc))
    record["raw_hdf5_valid"] = len(reasons) == 0
    record["conversion_candidate"] = bool(record["raw_hdf5_valid"])
    return record


def _output_complete(sample_dir: Path, target_frames: int) -> bool:
    required = ["target.mp4", "video.mp4", "image.jpg", "poses.npy", "intrinsics.npy", "prompt.txt", "metadata.json"]
    if not all((sample_dir / name).exists() for name in required):
        return False
    try:
        poses = np.load(sample_dir / "poses.npy")
        intr = np.load(sample_dir / "intrinsics.npy")
        return (
            poses.shape == (target_frames, 4, 4)
            and intr.shape == (target_frames, 4)
            and np.isfinite(poses).all()
            and np.isfinite(intr).all()
        )
    except Exception:
        return False


def convert_hdf5_sample(
    *,
    sample_id: str,
    hdf5_path: Path,
    row: dict,
    out_root: Path,
    target_frames: int,
    fps: int,
    force: bool,
) -> dict:
    out_dir = out_root / sample_id
    tmp_dir = out_root / f".{sample_id}.tmp"
    result = {
        "sample_id": sample_id,
        "converted_valid": False,
        "conversion_blocked_reasons": [],
        "converted_dir": str(out_dir),
        "target_video_path": str(out_dir / "target.mp4"),
        "video_path": str(out_dir / "video.mp4"),
        "poses_path": str(out_dir / "poses.npy"),
        "intrinsics_path": str(out_dir / "intrinsics.npy"),
        "prompt_path": str(out_dir / "prompt.txt"),
        "frame_indices": [],
    }
    reasons = result["conversion_blocked_reasons"]
    if imageio is None:
        reasons.append("imageio_unavailable")
        return result
    if h5py is None or Image is None:
        reasons.append("h5py_or_PIL_unavailable")
        return result
    if _output_complete(out_dir, target_frames) and not force:
        result["converted_valid"] = True
        try:
            meta = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
            result["frame_indices"] = meta.get("frame_indices", [])
        except Exception:
            pass
        return result
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        with h5py.File(hdf5_path, "r") as handle:
            keys = _frame_keys(handle)
            indices = _sample_indices(len(keys), target_frames)
            frames = []
            poses = []
            intrinsics = []
            source_height = None
            source_width = None
            for idx in indices:
                frame = handle["frames"][keys[idx]]
                rgb = _decode_rgb(frame["images"]["_img"])
                frames.append(rgb)
                poses.append(_matrix4(frame["labels"]["camera_pose"]))
                matrices = frame["camera_matrices"]
                key = "projection_matrix" if "projection_matrix" in matrices else "camera_matrix"
                if source_height is None or source_width is None:
                    source_height = int(rgb.shape[0])
                    source_width = int(rgb.shape[1])
                intrinsics.append(
                    _projection_matrix_to_lingbot_intrinsics(
                        _matrix4(matrices[key]), width=int(rgb.shape[1]), height=int(rgb.shape[0])
                    )
                )
            if not frames or source_height is None or source_width is None:
                raise RuntimeError("no frames decoded for conversion")
            imageio.mimsave(tmp_dir / "target.mp4", frames, fps=fps, macro_block_size=1, codec="libx264", ffmpeg_params=["-preset", "ultrafast"])
            shutil.copy2(tmp_dir / "target.mp4", tmp_dir / "video.mp4")
            Image.fromarray(frames[0]).save(tmp_dir / "image.jpg", quality=92)
            np.save(tmp_dir / "poses.npy", np.asarray(poses, dtype=np.float32))
            np.save(tmp_dir / "intrinsics.npy", np.asarray(intrinsics, dtype=np.float32))
            np.save(tmp_dir / "action.npy", np.zeros((target_frames, 4), dtype=np.float32))
            prompt = _prompt_for(row)
            (tmp_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
            meta = dict(row)
            meta.update(
                {
                    "sample_id": sample_id,
                    "source_hdf5_path": str(hdf5_path),
                    "target_num_frames": target_frames,
                    "target_fps": fps,
                    "source_fps": SOURCE_FPS,
                    "frame_indices": indices,
                    "control_type": "cam",
                    "use_action": False,
                    "dummy_action": True,
                    "prompt_variant": "structured_prompt_v2",
                    "prompt": prompt,
                    "source_height": int(source_height),
                    "source_width": int(source_width),
                    "target_height": int(source_height),
                    "target_width": int(source_width),
                    "target_video_path": str(out_dir / "target.mp4"),
                    "video_path": str(out_dir / "video.mp4"),
                    "poses_path": str(out_dir / "poses.npy"),
                    "intrinsics_path": str(out_dir / "intrinsics.npy"),
                }
            )
            _write_json(tmp_dir / "metadata.json", meta)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        tmp_dir.rename(out_dir)
        result["frame_indices"] = indices
    except Exception as exc:
        reasons.append("conversion_failed:" + repr(exc))
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        return result
    return result | validate_converted_sample(sample_id=sample_id, sample_dir=out_dir, target_frames=target_frames, fps=fps)


def _count_video_frames(path: Path) -> tuple[int, tuple[int, int] | None]:
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        cmd = [
            ffprobe,
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_read_frames,width,height",
            "-of",
            "json",
            str(path),
        ]
        try:
            proc = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            payload = json.loads(proc.stdout or "{}")
            streams = payload.get("streams") or []
            if streams:
                stream = streams[0]
                count = int(stream.get("nb_read_frames") or 0)
                width = int(stream.get("width") or 0)
                height = int(stream.get("height") or 0)
                if count > 0 and width > 0 and height > 0:
                    return count, (height, width)
            raise RuntimeError("ffprobe returned no decodable video stream")
        except Exception as exc:
            raise RuntimeError(f"ffprobe_failed:{exc!r}") from exc
    if imageio is None:
        raise RuntimeError("imageio unavailable")
    count = 0
    shape = None
    reader = imageio.get_reader(path)
    try:
        for frame in reader:
            arr = np.asarray(frame)
            if shape is None:
                shape = (int(arr.shape[0]), int(arr.shape[1]))
            count += 1
    finally:
        reader.close()
    return count, shape


def validate_converted_sample(*, sample_id: str, sample_dir: Path, target_frames: int, fps: int) -> dict:
    reasons: list[str] = []
    record = {
        "sample_id": sample_id,
        "converted_valid": False,
        "conversion_blocked_reasons": reasons,
        "converted_dir": str(sample_dir),
        "target_video_path": str(sample_dir / "target.mp4"),
        "video_path": str(sample_dir / "video.mp4"),
        "poses_path": str(sample_dir / "poses.npy"),
        "intrinsics_path": str(sample_dir / "intrinsics.npy"),
        "prompt_path": str(sample_dir / "prompt.txt"),
        "decoded_frame_count": 0,
        "decoded_resolution": None,
    }
    for name in ("target.mp4", "video.mp4", "image.jpg", "poses.npy", "intrinsics.npy", "prompt.txt", "metadata.json"):
        if not (sample_dir / name).exists():
            reasons.append(f"missing_{name}")
    if not reasons:
        try:
            count, shape = _count_video_frames(sample_dir / "target.mp4")
            record["decoded_frame_count"] = int(count)
            record["decoded_resolution"] = list(shape) if shape else None
            if count != target_frames:
                reasons.append(f"wrong_frame_count:{count}")
        except Exception as exc:
            reasons.append("video_decode_failed:" + repr(exc))
    try:
        poses = np.load(sample_dir / "poses.npy")
        intr = np.load(sample_dir / "intrinsics.npy")
        if poses.shape != (target_frames, 4, 4):
            reasons.append(f"bad_poses_shape:{poses.shape}")
        if intr.shape != (target_frames, 4):
            reasons.append(f"bad_intrinsics_shape:{intr.shape}")
        if not np.isfinite(poses).all():
            reasons.append("nonfinite_poses")
        if not np.isfinite(intr).all():
            reasons.append("nonfinite_intrinsics")
    except Exception as exc:
        reasons.append("numpy_probe_failed:" + repr(exc))
    try:
        prompt = (sample_dir / "prompt.txt").read_text(encoding="utf-8").strip()
        if not prompt:
            reasons.append("empty_prompt")
        meta = json.loads((sample_dir / "metadata.json").read_text(encoding="utf-8"))
        if meta.get("control_type") != "cam":
            reasons.append("metadata_control_type_not_cam")
        if meta.get("use_action") not in {False, "false", "False", 0}:
            reasons.append("metadata_use_action_not_false")
        frame_indices = meta.get("frame_indices") or []
        if len(frame_indices) != target_frames:
            reasons.append("bad_frame_indices")
    except Exception as exc:
        reasons.append("metadata_probe_failed:" + repr(exc))
    record["converted_valid"] = len(reasons) == 0
    return record


def _collect_chunk_rows(chunks_dir: Path, generated_root: Path, raw_subdir: str) -> list[dict]:
    rows_out: list[dict] = []
    for chunk_path in sorted(chunks_dir.glob("chunk_*.jsonl")):
        rows = _read_jsonl(chunk_path)
        chunk_id = _chunk_id_from_path(chunk_path)
        existing = sum(1 for idx, row in enumerate(rows) if _expected_hdf5(generated_root, raw_subdir, row, idx).exists())
        chunk_complete = existing == len(rows) and len(rows) > 0
        for idx, row in enumerate(rows):
            trial_name = _trial_name(row, idx)
            rows_out.append(
                {
                    "chunk_id": chunk_id,
                    "chunk_manifest": str(chunk_path),
                    "chunk_manifest_rows": len(rows),
                    "chunk_existing_hdf5": existing,
                    "chunk_complete": chunk_complete,
                    "manifest_index": idx,
                    "sample_id": trial_name,
                    "template": row.get("template"),
                    "camera_variant": row.get("camera_variant") or row.get("camera_motion"),
                    "seed": row.get("seed"),
                    "scene_seed": row.get("scene_seed") or row.get("seed"),
                    "manifest_row": row,
                    "hdf5_path": str(_expected_hdf5(generated_root, raw_subdir, row, idx)),
                }
            )
    return rows_out


def run_validate_convert(args: argparse.Namespace) -> int:
    generated_root = Path(args.generated_root).resolve()
    chunks_dir = Path(args.manifest_chunks_dir).resolve()
    converted_root = Path(args.converted_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = _collect_chunk_rows(chunks_dir, generated_root, args.raw_subdir)
    if args.only_converted_existing:
        rows = [row for row in rows if _output_complete(converted_root / row["sample_id"], args.target_frames)]
    if args.max_samples > 0:
        rows = rows[: args.max_samples]
    records = []
    converted_attempts = 0
    for row in rows:
        hdf5_path = Path(row["hdf5_path"])
        raw = raw_validate_hdf5(
            sample_id=row["sample_id"],
            hdf5_path=hdf5_path,
            chunk_complete=bool(row["chunk_complete"]),
            min_source_frames=args.min_source_frames,
            min_stable_seconds=args.min_stable_seconds,
            raw_probe_stride=args.raw_probe_stride,
        )
        record = {k: v for k, v in row.items() if k != "manifest_row"}
        record["manifest_row"] = row["manifest_row"]
        record.update(raw)
        converted = validate_converted_sample(
            sample_id=row["sample_id"],
            sample_dir=converted_root / row["sample_id"],
            target_frames=args.target_frames,
            fps=args.fps,
        )
        if args.convert and raw.get("conversion_candidate"):
            if args.convert_limit <= 0 or converted_attempts < args.convert_limit:
                converted_attempts += 1
                converted = convert_hdf5_sample(
                    sample_id=row["sample_id"],
                    hdf5_path=hdf5_path,
                    row=row["manifest_row"],
                    out_root=converted_root,
                    target_frames=args.target_frames,
                    fps=args.fps,
                    force=args.force_rebuild_incomplete and not converted.get("converted_valid", False),
                )
        record.update(converted)
        record["stage1_ready"] = bool(record.get("raw_hdf5_valid") and record.get("converted_valid"))
        record["blocked_reason"] = list(record.get("raw_blocked_reasons") or []) + list(
            record.get("conversion_blocked_reasons") or []
        )
        records.append(record)
        if args.progress_every > 0 and len(records) % args.progress_every == 0:
            print(f"processed={len(records)} raw_valid={sum(r.get('raw_hdf5_valid') for r in records)} converted={sum(r.get('converted_valid') for r in records)} stage1_ready={sum(r.get('stage1_ready') for r in records)}", flush=True)
    validation_path = out_dir / "stageA_v5_validation.jsonl"
    digest = _write_jsonl(validation_path, records)
    reason_counts = collections.Counter(reason for rec in records for reason in rec.get("blocked_reason", []))
    chunk_counts = collections.defaultdict(lambda: {"manifest_rows": 0, "raw_valid": 0, "converted_valid": 0, "stage1_ready": 0})
    for rec in records:
        item = chunk_counts[str(rec.get("chunk_id"))]
        item["manifest_rows"] += 1
        item["raw_valid"] += int(bool(rec.get("raw_hdf5_valid")))
        item["converted_valid"] += int(bool(rec.get("converted_valid")))
        item["stage1_ready"] += int(bool(rec.get("stage1_ready")))
    summary = {
        "generated_root": str(generated_root),
        "chunks_dir": str(chunks_dir),
        "converted_root": str(converted_root),
        "validation_jsonl": str(validation_path),
        "validation_sha256": digest,
        "total_records": len(records),
        "raw_hdf5_valid_count": sum(bool(r.get("raw_hdf5_valid")) for r in records),
        "conversion_candidate_count": sum(bool(r.get("conversion_candidate")) for r in records),
        "converted_valid_count": sum(bool(r.get("converted_valid")) for r in records),
        "stage1_ready_count": sum(bool(r.get("stage1_ready")) for r in records),
        "blocked_count": sum(not bool(r.get("stage1_ready")) for r in records),
        "blocked_reason_distribution": dict(reason_counts.most_common()),
        "chunk_distribution": dict(sorted(chunk_counts.items())),
        "target_frames": args.target_frames,
        "fps": args.fps,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    _write_json(out_dir / "stageA_v5_validation_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _load_validation_records(path: Path) -> list[dict]:
    rows = _read_jsonl(path)
    seen: set[str] = set()
    for row in rows:
        sid = str(row.get("sample_id") or "")
        if not sid:
            raise ValueError(f"validation record without sample_id in {path}")
        if sid in seen:
            raise ValueError(f"duplicate sample_id in validation records: {sid}")
        seen.add(sid)
    return rows


def _split_stage1(rows: list[dict], seed: int) -> tuple[list[dict], list[dict], list[dict]]:
    grouped: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        group = str(row.get("scene_hash") or row.get("scene_seed") or row.get("seed") or row["sample_id"])
        grouped[group].append(row)
    salt = hashlib.sha256(str(seed).encode("ascii")).hexdigest()
    keys = sorted(grouped, key=lambda key: hashlib.sha256((salt + key).encode("utf-8")).hexdigest())
    total = sum(len(grouped[k]) for k in keys)
    train_target = int(total * 0.85)
    val_target = int(total * 0.10)
    train: list[dict] = []
    val: list[dict] = []
    test: list[dict] = []
    for key in keys:
        target = train if len(train) < train_target else (val if len(val) < val_target else test)
        target.extend(grouped[key])
    for split, split_rows in (("train", train), ("val", val), ("test_holdout", test)):
        for row in split_rows:
            row["split"] = split
    return train, val, test


def _stage1_manifest_row(rec: dict) -> dict:
    meta = {}
    try:
        meta = json.loads(Path(rec["converted_dir"]).joinpath("metadata.json").read_text(encoding="utf-8"))
    except Exception:
        meta = {}
    prompt = str(meta.get("prompt") or "")
    return {
        "sample_id": rec["sample_id"],
        "source_hdf5_path": rec["hdf5_path"],
        "target_video_path": rec["target_video_path"],
        "video_path": rec["video_path"],
        "poses_path": rec["poses_path"],
        "intrinsics_path": rec["intrinsics_path"],
        "prompt_path": rec["prompt_path"],
        "prompt": prompt,
        "prompt_variant": meta.get("prompt_variant", "structured_prompt_v2"),
        "template": rec.get("template"),
        "camera_variant": rec.get("camera_variant"),
        "seed": rec.get("seed"),
        "scene_seed": rec.get("scene_seed") or rec.get("seed"),
        "chunk_id": rec.get("chunk_id"),
        "source_file_size": rec.get("source_file_size"),
        "source_file_mtime": rec.get("source_file_mtime"),
        "validation_record": rec,
        "raw_hdf5_valid": True,
        "converted_valid": True,
        "stage1_ready": True,
        "frame_indices": meta.get("frame_indices", rec.get("frame_indices")),
        "control_type": "cam",
        "use_action": False,
        "source_height": rec.get("source_height") or 480,
        "source_width": rec.get("source_width") or 832,
    }


def run_snapshot(args: argparse.Namespace) -> int:
    records = _load_validation_records(Path(args.validation_jsonl).resolve())
    eligible = [rec for rec in records if rec.get("stage1_ready") is True]
    if not eligible:
        raise RuntimeError("No stage1_ready records available for snapshot")
    rows = [_stage1_manifest_row(rec) for rec in eligible]
    sample_ids = [row["sample_id"] for row in rows]
    if len(sample_ids) != len(set(sample_ids)):
        raise RuntimeError("duplicate sample_id in snapshot rows")
    timestamp = args.timestamp or datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    train, val, test = _split_stage1(rows, args.seed)
    prefix = f"stageA_v5_{timestamp}"
    all_path = out_dir / f"{prefix}_all.jsonl"
    train_path = out_dir / f"{prefix}_train.jsonl"
    val_path = out_dir / f"{prefix}_val.jsonl"
    test_path = out_dir / f"{prefix}_test_holdout.jsonl"
    validation_copy = out_dir / f"{prefix}_validation.jsonl"
    sha = {
        "all": _write_jsonl(all_path, rows),
        "train": _write_jsonl(train_path, train),
        "val": _write_jsonl(val_path, val),
        "test_holdout": _write_jsonl(test_path, test),
        "validation": _write_jsonl(validation_copy, records),
    }
    blocked = [rec for rec in records if not rec.get("stage1_ready")]
    reason_counts = collections.Counter(reason for rec in blocked for reason in rec.get("blocked_reason", []))
    summary = {
        "timestamp": timestamp,
        "partial_generated_v5_snapshot": True,
        "validation_jsonl": str(args.validation_jsonl),
        "eligible_count": len(rows),
        "train_count": len(train),
        "val_count": len(val),
        "test_holdout_count": len(test),
        "raw_hdf5_valid_count": sum(bool(r.get("raw_hdf5_valid")) for r in records),
        "converted_valid_count": sum(bool(r.get("converted_valid")) for r in records),
        "stage1_ready_count": sum(bool(r.get("stage1_ready")) for r in records),
        "blocked_count": len(blocked),
        "blocked_reason_distribution": dict(reason_counts.most_common()),
        "template_distribution": dict(collections.Counter(str(r.get("template")) for r in rows).most_common()),
        "camera_distribution": dict(collections.Counter(str(r.get("camera_variant")) for r in rows).most_common()),
        "chunk_distribution": dict(collections.Counter(str(r.get("chunk_id")) for r in rows).most_common()),
        "manifests": {
            "all": str(all_path),
            "train": str(train_path),
            "val": str(val_path),
            "test_holdout": str(test_path),
            "validation": str(validation_copy),
        },
        "sha256": sha,
    }
    summary_path = out_dir / f"{prefix}_summary.json"
    _write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Physion v5 per-sample raw/conversion/stage1 data gate.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    vc = sub.add_parser("validate-convert")
    vc.add_argument("--generated_root", required=True)
    vc.add_argument("--manifest_chunks_dir", required=True)
    vc.add_argument("--raw_subdir", default=DEFAULT_RAW_SUBDIR)
    vc.add_argument("--converted_root", required=True)
    vc.add_argument("--out_dir", required=True)
    vc.add_argument("--target_frames", type=int, default=TARGET_FRAMES)
    vc.add_argument("--fps", type=int, default=TARGET_FPS)
    vc.add_argument("--min_source_frames", type=int, default=TARGET_FRAMES)
    vc.add_argument("--min_stable_seconds", type=int, default=300)
    vc.add_argument("--raw_probe_stride", type=int, default=10, help="Frame stride for expensive per-frame raw checks; use 1 for strict full-frame scan.")
    vc.add_argument("--convert", action="store_true")
    vc.add_argument("--convert_limit", type=int, default=0)
    vc.add_argument("--force_rebuild_incomplete", action="store_true")
    vc.add_argument("--only_converted_existing", action="store_true", help="Restrict validation to rows whose converted Stage1 files are already complete.")
    vc.add_argument("--max_samples", type=int, default=0)
    vc.add_argument("--progress_every", type=int, default=100)
    vc.set_defaults(func=run_validate_convert)

    snap = sub.add_parser("snapshot")
    snap.add_argument("--validation_jsonl", required=True)
    snap.add_argument("--out_dir", required=True)
    snap.add_argument("--timestamp", default="")
    snap.add_argument("--seed", type=int, default=42)
    snap.set_defaults(func=run_snapshot)
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
