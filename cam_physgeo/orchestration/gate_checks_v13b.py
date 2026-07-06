from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Any
ALLOWED_GPUS={4,5}; FORBIDDEN_GPUS={0,1,2,3,6,7}
def check_only_gpu45(assigned_gpus): return bool(assigned_gpus) and all(int(g) in ALLOWED_GPUS for g in assigned_gpus) and not any(int(g) in FORBIDDEN_GPUS for g in assigned_gpus)
def _float(v: Any, default=0.0):
    try: return float(v)
    except Exception: return default
def check_training_signal_csv(csv_path: str|Path) -> dict[str,Any]:
    with Path(csv_path).open(newline='', encoding='utf-8') as f: rows=list(csv.DictReader(f))
    pass_rows=[r for r in rows if r.get('status')=='PASS'] or rows
    def mean(k):
        vals=[_float(r.get(k), float('nan')) for r in pass_rows]; vals=[v for v in vals if v==v]; return sum(vals)/len(vals) if vals else 0.0
    final=pass_rows[-1] if pass_rows else {}; mean_wi=mean('winner_improvement_post'); final_wi=_float(final.get('winner_improvement_post')); ratio=mean('winner_contribution_ratio') if 'winner_contribution_ratio' in final else mean('winner_contribution_ratio_post'); loser_dom=mean('loser_dominance')
    return {'decision':'PASS' if mean_wi>0 and final_wi>0 and ratio>=0.30 and loser_dom<=0.70 else 'FAIL','rows':len(rows),'mean_winner_improvement_post':mean_wi,'final_winner_improvement_post':final_wi,'winner_contribution_ratio':ratio,'loser_dominance':loser_dom}
def check_summary_json(path: str|Path) -> dict[str,Any]:
    data=json.loads(Path(path).read_text()); decision=data.get('training_signal_decision') or data.get('status') or ''; return {'decision':'PASS' if 'PASS' in str(decision) else 'FAIL','raw_decision':decision,'path':str(path)}
