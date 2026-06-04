from __future__ import annotations
import json, subprocess
from pathlib import Path
from typing import Any

def probe_video(path: str|Path|None) -> dict[str, Any]:
    base={'ok':False,'exists':False,'path':str(path) if path else None,'num_frames':None,'fps':None,'width':None,'height':None}
    if not path or not Path(str(path)).exists(): return base
    p=Path(str(path)); base['exists']=True
    try:
        import cv2  # type: ignore
        cap=cv2.VideoCapture(str(p))
        if cap.isOpened():
            out={'ok':True,'exists':True,'path':str(p),'num_frames':int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) or None,'fps':float(cap.get(cv2.CAP_PROP_FPS) or 0) or None,'width':int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or None,'height':int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or None}
            cap.release(); return out
    except Exception: pass
    try:
        cmd=['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,r_frame_rate','-of','json',str(p)]
        pr=subprocess.run(cmd,capture_output=True,text=True,timeout=20)
        st=(json.loads(pr.stdout).get('streams') or [{}])[0]
        fps=_ratio(st.get('r_frame_rate')); nf=st.get('nb_frames')
        return {'ok':pr.returncode==0,'exists':True,'path':str(p),'num_frames':int(nf) if nf and nf!='N/A' else None,'fps':fps,'width':int(st['width']) if st.get('width') else None,'height':int(st['height']) if st.get('height') else None}
    except Exception: pass
    try:
        import imageio  # type: ignore
        reader=imageio.get_reader(str(p))
        meta=reader.get_meta_data() or {}
        size=meta.get('size') or (None, None)
        fps=meta.get('fps')
        num_frames=None
        try:
            num_frames=reader.count_frames()
        except Exception:
            try:
                num_frames=reader.get_length()
                if num_frames == float('inf'):
                    num_frames=None
            except Exception:
                num_frames=None
        try:
            first=reader.get_data(0)
            height,width=first.shape[:2]
        except Exception:
            width,height=(int(size[0]) if size and size[0] else None, int(size[1]) if size and size[1] else None)
        try:
            reader.close()
        except Exception:
            pass
        return {'ok':True,'exists':True,'path':str(p),'num_frames':int(num_frames) if num_frames not in (None, float('inf')) else None,'fps':float(fps) if fps else None,'width':int(width) if width else None,'height':int(height) if height else None}
    except Exception:
        return base

def _ratio(v):
    try:
        if not v or v=='0/0': return None
        if '/' in v:
            a,b=v.split('/',1); return float(a)/float(b) if float(b) else None
        return float(v)
    except Exception: return None

def extract_first_frame(video_path: str|Path, out_path: str|Path, dry_run: bool=False) -> bool:
    if dry_run: return False
    out=Path(out_path); out.parent.mkdir(parents=True, exist_ok=True)
    try:
        import cv2  # type: ignore
        cap=cv2.VideoCapture(str(video_path)); ok,frame=cap.read(); cap.release()
        if ok: return bool(cv2.imwrite(str(out), frame))
    except Exception: pass
    try:
        pr=subprocess.run(['ffmpeg','-y','-i',str(video_path),'-frames:v','1',str(out)],capture_output=True,text=True,timeout=30)
        return pr.returncode==0 and out.exists()
    except Exception: return False

