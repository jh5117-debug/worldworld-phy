#!/usr/bin/env python3
from __future__ import annotations

import csv, json, math
from pathlib import Path
from collections import Counter
import numpy as np
import av
from PIL import Image, ImageDraw, ImageFont

from scripts.build_reward_guided_protocol_v4 import build_showcase, read_video, resolve_path, clamp_bbox, sample_frames, heatmap_frame
from cam_physgeo.dpo.reward_guided_pair_selector import alignment_decision

REPO = Path('.')
OUT = REPO / 'reports' / 'reward_visual_alignment_v5'
PPT = REPO / 'reports' / 'ppt_winlose_showcase_latest'
OUT.mkdir(parents=True, exist_ok=True)
PPT.mkdir(parents=True, exist_ok=True)

MIN_REWARD_MARGIN = 0.12
MIN_LOCAL_P95 = 35.0
MIN_LOCAL_MEAN = 6.0
MIN_VISUAL_SCORE = 0.070
MIN_SHARPNESS = 0.65


def read_rows(path: Path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def rel(p: Path) -> str:
    try: return str(p.relative_to(REPO))
    except Exception: return str(p)


def write_jsonl(path: Path, rows):
    with path.open('w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n')


def write_csv(path: Path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
        w.writeheader(); w.writerows(rows)


def floaty(x, default=0.0):
    try:
        if x is None or x == '': return default
        return float(x)
    except Exception:
        return default


def video_metrics(winner_frames, loser_frames, bbox):
    n = min(len(winner_frames), len(loser_frames))
    idxs = np.linspace(0, n-1, min(16, n), dtype=int).tolist() if n else []
    x0,y0,x1,y1 = bbox
    local_means=[]; local_p95=[]; global_means=[]; global_p95=[]
    for i in idxs:
        diff = np.abs(winner_frames[i].astype(np.int16) - loser_frames[i].astype(np.int16)).mean(axis=2)
        local = diff[y0:y1, x0:x1]
        local_means.append(float(local.mean()) if local.size else 0.0)
        local_p95.append(float(np.percentile(local, 95)) if local.size else 0.0)
        global_means.append(float(diff.mean()))
        global_p95.append(float(np.percentile(diff, 95)))
    area_frac = ((x1-x0)*(y1-y0)) / max(winner_frames[0].shape[0]*winner_frames[0].shape[1], 1)
    lm = float(np.mean(local_means)) if local_means else 0.0
    lp = float(np.mean(local_p95)) if local_p95 else 0.0
    gm = float(np.mean(global_means)) if global_means else 0.0
    gp = float(np.mean(global_p95)) if global_p95 else 0.0
    # Deliberately conservative: tiny boxes need larger local contrast; large boxes need visible average change.
    visual_score = (lp / 255.0) * math.sqrt(max(area_frac, 1e-6)) + (lm / 255.0) * 0.35
    return {
        'local_absdiff_mean': lm,
        'local_absdiff_p95': lp,
        'global_absdiff_mean': gm,
        'global_absdiff_p95': gp,
        'diff_bbox_area': area_frac,
        'visual_difference_score': visual_score,
    }


def dominant_margin(margins):
    if not margins: return 'none'
    return max(margins.items(), key=lambda kv: floaty(kv[1]))[0]


def make_diag_video(rows, out_path):
    W,H = 1920,1080
    try:
        font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 48)
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
        small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
    except Exception:
        font_big = font = small = ImageFont.load_default()
    frames=[]
    chosen = rows[:5]
    for rank,row in enumerate(chosen,1):
        win,_ = read_video(resolve_path(row['winner_video']))
        lose,_ = read_video(resolve_path(row['loser_video']))
        prefix,_ = read_video(resolve_path(row['prefix_video']))
        n=72
        idxs=np.linspace(0,min(len(win),len(lose))-1,n,dtype=int).tolist()
        x0,y0,x1,y1 = row['bbox_tuple']
        pref = sample_frames(prefix,5) or win[:5]
        for idx in idxs:
            canvas=Image.new('RGB',(W,H),(16,18,22)); d=ImageDraw.Draw(canvas)
            status='DPO READY' if row['medium_hard'] else 'VISUAL_TOO_SUBTLE - NOT DPO READY'
            color=(0,235,85) if row['medium_hard'] else (255,90,70)
            d.text((36,24),f"Pair {rank}/{len(chosen)} {row['pair_id'][:80]}",fill=(255,255,255),font=font_big)
            d.text((36,82),f"{row['pair_type']} | {row['corruption_type']} | Rmargin={row['reward_margin']:.3f} | local_p95={row['local_absdiff_p95']:.1f} | {status}",fill=color,font=font)
            for j,pf in enumerate(pref):
                im=Image.fromarray(pf).resize((210,121),Image.Resampling.BICUBIC); canvas.paste(im,(36+j*218,145))
            win_im=Image.fromarray(win[idx]).resize((590,340),Image.Resampling.BICUBIC)
            lose_im=Image.fromarray(lose[idx]).resize((590,340),Image.Resampling.BICUBIC)
            canvas.paste(win_im,(36,340)); canvas.paste(lose_im,(36,725))
            d.rectangle((36,340,626,680),outline=(0,230,80),width=8); d.rectangle((36,725,626,1065),outline=(240,45,45),width=8)
            d.text((54,354),'WIN',fill=(0,255,90),font=font_big); d.text((54,739),'LOSE',fill=(255,80,80),font=font_big)
            zwin=Image.fromarray(win[idx][y0:y1,x0:x1]).resize((420,280),Image.Resampling.BICUBIC)
            zlose=Image.fromarray(lose[idx][y0:y1,x0:x1]).resize((420,280),Image.Resampling.BICUBIC)
            hm=heatmap_frame(win[idx],lose[idx]).resize((420,280),Image.Resampling.BICUBIC)
            canvas.paste(zwin,(710,350)); canvas.paste(zlose,(1165,350)); canvas.paste(hm,(710,735))
            d.text((710,315),'Affected zoom WIN',fill=(0,255,90),font=small); d.text((1165,315),'Affected zoom LOSE',fill=(255,80,80),font=small); d.text((710,700),'Diff heatmap',fill=(255,210,100),font=small)
            d.text((1165,735),row['written_reason'][:220],fill=(235,235,235),font=small)
            frames.append(canvas)
    from scripts.build_reward_guided_protocol_v4 import write_video
    return write_video(frames,out_path,fps=12)


def main():
    pairs = read_rows(Path('manifests/dpo_preference_protocol_v4_pairs.jsonl'))
    audit=[]; ready=[]; rejected=[]
    for p in pairs:
        win_path = resolve_path(p['winner'].get('future_video_path'))
        lose_path = resolve_path(p['loser'].get('future_video_path'))
        prefix_path = p.get('condition',{}).get('prefix_video_path')
        if not win_path or not lose_path or not win_path.exists() or not lose_path.exists():
            row={'pair_id':p['pair_id'],'pair_type':p.get('pair_type'),'status':'MISSING_VIDEO','medium_hard':False,'too_subtle':True,'written_reason':'missing winner/loser video path'}
            audit.append(row); rejected.append(p); continue
        win,_=read_video(win_path); lose,_=read_video(lose_path)
        h,w=win[0].shape[:2]
        bbox=clamp_bbox(p['loser'].get('affected_region'),w,h)
        metrics=video_metrics(win,lose,bbox)
        reward_margin=floaty(p.get('reward_margin'))
        sub=p.get('subreward_margins',{})
        failure=p['loser'].get('corruption_type') or p['loser'].get('failure_type') or ''
        align=alignment_decision(failure, sub)
        sharp=floaty(p['loser'].get('traditional_metrics',{}).get('sharpness_ratio'),1.0)
        visible = metrics['local_absdiff_p95'] >= MIN_LOCAL_P95 and metrics['local_absdiff_mean'] >= MIN_LOCAL_MEAN and metrics['visual_difference_score'] >= MIN_VISUAL_SCORE
        explain = visible and bool(failure)
        too_degraded = sharp < MIN_SHARPNESS or p.get('codex_audit',{}).get('loser_collapsed') or p.get('codex_audit',{}).get('winner_bad')
        medium = reward_margin > MIN_REWARD_MARGIN and align['aligned'] and visible and explain and not too_degraded
        reason_bits=[]
        if not visible: reason_bits.append('VISUAL_TOO_SUBTLE: full-frame WIN/LOSE difference is hard to see without heatmap')
        if not align['aligned']: reason_bits.append('REWARD_FAILURE_MISMATCH')
        if reward_margin <= MIN_REWARD_MARGIN: reason_bits.append('REWARD_MARGIN_TOO_SMALL')
        if too_degraded: reason_bits.append('TOO_DEGRADED_OR_BLURRY')
        if medium: reason_bits.append('VISIBLE_MEDIUM_HARD: local difference is visible and reward-aligned')
        row={
            'pair_id':p['pair_id'], 'pair_type':p.get('pair_type'), 'corruption_type':failure, 'severity':p['loser'].get('severity'),
            'reward_winner':1.0, 'reward_loser':1.0-reward_margin, 'reward_margin':reward_margin,
            'main_subreward_drop':dominant_margin(sub), 'PSNR':p['loser'].get('traditional_metrics',{}).get('psnr_future',''),
            'SSIM':p['loser'].get('traditional_metrics',{}).get('ssim_future_proxy',''), 'LPIPS':'BLOCKED_NOT_RUN',
            'sharpness_ratio':sharp, 'affected_region_diff':metrics['local_absdiff_mean'],
            'local_absdiff_mean':metrics['local_absdiff_mean'], 'local_absdiff_p95':metrics['local_absdiff_p95'],
            'local_lpips':'BLOCKED_NOT_RUN', 'diff_bbox_area':metrics['diff_bbox_area'], 'visual_difference_score':metrics['visual_difference_score'],
            'codex_can_see_difference':'yes' if visible else 'no', 'codex_failure_explainable':'yes' if explain else 'no',
            'too_subtle':'no' if visible else 'yes', 'too_degraded':'yes' if too_degraded else 'no', 'medium_hard':'yes' if medium else 'no',
            'status':'DPO_READY_VISUAL_V5' if medium else ('TOO_DEGRADED' if too_degraded else 'VISUAL_TOO_SUBTLE'),
            'winner_video':p['winner'].get('future_video_path'), 'loser_video':p['loser'].get('future_video_path'), 'prefix_video':prefix_path,
            'bbox_tuple':bbox, 'written_reason':'; '.join(reason_bits),
        }
        audit.append(row)
        if medium: ready.append(p)
        else: rejected.append(p)
    fields=[k for k in audit[0].keys() if k!='bbox_tuple']
    write_csv(OUT/'pair_visual_alignment.csv', audit, fields)
    write_jsonl(OUT/'dpo_ready_pairs_visual_v5.jsonl', ready)
    write_jsonl(OUT/'rejected_too_subtle_pairs.jsonl', rejected)
    c=Counter((r['pair_type'],r['status']) for r in audit)
    visible=sum(1 for r in audit if r['codex_can_see_difference']=='yes')
    medium=sum(1 for r in audit if r['medium_hard']=='yes')
    too_subtle=sum(1 for r in audit if r['status']=='VISUAL_TOO_SUBTLE')
    typea_subtle=sum(1 for r in audit if r['pair_type']=='TypeA_plus' and r['status']=='VISUAL_TOO_SUBTLE')
    typem_medium=sum(1 for r in audit if r['pair_type']=='TypeM' and r['medium_hard']=='yes')
    margins=np.array([floaty(r['reward_margin']) for r in audit])
    scores=np.array([floaty(r['visual_difference_score']) for r in audit])
    corr=float(np.corrcoef(margins,scores)[0,1]) if len(audit)>1 and scores.std()>1e-9 else 0.0
    summary=f'''# Reward Visual Alignment v5 Summary\n\nCurrent Status: {'PASS_VISIBLE_PAIRS_AVAILABLE' if medium>=4 else 'PROTOCOL_V4_NOT_READY_TOO_SUBTLE'}\n\n- Total v4 pairs checked: {len(audit)}\n- Human-visible count: {visible}\n- True medium-hard count: {medium}\n- Too subtle count: {too_subtle}\n- TypeA_plus too subtle: {typea_subtle}\n- TypeM true medium-hard: {typem_medium}\n- Reward margin / visual score correlation: {corr:.4f}\n- Ready JSONL: `reports/reward_visual_alignment_v5/dpo_ready_pairs_visual_v5.jsonl`\n- Rejected JSONL: `reports/reward_visual_alignment_v5/rejected_too_subtle_pairs.jsonl`\n\n## Interpretation\n\nThe v5 gate is intentionally stricter than v4: positive proxy reward is not enough. A pair must have visible local difference, explainable failure, aligned subreward drop, and non-blurry loser. Pairs that look the same without a heatmap are marked `VISUAL_TOO_SUBTLE` and removed from DPO-ready.\n\nReward innovation is only partially grounded while reward backend remains proxy/diagnostic. The missing pieces are real perceptual/local LPIPS, real physics subreward backends, and a human-visible local difference gate.\n'''
    (OUT/'pair_visual_alignment_summary.md').write_text(summary, encoding='utf-8')
    # PPT selection: visible first; if insufficient, top diagnostic too-subtle rows.
    selected=[r for r in audit if r['medium_hard']=='yes'][:5]
    if len(selected)<4:
        selected=sorted(audit, key=lambda r: floaty(r['visual_difference_score']), reverse=True)[:5]
    csv_rows=[]
    for i,r in enumerate(selected,1):
        rr={k:v for k,v in r.items() if k!='bbox_tuple'}; rr['rank']=i; csv_rows.append(rr)
    flds=['rank']+[k for k in csv_rows[0].keys() if k!='rank'] if csv_rows else ['rank']
    write_csv(PPT/'visible_mediumhard_v5_selected_pairs.csv', csv_rows, flds)
    notes=f'''# Visible Medium-Hard v5 PPT Notes\n\nCurrent Status: {'PASS_VISIBLE_SELECTION' if medium>=4 else 'DIAGNOSTIC_TOO_SUBTLE_SELECTION'}\n\n- Total checked: {len(audit)}\n- Human-visible: {visible}\n- DPO-ready after visual gate: {medium}\n- Selected segments: {len(selected)}\n- If a segment is not ready, the video labels it `VISUAL_TOO_SUBTLE - NOT DPO READY`.\n- Main conclusion: reward-selected v4 pairs require visual alignment gating before DPO.\n'''
    (PPT/'visible_mediumhard_v5_notes.md').write_text(notes, encoding='utf-8')
    # Need bbox tuples for video rows.
    by_id={r['pair_id']:r for r in audit}
    vid_rows=[]
    for r in selected:
        row=dict(r); row['bbox_tuple']=by_id[r['pair_id']]['bbox_tuple']; vid_rows.append(row)
    codec=make_diag_video(vid_rows, PPT/'winlose_showcase_visible_mediumhard_v5_for_ppt.mp4') if vid_rows else 'NO_SELECTION'
    print(json.dumps({'total':len(audit),'visible':visible,'medium_hard':medium,'too_subtle':too_subtle,'typeA_plus_too_subtle':typea_subtle,'typeM_medium':typem_medium,'corr':corr,'video_codec':codec}, indent=2))

if __name__=='__main__': main()
