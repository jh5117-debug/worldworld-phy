from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterator

from cam_physgeo.data.physion_hdf5_reader import infer_key_mapping
from cam_physgeo.data.sample_schema import normalize_sample
from cam_physgeo.data.scan_physion_movingcam import infer_template
from cam_physgeo.utils.camera import infer_camera_motion_name
from cam_physgeo.utils.video import probe_video


def iter_physion_official_samples(root: str | Path, *, limit: int | None = None) -> Iterator[dict]:
    root_path = Path(root).expanduser()
    if not root_path.exists():
        print(f"WARNING: Physion official root missing: {root_path}")
        return
    count = 0
    for dirpath, _, filenames in os.walk(root_path):
        files = [Path(dirpath) / name for name in filenames]
        hdf5_files = sorted(p for p in files if p.suffix.lower() in {".hdf5", ".h5"})
        video_files = sorted(p for p in files if p.suffix.lower() in {".mp4", ".avi", ".mov"})
        if not hdf5_files and not video_files:
            continue
        hdf5_path = hdf5_files[0] if hdf5_files else None
        video_path = video_files[0] if video_files else None
        mapping = {}
        flags: list[str] = []
        if hdf5_path:
            try:
                mapping = infer_key_mapping(hdf5_path)
            except Exception as exc:
                flags.append(f"hdf5_key_audit_failed:{type(exc).__name__}")
        camera_motion = infer_camera_motion_name(str(dirpath))
        if camera_motion == "unknown":
            camera_motion = "static"
        if not mapping.get("poses_key") and not (mapping.get("camera_position_key") and mapping.get("camera_aim_key")):
            flags.append("official_camera_pose_missing_or_not_audited")
        if not mapping.get("intrinsics_key") and not mapping.get("fov_key"):
            flags.append("official_intrinsics_missing_or_not_audited")
        probe = probe_video(video_path) if video_path else {}
        sample = {
            "sample_id": sample_id("physion_official", Path(dirpath)),
            "source": "physion_official",
            "template": infer_template(str(dirpath)),
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
            "prompt_path": "generated://physion_official",
            "num_frames": probe.get("num_frames") or mapping.get("frame_count"),
            "fps": probe.get("fps") or 16,
            "width": probe.get("width") or 832,
            "height": probe.get("height") or 480,
            "has_moving_camera": camera_motion not in {"static", "fixed", "unknown"},
            "has_depth": bool(mapping.get("depth_key")),
            "has_id_mask": bool(mapping.get("id_key")),
            "has_flow": bool(mapping.get("flow_key")),
            "has_normals": bool(mapping.get("normal_key")),
            "has_object_state": bool(mapping.get("object_state_key")),
            "has_camera_pose": bool(mapping.get("poses_key") or (mapping.get("camera_position_key") and mapping.get("camera_aim_key"))),
            "has_intrinsics": bool(mapping.get("intrinsics_key") or mapping.get("fov_key")),
            "has_reobserve": False,
            "quality_flags": flags,
        }
        yield normalize_sample(sample)
        count += 1
        if limit and count >= limit:
            return


def sample_id(source: str, path: Path) -> str:
    return f"{source}_{hashlib.sha1(str(path).encode()).hexdigest()[:12]}"
