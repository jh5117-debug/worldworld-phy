from __future__ import annotations
import argparse
from pathlib import Path
from cam_physgeo.utils.io import read_jsonl, write_jsonl
CORRUPTIONS=['background_drift','nonrigid_background_warp','object_deformation','object_color_identity_change','wrong_camera_motion','camera_shuffle','reobserve_mismatch','freeze_foreground','freeze_camera','global_freeze','remove_object']

def make_corruption_records(sample: dict, *, out_dir: str|None=None, dry_run: bool=True) -> list[dict]:
    rows=[]
    for c in CORRUPTIONS:
        loser=f'corruption://{sample.get("sample_id")}/{c}'
        flags=list(sample.get('quality_flags') or [])
        if out_dir and sample.get('video_path'):
            out_path=Path(out_dir)/str(sample.get('sample_id'))/f'{c}.mp4'
            if not dry_run and c in {'freeze_camera','global_freeze','background_drift','camera_shuffle','wrong_camera_motion'}:
                if write_corrupted_video(sample['video_path'], out_path, c):
                    loser=str(out_path)
                else:
                    flags.append(f'corruption_failed:{c}')
            else:
                loser=str(out_path) if not dry_run else str(out_path)
        rows.append({'sample_id':sample.get('sample_id'),'corruption':c,'loser_video':loser,'source_video':sample.get('video_path'),'risk':'synthetic_negative','quality_flags':flags,'requires_mask':c in {'object_deformation','object_color_identity_change','freeze_foreground','remove_object'}})
    return rows

def write_corrupted_video(video_path: str, out_path: Path, corruption: str) -> bool:
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
        cap=cv2.VideoCapture(str(video_path)); fps=float(cap.get(cv2.CAP_PROP_FPS) or 16); frames=[]
        while True:
            ok,frame=cap.read()
            if not ok: break
            frames.append(frame)
        cap.release()
        if not frames: return False
        h,w=frames[0].shape[:2]; out_path.parent.mkdir(parents=True, exist_ok=True)
        if corruption in {'freeze_camera','global_freeze'}:
            frames=[frames[0].copy() for _ in frames]
        elif corruption in {'camera_shuffle','wrong_camera_motion'}:
            frames=list(reversed(frames))
        elif corruption=='background_drift':
            shifted=[]
            for i,frame in enumerate(frames):
                dx=int(round((i+1)*w/max(len(frames),1)*0.04))
                mat=np.float32([[1,0,dx],[0,1,0]])
                shifted.append(cv2.warpAffine(frame, mat, (w,h), borderMode=cv2.BORDER_REFLECT))
            frames=shifted
        fourcc=cv2.VideoWriter_fourcc(*'mp4v'); writer=cv2.VideoWriter(str(out_path), fourcc, fps, (w,h))
        for frame in frames: writer.write(frame)
        writer.release(); return out_path.exists()
    except Exception:
        return False

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--out',default='manifests/cam_physgeo_corruptions.jsonl'); ap.add_argument('--out_dir',default=''); ap.add_argument('--limit',type=int,default=0); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    rows=[]
    for i,s in enumerate(read_jsonl(a.manifest)):
        if a.limit and i>=a.limit: break
        rows.extend(make_corruption_records(s,out_dir=a.out_dir or None,dry_run=a.dry_run))
    print({'corruption_records':len(rows),'out':a.out,'dry_run':a.dry_run})
    if not a.dry_run: write_jsonl(rows,a.out)
    return 0
if __name__=='__main__': raise SystemExit(main())
