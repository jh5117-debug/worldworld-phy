from cam_physgeo.utils.io import read_jsonl
def iter_filtered_self_rollout_pairs(pair_jsonl, min_winner_quality: float=0.5, min_margin: float=0.1):
    for p in read_jsonl(pair_jsonl):
        if p.get('pair_type')!='self_rollout': continue
        if float(p.get('margin') or 0) >= min_margin: yield p
