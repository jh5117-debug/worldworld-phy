
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    rows: list[dict[str, Any]] = []
    if not p.exists():
        return rows
    with p.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def repo_path(path: Any, repo_root: str | Path = '.') -> Path:
    p = Path(str(path or ''))
    return p if p.is_absolute() else Path(repo_root) / p


def audit(row: dict[str, Any]) -> dict[str, Any]:
    return row.get('codex_visual_audit') or row.get('codex_audit') or {}


def pair_source(row: dict[str, Any]) -> str:
    pair_type = str(row.get('pair_type') or '')
    pair_source_raw = str(row.get('pair_source') or row.get('source_protocol') or '')
    if row.get('is_rollout_derived') or pair_type in {'GT_C', 'B_C', 'M0_C'} or 'rollout' in pair_type.lower() or 'rollout' in pair_source_raw.lower():
        return 'rollout'
    if row.get('is_synthetic') or row.get('is_controlled_corruption') or 'synthetic' in pair_type.lower() or 'synthetic' in pair_source_raw.lower() or 'typem' in pair_type.lower():
        return 'synthetic'
    return pair_source_raw or pair_type or 'other'


def failure_tag(row: dict[str, Any]) -> str:
    loser = row.get('loser') or {}
    return str(row.get('failure_tag') or loser.get('failure_type') or loser.get('corruption_type') or row.get('main_failure') or 'unknown')


def has_region(row: dict[str, Any]) -> bool:
    loser = row.get('loser') or {}
    return bool(loser.get('affected_region') or loser.get('affected_mask'))


def has_time(row: dict[str, Any]) -> bool:
    loser = row.get('loser') or {}
    return bool(loser.get('affected_time_span') or row.get('loss_frame_indices') or row.get('reward_frame_indices'))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def find_s_pass_manifest(requested: Path) -> Path:
    if requested.exists():
        return requested
    fallback = Path('reports/dpo_objective_repair_v12b/winner_anchor_diag/s_pass_winner_anchor.jsonl')
    if fallback.exists():
        requested.parent.mkdir(parents=True, exist_ok=True)
        requested.write_text(fallback.read_text(encoding='utf-8'), encoding='utf-8')
        return requested
    raise FileNotFoundError(f'S_pass manifest not found: {requested} or {fallback}')


def find_s_fail_ids() -> set[str]:
    ids: set[str] = set()
    for path in [Path('manifests/dpo_v12b_subsets/s_fail_winner_anchor.jsonl'), Path('reports/dpo_objective_repair_v12b/winner_anchor_diag/s_fail_winner_anchor.jsonl')]:
        for row in read_jsonl(path):
            ids.add(str(row.get('pair_id')))
    return ids


