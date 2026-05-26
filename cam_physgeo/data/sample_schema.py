from pathlib import Path
from typing import Any
REQUIRED_FIELDS=['sample_id','source','template','camera_motion','video_path','hdf5_path','rgb_frames','depth_path','id_path','poses_path','intrinsics_path','prompt_path','num_frames','fps','width','height','has_moving_camera','has_depth','has_id_mask','has_object_state','quality_flags']
DEFAULT_SAMPLE={'video_path':None,'hdf5_path':None,'rgb_frames':None,'depth_path':None,'id_path':None,'poses_path':None,'intrinsics_path':None,'prompt_path':None,'num_frames':None,'fps':None,'width':None,'height':None,'has_moving_camera':False,'has_depth':False,'has_id_mask':False,'has_object_state':False,'quality_flags':[]}
def normalize_sample(sample: dict[str, Any]) -> dict[str, Any]:
    out=dict(DEFAULT_SAMPLE); out.update(sample); out['quality_flags']=out.get('quality_flags') or []; return out
def validate_sample(sample: dict[str, Any], check_paths: bool=True) -> list[str]:
    errors=[f'missing:{k}' for k in REQUIRED_FIELDS if k not in sample]
    if sample.get('source') not in {'phyinone','movingcam_synthetic'}: errors.append('invalid:source')
    if check_paths:
        for k in ['video_path','hdf5_path','poses_path','intrinsics_path','prompt_path']:
            v=sample.get(k)
            if not v or str(v).startswith(('hdf5://','generated://')): continue
            if not Path(str(v)).exists(): errors.append(f'missing_path:{k}')
    return errors
