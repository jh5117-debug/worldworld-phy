
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]


def repo_path(path: Any, repo: Path = REPO_ROOT) -> Path:
    if path is None:
        return Path('')
    s = str(path)
    if not s:
        return Path('')
    p = Path(s)
    if p.is_absolute():
        return p
    return repo / p


def rel(path: Any, repo: Path = REPO_ROOT) -> str:
    p = repo_path(path, repo)
    try:
        return str(p.relative_to(repo))
    except Exception:
        return str(path or '')


def read_jsonl(path: Path) -> List[dict]:
    rows=[]
    if not path.exists():
        return rows
    with path.open() as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def write_csv(path: Path, rows: List[dict], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys=[]
        seen=set()
        for r in rows:
            for k in r.keys():
                if k not in seen:
                    seen.add(k); keys.append(k)
        fieldnames=keys
    with path.open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv_dict(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def video_info(path: Path) -> Dict[str, Any]:
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {'exists': path.exists(), 'decodable': False, 'frames': 0, 'width': 0, 'height': 0, 'fps': 0.0}
    frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps=float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    ok, _ = cap.read()
    cap.release()
    return {'exists': path.exists(), 'decodable': bool(ok), 'frames': frames, 'width': width, 'height': height, 'fps': fps}


def read_video_frames(path: Path, max_frames: Optional[int] = None) -> Tuple[List[np.ndarray], float]:
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f'cannot open video: {path}')
    fps=float(cap.get(cv2.CAP_PROP_FPS) or 16.0)
    frames=[]
    while True:
        ok, frame=cap.read()
        if not ok:
            break
        frames.append(frame)
        if max_frames and len(frames)>=max_frames:
            break
    cap.release()
    return frames, fps


def write_video(path: Path, frames: List[np.ndarray], fps: float = 16.0) -> None:
    if not frames:
        raise RuntimeError(f'no frames for {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    h,w=frames[0].shape[:2]
    fourcc=cv2.VideoWriter_fourcc(*'mp4v')
    tmp=path.with_suffix('.tmp.mp4')
    writer=cv2.VideoWriter(str(tmp), fourcc, fps or 16.0, (w,h))
    if not writer.isOpened():
        raise RuntimeError(f'cannot write video: {tmp}')
    for fr in frames:
        if fr.shape[:2] != (h,w):
            fr=cv2.resize(fr,(w,h))
        writer.write(fr)
    writer.release()
    # Re-encode to H.264 if ffmpeg is present; keep mp4v fallback otherwise.
    try:
        cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(tmp),'-c:v','libx264','-pix_fmt','yuv420p','-crf','20',str(path)]
        subprocess.run(cmd, check=True, timeout=120)
        tmp.unlink(missing_ok=True)
    except Exception:
        tmp.replace(path)


def sample_frames(frames: List[np.ndarray], count: int) -> List[np.ndarray]:
    if not frames:
        return []
    if len(frames) <= count:
        return frames[:]
    idx=np.linspace(0, len(frames)-1, count).astype(int)
    return [frames[int(i)] for i in idx]


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    a=a.astype(np.float32); b=b.astype(np.float32)
    mse=float(np.mean((a-b)**2))
    if mse <= 1e-9:
        return 99.0
    return float(20*math.log10(255.0/math.sqrt(mse)))


def ssim_gray(a: np.ndarray, b: np.ndarray) -> float:
    # Lightweight global SSIM proxy, deterministic and dependency-free.
    ga=cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb=cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)
    c1=(0.01*255)**2; c2=(0.03*255)**2
    mu_a=float(ga.mean()); mu_b=float(gb.mean())
    var_a=float(ga.var()); var_b=float(gb.var())
    cov=float(((ga-mu_a)*(gb-mu_b)).mean())
    return float(((2*mu_a*mu_b+c1)*(2*cov+c2))/((mu_a**2+mu_b**2+c1)*(var_a+var_b+c2)+1e-9))


