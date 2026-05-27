from __future__ import annotations
import argparse, hashlib
from collections import defaultdict
from pathlib import Path
from cam_physgeo.utils.io import read_jsonl, write_jsonl

def assign_base(sample_id: str, val_ratio: float, test_ratio: float) -> str:
    v=int(hashlib.sha1(sample_id.encode()).hexdigest()[:8],16)/0xffffffff
    return 'test' if v<test_ratio else ('val' if v<test_ratio+val_ratio else 'train')
def semantic_splits(s: dict) -> list[str]:
    out=[]; motion=str(s.get('camera_motion') or ''); template=str(s.get('template') or 'unknown')
    if any(k in motion for k in ['reobserve','offscreen','lookaway','yaw']): out.append('reobserve')
    if template=='unknown' and s.get('has_moving_camera'): out.append('camera_only')
    if template!='unknown' and not s.get('has_moving_camera'): out.append('static_camera_physics')
    if template!='unknown' and s.get('has_moving_camera'): out.append('moving_camera_physics')
    if s.get('quality_flags'): out.append('stress')
    return out
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--out_dir',default='manifests'); ap.add_argument('--prefix',default='physion_cam_physgeo'); ap.add_argument('--val-ratio',type=float,default=0.05); ap.add_argument('--test-ratio',type=float,default=0.05); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    buckets=defaultdict(list)
    for s in read_jsonl(a.manifest):
        buckets[assign_base(str(s['sample_id']),a.val_ratio,a.test_ratio)].append(s)
        for name in semantic_splits(s): buckets[name].append(s)
    counts={k:len(v) for k,v in sorted(buckets.items())}; print({'out_dir':a.out_dir,'counts':counts,'dry_run':a.dry_run})
    if not a.dry_run:
        out=Path(a.out_dir)
        for k,v in buckets.items(): write_jsonl(v,out/f'{a.prefix}_{k}.jsonl')
    return 0
if __name__=='__main__': raise SystemExit(main())
