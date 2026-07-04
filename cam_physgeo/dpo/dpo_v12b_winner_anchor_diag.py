"""Per-pair v12b winner-anchor diagnosis with LoRA reset between pairs."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from cam_physgeo.dpo.dpo_v12b_subset_repair import condition_id, failure, source
from cam_physgeo.dpo.pair_cache_builder_v8m import build_pair_cache
from cam_physgeo.dpo.pair_cache_objective_runner import FIELDNAMES as OBJECTIVE_FIELDS
from cam_physgeo.dpo.pair_cache_objective_runner import run_objective

EXTRA_FIELDS = [
    'pair_index', 'pair_type', 'pair_source', 'failure_type', 'condition_id',
    'per_pair_decision', 'cache_root', 'pair_manifest_path', 'summary_path',
]
FIELDNAMES = EXTRA_FIELDS + OBJECTIVE_FIELDS


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + '\n')


def sanitize(text: str) -> str:
    return ''.join(ch if ch.isalnum() or ch in {'-', '_', '.'} else '_' for ch in text)[:160]


def append_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open('a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction='ignore', lineterminator='\n')
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in FIELDNAMES})
        f.flush()


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def safe_float(value: Any) -> float | None:
    try:
        if value == '':
            return None
        return float(value)
    except Exception:
        return None


def summarize_pair(rows: list[dict[str, Any]], steps: int) -> dict[str, Any]:
    pass_rows = [r for r in rows if r.get('status') == 'PASS']
    vals = [safe_float(r.get('winner_improvement_post')) for r in pass_rows]
    vals = [v for v in vals if v is not None]
    final = vals[-1] if vals else None
    mean = sum(vals) / len(vals) if vals else None
    grad_nonzero = any((safe_float(r.get('grad_norm')) or 0.0) > 0.0 for r in pass_rows)
    update_nonzero = any((safe_float(r.get('update_norm')) or 0.0) > 0.0 for r in pass_rows)
    finite = all(str(r.get('finite')) in {'True', 'true', '1'} for r in pass_rows) if pass_rows else False
    positive = len(pass_rows) >= int(steps) and mean is not None and final is not None and mean > 0.0 and final > 0.0 and grad_nonzero and update_nonzero and finite
    return {
        'rows_written': len(rows),
        'pass_rows': len(pass_rows),
        'mean_winner_improvement_post': '' if mean is None else mean,
        'final_winner_improvement_post': '' if final is None else final,
        'grad_nonzero': grad_nonzero,
        'update_nonzero': update_nonzero,
        'finite': finite,
        'decision': 'S_PASS' if positive else 'S_FAIL',
    }


def write_summary(output: Path, summaries: list[dict[str, Any]], pass_rows: list[dict[str, Any]], fail_rows: list[dict[str, Any]]) -> None:
    summary_csv = output.with_name(output.stem + '_summary.csv')
    fields = [
        'pair_index', 'pair_id', 'pair_type', 'pair_source', 'failure_type', 'condition_id',
        'decision', 'rows_written', 'pass_rows', 'mean_winner_improvement_post',
        'final_winner_improvement_post', 'grad_nonzero', 'update_nonzero', 'finite', 'csv', 'error_reason',
    ]
    with summary_csv.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
        writer.writeheader(); writer.writerows(summaries)
    pass_manifest = output.parent / 's_pass_winner_anchor.jsonl'
    fail_manifest = output.parent / 's_fail_winner_anchor.jsonl'
    write_jsonl(pass_manifest, pass_rows)
    write_jsonl(fail_manifest, fail_rows)
    total = len(summaries)
    passed = len(pass_rows)
    failed = len(fail_rows)
    md = output.with_name(output.stem + '_summary.md')
    md.write_text(
        'Current Status: ' + ('WINNER_ANCHOR_PER_PAIR_PASS' if passed >= 4 else 'WINNER_ANCHOR_PER_PAIR_INSUFFICIENT_POSITIVES') + '\n\n'
        '# v12b Per-Pair Winner-Anchor Diagnosis\n\n'
        f'- Total pairs: `{total}`\n'
        f'- Positive S_pass pairs: `{passed}`\n'
        f'- S_fail pairs: `{failed}`\n'
        f'- S_pass manifest: `{pass_manifest}`\n'
        f'- S_fail manifest: `{fail_manifest}`\n'
        f'- DPO/curriculum may continue only if S_pass >= 4.\n',
        encoding='utf-8',
    )


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description='Run v12b per-pair winner-anchor diagnosis with LoRA reset per pair.')
    ap.add_argument('--pair_manifest', required=True)
    ap.add_argument('--scope', default='L0_camera_r4')
    ap.add_argument('--steps', type=int, default=5)
    ap.add_argument('--gpu', type=int, default=0)
    ap.add_argument('--output', required=True)
    ap.add_argument('--cache_root', default='local_assets/dpo_objective_repair_v12b/winner_anchor_diag')
    ap.add_argument('--config', default='configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml')
    ap.add_argument('--height', type=int, default=480)
    ap.add_argument('--width', type=int, default=832)
    ap.add_argument('--used_window_frames', type=int, default=49)
    ap.add_argument('--target_sigma', type=float, default=0.35)
    ap.add_argument('--seed', type=int, default=1234)
    ap.add_argument('--lr', type=float, default=1e-6)
    args = ap.parse_args(argv)

    output = Path(args.output)
    if output.exists():
        output.unlink()
    pairs = read_jsonl(args.pair_manifest)
    summaries: list[dict[str, Any]] = []
    pass_pairs: list[dict[str, Any]] = []
    fail_pairs: list[dict[str, Any]] = []
    tmp_dir = output.parent / 'tmp_pair_manifests'
    cache_base = Path(args.cache_root)
    for idx, pair in enumerate(pairs):
        pair_id = str(pair.get('pair_id') or f'pair_{idx:03d}')
        safe_id = sanitize(f'{idx:03d}_{pair_id}')
        one_manifest = tmp_dir / f'{safe_id}.jsonl'
        write_jsonl(one_manifest, [pair])
        pair_cache = cache_base / safe_id
        pair_csv = output.parent / 'per_pair_runs' / f'{safe_id}_{args.scope}_{args.steps}step.csv'
        error_reason = ''
        rows: list[dict[str, Any]] = []
        try:
            build_pair_cache(SimpleNamespace(
                pair_manifest=str(one_manifest), num_pairs=1, gpu=int(args.gpu), prefix_len=5,
                prediction_start_frame=5, future_only='true', used_window_frames=int(args.used_window_frames),
                output_root=str(pair_cache), report=str(output.parent / 'cache_reports' / f'{safe_id}_cache.csv'),
                progress=str(output.parent / 'cache_reports' / f'{safe_id}_cache_progress.jsonl'),
                heartbeat_seconds=15.0, per_stage_timeout_seconds=180.0, per_pair_timeout_seconds=600.0,
                config=args.config, repo_root='.', runtime_device='cuda', height=int(args.height), width=int(args.width),
                target_sigma=float(args.target_sigma), seed=int(args.seed), loader_mode='safe_wan_policy_only',
            ))
            run_objective(SimpleNamespace(
                cache_root=str(pair_cache), pair_subset=str(pair_cache / 'cache_index.jsonl'), objective='winner_anchor_repeat',
                steps=int(args.steps), gpu=int(args.gpu), output=str(pair_csv), scope=args.scope, config=args.config,
                height=int(args.height), width=int(args.width), used_window_frames=int(args.used_window_frames), lr=float(args.lr),
                beta=1.0, u_clip=1.0, lambda_winner_anchor=1.0, max_lambda_loser=0.0,
                checkpoint_root='', checkpoint_steps='', gradient_checkpointing=True,
            ))
            rows = read_csv(pair_csv)
        except Exception as exc:  # noqa: BLE001
            error_reason = repr(exc)
            rows = [{
                'step': 0, 'pair_id': pair_id, 'scope': args.scope, 'objective': 'winner_anchor_repeat',
                'status': 'FAIL', 'finite': False, 'error_reason': error_reason,
            }]
        decision = summarize_pair(rows, int(args.steps))
        meta = {
            'pair_index': idx,
            'pair_type': pair.get('pair_type', ''),
            'pair_source': source(pair),
            'failure_type': failure(pair),
            'condition_id': condition_id(pair),
            'per_pair_decision': decision['decision'],
            'cache_root': str(pair_cache),
            'pair_manifest_path': str(one_manifest),
            'summary_path': str(pair_csv.with_suffix('.summary.json')),
        }
        enriched = [{**meta, **r, 'pair_id': r.get('pair_id') or pair_id} for r in rows]
        append_rows(output, enriched)
        summary = {
            **meta, **decision, 'pair_id': pair_id, 'csv': str(pair_csv), 'error_reason': error_reason,
            'decision': decision['decision'],
        }
        summaries.append(summary)
        if decision['decision'] == 'S_PASS':
            pass_pairs.append(pair)
        else:
            fail_pairs.append(pair)
        write_summary(output, summaries, pass_pairs, fail_pairs)
    write_summary(output, summaries, pass_pairs, fail_pairs)


if __name__ == '__main__':
    main()
