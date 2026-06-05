from __future__ import annotations

import argparse
import io
import json
import math
import statistics
from pathlib import Path
from typing import Any

try:
    import h5py  # type: ignore
except Exception:  # pragma: no cover
    h5py = None

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None

try:
    from PIL import Image, ImageDraw  # type: ignore
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None


def _visit_keys(h5) -> set[str]:
    keys: set[str] = set()
    def visitor(name, obj):
        keys.add(name)
    h5.visititems(visitor)
    return keys


def _scalar_bool(ds: Any) -> bool | None:
    try:
        value = ds[()]
        if hasattr(value, "item"):
            value = value.item()
        return bool(value)
    except Exception:
        return None


def _max_consecutive_false(values: list[bool]) -> int:
    best = cur = 0
    for value in values:
        if value:
            cur = 0
        else:
            cur += 1
            best = max(best, cur)
    return best


def _vector(ds: Any) -> list[float] | None:
    if np is None:
        return None
    try:
        arr = np.asarray(ds[()], dtype="float64").reshape(-1)
        return [float(x) for x in arr.tolist()]
    except Exception:
        return None


def _camera_motion_stats(positions: list[list[float]]) -> dict[str, Any]:
    if np is None or len(positions) < 2:
        return {"camera_translation_total": None, "camera_path_length": None, "camera_step_max": None}
    arr = np.asarray(positions, dtype="float64")
    deltas = arr[1:] - arr[:-1]
    steps = np.linalg.norm(deltas, axis=1)
    total = float(np.linalg.norm(arr[-1] - arr[0]))
    return {
        "camera_translation_total": total,
        "camera_path_length": float(steps.sum()),
        "camera_step_max": float(steps.max()) if steps.size else 0.0,
    }


def _angle_deg(vec: list[float]) -> float:
    if len(vec) < 3:
        return 0.0
    return float(math.degrees(math.atan2(vec[0], vec[2])))


def _unwrap_degrees(values: list[float]) -> list[float]:
    if not values:
        return []
    out = [float(values[0])]
    for value in values[1:]:
        prev = out[-1]
        delta = float(value) - prev
        while delta > 180.0:
            value -= 360.0
            delta = float(value) - prev
        while delta < -180.0:
            value += 360.0
            delta = float(value) - prev
        out.append(float(value))
    return out


def _yaw_stats(positions: list[list[float]], aims: list[list[float]]) -> dict[str, Any]:
    if np is None or len(positions) < 2 or len(aims) != len(positions):
        return {"yaw_change_proxy": None, "yaw_path_proxy": None}
    yaws = []
    for pos, aim in zip(positions, aims):
        direction = [float(aim[i]) - float(pos[i]) for i in range(3)]
        yaws.append(_angle_deg(direction))
    unwrapped = _unwrap_degrees(yaws)
    if len(unwrapped) < 2:
        return {"yaw_change_proxy": None, "yaw_path_proxy": None}
    diffs = [abs(unwrapped[i + 1] - unwrapped[i]) for i in range(len(unwrapped) - 1)]
    return {
        "yaw_change_proxy": float(abs(unwrapped[-1] - unwrapped[0])),
        "yaw_path_proxy": float(sum(diffs)),
    }


def _image_to_gray_array(img) -> Any:
    if np is None:
        return None
    arr = np.asarray(img.convert("L"), dtype="float32") / 255.0
    if arr.ndim != 2:
        return None
    # Downsample by slicing to keep validation light.
    return arr[::8, ::8]


