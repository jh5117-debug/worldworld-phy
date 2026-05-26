from __future__ import annotations
import argparse
from collections import Counter
from cam_physgeo.utils.io import load_yaml, read_jsonl, write_json

def audit_manifest(path: str, limit: int=0) -> dict:
    c=Counter(); src=Counter(); tmpl=Counter(); moving=0; total=0; pose=0; intr=0; depth=0; ids=0; reobs=0
    for s in read_jsonl(path):
        if limit and total>=limit: break
        total+=1; c[s.get('camera_motion','unknown')]+=1; src[s.get('source','unknown')]+=1; tmpl[s.get('template','unknown')]+=1
        moving+=1 if s.get('has_moving_camera') else 0; pose+=1 if s.get('poses_path') else 0; intr+=1 if s.get('intrinsics_path') else 0; depth+=1 if s.get('has_depth') else 0; ids+=1 if s.get('has_id_mask') else 0
        reobs+=1 if any(k in str(s.get('camera_motion','')).lower() for k in ['reobserve','lookaway','offscreen','yaw']) else 0
    return {'manifest':path,'total':total,'moving_camera':moving,'has_pose':pose,'has_intrinsics':intr,'has_depth':depth,'has_id_mask':ids,'reobserve_candidates':reobs,'by_source':dict(src),'by_template':dict(tmpl),'by_camera_motion':dict(c),'audit_variants':['correct_camera','frozen_camera','wrong_camera','shuffled_camera','short_prompt','structured_prompt','i2v_first_frame','v2v_prefix_8_16']}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default=''); ap.add_argument('--manifest',default=''); ap.add_argument('--out',default=''); ap.add_argument('--limit',type=int,default=0); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    cfg=load_yaml(a.config) if a.config else {}; manifest=a.manifest or cfg.get('manifest') or 'manifests/cam_physgeo_all.jsonl'
    rep=audit_manifest(manifest,limit=a.limit); print(rep)
    if a.out and not a.dry_run: write_json(rep,a.out)
    return 0
if __name__=='__main__': raise SystemExit(main())
