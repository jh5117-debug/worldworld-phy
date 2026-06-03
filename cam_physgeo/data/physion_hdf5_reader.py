from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Any

import numpy as np


RGB_HINTS = ("images/_img", "_img", "rgb", "image")
DEPTH_HINTS = ("images/_depth", "_depth", "depth")
ID_HINTS = ("images/_id", "_id", "id_mask", "segmentation")
FLOW_HINTS = ("flow", "optical_flow")
NORMAL_HINTS = ("normal", "normals")
POSE_HINTS = ("labels/camera_pose", "camera_pose")
CAMERA_MATRIX_HINTS = ("camera_matrix", "camera_matrices/camera_matrix", "view_matrix", "extrinsic", "extrinsics")
PROJECTION_HINTS = ("projection_matrix", "camera_matrices/projection_matrix", "camera_projection_matrix")
INTRINSICS_HINTS = ("intrinsics", "camera_intrinsics", "intrinsic", "camera_matrix_k")
POSITION_HINTS = ("labels/camera_position", "camera_position", "avatar_position")
AIM_HINTS = ("labels/camera_aim", "camera_aim", "look_at", "look_at_position")
FOV_HINTS = ("field_of_view", "fov")
OBJECT_HINTS = ("objects/positions", "object_states", "objects")


def list_hdf5_datasets(path: str | Path, *, limit: int | None = None) -> dict[str, dict[str, Any]]:
    import h5py

    out: dict[str, dict[str, Any]] = {}
    with h5py.File(path, "r") as handle:
        def visit(name: str, obj: Any) -> None:
            if hasattr(obj, "shape"):
                if limit is None or len(out) < limit:
                    out[name] = {"shape": tuple(int(x) for x in obj.shape), "dtype": str(obj.dtype)}

        handle.visititems(visit)
    return out


def first_frame_group(handle: Any) -> str | None:
    if "frames" not in handle:
        return None
    names = sorted(handle["frames"].keys())
    return f"frames/{names[0]}" if names else None


def find_key(keys: dict[str, Any] | list[str], hints: tuple[str, ...]) -> str | None:
    names = list(keys.keys()) if isinstance(keys, dict) else list(keys)
    lowered = {n.lower(): n for n in names}
    for hint in hints:
        h = hint.lower()
        if h in lowered:
            return lowered[h]
    for hint in hints:
        h = hint.lower()
        for low, original in lowered.items():
            basename = low.rsplit("/", 1)[-1]
            if low.endswith("/" + h) or basename == h:
                return original
            if len(h) <= 2:
                continue
            if h in low:
                return original
    return None


def frame_dataset_key(handle: Any, frame_group: str | None, hints: tuple[str, ...]) -> str | None:
    if not frame_group:
        return find_key(_all_dataset_names(handle), hints)
    names = _all_dataset_names(handle[frame_group], prefix=frame_group)
    return find_key(names, hints)


def infer_key_mapping(path: str | Path) -> dict[str, Any]:
    import h5py

    with h5py.File(path, "r") as handle:
        fg = first_frame_group(handle)
        all_names = _all_dataset_names(handle)
        frame_names = _all_dataset_names(handle[fg], prefix=fg) if fg else all_names
        frames = sorted(handle["frames"].keys()) if "frames" in handle else []
        mapping = {
            "frame_count": len(frames) if frames else None,
            "first_frame_group": fg,
            "rgb_key": find_key(frame_names, RGB_HINTS),
            "depth_key": find_key(frame_names, DEPTH_HINTS),
            "id_key": find_key(frame_names, ID_HINTS),
            "flow_key": find_key(frame_names, FLOW_HINTS),
            "normal_key": find_key(frame_names, NORMAL_HINTS),
            "poses_key": find_key(frame_names, POSE_HINTS + CAMERA_MATRIX_HINTS),
            "camera_matrix_key": find_key(frame_names, CAMERA_MATRIX_HINTS),
            "projection_matrix_key": find_key(frame_names, PROJECTION_HINTS),
            "intrinsics_key": find_key(frame_names, INTRINSICS_HINTS + PROJECTION_HINTS),
            "camera_position_key": find_key(frame_names, POSITION_HINTS),
            "camera_aim_key": find_key(frame_names, AIM_HINTS),
            "fov_key": find_key(frame_names + all_names, FOV_HINTS),
            "object_state_key": find_key(frame_names, OBJECT_HINTS),
            "object_state_keys": [name for name in frame_names if any(h in name.lower() for h in OBJECT_HINTS)][:16],
            "static_moving_camera_key": find_key(all_names, ("static/moving_camera/motion", "moving_camera/motion")),
            "static_target_key": find_key(all_names, ("static/target_id", "target_id")),
        }
    return mapping


