from __future__ import annotations
import argparse, os, shutil
from pathlib import Path
from cam_physgeo.data.prompt_templates import build_prompt
from cam_physgeo.utils.io import read_jsonl, write_json
from cam_physgeo.utils.video import extract_first_frame, probe_video

def link_or_copy(src, dst, mode, dry_run):
    if dry_run: return
    src=Path(src); dst=Path(dst); dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists(): return
    os.symlink(src,dst) if mode=='symlink' else shutil.copy2(src,dst)
def convert_sample(sample: dict, out_root: Path, args) -> dict:
    d=out_root/str(sample['sample_id']); dry=args.dry_run
    if not dry: d.mkdir(parents=True, exist_ok=True)
    if sample.get('video_path'):
        link_or_copy(sample['video_path'], d/'target.mp4', args.link_mode, dry); extract_first_frame(sample['video_path'], d/'image.jpg', dry_run=dry)
        if int(args.prefix_frames or 0) > 0:
            write_prefix_video(sample['video_path'], d/'prefix.mp4', int(args.prefix_frames), args.fps, dry)
    for key,name in [('poses_path','poses.npy'),('intrinsics_path','intrinsics.npy')]:
        value = sample.get(key)
        if value and not str(value).startswith('hdf5://'):
            link_or_copy(value, d/name, args.link_mode, dry)
        elif value and str(value).startswith('hdf5://') and not dry:
            extract_hdf5_npy(value, d/name)
    prompt=_read_prompt(sample) or build_prompt(sample,args.prompt_level)
    if not dry:
        (d/'prompt.txt').write_text(prompt+'\n', encoding='utf-8')
        meta=dict(sample); meta.update({'use_action':bool(args.use_action),'dummy_action':bool(args.make_dummy_action and not args.use_action),'prompt_level':args.prompt_level,'target_num_frames':args.num_frames,'target_fps':args.fps,'target_size':args.size,'input_mode':'v2v_prefix' if int(args.prefix_frames or 0)>0 else 'i2v_first_frame','video_probe':probe_video(sample.get('video_path'))})
        write_json(meta,d/'metadata.json')
        if args.make_dummy_action and not args.use_action: _write_dummy_action(d/'action.npy', args.num_frames)
    return {'sample_id':sample['sample_id'],'out_dir':str(d)}
def _read_prompt(sample):
    p=sample.get('prompt_path')
    if not p or str(p).startswith('generated://'): return None
    try: return Path(p).read_text(encoding='utf-8').strip()
    except Exception: return None
def _write_dummy_action(path: Path, num_frames: int):
    try:
        import numpy as np  # type: ignore
        np.save(path, np.zeros((int(num_frames),4), dtype='float32'))
    except Exception as e: path.with_suffix('.fallback.txt').write_text(f'dummy zero action unavailable: {e}\n', encoding='utf-8')

def extract_hdf5_npy(uri: str, out_path: Path) -> bool:
    try:
        import h5py  # type: ignore
        import numpy as np  # type: ignore
        path, key = uri[len('hdf5://'):].split('::', 1)
        with h5py.File(path, 'r') as handle:
            arr = handle[key][()]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(out_path, arr)
        return True
    except Exception as exc:
        out_path.with_suffix(out_path.suffix + '.error.txt').write_text(f'{uri}: {exc}\n', encoding='utf-8')
        return False

def write_prefix_video(video_path: str|Path, out_path: Path, prefix_frames: int, fps: int, dry_run: bool=False) -> bool:
    if dry_run:
        return False
    try:
        import cv2  # type: ignore
        cap = cv2.VideoCapture(str(video_path))
        ok, frame = cap.read()
        if not ok:
            cap.release()
            return False
        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(str(out_path), fourcc, float(fps or 16), (w, h))
        count = 0
        while ok and count < prefix_frames:
            writer.write(frame)
            count += 1
            ok, frame = cap.read()
        cap.release(); writer.release()
        return out_path.exists() and count > 0
    except Exception:
        return False
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--out',required=True); ap.add_argument('--num_frames',type=int,default=81); ap.add_argument('--fps',type=int,default=16); ap.add_argument('--size',default='480x832'); ap.add_argument('--use_action',type=lambda x:str(x).lower()=='true',default=False); ap.add_argument('--make_dummy_action',type=lambda x:str(x).lower()=='true',default=True); ap.add_argument('--prefix_frames',type=int,default=0); ap.add_argument('--prompt-level',default='P1',choices=['P0','P1','P2']); ap.add_argument('--link-mode',default='symlink',choices=['symlink','copy']); ap.add_argument('--limit',type=int,default=0); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    converted=[]
    for i,s in enumerate(read_jsonl(a.manifest)):
        if a.limit and i>=a.limit: break
        converted.append(convert_sample(s, Path(a.out), a))
    print({'converted':len(converted),'out':a.out,'dry_run':a.dry_run,'use_action':a.use_action}); return 0
if __name__=='__main__': raise SystemExit(main())
