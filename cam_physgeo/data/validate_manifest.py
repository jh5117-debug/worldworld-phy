from __future__ import annotations
import argparse
from collections import Counter
from cam_physgeo.data.sample_schema import validate_sample
from cam_physgeo.utils.io import read_jsonl, write_json

def validate_manifest(path: str, check_paths: bool=True) -> dict:
    total=bad=0; errors=Counter(); src=Counter(); tmpl=Counter(); cam=Counter()
    for s in read_jsonl(path):
        total+=1; src[s.get('source','missing')]+=1; tmpl[s.get('template','missing')]+=1; cam[s.get('camera_motion','missing')]+=1
        es=validate_sample(s, check_paths=check_paths)
        if es: bad+=1; errors.update(es)
    return {'manifest':path,'total':total,'bad_samples':bad,'errors':dict(errors),'by_source':dict(src),'by_template':dict(tmpl),'by_camera_motion':dict(cam)}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--report',default=''); ap.add_argument('--no-path-check',action='store_true'); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    rep=validate_manifest(a.manifest, check_paths=not a.no_path_check); print(rep)
    if a.report and not a.dry_run: write_json(rep,a.report)
    return 1 if rep['bad_samples'] else 0
if __name__=='__main__': raise SystemExit(main())