def read_physion_sample(
    path: str | Path,
    *,
    limit_frames: int | None = None,
    lazy: bool = False,
) -> dict[str, Any]:
    import h5py

    path = Path(path)
    mapping = infer_key_mapping(path)
    result: dict[str, Any] = {
        "rgb": None,
        "depth": None,
        "id_mask": None,
        "flow": None,
        "normals": None,
        "camera_pose": None,
        "camera_position": None,
        "camera_aim": None,
        "intrinsics": None,
        "object_states": None,
        "metadata": {"path": str(path), "key_mapping": mapping, "camera_metadata_missing": False},
    }
    if lazy:
        result["metadata"]["lazy"] = True
        return result

    with h5py.File(path, "r") as handle:
        frame_names = sorted(handle["frames"].keys()) if "frames" in handle else []
        if limit_frames:
            frame_names = frame_names[: int(limit_frames)]
        rgb = []
        depth = []
        ids = []
        poses = []
        positions = []
        aims = []
        projections = []
        object_positions = []
        for frame in frame_names:
            base = f"frames/{frame}"
            rgb_arr = _read_dataset(handle, _relative_frame_key(mapping.get("rgb_key"), base))
            if rgb_arr is not None:
                rgb.append(decode_image_array(rgb_arr))
            dep_arr = _read_dataset(handle, _relative_frame_key(mapping.get("depth_key"), base))
            if dep_arr is not None:
                depth.append(decode_image_array(dep_arr))
            id_arr = _read_dataset(handle, _relative_frame_key(mapping.get("id_key"), base))
            if id_arr is not None:
                ids.append(decode_image_array(id_arr))
            pose = _read_dataset(handle, _relative_frame_key(mapping.get("poses_key") or mapping.get("camera_matrix_key"), base))
            if pose is not None:
                poses.append(_reshape_matrix(pose))
            pos = _read_dataset(handle, _relative_frame_key(mapping.get("camera_position_key"), base))
            aim = _read_dataset(handle, _relative_frame_key(mapping.get("camera_aim_key"), base))
            if pos is not None:
                positions.append(np.asarray(pos, dtype=np.float32).reshape(-1)[:3])
            if aim is not None:
                aims.append(np.asarray(aim, dtype=np.float32).reshape(-1)[:3])
            proj = _read_dataset(handle, _relative_frame_key(mapping.get("intrinsics_key") or mapping.get("projection_matrix_key"), base))
            if proj is not None:
                projections.append(_reshape_matrix(proj))
            obj = _read_dataset(handle, f"{base}/objects/positions")
            if obj is not None:
                object_positions.append(np.asarray(obj))
        if rgb:
            result["rgb"] = _stack_same_shape(rgb)
            if result["rgb"] is None:
                result["metadata"]["rgb_stack_skipped"] = "decoded RGB frames had inconsistent shapes"
        if depth:
            result["depth"] = _stack_same_shape(depth)
            if result["depth"] is None:
                result["metadata"]["depth_stack_skipped"] = "decoded depth frames had inconsistent shapes"
        if ids:
            result["id_mask"] = _stack_same_shape(ids)
            if result["id_mask"] is None:
                result["metadata"]["id_mask_stack_skipped"] = "decoded ID frames had inconsistent shapes"
        if poses:
            result["camera_pose"] = np.stack(poses)
        elif positions and aims:
            result["camera_pose"] = np.stack([pose_from_position_aim(p, a) for p, a in zip(positions, aims)])
            result["metadata"]["camera_metadata_source"] = "computed_from_position_aim"
        if positions:
            result["camera_position"] = np.stack(positions)
        if aims:
            result["camera_aim"] = np.stack(aims)
        if projections:
            result["intrinsics"] = np.stack([intrinsics_from_projection(p, width=None, height=None) for p in projections])
            result["metadata"]["intrinsics_source"] = "hdf5" if mapping.get("intrinsics_key") else "projection_matrix"
        if object_positions:
            stacked_objects = _stack_same_shape(object_positions)
            if stacked_objects is not None:
                result["object_states"] = {"positions": stacked_objects}
            else:
                result["metadata"]["object_state_stack_skipped"] = "object position arrays had inconsistent shapes"
    if result["camera_pose"] is None:
        result["metadata"]["camera_metadata_missing"] = True
    return result


