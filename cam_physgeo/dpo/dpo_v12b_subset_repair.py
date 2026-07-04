from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + '\n')


def audit(row: dict[str, Any]) -> dict[str, Any]:
    return row.get('codex_visual_audit') or row.get('codex_audit') or {}


def condition_id(row: dict[str, Any]) -> str:
    c = row.get('condition') or {}
    return str(c.get('condition_id') or c.get('sample_id') or row.get('condition_id') or row.get('pair_id'))


def failure(row: dict[str, Any]) -> str:
    loser = row.get('loser') or {}
    return str(row.get('failure_tag') or loser.get('failure_type') or loser.get('corruption_type') or row.get('main_failure') or 'unknown')


def source(row: dict[str, Any]) -> str:
    pair_type = str(row.get('pair_type') or '')
    pair_source = str(row.get('pair_source') or row.get('source_protocol') or '')
    rollout_types = {'GT_C', 'B_C', 'M0_C', 'teacher_rollout'}
    if (
        row.get('is_rollout_derived')
        or pair_type in rollout_types
        or 'rollout' in pair_type.lower()
        or 'rollout' in pair_source.lower()
    ):
        return 'rollout'
    if (
        row.get('is_synthetic')
        or row.get('is_controlled_corruption')
        or 'synthetic' in pair_type.lower()
        or 'synthetic' in pair_source.lower()
    ):
        return 'synthetic'
    return str(row.get('pair_source') or row.get('pair_type') or 'other')


def has_region(row: dict[str, Any]) -> bool:
    loser = row.get('loser') or {}
    return bool(loser.get('affected_region') or loser.get('affected_mask'))


def has_time(row: dict[str, Any]) -> bool:
    loser = row.get('loser') or {}
    return bool(loser.get('affected_time_span') or row.get('loss_frame_indices'))


def is_clean(row: dict[str, Any]) -> bool:
    a = audit(row)
    return bool(a.get('reviewed')) and bool(a.get('is_dpo_ready', row.get('medium_hard', False))) and bool(a.get('medium_hard', row.get('medium_hard', False))) and not any(bool(a.get(k)) for k in ['too_subtle', 'too_blurry', 'too_collapsed', 'winner_bad']) and str(a.get('written_reason', '')).strip()


def score(row: dict[str, Any]) -> tuple[float, str]:
    a = audit(row)
    margin = float(row.get('reward_margin') or 0.0)
    s = margin
    if has_region(row): s += 0.20
    if has_time(row): s += 0.10
    if source(row) == 'rollout': s += 0.15
    if len(str(a.get('written_reason', ''))) > 60: s += 0.05
    return (-s, row.get('pair_id', ''))


def diverse_select(rows: list[dict[str, Any]], target: int, *, min_rollout: int = 0, min_synth: int = 0, prefer_local: bool = False) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used_conditions: set[str] = set()
    def try_add(candidates: list[dict[str, Any]], needed: int) -> None:
        nonlocal selected
        for row in candidates:
            if len(selected) >= target or needed <= 0:
                return
            cid = condition_id(row)
            if cid in used_conditions:
                continue
            selected.append(row); used_conditions.add(cid); needed -= 1
    ordered = sorted(rows, key=score)
    if min_rollout:
        try_add([r for r in ordered if source(r) == 'rollout'], min_rollout)
    if min_synth:
        try_add([r for r in ordered if source(r) == 'synthetic'], min_synth)
    pool = [r for r in ordered if (not prefer_local or has_region(r) or has_time(r))]
    try_add(pool, target - len(selected))
    if len(selected) < target:
        # permit duplicate conditions only as a final fallback, keeping score order.
        for row in ordered:
            if len(selected) >= target:
                break
            if row not in selected:
                selected.append(row)
    return selected[:target]


def write_subset_summary(path: Path, subsets: dict[str, list[dict[str, Any]]]) -> None:
    rows: list[dict[str, Any]] = []
    for name, items in subsets.items():
        rows.append({
            'subset': name,
            'count': len(items),
            'source_breakdown': json.dumps(Counter(source(r) for r in items), sort_keys=True),
            'failure_breakdown': json.dumps(Counter(failure(r) for r in items), sort_keys=True),
            'template_breakdown': json.dumps(Counter((r.get('condition') or {}).get('template', '') for r in items), sort_keys=True),
            'camera_motion_breakdown': json.dumps(Counter((r.get('condition') or {}).get('camera_motion', '') for r in items), sort_keys=True),
            'local_spatial_ready': sum(1 for r in items if has_region(r)),
            'local_time_ready': sum(1 for r in items if has_time(r) and not has_region(r)),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--canonical', required=True)
    p.add_argument('--train', required=True)
    p.add_argument('--val', required=True)
    p.add_argument('--output_dir', required=True)
    p.add_argument('--manifest_dir', required=True)
    args = p.parse_args(argv)
    out = Path(args.output_dir); man = Path(args.manifest_dir)
    canonical = [r for r in read_jsonl(args.canonical) if is_clean(r)]
    train = [r for r in read_jsonl(args.train) if is_clean(r)]
    val = [r for r in read_jsonl(args.val) if is_clean(r)]
    by_pair_id: dict[str, dict[str, Any]] = {}
    for row in canonical + train:
        by_pair_id[str(row.get('pair_id') or len(by_pair_id))] = row
    clean = sorted(by_pair_id.values(), key=score)
    s8 = diverse_select(clean, 8, min_rollout=2, min_synth=4)
    s16 = diverse_select(clean, 16, min_rollout=4, min_synth=8)
    local_pool = [r for r in clean if has_region(r) or has_time(r)]
    s8_local = diverse_select(local_pool, 8, min_synth=4, prefer_local=True)
    val_video = diverse_select(sorted(val, key=score), 4, min_rollout=1, min_synth=2)
    subsets = {
        's8_winner_anchor_clean': s8,
        's16_winner_curriculum': s16,
        's8_local_mask': s8_local,
        'val_video_4': val_video,
    }
    for name, rows in subsets.items():
        write_jsonl(man / f'{name}.jsonl', rows)
    write_subset_summary(out / 'subset_summary.csv', subsets)
    lines = ['Current Status: SUBSETS_READY', '', '# v12b Subset Repair Summary', '']
    for name, rows in subsets.items():
        lines += [f'## {name}', '', f'- Count: `{len(rows)}`', f'- Source: `{dict(Counter(source(r) for r in rows))}`', f'- Local spatial ready: `{sum(1 for r in rows if has_region(r))}`', f'- Local time-only ready: `{sum(1 for r in rows if has_time(r) and not has_region(r))}`', '']
    (out / 'subset_summary.md').write_text('\n'.join(lines) + '\n')

if __name__ == '__main__':
    main()
