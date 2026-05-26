from __future__ import annotations
import argparse
from collections import defaultdict
from pathlib import Path
from cam_physgeo.rewards.corruption import make_corruption_records
from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.utils.io import read_jsonl, write_jsonl

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--out',default='manifests/reward_calibration_scores.jsonl'); ap.add_argument('--report',default='docs/reward_calibration_report.md'); ap.add_argument('--corruptions_out_dir',default=''); ap.add_argument('--limit',type=int,default=0); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    rows=[]; drops=defaultdict(list); clean_wins=0; comparisons=0
    for i,s in enumerate(read_jsonl(a.manifest)):
        if a.limit and i>=a.limit: break
        clean=score_sample(s); clean['kind']='clean_gt'; rows.append(clean)
        for corr in make_corruption_records(s,out_dir=a.corruptions_out_dir or None,dry_run=a.dry_run):
            corrupt_sample=dict(s); corrupt_sample['candidate_video_path']=corr['loser_video']; corrupt=score_sample(corrupt_sample)
            corrupt['kind']='corrupted_gt'; corrupt['corruption']=corr['corruption']; rows.append(corrupt)
            drop=float(clean.get('reward_total') or 0)-float(corrupt.get('reward_total') or 0); drops[corr['corruption']].append(drop); comparisons+=1
            if drop>0: clean_wins+=1
    summary={'calibration_rows':len(rows),'comparisons':comparisons,'clean_gt_win_rate':(clean_wins/comparisons if comparisons else None),'mean_drop_by_corruption':{k:sum(v)/len(v) for k,v in drops.items()},'dry_run':a.dry_run}
    print(summary)
    if not a.dry_run: write_jsonl(rows,a.out)
    if a.report and not a.dry_run:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        lines=['# Reward Calibration Report','',f"- rows: {len(rows)}",f"- comparisons: {comparisons}",f"- clean_gt_win_rate: {summary['clean_gt_win_rate']}","",'## Mean Reward Drop']
        for k,v in sorted(summary['mean_drop_by_corruption'].items()):
            lines.append(f"- {k}: {v:.4f}")
        if summary['clean_gt_win_rate'] is not None and summary['clean_gt_win_rate'] < 0.7:
            lines.extend(['','WARNING: clean GT is not reliably above corrupted negatives; tune reward weights/backends before DPO.'])
        Path(a.report).write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return 0
if __name__=='__main__': raise SystemExit(main())