def sharpness(fr: np.ndarray) -> float:
    gray=cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def video_metrics(win_frames: List[np.ndarray], lose_frames: List[np.ndarray]) -> Dict[str, float]:
    n=min(len(win_frames), len(lose_frames))
    if n == 0:
        return {}
    idx=np.linspace(0,n-1,min(12,n)).astype(int)
    ps=[]; ss=[]; diffs=[]; sharp_w=[]; sharp_l=[]; brightness=[]; contrast=[]
    for i in idx:
        w=win_frames[int(i)]; l=lose_frames[int(i)]
        if w.shape != l.shape:
            l=cv2.resize(l,(w.shape[1], w.shape[0]))
        ps.append(psnr(w,l)); ss.append(ssim_gray(w,l)); diffs.append(float(np.mean(np.abs(w.astype(np.float32)-l.astype(np.float32)))))
        sharp_w.append(sharpness(w)); sharp_l.append(sharpness(l))
        gray=cv2.cvtColor(l, cv2.COLOR_BGR2GRAY)
        brightness.append(float(gray.mean())); contrast.append(float(gray.std()))
    # flicker/freeze proxies
    flick=[]; freeze=[]
    prev=None
    for fr in sample_frames(lose_frames, min(16, len(lose_frames))):
        if prev is not None:
            d=float(np.mean(np.abs(fr.astype(np.float32)-prev.astype(np.float32))))
            flick.append(d); freeze.append(1.0 if d < 1.0 else 0.0)
        prev=fr
    return {
        'PSNR': float(np.mean(ps)),
        'SSIM': float(np.mean(ss)),
        'mean_absdiff': float(np.mean(diffs)),
        'sharpness_winner': float(np.mean(sharp_w)),
        'sharpness_loser': float(np.mean(sharp_l)),
        'sharpness_ratio': float((np.mean(sharp_l)+1e-6)/(np.mean(sharp_w)+1e-6)),
        'brightness': float(np.mean(brightness)),
        'contrast': float(np.mean(contrast)),
        'flicker': float(np.std(flick) if flick else 0.0),
        'freeze_rate': float(np.mean(freeze) if freeze else 0.0),
    }


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == '': return default
        return float(v)
    except Exception:
        return default


def boolish(v: Any, default: bool=False) -> bool:
    if v is None or v == '': return default
    if isinstance(v, bool): return v
    if isinstance(v, (int,float)): return bool(v)
    return str(v).strip().lower() in {'1','true','yes','y','pass'}


def pair_paths(pair: dict) -> Tuple[str,str,str]:
    cond=pair.get('condition') or {}
    winner=pair.get('winner') or {}
    loser=pair.get('loser') or {}
    prefix=cond.get('prefix_video_path') or pair.get('prefix_video_path') or ''
    win=winner.get('future_video_path') or winner.get('full_video_path') or pair.get('winner_video_path') or ''
    lose=loser.get('future_video_path') or loser.get('full_video_path') or pair.get('loser_video_path') or ''
    return prefix, win, lose


def normalize_condition_from_pair(pair: dict) -> dict:
    cond=dict(pair.get('condition') or {})
    return {
        'condition_id': cond.get('condition_id') or cond.get('sample_id') or pair.get('condition_id') or pair.get('pair_id'),
        'sample_id': cond.get('sample_id') or pair.get('sample_id') or cond.get('condition_id') or pair.get('pair_id'),
        'template': cond.get('template') or pair.get('template') or '',
        'camera_motion': cond.get('camera_motion') or cond.get('camera_variant') or pair.get('camera_motion') or '',
        'prefix_len': int(cond.get('prefix_len') or 5),
        'prediction_start_frame': int(cond.get('prediction_start_frame') or 5),
        'prefix_video_path': cond.get('prefix_video_path') or pair.get('prefix_video_path') or '',
        'image_path': cond.get('image_path') or cond.get('image') or cond.get('condition_image_path') or '',
        'prompt': cond.get('prompt') or cond.get('prompt_path') or pair.get('prompt') or '',
        'prompt_path': cond.get('prompt_path') or cond.get('prompt') or '',
        'poses_path': cond.get('poses_path') or cond.get('poses') or '',
        'intrinsics_path': cond.get('intrinsics_path') or cond.get('intrinsics') or '',
        'gt_full_video_path': cond.get('gt_full_video_path') or (pair.get('winner') or {}).get('full_video_path') or '',
        'gt_future_video_path': cond.get('gt_future_video_path') or (pair.get('winner') or {}).get('future_video_path') or '',
        'fps': float(cond.get('fps') or 16.0),
        'height': int(cond.get('height') or 0),
        'width': int(cond.get('width') or 0),
        'num_frames': int(cond.get('num_frames') or 0),
        'source_manifest': pair.get('_manifest_source') or pair.get('source_manifest') or '',
        'source_pair_id': pair.get('pair_id') or '',
    }


def condition_key(c: dict) -> str:
    return str(c.get('sample_id') or c.get('condition_id') or c.get('gt_full_video_path') or c.get('prefix_video_path'))


def append_blocker(output_dir: Path, classification: str, message: str, detail: Optional[dict]=None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    row={'classification': classification, 'message': message, 'detail': detail or {}}
    with (output_dir/'autonomous_blocker_log.jsonl').open('a') as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n')
    md=output_dir/'autonomous_blocker_log.md'
    with md.open('a') as f:
        f.write(f"- `{classification}`: {message}; detail={json.dumps(detail or {}, ensure_ascii=False)}\n")
