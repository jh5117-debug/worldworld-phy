from __future__ import annotations
from pathlib import Path
from typing import Any

def load_npy(path: str|Path|None):
    if not path: return None
    if str(path).startswith('hdf5://'):
        try:
            import h5py  # type: ignore
            uri=str(path); file_path,key=uri[len('hdf5://'):].split('::',1)
            with h5py.File(file_path,'r') as handle:
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
        arr=np.asarray(poses); xyz=arr[:, :3, 3]
        steps=np.linalg.norm(np.diff(xyz,axis=0),axis=1) if len(xyz)>1 else np.zeros((0,))
        total=float(steps.sum()); mean=float(steps.mean()) if len(steps) else 0.0
        return {'available':True,'num_frames':int(arr.shape[0]),'translation_total':total,'translation_mean':mean,'has_moving_camera':total>1e-4}
    except Exception as e: return {'available':True,'error':str(e),'num_frames':None,'translation_total':None,'translation_mean':None,'has_moving_camera':None}

def infer_camera_motion_name(text: str) -> str:
    s=text.lower()
    for name,keys in [('relative_yaw_180_reobserve',['relative_yaw_180','yaw180']),('lookaway_up_reobserve',['lookaway_up']),('occluder_lookaway_reobserve',['occluder_lookaway']),('offscreen_z_reobserve',['offscreen_z']),('offscreen_x_reobserve',['offscreen_x']),('reobserve',['reobserve','return']),('orbit',['orbit']),('strafe',['strafe']),('dolly',['dolly','pushin','pullback']),('static',['static','fixed'])]:
        if any(k in s for k in keys): return name
    return 'unknown'
