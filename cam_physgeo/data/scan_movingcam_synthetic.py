from __future__ import annotations
import hashlib, json, os
from pathlib import Path
from typing import Iterator
from cam_physgeo.data.sample_schema import normalize_sample
from cam_physgeo.utils.camera import infer_camera_motion_name
from cam_physgeo.utils.video import probe_video
TEMPLATE_HINTS={'drop':['drop'],'collision':['collision','impact'],'roll':['roll'],'containment':['containment','container'],'support':['support']}
def candidate_data_roots(movingcam_root: str|Path) -> list[Path]:
    root=Path(movingcam_root).expanduser(); roots=[]
    for c in [root, root.parent/'outputs']:
        if c.exists(): roots.append(c)
    # Do not recursively scan local_assets wholesale: it contains LingBot
    # checkouts, asset bundles and historical outputs. The dataset samples live
    # under root.parent/outputs or explicit manifests under synthetic_data_assets.
    out=[]; seen=set()
    for r in roots:
        key=str(r.resolve()) if r.exists() else str(r)
        if key not in seen: out.append(r); seen.add(key)
    return out
def iter_movingcam_samples(root: str|Path, limit: int|None=None) -> Iterator[dict]:
    count=0
    probe=os.environ.get('CAM_PHYSGEO_PROBE_VIDEO','').lower() in {'1','true','yes','on'}
    scan_hdf5=os.environ.get('CAM_PHYSGEO_SCAN_HDF5_KEYS','').lower() in {'1','true','yes','on'}
    for scan_root in candidate_data_roots(root):
        for dirpath,_,filenames in os.walk(scan_root):
            files=[Path(dirpath)/n for n in filenames]
            hdf5=sorted([p for p in files if p.suffix.lower() in {'.hdf5','.h5'}])
            vids=sorted([p for p in files if p.suffix.lower()=='.mp4'])
            if not hdf5 and not vids: continue
            d=Path(dirpath); h=hdf5[0] if hdf5 else None; v=_choose_video(vids); pr=probe_video(v) if probe else {}; text=str(d); flags=[]
            poses=_first(d,['poses.npy','camera_pose.npy','camera_poses.npy']); intr=_first(d,['intrinsics.npy','camera_intrinsics.npy']); prompt=_first(d,['prompt.txt']); meta=_first(d,['metadata.json','tdw_commands.json','summary.json'])
            hdf5_keys = inspect_hdf5_keys(h) if (h and scan_hdf5) else {}
            h_poses = _best_hdf5_key(hdf5_keys, ['camera_pose', 'camera_poses', 'poses', 'camera_matrix', 'camera_matrices'])
            h_intr = _best_hdf5_key(hdf5_keys, ['intrinsics', 'camera_intrinsics', 'K', 'camera_K'])
            h_depth = _best_hdf5_key(hdf5_keys, ['depth', '_depth', 'depths'])
            h_id = _best_hdf5_key(hdf5_keys, ['id', '_id', 'id_mask', 'segmentation', 'object_ids'])
            h_state = _best_hdf5_key(hdf5_keys, ['object_state', 'states', 'objects'])
            if h and not scan_hdf5:
                flags.append('hdf5_keys_not_scanned_fast_manifest')
                h_poses = h_poses or 'camera_pose'
                h_intr = h_intr or 'intrinsics'
                h_depth = h_depth or 'depth'
                h_id = h_id or 'id'
            if h and not poses and not h_poses: flags.append('missing_camera_pose_key')
            if h and not intr and not h_intr: flags.append('missing_intrinsics_key')
            if h and not v: flags.append('needs_video_preview_or_decode')
            meta_payload = _read_json(meta)
            camera_motion = str(meta_payload.get('camera_motion') or meta_payload.get('camera_path') or infer_camera_motion_name(text))
            template = str(meta_payload.get('template') or meta_payload.get('trial_type') or infer_template(text))
            yield normalize_sample({'sample_id':_sample_id('movingcam_synthetic',d),'source':'movingcam_synthetic','template':template,'camera_motion':camera_motion,'video_path':str(v) if v else None,'hdf5_path':str(h) if h else None,'rgb_frames':_first(d,['frames','rgb','_img']),'depth_path':_first(d,['depth','_depth','depth.npy']) or (f'hdf5://{h}::{h_depth}' if h and h_depth else None),'id_path':_first(d,['id_mask','_id','id.npy','mask.npy']) or (f'hdf5://{h}::{h_id}' if h and h_id else None),'poses_path':str(poses) if poses else (f'hdf5://{h}::{h_poses}' if h and h_poses else None),'intrinsics_path':str(intr) if intr else (f'hdf5://{h}::{h_intr}' if h and h_intr else None),'prompt_path':str(prompt) if prompt else 'generated://movingcam_synthetic','num_frames':pr.get('num_frames') or _hdf5_len(hdf5_keys, h_poses),'fps':pr.get('fps') or meta_payload.get('fps'),'width':pr.get('width') or meta_payload.get('width'),'height':pr.get('height') or meta_payload.get('height'),'has_moving_camera':camera_motion not in {'unknown','static','fixed'},'has_depth':bool(h_depth or _first(d,['depth','_depth','depth.npy'])),'has_id_mask':bool(h_id or _first(d,['id_mask','_id','id.npy','mask.npy'])),'has_object_state':bool(meta or h_state),'quality_flags':flags})
            count+=1
            if limit and count>=limit: return
def infer_template(text: str) -> str:
    s=text.lower()
    for label,keys in TEMPLATE_HINTS.items():
        if any(k in s for k in keys): return label
    return 'unknown'
def _choose_video(videos: list[Path]) -> Path|None:
    if not videos: return None
    pref=[p for p in videos if 'preview' in p.name.lower() or 'aligned' in p.name.lower()]
    return (pref or videos)[0]
def _first(root: Path, names: list[str]) -> str|None:
    for n in names:
        p=root/n
        if p.exists(): return str(p)
    return None
def _sample_id(source: str, path: Path) -> str: return f'{source}_{hashlib.sha1(str(path).encode()).hexdigest()[:12]}'

def inspect_hdf5_keys(path: Path | None) -> dict[str, dict]:
    if not path:
        return {}
    try:
        import h5py  # type: ignore
    except Exception:
        return {}
    out: dict[str, dict] = {}
    try:
        with h5py.File(path, 'r') as handle:
            def visit(name, obj):
                if hasattr(obj, 'shape'):
                    out[name] = {'shape': tuple(int(x) for x in obj.shape), 'dtype': str(obj.dtype)}
            handle.visititems(visit)
    except Exception:
        return {}
    return out

def _best_hdf5_key(keys: dict[str, dict], hints: list[str]) -> str | None:
    if not keys:
        return None
    lowered = {name.lower(): name for name in keys}
    for hint in hints:
        h = hint.lower()
        if h in lowered:
            return lowered[h]
    for hint in hints:
        h = hint.lower()
        for low, original in lowered.items():
            if h in low:
                return original
    return None

def _hdf5_len(keys: dict[str, dict], key: str | None) -> int | None:
    if not key or key not in keys:
        return None
    shape = keys[key].get('shape') or ()
    return int(shape[0]) if shape else None

def _read_json(path: str | None) -> dict:
    if not path:
        return {}
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception:
        return {}
