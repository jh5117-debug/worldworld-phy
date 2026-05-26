from __future__ import annotations
import argparse
from cam_physgeo.data.scan_movingcam_synthetic import iter_movingcam_samples
from cam_physgeo.data.scan_phyinone import iter_phyinone_samples
from cam_physgeo.utils.io import write_jsonl

def build_manifest(phyinone_root: str|None, movingcam_root: str|None, limit: int|None=None) -> list[dict]:
    records=[]
    if phyinone_root: records.extend(iter_phyinone_samples(phyinone_root, limit=limit))
    if movingcam_root: records.extend(iter_movingcam_samples(movingcam_root, limit=limit))
    records.sort(key=lambda x:(x.get('source',''), x.get('sample_id',''))); return records
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--phyinone_root',default=''); ap.add_argument('--movingcam_root',default=''); ap.add_argument('--out',default='manifests/cam_physgeo_all.jsonl'); ap.add_argument('--limit',type=int,default=0); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    records=build_manifest(a.phyinone_root or None, a.movingcam_root or None, a.limit or None); by={}
    for r in records: by[r['source']]=by.get(r['source'],0)+1
    print({'total':len(records),'by_source':by,'out':a.out,'dry_run':a.dry_run})
    if not a.dry_run: print(f'wrote {write_jsonl(records,a.out)} samples to {a.out}')
    return 0
if __name__=='__main__': raise SystemExit(main())
