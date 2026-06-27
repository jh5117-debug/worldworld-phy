from __future__ import annotations

import argparse, csv, json, math
from pathlib import Path
from typing import Any
import cv2
import numpy as np

def _rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", newline="", encoding="utf-8") as f: return list(csv.DictReader(f))
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def _read(path):
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened(): return None,"open_failed"
    frames=[]
    while True:
        ok,fr=cap.read()
        if not ok: break
        frames.append(cv2.cvtColor(fr,cv2.COLOR_BGR2RGB).astype(np.float32)/255.0)
    cap.release()
    return (np.stack(frames,axis=0),"ok") if frames else (None,"decode_failed")

def _align(a,b):
    n=min(len(a),len(b)); a=a[:n]; b=b[:n]
    if a.shape[1:3] != b.shape[1:3]:
        h,w=a.shape[1:3]; b=np.stack([cv2.resize(fr,(w,h),interpolation=cv2.INTER_AREA) for fr in b],axis=0)
    return a,b

def _ssim(x,y):
    xg=0.299*x[...,0]+0.587*x[...,1]+0.114*x[...,2]; yg=0.299*y[...,0]+0.587*y[...,1]+0.114*y[...,2]
    mx=float(xg.mean()); my=float(yg.mean()); vx=float(((xg-mx)**2).mean()); vy=float(((yg-my)**2).mean()); cov=float(((xg-mx)*(yg-my)).mean())
    c1=0.01**2; c2=0.03**2
    return float(((2*mx*my+c1)*(2*cov+c2))/((mx*mx+my*my+c1)*(vx+vy+c2)))

def _quality(pred):
    if len(pred)<2: return {"freeze_rate":1.0,"blur_laplacian":0.0,"flicker_proxy":0.0}
    diffs=np.mean(np.abs(pred[1:]-pred[:-1]),axis=(1,2,3))
    grays=[0.299*fr[...,0]+0.587*fr[...,1]+0.114*fr[...,2] for fr in pred]
    blur=[float(cv2.Laplacian((g*255).astype(np.uint8),cv2.CV_64F).var()) for g in grays]
    means=np.array([float(g.mean()) for g in grays])
    flick=float(np.mean(np.abs(np.diff(means,n=2)))) if len(means)>=3 else 0.0
    return {"freeze_rate":float(np.mean(diffs<0.002)),"blur_laplacian":float(np.mean(blur)),"flicker_proxy":flick}

def _pair(gt,pred):
    gt,pred=_align(gt,pred); diff=gt-pred; mse=float(np.mean(diff**2)); psnr=99.0 if mse<=1e-12 else float(-10.0*math.log10(mse))
    return {"frame_count_aligned":float(len(gt)),"mse":mse,"psnr":psnr,"ssim":float(np.mean([_ssim(a,b) for a,b in zip(gt,pred)])),"pixel_l1":float(np.mean(np.abs(diff)))}

def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True); keys=sorted({k for r in rows for k in r})
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def run(args):
    rows=_rows(Path(args.generated_manifest)); rows=rows[:args.max_samples] if args.max_samples else rows; out=Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    res=[]
    for r in rows:
        gt_path=r.get("gt_future_video_path") or r.get("gt_video") or r.get("target_video"); pred_path=r.get("generated_future_video_path") or r.get("generated_video")
        base={"sample_id":r.get("sample_id",""),"model_name":r.get("model_name",""),"template":r.get("template",""),"gt_future_video_path":gt_path,"generated_future_video_path":pred_path}
        gt,gs=_read(gt_path) if gt_path else (None,"missing_gt"); pred,ps=_read(pred_path) if pred_path else (None,"missing_pred")
        if gt is None or pred is None: res.append({**base,"status":f"gt={gs};pred={ps}"}); continue
        m=_pair(gt,pred); m.update(_quality(pred)); res.append({**base,"status":"ok",**m})
    _write_csv(out/"psnr_ssim_quality_per_sample.csv",res)
    ok=[r for r in res if r.get("status")=="ok"]; summary={"count":len(ok),"metric_scope":"future_frames_5_80","lpips_status":"BLOCKED_BY_ENV_or_not_requested","fvd_status":"BLOCKED_BY_ENV_or_not_requested","vbench_status":"BLOCKED_BY_ENV_or_not_requested"}
    for k in ["psnr","ssim","mse","pixel_l1","freeze_rate","blur_laplacian","flicker_proxy"]:
        vals=[float(r[k]) for r in ok if k in r]
        summary[k+"_mean"]=float(np.mean(vals)) if vals else "missing"; summary[k+"_median"]=float(np.median(vals)) if vals else "missing"
    (out/"checkpoint_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({"rows":len(res),"out_dir":str(out),**summary},indent=2))

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--generated_manifest",required=True); p.add_argument("--out_dir",required=True); p.add_argument("--max_samples",type=int,default=0); run(p.parse_args(argv)); return 0
if __name__=="__main__": raise SystemExit(main())
