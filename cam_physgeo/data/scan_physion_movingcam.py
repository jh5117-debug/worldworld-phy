from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterator

from cam_physgeo.data.physion_hdf5_reader import infer_key_mapping
from cam_physgeo.data.sample_schema import normalize_sample
from cam_physgeo.utils.camera import infer_camera_motion_name
from cam_physgeo.utils.video import probe_video


TEMPLATE_HINTS = {
    "drop": ["drop"],
    "collision": ["collision", "collide", "impact"],
    "roll": ["roll", "rolling", "slide", "sliding"],
    "containment": ["containment", "container"],
    "support": ["support"],
    "dominoes": ["domino"],
    "drape": ["drape"],
    "link": ["link"],
}


def candidate_roots(root: str | Path | None, outputs_root: str | Path | None = None) -> list[Path]:
    roots: list[Path] = []
    if outputs_root:
        roots.append(Path(outputs_root).expanduser())
    if root:
        r = Path(root).expanduser()
        roots.extend([r.parent / "outputs", r])
    out: list[Path] = []
    seen: set[str] = set()
    for candidate in roots:
        if not candidate.exists():
            continue
        key = str(candidate.resolve())
        if key not in seen:
            out.append(candidate)
            seen.add(key)
    return out


def iter_physion_movingcam_samples(
    root: str | Path | None,
    *,
    outputs_root: str | Path | None = None,
    limit: int | None = None,
) -> Iterator[dict]:
    count = 0
    for scan_root in candidate_roots(root, outputs_root):
        for dirpath, _, filenames in os.walk(scan_root):
            files = [Path(dirpath) / name for name in filenames]
            hdf5_files = sorted(p for p in files if p.suffix.lower() in {".hdf5", ".h5"})
            video_files = sorted(p for p in files if p.suffix.lower() in {".mp4", ".avi", ".mov"})
            if not hdf5_files and not video_files:
                continue
            hdf5_path = hdf5_files[0] if hdf5_files else None
            video_path = choose_video(video_files)
            directory = Path(dirpath)
            meta = read_metadata(directory)
            mapping = {}
            flags: list[str] = []
            if hdf5_path:
                try:
                    mapping = infer_key_mapping(hdf5_path)
                except Exception as exc:
                    flags.append(f"hdf5_key_audit_failed:{type(exc).__name__}")
            probe = probe_video(video_path) if video_path else {}
            template = str(meta.get("template") or meta.get("trial_type") or infer_template(str(directory)))
            camera_motion = str(meta.get("camera_motion") or meta.get("camera_path") or infer_camera_motion_name(str(directory)))
            has_reobserve = any(k in camera_motion for k in ["reobserve", "lookaway", "offscreen", "yaw"])
            if hdf5_path and not mapping.get("poses_key") and not (
                mapping.get("camera_position_key") and mapping.get("camera_aim_key")
            ):
                flags.append("missing_camera_pose_or_position_aim")
            if hdf5_path and not mapping.get("intrinsics_key") and not mapping.get("fov_key"):
                flags.append("missing_intrinsics_or_projection")
            if hdf5_path and not video_path:
                flags.append("video_missing_hdf5_rgb_available")
            sample = {
                "sample_id": sample_id("physion_movingcam", directory),
                "source": "physion_movingcam",
                "template": template,
                "camera_motion": camera_motion,
                "video_path": str(video_path) if video_path else None,
                "hdf5_path": str(hdf5_path) if hdf5_path else None,
                "rgb_key": mapping.get("rgb_key"),
                "depth_key": mapping.get("depth_key"),
                "id_key": mapping.get("id_key"),
                "flow_key": mapping.get("flow_key"),
                "normal_key": mapping.get("normal_key"),
                "poses_key": mapping.get("poses_key"),
                "intrinsics_key": mapping.get("intrinsics_key"),
                "camera_position_key": mapping.get("camera_position_key"),
                "camera_aim_key": mapping.get("camera_aim_key"),
                "camera_matrix_key": mapping.get("camera_matrix_key"),
                "projection_matrix_key": mapping.get("projection_matrix_key"),
                "object_state_keys": mapping.get("object_state_keys") or [],
                "prompt_path": first_existing(directory, ["prompt.txt"]) or "generated://physion_movingcam",
                "num_frames": probe.get("num_frames") or mapping.get("frame_count"),
                "fps": probe.get("fps") or meta.get("fps") or 16,
                "width": probe.get("width") or meta.get("width") or 832,
                "height": probe.get("height") or meta.get("height") or 480,
                "has_moving_camera": camera_motion not in {"static", "fixed", "unknown"},
                "has_depth": bool(mapping.get("depth_key")),
                "has_id_mask": bool(mapping.get("id_key")),
                "has_flow": bool(mapping.get("flow_key")),
                "has_normals": bool(mapping.get("normal_key")),
                "has_object_state": bool(mapping.get("object_state_key") or mapping.get("object_state_keys")),
                "has_camera_pose": bool(mapping.get("poses_key") or mapping.get("camera_matrix_key") or (mapping.get("camera_position_key") and mapping.get("camera_aim_key"))),
                "has_intrinsics": bool(mapping.get("intrinsics_key") or mapping.get("projection_matrix_key") or mapping.get("fov_key")),
                "has_reobserve": has_reobserve,
                "quality_flags": flags,
            }
            yield normalize_sample(sample)
            count += 1
            if limit and count >= limit:
                return


def choose_video(videos: list[Path]) -> Path | None:
    if not videos:
        return None
    preferred = [p for p in videos if "preview" in p.name.lower() or "aligned" in p.name.lower() or "video" in p.name.lower()]
    return (preferred or videos)[0]


def infer_template(text: str) -> str:
    s = text.lower()
    for label, hints in TEMPLATE_HINTS.items():
        if any(hint in s for hint in hints):
            return label
    return "unknown"


def read_metadata(directory: Path) -> dict:
    for name in ["metadata.json", "summary.json", "batch_config.json", "tdw_commands.json"]:
        path = directory / name
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
    return {}


def first_existing(directory: Path, names: list[str]) -> str | None:
    for name in names:
        path = directory / name
        if path.exists():
            return str(path)
    return None


def sample_id(source: str, path: Path) -> str:
    return f"{source}_{hashlib.sha1(str(path).encode()).hexdigest()[:12]}"