def decode_image_array(arr: Any) -> np.ndarray:
    arr = np.asarray(arr)
    if arr.ndim == 1 and arr.dtype == np.uint8:
        try:
            import cv2

            decoded = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
            if decoded is not None:
                if decoded.ndim == 3:
                    decoded = cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)
                return decoded
        except Exception:
            pass
        try:
            from PIL import Image

            image = Image.open(io.BytesIO(arr.tobytes()))
            return np.asarray(image.convert("RGB"))
        except Exception:
            pass
    return arr


def compute_intrinsics_from_fov(fov_degrees: float, width: int, height: int) -> np.ndarray:
    fov = math.radians(float(fov_degrees))
    fy = 0.5 * float(height) / math.tan(fov / 2.0)
    fx = fy
    return np.array([[fx, 0.0, width / 2.0], [0.0, fy, height / 2.0], [0.0, 0.0, 1.0]], dtype=np.float32)


def intrinsics_from_projection(projection: np.ndarray, width: int | None, height: int | None) -> np.ndarray:
    mat = _reshape_matrix(projection)
    if width and height:
        fx = float(mat[0, 0]) * width / 2.0
        fy = float(mat[1, 1]) * height / 2.0
        return np.array([[fx, 0.0, width / 2.0], [0.0, fy, height / 2.0], [0.0, 0.0, 1.0]], dtype=np.float32)
    return mat.astype(np.float32)


def pose_from_position_aim(position: np.ndarray, aim: np.ndarray, up: np.ndarray | None = None) -> np.ndarray:
    position = np.asarray(position, dtype=np.float32).reshape(3)
    aim = np.asarray(aim, dtype=np.float32).reshape(3)
    up = np.asarray(up if up is not None else [0.0, 1.0, 0.0], dtype=np.float32)
    forward = aim - position
    forward = forward / (np.linalg.norm(forward) + 1e-8)
    right = np.cross(forward, up)
    right = right / (np.linalg.norm(right) + 1e-8)
    true_up = np.cross(right, forward)
    pose = np.eye(4, dtype=np.float32)
    pose[:3, 0] = right
    pose[:3, 1] = true_up
    pose[:3, 2] = forward
    pose[:3, 3] = position
    return pose


def _all_dataset_names(group: Any, prefix: str = "") -> list[str]:
    names: list[str] = []

    def visit(name: str, obj: Any) -> None:
        if hasattr(obj, "shape"):
            names.append(f"{prefix}/{name}" if prefix else name)

    group.visititems(visit)
    return names


def _read_dataset(handle: Any, key: str | None) -> Any:
    if not key or key not in handle:
        return None
    return handle[key][()]


def _relative_frame_key(key: str | None, base: str) -> str | None:
    if not key:
        return None
    if key.startswith("frames/"):
        parts = key.split("/", 2)
        return f"{base}/{parts[2]}" if len(parts) == 3 else key
    return f"{base}/{key}" if not key.startswith(base) else key


def _reshape_matrix(arr: Any) -> np.ndarray:
    mat = np.asarray(arr, dtype=np.float32)
    if mat.shape == (16,):
        mat = mat.reshape(4, 4)
    return mat


def _stack_same_shape(values: list[Any]) -> np.ndarray | None:
    arrays = [np.asarray(v) for v in values]
    if not arrays:
        return None
    first_shape = arrays[0].shape
    if any(arr.shape != first_shape for arr in arrays):
        return None
    return np.stack(arrays)
