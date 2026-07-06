from __future__ import annotations
import argparse, csv, json
from collections import Counter
from pathlib import Path
from typing import Any
def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p=Path(path); rows=[]
    if not p.exists(): return rows
    with p.open(encoding='utf-8') as f:
        for line in f:
            if line.strip(): rows.append(json.loads(line))
    return rows
def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        for row in rows: f.write(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n')
def breakdown(rows):
    return {'count':len(rows),'pair_type':dict(Counter(str(r.get('pair_type','')) for r in rows)),'failure_tag':dict(Counter(str(r.get('failure_tag') or r.get('loser',{}).get('failure_type','')) for r in rows)),'local_mask_ready':sum(1 for r in rows if r.get('loser',{}).get('affected_region') or r.get('loser',{}).get('affected_time_span'))}
def build(args):
    out_dir=Path(args.output_dir); out_dir.mkdir(parents=True, exist_ok=True); manifest_dir=Path(args.manifest_dir); manifest_dir.mkdir(parents=True, exist_ok=True)
    s_pass=read_jsonl(args.s_pass); s8_clean=read_jsonl(args.s8_clean); s16_src=read_jsonl(args.s16_src); s4_local_src=read_jsonl(args.s4_local_src); val_video=read_jsonl(args.val_video)
    s4=s_pass[:4]; s8=(s8_clean or s_pass)[:8]
    if len(s8)<8:
        seen={r.get('pair_id') for r in s8}
        for row in read_jsonl(args.train_manifest):
            if row.get('pair_id') not in seen: s8.append(row); seen.add(row.get('pair_id'))
            if len(s8)>=8: break
    s16=(s16_src or s8)[:16]; s4_local=(s4_local_src or s8)[:4]
    outputs={'s4_pass':manifest_dir/'s4_pass.jsonl','s8_pass_expand':manifest_dir/'s8_pass_expand.jsonl','s16_confident':manifest_dir/'s16_confident.jsonl','s4_local_mask':manifest_dir/'s4_local_mask.jsonl','val_video_4':manifest_dir/'val_video_4.jsonl'}
    for key, rows in [('s4_pass',s4),('s8_pass_expand',s8),('s16_confident',s16),('s4_local_mask',s4_local),('val_video_4',val_video[:4])]: write_jsonl(outputs[key], rows)
    summary=[]
    for key, rows in [('s4_pass',s4),('s8_pass_expand',s8),('s16_confident',s16),('s4_local_mask',s4_local),('val_video_4',val_video[:4])]:
        b=breakdown(rows); summary.append({'subset':key,'path':str(outputs[key]),'count':b['count'],'local_mask_ready':b['local_mask_ready'],'pair_type':json.dumps(b['pair_type'],sort_keys=True),'failure_tag':json.dumps(b['failure_tag'],sort_keys=True)})
    with (out_dir/'subset_summary.csv').open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=list(summary[0].keys()), lineterminator='\n'); w.writeheader(); w.writerows(summary)
    (out_dir/'subset_summary.md').write_text('# v13b Subset Summary\n\n'+'\n'.join(f"- `{r['subset']}`: {r['count']} rows, local-mask-ready={r['local_mask_ready']}, path=`{r['path']}`" for r in summary)+'\n', encoding='utf-8')
    return {'outputs':{k:str(v) for k,v in outputs.items()}, 'summary_csv':str(out_dir/'subset_summary.csv'), 'summary_md':str(out_dir/'subset_summary.md')}
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--ready_manifest',default='manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl'); p.add_argument('--train_manifest',default='manifests/dpo_pair_factory_v11_train400_repaired.jsonl'); p.add_argument('--s_pass',default='manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl'); p.add_argument('--s8_clean',default='manifests/dpo_v12b_subsets/s8_winner_anchor_clean.jsonl'); p.add_argument('--s16_src',default='manifests/dpo_v12b_subsets/s16_winner_curriculum.jsonl'); p.add_argument('--s4_local_src',default='manifests/dpo_v12b_subsets/s8_local_mask.jsonl'); p.add_argument('--val_video',default='manifests/dpo_v12b_subsets/val_video_4.jsonl'); p.add_argument('--manifest_dir',default='manifests/dpo_v13b_subsets'); p.add_argument('--output_dir',default='reports/dpo_objective_search_v13b')
    print(json.dumps(build(p.parse_args(argv)), indent=2, sort_keys=True))
if __name__=='__main__': main()
