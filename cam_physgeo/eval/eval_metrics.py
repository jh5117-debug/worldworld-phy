from __future__ import annotations
import argparse
from cam_physgeo.utils.io import read_jsonl

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--scores',required=True); a=ap.parse_args(argv)
    vals=[float(r.get('reward_total') or 0.0) for r in read_jsonl(a.scores)]
    print({'count':len(vals),'mean_reward':sum(vals)/len(vals) if vals else None})
    return 0
if __name__=='__main__': raise SystemExit(main())
