
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from cam_physgeo.dpo.pair_cache_objective_runner import run_objective
from cam_physgeo.dpo.dpo_v12c_probe_setup import find_warm_start


def existing_cache() -> tuple[Path, Path] | tuple[None, None]:
    root = Path('local_assets/dpo_objective_repair_v12b/winner_curriculum/cache_s_pass4')
    index = root / 'cache_index.jsonl'
    if root.exists() and index.exists():
        return root, index
    return None, None


def build_cache(args: argparse.Namespace) -> tuple[Path, Path]:
    root = Path(args.output_root) / 'cache_s_pass4'
    report_root = Path(args.report_root)
    report_root.mkdir(parents=True, exist_ok=True)
    cmd = [
        'python3', '-m', 'cam_physgeo.dpo.pair_cache_builder_v8m',
        '--pair_manifest', args.train_manifest,
        '--num_pairs', '4',
        '--gpu', str(args.gpu),
        '--prefix_len', str(args.prefix_len),
        '--prediction_start_frame', str(args.prediction_start_frame),
        '--future_only', 'true',
        '--used_window_frames', str(args.used_window_frames),
        '--output_root', str(root),
        '--report', str(report_root / 'cache_build.csv'),
        '--progress', str(report_root / 'cache_build_progress.jsonl'),
        '--heartbeat_seconds', '15',
        '--per_stage_timeout_seconds', '180',
        '--per_pair_timeout_seconds', '600',
        '--loader_mode', 'safe_wan_policy_only',
    ]
    subprocess.run(cmd, check=True)
    return root, root / 'cache_index.jsonl'


def choose_init_lora(objective: str, requested: str) -> str:
    if requested:
        return requested
    if objective == 'winner_only_warmstart':
        return ''
    warm = find_warm_start()
    return str(warm.get('checkpoint_path') or '') if warm.get('warm_start_available') else ''


def mapped_objective(name: str) -> str:
    return 'winner_anchor_repeat' if name == 'winner_only_warmstart' else name


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    report_root = Path(args.report_root); report_root.mkdir(parents=True, exist_ok=True)
    output_root = Path(args.output_root); output_root.mkdir(parents=True, exist_ok=True)
    cache_root, pair_subset = existing_cache()
    if cache_root is None or pair_subset is None:
        cache_root, pair_subset = build_cache(args)
    objective = mapped_objective(args.objective)
    init_lora = choose_init_lora(args.objective, args.init_lora_state)
    out_csv = report_root / f'{args.objective}_{args.steps}step.csv'
    ns = SimpleNamespace(
        cache_root=str(cache_root),
        pair_subset=str(pair_subset),
        objective=objective,
        steps=int(args.steps),
        gpu=int(args.gpu),
        output=str(out_csv),
        scope=args.scope,
        config=args.config,
        height=int(args.height),
        width=int(args.width),
        used_window_frames=int(args.used_window_frames),
        lr=float(args.lr),
        beta=float(args.beta),
        u_clip=float(args.u_clip),
        lambda_winner_anchor=float(args.lambda_winner_anchor),
        lambda_pref=float(args.lambda_pref),
        max_lambda_loser=float(args.max_lambda_loser),
        init_lora_state=init_lora,
        checkpoint_root=str(output_root / 'checkpoints'),
        checkpoint_steps=args.checkpoint_steps,
        gradient_checkpointing=True,
    )
    summary = run_objective(ns)
    summary['v12c_objective'] = args.objective
    summary['cache_root'] = str(cache_root)
    summary['pair_subset'] = str(pair_subset)
    summary['init_lora_state'] = init_lora
    summary_path = report_root / 'training_summary.json'
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    md = [
        f'Current Status: {summary.get("status")}', '',
        f'# v12c {args.objective} Training Summary', '',
        f'- Objective: `{args.objective}`',
        f'- Runner objective: `{objective}`',
        f'- Rows written: `{summary.get("rows_written")}`',
        f'- Steps requested: `{summary.get("steps_requested")}`',
        f'- Mean winner_improvement_post: `{summary.get("mean_winner_improvement_post")}`',
        f'- Final winner_improvement_post: `{summary.get("final_winner_improvement_post")}`',
        f'- Mean loser_degradation_post: `{summary.get("mean_loser_degradation_post")}`',
        f'- Mean winner_contribution_ratio_post: `{summary.get("mean_winner_contribution_ratio_post")}`',
        f'- Init LoRA state: `{init_lora}`',
        f'- Checkpoint manifest: `{summary.get("checkpoint_manifest")}`',
        f'- Decision: `{summary.get("status")}`',
    ]
    (report_root / 'training_summary.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Run v12c tiny guarded preference probes via the validated pair cache runner.')
    parser.add_argument('--train_manifest', required=True)
    parser.add_argument('--val_manifest', required=True)
    parser.add_argument('--scope', default='L0_camera_r4')
    parser.add_argument('--objective', required=True, choices=['winner_only_warmstart', 'winner_detached_preference', 'tiny_loser_gradient_preference', 'linear_winner_detached'])
    parser.add_argument('--steps', type=int, default=10)
    parser.add_argument('--beta', type=float, default=0.1)
    parser.add_argument('--lambda_winner_anchor', type=float, default=1.0)
    parser.add_argument('--lambda_pref', type=float, default=0.02)
    parser.add_argument('--lambda_loser', type=float, default=0.0)
    parser.add_argument('--max_lambda_loser', type=float, default=0.05)
    parser.add_argument('--u_clip', type=float, default=1.0)
    parser.add_argument('--gpu', type=int, default=0)
    parser.add_argument('--prefix_len', type=int, default=5)
    parser.add_argument('--prediction_start_frame', type=int, default=5)
    parser.add_argument('--future_only', default='true')
    parser.add_argument('--output_root', required=True)
    parser.add_argument('--report_root', required=True)
    parser.add_argument('--config', default='configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml')
    parser.add_argument('--height', type=int, default=480)
    parser.add_argument('--width', type=int, default=832)
    parser.add_argument('--used_window_frames', type=int, default=49)
    parser.add_argument('--lr', type=float, default=1e-6)
    parser.add_argument('--checkpoint_steps', default='0,5,10')
    parser.add_argument('--init_lora_state', default='')
    args = parser.parse_args(argv)
    run_probe(args)

if __name__ == '__main__':
    main()
