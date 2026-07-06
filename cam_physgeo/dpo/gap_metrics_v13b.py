from __future__ import annotations
import csv, math
from pathlib import Path
from typing import Any
EPS = 1e-8
def positive(value: float) -> float: return max(float(value), 0.0)
def compute_gap_metrics(m_w: float, m_l: float, m_w_ref: float, m_l_ref: float, *, clip_loser: float = 1.0) -> dict[str, float | str]:
    win_gap = float(m_w) - float(m_w_ref); lose_gap = float(m_l) - float(m_l_ref)
    winner_improvement = -win_gap; loser_degradation = lose_gap
    g_w = math.log((max(float(m_w), 0.0) + EPS) / (max(float(m_w_ref), 0.0) + EPS))
    g_l = math.log((max(float(m_l), 0.0) + EPS) / (max(float(m_l_ref), 0.0) + EPS))
    g_l_clip = min(g_l, float(clip_loser)); wi = positive(-g_w); ld = positive(g_l_clip); denom = wi + ld + EPS
    flags=[]
    flags.append('WINNER_IMPROVES' if winner_improvement > 0 else 'WINNER_WORSE')
    if loser_degradation > 0: flags.append('LOSER_DEGRADES')
    if ld / denom > 0.70: flags.append('LOSER_DOMINANT')
    if abs(win_gap) < 1e-8 and abs(lose_gap) < 1e-8: flags.append('NO_SIGNAL')
    if winner_improvement <= 0 and loser_degradation > 0: flags.append('CONFLICT')
    return {'win_gap': win_gap, 'lose_gap': lose_gap, 'winner_improvement': winner_improvement, 'loser_degradation': loser_degradation, 'g_w': g_w, 'g_l': g_l, 'g_l_clip': g_l_clip, 'winner_contribution_ratio': wi / denom, 'loser_dominance': ld / denom, 'health_flags': ';'.join(flags)}
def _float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try: return float(row.get(key, default))
    except Exception: return default
def enrich_training_csv(input_csv: str | Path, output_csv: str | Path | None = None, *, clip_loser: float = 1.0) -> Path:
    src=Path(input_csv); dst=Path(output_csv) if output_csv else src.with_name(src.stem + '_gap_enriched.csv'); rows=[]
    with src.open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            m=compute_gap_metrics(_float(row,'E_policy_winner_post'), _float(row,'E_policy_loser_post'), _float(row,'E_ref_winner_cached'), _float(row,'E_ref_loser_cached'), clip_loser=clip_loser)
            row.update({k:v for k,v in m.items() if k not in {'winner_improvement','loser_degradation'}}); rows.append(row)
    fieldnames=[]
    for row in rows:
        for key in row:
            if key not in fieldnames: fieldnames.append(key)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fieldnames, lineterminator='\n'); w.writeheader(); w.writerows(rows)
    return dst
def summarize_gap_csv(path: str | Path) -> dict[str, Any]:
    with Path(path).open(newline='', encoding='utf-8') as f: rows=list(csv.DictReader(f))
    pass_rows=[r for r in rows if r.get('status')=='PASS'] or rows
    def mean(key: str):
        vals=[]
        for r in pass_rows:
            try: vals.append(float(r.get(key,'')))
            except Exception: pass
        return '' if not vals else sum(vals)/len(vals)
    final=pass_rows[-1] if pass_rows else {}
    return {'rows':len(rows),'pass_rows':len(pass_rows),'mean_win_gap':mean('win_gap'),'mean_lose_gap':mean('lose_gap'),'mean_g_w':mean('g_w'),'mean_g_l':mean('g_l'),'mean_winner_improvement_post':mean('winner_improvement_post'),'mean_loser_degradation_post':mean('loser_degradation_post'),'mean_winner_contribution_ratio':mean('winner_contribution_ratio'),'mean_loser_dominance':mean('loser_dominance'),'final_winner_improvement_post':final.get('winner_improvement_post',''),'final_win_gap':final.get('win_gap',''),'final_health_flags':final.get('health_flags','')}
def decide_gap_health(summary: dict[str, Any]) -> str:
    try: mean_wi=float(summary.get('mean_winner_improvement_post',0)); final_wi=float(summary.get('final_winner_improvement_post',0)); ratio=float(summary.get('mean_winner_contribution_ratio',0)); loser_dom=float(summary.get('mean_loser_dominance',1))
    except Exception: return 'GAP_HEALTH_INVALID'
    if mean_wi>0 and final_wi>0 and ratio>=0.30 and loser_dom<=0.70: return 'TRAINING_SIGNAL_PASS'
    if mean_wi<=0 or final_wi<=0: return 'TRAINING_SIGNAL_FAIL_WINNER'
    if ratio<0.30 or loser_dom>0.70: return 'TRAINING_SIGNAL_FAIL_LOSER_DOMINANT'
    return 'TRAINING_SIGNAL_FAIL'
