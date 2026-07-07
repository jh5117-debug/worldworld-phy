from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from cam_physgeo.dpo.dpo_v12c_probe_setup import find_warm_start
from cam_physgeo.dpo.gap_metrics_v13b import decide_gap_health, enrich_training_csv, summarize_gap_csv
from cam_physgeo.dpo.pair_cache_objective_runner import run_objective

DEFAULT_CACHE_ROOT = 'local_assets/dpo_objective_repair_v12b/winner_curriculum/cache_s_pass4'
DEFAULT_PAIR_SUBSET = 'local_assets/dpo_objective_repair_v12b/winner_curriculum/cache_s_pass4/cache_index.jsonl'
DEFAULT_SCALE = 'reports/dpo_utility_calibration_v14/recommended_dpo_scale.json'

SCHEMES: dict[str, dict[str, Any]] = {
    'E01': {'objective': 'calibrated_winner_detached_raw', 'utility_type': 'u_raw', 'scope': 'L0_camera_r4', 'lambda_pref': 0.005, 'lr': 1e-6, 'steps': 200},
    'E02': {'objective': 'calibrated_winner_detached_log', 'utility_type': 'u_log', 'scope': 'L0_camera_r4', 'lambda_pref': 0.005, 'lr': 1e-6, 'steps': 200},
    'E03': {'objective': 'calibrated_winner_detached_log', 'utility_type': 'u_log_lower_lr', 'scope': 'L0_camera_r4', 'lambda_pref': 0.003, 'lr': 5e-7, 'steps': 200},
    'E04': {'objective': 'no_lose_gap_normalized_win_only', 'utility_type': 'winner_only', 'scope': 'L0_camera_r4', 'lambda_pref': 0.0, 'lambda_win': 0.5, 'lr': 1e-6, 'steps': 200},
    'E05': {'objective': 'normalized_clipped_loser', 'utility_type': 'clipped_loser_alpha002', 'scope': 'L0_camera_r4', 'alpha_l': 0.02, 'lambda_anchor': 1.0, 'lambda_win': 0.5, 'lr': 1e-6, 'steps': 200},
    'E06': {'objective': 'normalized_clipped_loser', 'utility_type': 'clipped_loser_alpha005', 'scope': 'L0_camera_r4', 'alpha_l': 0.05, 'lambda_anchor': 1.0, 'lambda_win': 0.5, 'lr': 1e-6, 'steps': 200},
    'E07': {'objective': 'linear_winner_detached', 'utility_type': 'linear_u_raw', 'scope': 'L0_camera_r4', 'lr': 1e-6, 'steps': 200},
    'E08': {'objective': 'calibrated_winner_detached_log', 'utility_type': 'local_or_full_u_log', 'scope': 'L0_camera_r4', 'lambda_pref': 0.005, 'lr': 1e-6, 'steps': 200},
    'E09': {'objective': 'calibrated_winner_detached_log', 'utility_type': 'source_weighted_u_log', 'scope': 'L0_camera_r4', 'lambda_pref': 0.005, 'lr': 1e-6, 'steps': 200},
    'E10': {'objective': 'calibrated_winner_detached_log', 'utility_type': 'u_log_temporal_lora', 'scope': 'L2_camera_temporal_r4', 'lambda_pref': 0.005, 'lr': 1e-6, 'steps': 100},
}


def allowed_cuda_visible_devices() -> bool:
    return os.environ.get('CUDA_VISIBLE_DEVICES', '') in {'4', '5'}


def load_scale(path: str) -> dict[str, Any]:
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return {'recommended_beta': 1000, 'recommended_utility_type': 'u_log'}


def scheme_config(scheme_id: str, scale: dict[str, Any]) -> dict[str, Any]:
    key = scheme_id.split('_', 1)[0]
    if key not in SCHEMES:
        raise KeyError(f'unknown scheme_id={scheme_id}')
    cfg = dict(SCHEMES[key])
    cfg['scheme_id'] = scheme_id
    cfg['beta'] = float(scale.get('recommended_beta') or 1000.0)
    cfg['lambda_winner_anchor'] = float(cfg.get('lambda_winner_anchor', 1.0))
    return cfg


