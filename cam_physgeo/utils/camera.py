from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any


def convert_projection_to_lingbot_intrinsics(
    projection_matrices,
    width: int,
    height: int,
    convention: str = "auto",
):
    """Convert camera intrinsics/projection arrays to LingBot [fx, fy, cx, cy].

    LingBot-Fast's camera utility expects per-frame pixel-space vectors with
    shape ``(F, 4)``. Physion/TDW moving-camera exports may instead store a
    4x4 projection matrix per frame. This helper keeps source assets untouched;
    callers should write the converted array only to a runtime condition folder.

    Supported inputs:
    - ``(F, 4)`` or ``(4,)``: already LingBot-style vectors.
    - ``(F, 3, 3)`` or ``(3, 3)``: pixel-space camera matrices.
    - ``(F, 4, 4)`` or ``(4, 4)``: TDW/Unity/OpenGL-style projection matrices.

    Returns ``(converted, metadata)`` where converted has dtype float32 and
    shape ``(F, 4)``.
    """
    import numpy as np  # type: ignore

    if width <= 0 or height <= 0:
        raise ValueError(f"width and height must be positive, got width={width}, height={height}")
    arr = np.asarray(projection_matrices, dtype=np.float32)
    metadata: dict[str, Any] = {
        "input_shape": list(arr.shape),
        "width": int(width),
        "height": int(height),
        "convention": convention,
        "warning": "",
    }

    if arr.ndim == 1 and arr.shape[0] == 4:
        converted = arr[None, :]
        metadata["source_format"] = "vector_single"
    elif arr.ndim == 2 and arr.shape[-1] == 4 and arr.shape[-2] != 4:
        converted = arr
        metadata["source_format"] = "vector_per_frame"
    elif arr.ndim == 2 and arr.shape == (3, 3):
        converted = np.array([[arr[0, 0], arr[1, 1], arr[0, 2], arr[1, 2]]], dtype=np.float32)
        metadata["source_format"] = "matrix3x3_single"
    elif arr.ndim == 3 and arr.shape[-2:] == (3, 3):
        converted = np.stack([arr[:, 0, 0], arr[:, 1, 1], arr[:, 0, 2], arr[:, 1, 2]], axis=-1)
        metadata["source_format"] = "matrix3x3_per_frame"
    else:
        if arr.ndim == 2 and arr.shape == (4, 4):
            arr = arr[None, :, :]
            metadata["expanded_single_matrix"] = True
        if not (arr.ndim == 3 and arr.shape[-2:] == (4, 4)):
            raise ValueError(
                f"unsupported intrinsics shape {tuple(np.asarray(projection_matrices).shape)}; "
                "expected (F,4), (4,), (F,3,3), (3,3), (F,4,4), or (4,4)"
            )
        if convention not in {"auto", "tdw_opengl", "opengl", "unity"}:
            raise ValueError(f"unsupported convention {convention!r}")
        if convention == "auto":
            metadata["warning"] = (
                "Assuming TDW/Unity/OpenGL projection convention: "
                "fx=P00*width/2, fy=P11*height/2, cx=(1-P02)*width/2, cy=(1-P12)*height/2."
            )
            warnings.warn(metadata["warning"], RuntimeWarning, stacklevel=2)
        fx = arr[:, 0, 0] * float(width) / 2.0
        fy = arr[:, 1, 1] * float(height) / 2.0
        cx = (1.0 - arr[:, 0, 2]) * float(width) / 2.0
        cy = (1.0 - arr[:, 1, 2]) * float(height) / 2.0
        converted = np.stack([fx, fy, cx, cy], axis=-1)
        metadata["source_format"] = "projection4x4_to_pixel_vector"

    converted = np.asarray(converted, dtype=np.float32)
    if converted.ndim != 2 or converted.shape[1] != 4:
        raise ValueError(f"converted intrinsics must have shape (F,4), got {converted.shape}")
    if not np.isfinite(converted).all():
        raise ValueError("converted intrinsics contain non-finite values")
    if not (converted[:, 0] > 0).all() or not (converted[:, 1] > 0).all():
        raise ValueError("converted intrinsics have non-positive focal lengths")
    if not ((converted[:, 2] >= -width) & (converted[:, 2] <= 2 * width)).all():
        warnings.warn("converted cx is outside a loose image-width sanity range", RuntimeWarning, stacklevel=2)
        metadata["cx_range_warning"] = True
    if not ((converted[:, 3] >= -height) & (converted[:, 3] <= 2 * height)).all():
        warnings.warn("converted cy is outside a loose image-height sanity range", RuntimeWarning, stacklevel=2)
        metadata["cy_range_warning"] = True
    metadata["output_shape"] = list(converted.shape)
    metadata["intrinsics_source"] = "projection_matrix_converted" if "projection4x4" in metadata["source_format"] else metadata["source_format"]
    return converted, metadata

def load_npy(path: str|Path|None):
    if not path: return None
    if str(path).startswith('hdf5://'):
        try:
            import h5py  # type: ignore
            import numpy as np  # type: ignore
            uri=str(path); file_path,key=uri[len('hdf5://'):].split('::',1)
            with h5py.File(file_path,'r') as handle:
                if key.startswith('frames/') and '/0000/' in key and 'frames' in handle:
                    suffix=key.split('/0000/',1)[1]
                    vals=[]
                    for frame in sorted(handle['frames'].keys()):
                        k=f'frames/{frame}/{suffix}'
                        if k in handle:
                            vals.append(handle[k][()])
                    if vals:
                        return np.stack(vals)
                return handle[key][()]
        except Exception:
            return None
    try:
        import numpy as np  # type: ignore
        return np.load(str(path))
    except Exception: return None

def camera_motion_stats(poses_path: str|Path|None) -> dict[str, Any]:
    poses=load_npy(poses_path)
    if poses is None: return {'available':False,'num_frames':None,'translation_total':None,'translation_mean':None,'has_moving_camera':None}
    try:
        import numpy as np  # type: ignore
        arr=np.asarray(poses)
        if arr.shape == (4,4):
            return {'available':True,'num_frames':1,'translation_total':0.0,'translation_mean':0.0,'has_moving_camera':False}
        if arr.ndim == 2 and arr.shape[-1] >= 3:
            xyz = arr[:, :3]
        else:
            xyz=arr[:, :3, 3]
        steps=np.linalg.norm(np.diff(xyz,axis=0),axis=1) if len(xyz)>1 else np.zeros((0,))
        total=float(steps.sum()); mean=float(steps.mean()) if len(steps) else 0.0
        return {'available':True,'num_frames':int(arr.shape[0]),'translation_total':total,'translation_mean':mean,'has_moving_camera':total>1e-4}
    except Exception as e: return {'available':True,'error':str(e),'num_frames':None,'translation_total':None,'translation_mean':None,'has_moving_camera':None}

def infer_camera_motion_name(text: str) -> str:
    s=text.lower()
    for name,keys in [('relative_yaw_180_reobserve',['relative_yaw_180','yaw180']),('lookaway_up_reobserve',['lookaway_up']),('occluder_lookaway_reobserve',['occluder_lookaway']),('offscreen_z_reobserve',['offscreen_z']),('offscreen_x_reobserve',['offscreen_x']),('reobserve',['reobserve','return']),('orbit',['orbit']),('strafe',['strafe']),('dolly',['dolly','pushin','pullback']),('static',['static','fixed'])]:
        if any(k in s for k in keys): return name
    return 'unknown'
