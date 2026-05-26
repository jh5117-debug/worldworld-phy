from __future__ import annotations
import hashlib, os
from pathlib import Path
from typing import Iterator
from cam_physgeo.data.sample_schema import normalize_sample
from cam_physgeo.utils.camera import camera_motion_stats, infer_camera_motion_name
from cam_physgeo.utils.video import probe_video
TEMPLATE_HINTS={'drop':['drop','verticalfall','fall'],'collision':['collision','hit','impact'],'roll':['roll','sliding','friction'],'containment':['contain','container','liquid'],'support':['support','stick','seesaw']}
def iter_phyinone_samples(root: str|Path, limit: int|None=None) -> Iterator[dict]:
    root=Path(root).expanduser(); count=0
    if not root.exists(): return
    probe=os.environ.get('CAM_PHYSGEO_PROBE_VIDEO','').lower() in {'1','true','yes','on'}
    for dirpath,_,filenames in os.walk(root):
        if 'video.mp4' not in filenames: continue
        d=Path(dirpath); video=d/'video.mp4'; poses=d/'poses.npy'; intr=d/'intrinsics.npy'; prompt=d/'prompt.txt'
        pr=probe_video(video) if probe else {}; stats=camera_motion_stats(poses if poses.exists() else None); text=str(d)
        yield normalize_sample({'sample_id':_sample_id('phyinone',d),'source':'phyinone','template':infer_template(text),'camera_motion':infer_camera_motion_name(text),'video_path':str(video),'hdf5_path':None,'rgb_frames':None,'depth_path':_first(d,['depth','depth.npy']),'id_path':_first(d,['id_mask','id.npy','mask.npy']),'poses_path':str(poses) if poses.exists() else None,'intrinsics_path':str(intr) if intr.exists() else None,'prompt_path':str(prompt) if prompt.exists() else 'generated://phyinone','num_frames':pr.get('num_frames'),'fps':pr.get('fps'),'width':pr.get('width'),'height':pr.get('height'),'has_moving_camera':bool(stats.get('has_moving_camera')),'has_depth':bool(_first(d,['depth','depth.npy'])),'has_id_mask':bool(_first(d,['id_mask','id.npy','mask.npy'])),'has_object_state':bool(_first(d,['metadata.json','object_state.json','states.json'])),'quality_flags':[]})
        count+=1
        if limit and count>=limit: return
def infer_template(text: str) -> str:
    s=text.lower()
    for label,keys in TEMPLATE_HINTS.items():
        if any(k in s for k in keys): return label
    return 'unknown'
def _sample_id(source: str, path: Path) -> str: return f'{source}_{hashlib.sha1(str(path).encode()).hexdigest()[:12]}'
def _first(root: Path, names: list[str]) -> str|None:
    for n in names:
        p=root/n
        if p.exists(): return str(p)
    return None