def run_scheme(args: argparse.Namespace) -> dict[str, Any]:
    if not args.dry_run and not allowed_cuda_visible_devices():
        raise RuntimeError(f'CUDA_VISIBLE_DEVICES must be exactly physical GPU4 or GPU5 for v14, got {os.environ.get("CUDA_VISIBLE_DEVICES", "")}')
    scale = load_scale(args.scale_json)
    cfg = scheme_config(args.scheme_id, scale)
    report_root = Path(args.report_root) / args.scheme_id
    output_root = Path(args.output_root) / args.scheme_id
    report_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        summary = {'scheme_id': args.scheme_id, 'status': 'DRY_RUN', 'config': cfg, 'scale': scale}
        (report_root / 'training_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print(json.dumps(summary, indent=2, sort_keys=True))
        return summary
    init = args.init_lora_state
    if not init:
        warm = find_warm_start()
        init = str(warm.get('checkpoint_path') or '') if warm.get('warm_start_available') else ''
    steps = int(args.steps or cfg.get('steps', 200))
    out_csv = report_root / f'{args.scheme_id}_{steps}step.csv'
    ns = SimpleNamespace(
        cache_root=args.cache_root,
        pair_subset=args.pair_subset,
        objective=cfg['objective'],
        steps=steps,
        gpu=int(args.gpu),
        output=str(out_csv),
        scope=cfg.get('scope', 'L0_camera_r4'),
        config=args.config,
        height=int(args.height),
        width=int(args.width),
        used_window_frames=int(args.used_window_frames),
        lr=float(args.lr if args.lr is not None else cfg.get('lr', 1e-6)),
        beta=float(args.beta if args.beta is not None else cfg.get('beta', 1000.0)),
        u_clip=float(args.u_clip),
        lambda_winner_anchor=float(cfg.get('lambda_winner_anchor', 1.0)),
        lambda_pref=float(cfg.get('lambda_pref', 0.005)),
        max_lambda_loser=0.0,
        alpha_l=float(cfg.get('alpha_l', 0.02)),
        clip_loser=float(args.clip_loser),
        lambda_win=float(cfg.get('lambda_win', 0.5)),
        lambda_anchor=float(cfg.get('lambda_anchor', 1.0)),
        init_lora_state=init,
        checkpoint_root=str(output_root / 'checkpoints'),
        checkpoint_steps=args.checkpoint_steps,
        gradient_checkpointing=True,
    )
    raw = run_objective(ns)
    enriched = enrich_training_csv(out_csv, report_root / f'{args.scheme_id}_{steps}step_gap_enriched.csv', clip_loser=float(args.clip_loser))
    gaps = summarize_gap_csv(enriched)
    decision = decide_gap_health(gaps)
    summary = {**raw, 'scheme_id': args.scheme_id, 'scheme_config': cfg, 'scale': scale, 'gap_summary': gaps, 'training_signal_decision': decision, 'gap_enriched_csv': str(enriched), 'init_lora_state': init}
    (report_root / 'training_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (report_root / 'training_summary.md').write_text(
        f"# v14 {args.scheme_id} Summary\n\n"
        f"- Objective: `{cfg['objective']}`\n"
        f"- Utility type: `{cfg.get('utility_type')}`\n"
        f"- Beta: `{ns.beta}`\n"
        f"- Scope: `{cfg.get('scope')}`\n"
        f"- Steps requested: `{steps}`\n"
        f"- Raw status: `{raw.get('status')}`\n"
        f"- Training signal decision: `{decision}`\n"
        f"- Mean winner_improvement_post: `{gaps.get('mean_winner_improvement_post')}`\n"
        f"- Final winner_improvement_post: `{gaps.get('final_winner_improvement_post')}`\n"
        f"- Mean winner_contribution_ratio: `{gaps.get('mean_winner_contribution_ratio')}`\n\n"
        "Checkpoint video and metrics are required before this can be called a valid recipe.\n",
        encoding='utf-8')
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--scheme_id', required=True)
    p.add_argument('--cache_root', default=DEFAULT_CACHE_ROOT)
    p.add_argument('--pair_subset', default=DEFAULT_PAIR_SUBSET)
    p.add_argument('--gpu', type=int, default=0)
    p.add_argument('--steps', type=int, default=0)
    p.add_argument('--output_root', default='local_assets/dpo_utility_calibration_v14/objective_search')
    p.add_argument('--report_root', default='reports/dpo_utility_calibration_v14/objective_search')
    p.add_argument('--scale_json', default=DEFAULT_SCALE)
    p.add_argument('--init_lora_state', default='')
    p.add_argument('--config', default='configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml')
    p.add_argument('--height', type=int, default=480)
    p.add_argument('--width', type=int, default=832)
    p.add_argument('--used_window_frames', type=int, default=49)
    p.add_argument('--lr', type=float, default=None)
    p.add_argument('--beta', type=float, default=None)
    p.add_argument('--u_clip', type=float, default=1.0)
    p.add_argument('--clip_loser', type=float, default=1.0)
    p.add_argument('--checkpoint_steps', default='0,50,100,200')
    p.add_argument('--dry_run', action='store_true')
    run_scheme(p.parse_args(argv))


if __name__ == '__main__':
    main()
