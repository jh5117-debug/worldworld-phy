from __future__ import annotations

from pathlib import Path
from typing import Any


VALID_SOURCES = {"physion_official", "physion_movingcam"}

REQUIRED_FIELDS = [
    "sample_id",
    "source",
    "template",
    "camera_motion",
    "video_path",
    "hdf5_path",
    "rgb_key",
    "depth_key",
    "id_key",
    "flow_key",
    "normal_key",
    "poses_key",
    "intrinsics_key",
    "camera_position_key",
    "camera_aim_key",
    "camera_matrix_key",
    "projection_matrix_key",
    "object_state_keys",
    "prompt_path",
    "num_frames",
    "fps",
    "width",
    "height",
    "has_moving_camera",
    "has_depth",
    "has_id_mask",
    "has_flow",
    "has_normals",
    "has_object_state",
    "has_camera_pose",
    "has_intrinsics",
    "has_reobserve",
    "quality_flags",
]

DEFAULT_SAMPLE: dict[str, Any] = {
    "video_path": None,
    "hdf5_path": None,
    "rgb_key": None,
    "depth_key": None,
    "id_key": None,
    "flow_key": None,
    "normal_key": None,
    "poses_key": None,
    "intrinsics_key": None,
    "camera_position_key": None,
    "camera_aim_key": None,
    "camera_matrix_key": None,
    "projection_matrix_key": None,
    "object_state_keys": [],
    "camera_position_path": None,
    "camera_aim_path": None,
    "rgb_frames": None,
    "depth_path": None,
    "id_path": None,
    "poses_path": None,
    "intrinsics_path": None,
    "prompt_path": "generated://physion",
    "num_frames": None,
    "fps": None,
    "width": None,
    "height": None,
    "has_moving_camera": False,
    "has_depth": False,
    "has_id_mask": False,
    "has_flow": False,
    "has_normals": False,
    "has_object_state": False,
    "has_camera_pose": False,
    "has_intrinsics": False,
    "has_reobserve": False,
    "quality_flags": [],
}


def normalize_sample(sample: dict[str, Any]) -> dict[str, Any]:
    out = dict(DEFAULT_SAMPLE)
    out.update(sample)
    out["quality_flags"] = list(out.get("quality_flags") or [])
    if out.get("poses_key") and not out.get("poses_path") and out.get("hdf5_path"):
        out["poses_path"] = f"hdf5://{out['hdf5_path']}::{out['poses_key']}"
    if out.get("intrinsics_key") and not out.get("intrinsics_path") and out.get("hdf5_path"):
        out["intrinsics_path"] = f"hdf5://{out['hdf5_path']}::{out['intrinsics_key']}"
    if out.get("camera_position_key") and not out.get("camera_position_path") and out.get("hdf5_path"):
        out["camera_position_path"] = f"hdf5://{out['hdf5_path']}::{out['camera_position_key']}"
    if out.get("camera_aim_key") and not out.get("camera_aim_path") and out.get("hdf5_path"):
        out["camera_aim_path"] = f"hdf5://{out['hdf5_path']}::{out['camera_aim_key']}"
    if out.get("camera_matrix_key") and not out.get("poses_path") and out.get("hdf5_path"):
        out["poses_path"] = f"hdf5://{out['hdf5_path']}::{out['camera_matrix_key']}"
    if out.get("projection_matrix_key") and not out.get("intrinsics_path") and out.get("hdf5_path"):
        out["intrinsics_path"] = f"hdf5://{out['hdf5_path']}::{out['projection_matrix_key']}"
    if out.get("depth_key") and not out.get("depth_path") and out.get("hdf5_path"):
        out["depth_path"] = f"hdf5://{out['hdf5_path']}::{out['depth_key']}"
    if out.get("id_key") and not out.get("id_path") and out.get("hdf5_path"):
        out["id_path"] = f"hdf5://{out['hdf5_path']}::{out['id_key']}"
    return out


def validate_sample(sample: dict[str, Any], check_paths: bool = True) -> list[str]:
    errors = [f"missing:{k}" for k in REQUIRED_FIELDS if k not in sample]
    if sample.get("source") not in VALID_SOURCES:
        errors.append("invalid:source")
    if check_paths:
        for key in ["video_path", "hdf5_path", "poses_path", "intrinsics_path", "prompt_path"]:
            value = sample.get(key)
            if not value or str(value).startswith(("hdf5://", "generated://", "computed://")):
                continue
            if not Path(str(value)).exists():
                errors.append(f"missing_path:{key}")
    return errors