def _background_band(arr: Any) -> Any:
    if np is None or arr is None or arr.ndim != 2:
        return arr
    h, w = arr.shape
    top = arr[: max(1, h // 2), :]
    left = arr[:, : max(1, w // 6)]
    right = arr[:, max(0, w - max(1, w // 6)) :]
    return np.concatenate([top.reshape(-1), left.reshape(-1), right.reshape(-1)])


def _rgb_motion_stats_from_images(images: list[Any]) -> dict[str, Any]:
    if np is None or len(images) < 2:
        return {
            "video_motion_proxy": None,
            "background_motion_proxy": None,
            "parallax_proxy": None,
        }
    grays = [_image_to_gray_array(img) for img in images]
    grays = [g for g in grays if g is not None]
    if len(grays) < 2:
        return {
            "video_motion_proxy": None,
            "background_motion_proxy": None,
            "parallax_proxy": None,
        }
    all_diffs = []
    bg_diffs = []
    for a, b in zip(grays, grays[1:]):
        all_diffs.append(float(np.mean(np.abs(b - a))))
        bg_a = _background_band(a)
        bg_b = _background_band(b)
        bg_diffs.append(float(np.mean(np.abs(bg_b - bg_a))))
    video_motion = float(statistics.mean(all_diffs)) if all_diffs else None
    background_motion = float(statistics.mean(bg_diffs)) if bg_diffs else None
    return {
        "video_motion_proxy": video_motion,
        "background_motion_proxy": background_motion,
        "parallax_proxy": background_motion,
    }


def _decode_image_dataset(ds: Any):
    if Image is None or np is None:
        return None
    try:
        arr = np.asarray(ds[()])
        if arr.ndim == 3:
            return Image.fromarray(arr.astype("uint8")).convert("RGB")
        raw = arr.astype("uint8").tobytes()
        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None


VISIBLE_MOTION_THRESHOLDS = {
    "target_visible_ratio_min": 0.75,
    "max_invisible_frames": 8,
    "min_camera_path_length": 0.45,
    "max_camera_path_length": 1.50,
    "min_background_motion_proxy": 0.012,
    "min_video_motion_proxy": 0.015,
}


def _classify_motion(info: dict[str, Any], profile: str | None) -> dict[str, Any]:
    if profile != "warmup_visible_motion":
        return {
            "too_static": False,
            "too_extreme": False,
            "suitable_for_visible_motion": None,
            "motion_rejection_reasons": [],
        }
    t = VISIBLE_MOTION_THRESHOLDS
    reasons: list[str] = []
    extreme: list[str] = []
    camera_path = info.get("camera_path_length")
    bg_motion = info.get("background_motion_proxy")
    video_motion = info.get("video_motion_proxy")
    visible_ratio = info.get("target_visible_ratio")
    max_invisible = info.get("target_disappeared_consecutive_max")
    if camera_path is None or float(camera_path) < t["min_camera_path_length"]:
        reasons.append("camera_path_too_short")
    if bg_motion is not None and float(bg_motion) < t["min_background_motion_proxy"]:
        reasons.append("background_motion_too_low")
    if video_motion is not None and float(video_motion) < t["min_video_motion_proxy"]:
        reasons.append("video_motion_too_low")
    if camera_path is not None and float(camera_path) > t["max_camera_path_length"]:
        extreme.append("camera_path_too_long")
    if visible_ratio is not None and float(visible_ratio) < t["target_visible_ratio_min"]:
        extreme.append("low_target_visible_ratio")
    if max_invisible is not None and int(max_invisible) > t["max_invisible_frames"]:
        extreme.append("target_invisible_too_long")
    too_static = bool(reasons)
    too_extreme = bool(extreme)
    return {
        "too_static": too_static,
        "too_extreme": too_extreme,
        "suitable_for_visible_motion": not too_static and not too_extreme,
        "motion_rejection_reasons": reasons + extreme,
        "visible_motion_thresholds": dict(t),
    }


def make_contact_sheet(path: Path, out_dir: Path, *, max_frames: int = 12) -> str | None:
    if h5py is None or Image is None or ImageDraw is None:
        return None
    try:
        with h5py.File(path, "r") as f:
            frame_keys = sorted(f["frames"].keys()) if "frames" in f else []
            if not frame_keys:
                return None
            if len(frame_keys) <= max_frames:
                selected = frame_keys
            else:
                selected = [frame_keys[round(i * (len(frame_keys) - 1) / (max_frames - 1))] for i in range(max_frames)]
            thumbs = []
            for frame in selected:
                ds = f.get(f"frames/{frame}/images/_img")
                if ds is None:
                    continue
                img = _decode_image_dataset(ds)
                if img is None:
                    continue
                img.thumbnail((240, 140))
                canvas = Image.new("RGB", (240, 165), (20, 24, 31))
                canvas.paste(img, ((240 - img.width) // 2, 0))
                draw = ImageDraw.Draw(canvas)
                draw.text((8, 145), frame, fill=(230, 235, 245))
                thumbs.append(canvas)
            if not thumbs:
                return None
            cols = min(4, len(thumbs))
            rows = int(math.ceil(len(thumbs) / cols))
            sheet = Image.new("RGB", (cols * 240, rows * 165), (10, 14, 22))
            for idx, thumb in enumerate(thumbs):
                sheet.paste(thumb, ((idx % cols) * 240, (idx // cols) * 165))
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{path.parent.name}_{path.stem}_contact_sheet.jpg"
            sheet.save(out_path, quality=90)
            return str(out_path)
    except Exception:
        return None


def validate_hdf5(path: Path, *, profile: str | None = None) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}
    if h5py is None:
        info.update({"status": "blocked", "error": "h5py unavailable"})
        return info
    if not path.exists():
        info.update({"status": "missing"})
        return info
    try:
        with h5py.File(path, "r") as f:
            keys = _visit_keys(f)
            frame_keys = sorted(f["frames"].keys()) if "frames" in f else []
            first = f"frames/{frame_keys[0]}/images" if frame_keys else ""
            passes = sorted(f[first].keys()) if first and first in f else []
            label_counts = {"camera_pose": 0, "camera_position": 0, "camera_aim": 0}
            target_visible: list[bool] = []
            camera_positions: list[list[float]] = []
            camera_aims: list[list[float]] = []
            sampled_images: list[Any] = []
            sample_stride = max(1, len(frame_keys) // 12) if frame_keys else 1
            for frame in frame_keys:
                labels = f.get(f"frames/{frame}/labels")
                if labels is not None:
                    for k in label_counts:
                        if k in labels:
                            label_counts[k] += 1
                    if "has_target" in labels:
                        value = _scalar_bool(labels["has_target"])
                        if value is not None:
                            target_visible.append(value)
                    if "camera_position" in labels:
                        vec = _vector(labels["camera_position"])
                        if vec and len(vec) >= 3:
                            camera_positions.append(vec[:3])
                    if "camera_aim" in labels:
                        vec = _vector(labels["camera_aim"])
                        if vec and len(vec) >= 3:
                            camera_aims.append(vec[:3])
                if len(sampled_images) < 12:
                    try:
                        frame_num = int(str(frame))
                    except Exception:
                        frame_num = len(sampled_images) * sample_stride
                    if frame_num % sample_stride == 0 or frame == frame_keys[-1]:
                        ds = f.get(f"frames/{frame}/images/_img")
                        if ds is not None:
                            img = _decode_image_dataset(ds)
                            if img is not None:
                                sampled_images.append(img)
            target_visible_ratio = None
            target_disappeared_consecutive_max = None
            if target_visible:
                target_visible_ratio = float(sum(target_visible) / len(target_visible))
                target_disappeared_consecutive_max = _max_consecutive_false(target_visible)
            camera_stats = _camera_motion_stats(camera_positions)
            yaw_stats = _yaw_stats(camera_positions, camera_aims)
            rgb_motion_stats = _rgb_motion_stats_from_images(sampled_images)
            info.update({
                "status": "ok",
                "frame_count": len(frame_keys),
                "passes": passes,
                "has_rgb": "_img" in passes,
                "has_depth": "_depth" in passes,
                "has_id": "_id" in passes,
                "has_camera_pose": label_counts["camera_pose"] == len(frame_keys) and len(frame_keys) > 0,
                "has_camera_position": label_counts["camera_position"] == len(frame_keys) and len(frame_keys) > 0,
                "has_camera_aim": label_counts["camera_aim"] == len(frame_keys) and len(frame_keys) > 0,
                "has_projection_or_camera_matrix": any("projection" in k or "camera_matrix" in k for k in keys),
                "has_object_state": any("object" in k.lower() or "transforms" in k.lower() or "rigid" in k.lower() for k in keys),
                "target_visible_ratio": target_visible_ratio,
                "target_area_ratio_avg": None,
                "target_disappeared_consecutive_max": target_disappeared_consecutive_max,
                **camera_stats,
                **yaw_stats,
                **rgb_motion_stats,
            })
            info.update(_classify_motion(info, profile))
    except Exception as exc:
        info.update({"status": "error", "error": repr(exc)})
    return info


def _trial_dir_name(index: int, trial: dict[str, Any]) -> str:
    template = str(trial.get("template") or "unknown")
    variant = str(trial.get("camera_variant") or "unknown")
    seed = int(trial.get("seed", index))
    return f"{index:05d}_{template}_{variant}_seed{seed}"


def _manifest_output_subdir(profile: str, manifest: Path, num_trials: int) -> str:
    if "template_diverse" in manifest.stem:
        return f"{profile}_template_diverse_{num_trials}samples"
    return f"{profile}_plan_{num_trials}samples"


def _paths_from_manifest(root: Path, manifest: Path) -> list[Path]:
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    profile = str(rows[0].get("profile") or "warmup_mild") if rows else "warmup_mild"
    subdir = _manifest_output_subdir(profile, manifest, len(rows))
    paths: list[Path] = []
    for idx, row in enumerate(rows):
        trial_dir = root / "raw_hdf5" / subdir / _trial_dir_name(idx, row)
        final_path = trial_dir / "0000.hdf5"
        temp_path = trial_dir / "temp.hdf5"
        paths.append(final_path if final_path.exists() else temp_path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated TDW/Physion-style HDF5 files.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--make_contact_sheet", action="store_true")
    parser.add_argument("--profile", default=None)
    args = parser.parse_args()
    if args.manifest:
        hdf5_paths = _paths_from_manifest(args.root, args.manifest)
    else:
        hdf5_paths = sorted(args.root.rglob("*.hdf5")) + sorted(args.root.rglob("*.h5"))
    rows = [validate_hdf5(p, profile=args.profile) for p in hdf5_paths]
    contact_dir = args.out.parent / "contact_sheets"
    contact_index: list[dict[str, str]] = []
    if args.make_contact_sheet:
        for row in rows:
            if row.get("status") != "ok":
                continue
            sheet = make_contact_sheet(Path(str(row["path"])), contact_dir)
            if sheet:
                row["contact_sheet_path"] = sheet
                contact_index.append({"hdf5": str(row["path"]), "contact_sheet": sheet})
    ok = [r for r in rows if r.get("status") == "ok"]
    suitable = [
        r for r in ok
        if r.get("has_rgb")
        and r.get("has_depth")
        and r.get("has_id")
        and r.get("has_camera_pose")
        and r.get("has_projection_or_camera_matrix")
        and r.get("has_object_state")
        and (r.get("target_visible_ratio") is None or float(r.get("target_visible_ratio")) >= 0.75)
        and (r.get("target_disappeared_consecutive_max") is None or int(r.get("target_disappeared_consecutive_max")) <= 20)
    ]
    visible_motion_ok = [
        r for r in ok
        if r.get("suitable_for_visible_motion") is True
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TDW Generation v2 Validation Report",
        "",
        f"Root: `{args.root}`",
        f"Generated HDF5 count: {len(rows)}",
        f"Validation ok count: {len(ok)}",
        f"Suitable for warmup count: {len(suitable)}",
        f"Suitable for visible motion count: {len(visible_motion_ok)}",
        "",
        "| path | status | frames | rgb | depth | id | camera_pose | projection/camera_matrix | object_state | visible_ratio | max_invisible | camera_path | bg_motion | too_static | too_extreme | visible_motion | contact_sheet |",
        "|---|---|---:|---|---|---|---|---|---|---:|---:|---:|---:|---|---|---|---|",
    ]
    for r in rows[:200]:
        lines.append(
            f"| `{r.get('path')}` | {r.get('status')} | {r.get('frame_count', '')} | {r.get('has_rgb', '')} | {r.get('has_depth', '')} | {r.get('has_id', '')} | {r.get('has_camera_pose', '')} | {r.get('has_projection_or_camera_matrix', '')} | {r.get('has_object_state', '')} | {r.get('target_visible_ratio', '')} | {r.get('target_disappeared_consecutive_max', '')} | {r.get('camera_path_length', '')} | {r.get('background_motion_proxy', '')} | {r.get('too_static', '')} | {r.get('too_extreme', '')} | {r.get('suitable_for_visible_motion', '')} | `{r.get('contact_sheet_path', '')}` |"
        )
    if not rows:
        lines += ["", "No generated HDF5 files were found. This is a blocker for actual validation, not a fake success."]
    if contact_index:
        index_path = args.out.parent / "contact_sheet_index.md"
        index_lines = ["# TDW Generation v2 Contact Sheets", "", "| HDF5 | Contact Sheet |", "|---|---|"]
        for row in contact_index:
            index_lines.append(f"| `{row['hdf5']}` | `{row['contact_sheet']}` |")
        index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_out = args.out.with_suffix(".json")
    json_out.write_text(json.dumps({"rows": rows, "contact_sheets": contact_index}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "hdf5_count": len(rows),
        "ok_count": len(ok),
        "suitable_for_warmup": len(suitable),
        "suitable_for_visible_motion": len(visible_motion_ok),
    }, indent=2))


if __name__ == "__main__":
    main()