def write_video_frames(frames, out_path: str|Path, *, fps: int|float=16) -> bool:
    """Write RGB or grayscale numpy frames to an mp4 file."""
    import subprocess

    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
        arr=np.asarray(frames)
        if arr.ndim < 3 or len(arr)==0:
            return False
        out=Path(out_path); out.parent.mkdir(parents=True, exist_ok=True)
        first=arr[0]
        if first.ndim == 2:
            h,w=first.shape
        else:
            h,w=first.shape[:2]
        writer=cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*'mp4v'), float(fps or 16), (w,h))
        for frame in arr:
            f=np.asarray(frame)
            if f.ndim == 2:
                f=cv2.cvtColor(f.astype('uint8'), cv2.COLOR_GRAY2BGR)
            else:
                if f.dtype != np.uint8:
                    f=np.clip(f,0,255).astype('uint8')
                f=cv2.cvtColor(f, cv2.COLOR_RGB2BGR)
            writer.write(f)
        writer.release()
        if out.exists() and out.stat().st_size > 0 and probe_video(out).get('ok'):
            return True
        if out.exists():
            out.unlink(missing_ok=True)
    except Exception:
        pass
    try:
        import imageio  # type: ignore
        import numpy as np  # type: ignore

        arr=np.asarray(frames)
        if arr.ndim < 3 or len(arr)==0:
            return False
        if arr.dtype != np.uint8:
            arr=np.clip(arr,0,255).astype('uint8')
        if arr[0].ndim == 2:
            arr=np.repeat(arr[...,None],3,axis=-1)
        out=Path(out_path); out.parent.mkdir(parents=True, exist_ok=True)
        imageio.mimsave(str(out), list(arr), fps=float(fps or 16))
        if out.exists() and out.stat().st_size > 0 and probe_video(out).get('ok'):
            return True
        if out.exists():
            out.unlink(missing_ok=True)
    except Exception:
        pass
    try:
        import numpy as np  # type: ignore

        arr=np.asarray(frames)
        if arr.ndim < 3 or len(arr)==0:
            return False
        if arr.dtype != np.uint8:
            arr=np.clip(arr,0,255).astype('uint8')
        if arr[0].ndim == 2:
            arr=np.repeat(arr[...,None],3,axis=-1)
        h,w=arr[0].shape[:2]
        out=Path(out_path); out.parent.mkdir(parents=True, exist_ok=True)
        raw=arr[..., :3].copy().tobytes()
        for codec_args in (['-vcodec','libx264','-pix_fmt','yuv420p'], ['-vcodec','mpeg4','-pix_fmt','yuv420p']):
            if out.exists():
                out.unlink(missing_ok=True)
            cmd=[
                'ffmpeg','-y',
                '-f','rawvideo',
                '-vcodec','rawvideo',
                '-s',f'{w}x{h}',
                '-pix_fmt','rgb24',
                '-r',str(float(fps or 16)),
                '-i','-',
                '-an',
                *codec_args,
                str(out),
            ]
            pr=subprocess.run(cmd,input=raw,capture_output=True,timeout=300)
            if pr.returncode==0 and out.exists() and out.stat().st_size > 0 and probe_video(out).get('ok'):
                return True
        return False
    except Exception:
        return False

def read_video_frames(video_path: str|Path|None, *, max_frames: int=16, stride: int=1, size: tuple[int,int]|None=None) -> list:
    """Read a small RGB frame list for lightweight scoring.

    Returns an empty list when cv2 is unavailable or the video is unreadable.
    """
    if not video_path or not Path(str(video_path)).exists():
        return []
    try:
        import cv2  # type: ignore
        frames=[]; cap=cv2.VideoCapture(str(video_path)); idx=0
        while len(frames)<max_frames:
            ok,frame=cap.read()
            if not ok: break
            if idx % max(1,stride)==0:
                if size is not None:
                    frame=cv2.resize(frame, (int(size[0]), int(size[1])), interpolation=cv2.INTER_AREA)
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            idx+=1
        cap.release(); return frames
    except Exception:
        return []

def frame_motion_magnitude(video_path: str|Path|None, *, max_frames: int=16, size: tuple[int,int]=(96,64)) -> dict[str, Any]:
    frames=read_video_frames(video_path, max_frames=max_frames, size=size)
    if len(frames)<2:
        return {'available':False,'mean_absdiff':None,'max_absdiff':None,'num_pairs':0}
    try:
        import numpy as np  # type: ignore
        vals=[]
        for a,b in zip(frames[:-1], frames[1:]):
            vals.append(float(np.mean(np.abs(a.astype('float32')-b.astype('float32')))/255.0))
        return {'available':True,'mean_absdiff':float(np.mean(vals)),'max_absdiff':float(np.max(vals)),'num_pairs':len(vals)}
    except Exception as exc:
        return {'available':False,'error':str(exc),'mean_absdiff':None,'max_absdiff':None,'num_pairs':0}

def blur_brightness_flicker(video_path: str|Path|None, *, max_frames: int=16, size: tuple[int,int]=(160,96)) -> dict[str, Any]:
    frames=read_video_frames(video_path, max_frames=max_frames, size=size)
    if not frames:
        return {'available':False}
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
        blur=[]; brightness=[]; saturation=[]
        for frame in frames:
            gray=cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            blur.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
            hsv=cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            brightness.append(float(np.mean(hsv[...,2])/255.0))
            saturation.append(float(np.mean(hsv[...,1])/255.0))
        flicker=float(np.mean(np.abs(np.diff(brightness)))) if len(brightness)>1 else 0.0
        return {'available':True,'blur_var_mean':float(np.mean(blur)),'brightness_mean':float(np.mean(brightness)),'saturation_mean':float(np.mean(saturation)),'brightness_flicker':flicker,'num_frames':len(frames)}
    except Exception as exc:
        return {'available':False,'error':str(exc)}