def find_warm_start() -> dict[str, Any]:
    manifest = Path('local_assets/dpo_objective_repair_v12b/winner_curriculum/checkpoints/checkpoint_manifest.json')
    candidates: list[dict[str, Any]] = []
    if manifest.exists():
        try:
            candidates = json.loads(manifest.read_text(encoding='utf-8'))
        except Exception:
            candidates = []
    step20 = [r for r in candidates if int(r.get('step', -1)) == 20]
    selected = step20[-1] if step20 else (candidates[-1] if candidates else {})
    path = Path(str(selected.get('path') or ''))
    out = {
        'warm_start_available': False,
        'checkpoint_path': '',
        'checkpoint_step': selected.get('step', ''),
        'sha256': '',
        'tensor_count': '',
        'param_count': '',
        'status': 'NOT_FOUND',
    }
    if path.exists():
        import torch
        state = torch.load(path, map_location='cpu')
        out.update({
            'warm_start_available': True,
            'checkpoint_path': str(path),
            'sha256': sha256_file(path),
            'tensor_count': len(state),
            'param_count': sum(int(v.numel()) for v in state.values() if hasattr(v, 'numel')),
            'status': 'LOADABLE',
        })
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Verify v12c S_pass4 readiness and warm-start checkpoint inventory.')
    parser.add_argument('--s_pass_manifest', required=True)
    parser.add_argument('--v12b_report', required=True)
    parser.add_argument('--canonical', default='manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl')
    parser.add_argument('--output_dir', required=True)
    parser.add_argument('--repo_root', default='.')
    args = parser.parse_args(argv)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    s_pass_path = find_s_pass_manifest(Path(args.s_pass_manifest))
    pairs = read_jsonl(s_pass_path)
    canonical_ids = {str(r.get('pair_id')) for r in read_jsonl(args.canonical)}
    s_fail_ids = find_s_fail_ids()
    v12b_rows = []
    v12b_path = Path(args.v12b_report)
    if v12b_path.exists():
        with v12b_path.open(newline='', encoding='utf-8') as f:
            v12b_rows = list(csv.DictReader(f))
    v12b_ids = {str(r.get('pair_id')) for r in v12b_rows}
    rows: list[dict[str, Any]] = []
    for row in pairs:
        pid = str(row.get('pair_id'))
        condition = row.get('condition') or {}
        winner = row.get('winner') or {}
        loser = row.get('loser') or {}
        a = audit(row)
        rows.append({
            'pair_id': pid,
            'source': pair_source(row),
            'failure_tag': failure_tag(row),
            'in_canonical_ready500': pid in canonical_ids,
            'in_v12b_report': pid in v12b_ids,
            'in_s_fail': pid in s_fail_ids,
            'reviewed': bool(a.get('reviewed')),
            'written_reason_nonempty': bool(str(a.get('written_reason') or row.get('written_reason') or '').strip()),
            'medium_hard': bool(a.get('medium_hard', row.get('medium_hard', False))),
            'prefix_len': condition.get('prefix_len'),
            'prediction_start_frame': condition.get('prediction_start_frame'),
            'prefix_exists': repo_path(condition.get('prefix_video_path'), args.repo_root).exists(),
            'winner_path_exists': repo_path(winner.get('full_video_path') or winner.get('future_video_path'), args.repo_root).exists(),
            'loser_path_exists': repo_path(loser.get('full_video_path') or loser.get('future_video_path'), args.repo_root).exists(),
            'future_only_indices_present': bool(row.get('loss_frame_indices') or row.get('reward_frame_indices') or winner.get('latent_loss_indices') or loser.get('latent_loss_indices')),
            'affected_region': has_region(row),
            'affected_time_span': has_time(row),
            'status': 'READY' if pid not in s_fail_ids and bool(a.get('reviewed')) else 'CHECK',
        })
    fieldnames = list(rows[0].keys()) if rows else ['pair_id']
    with (out / 's_pass4_readiness.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader(); w.writerows(rows)
    warm = find_warm_start()
    with (out / 'warm_start_inventory.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(warm.keys()))
        w.writeheader(); w.writerow(warm)
    status = 'S_PASS4_READY' if len(pairs) == 4 and all(r['status'] == 'READY' for r in rows) else 'S_PASS4_CHECK_REQUIRED'
    lines = [
        f'Current Status: {status}', '',
        '# v12c Setup Summary', '',
        f'- S_pass manifest: `{s_pass_path}`',
        f'- S_pass count: `{len(pairs)}`',
        f'- Source breakdown: `{dict(Counter(r["source"] for r in rows))}`',
        f'- Failure breakdown: `{dict(Counter(r["failure_tag"] for r in rows))}`',
        f'- S_fail contamination count: `{sum(1 for r in rows if r["in_s_fail"])}`',
        f'- Warm start available: `{warm["warm_start_available"]}`',
        f'- Warm start path: `{warm["checkpoint_path"]}`',
        f'- Warm start LoRA params: `{warm["param_count"]}`',
    ]
    (out / 'setup_summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'status': status, 's_pass_count': len(pairs), 'warm_start': warm}, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
