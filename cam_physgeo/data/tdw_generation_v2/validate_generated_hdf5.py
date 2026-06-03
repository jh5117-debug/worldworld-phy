from __future__ import annotations

import argparse
import io
import json
import math
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


def validate_hdf5(path: Path) -> dict[str, Any]:
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
            target_visible_ratio = None
            target_disappeared_consecutive_max = None
            if target_visible:
                target_visible_ratio = float(sum(target_visible) / len(target_visible))
                target_disappeared_consecutive_max = _max_consecutive_false(target_visible)
            camera_stats = _camera_motion_stats(camera_positions)
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
            })
    except Exception as exc:
        info.update({"status": "error", "error": repr(exc)})
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated TDW/Physion-style HDF5 files.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--make_contact_sheet", action="store_true")
    args = parser.parse_args()
    hdf5_paths = sorted(args.root.rglob("*.hdf5")) + sorted(args.root.rglob("*.h5"))
    rows = [validate_hdf5(p) for p in hdf5_paths]
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
    args.out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TDW Generation v2 Validation Report",
        "",
        f"Root: `{args.root}`",
        f"Generated HDF5 count: {len(rows)}",
        f"Validation ok count: {len(ok)}",
        f"Suitable for warmup count: {len(suitable)}",
        "",
        "| path | status | frames | rgb | depth | id | camera_pose | projection/camera_matrix | object_state | visible_ratio | max_invisible | camera_path | contact_sheet |",
        "|---|---|---:|---|---|---|---|---|---|---:|---:|---:|---|",
    ]
    for r in rows[:200]:
        lines.append(
            f"| `{r.get('path')}` | {r.get('status')} | {r.get('frame_count', '')} | {r.get('has_rgb', '')} | {r.get('has_depth', '')} | {r.get('has_id', '')} | {r.get('has_camera_pose', '')} | {r.get('has_projection_or_camera_matrix', '')} | {r.get('has_object_state', '')} | {r.get('target_visible_ratio', '')} | {r.get('target_disappeared_consecutive_max', '')} | {r.get('camera_path_length', '')} | `{r.get('contact_sheet_path', '')}` |"
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
    print(json.dumps({"out": str(args.out), "hdf5_count": len(rows), "ok_count": len(ok), "suitable_for_warmup": len(suitable)}, indent=2))


if __name__ == "__main__":
    main()
