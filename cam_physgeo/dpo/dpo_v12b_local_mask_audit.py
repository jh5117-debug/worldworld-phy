
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    with p.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def audit_mask(row: dict[str, Any]) -> dict[str, Any]:
    loser = row.get('loser') or {}
    region = bool(loser.get('affected_region'))
    mask = bool(loser.get('affected_mask'))
    time = bool(loser.get('affected_time_span') or row.get('loss_frame_indices') or row.get('reward_frame_indices'))
    return {
        'pair_id': row.get('pair_id', ''),
        'affected_time_span': time,
        'affected_region': region,
        'affected_mask': mask,
        'spatial_mask_ready': region or mask,
        'time_only': time and not (region or mask),
        'localdpo_ready': time and (region or mask),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Audit LocalDPO mask readiness without training.')
    parser.add_argument('--pair_manifest', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--summary', required=True)
    args = parser.parse_args(argv)
    rows = [audit_mask(r) for r in read_jsonl(args.pair_manifest)]
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ['pair_id']
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader(); w.writerows(rows)
    total = len(rows)
    spatial = sum(1 for r in rows if r['spatial_mask_ready'])
    time_only = sum(1 for r in rows if r['time_only'])
    local = sum(1 for r in rows if r['localdpo_ready'])
    text = '\n'.join([
        'Current Status: LOCAL_MASK_AUDIT_READY', '',
        '# v12c LocalDPO Mask Audit', '',
        f'- Total pairs: `{total}`',
        f'- affected_time_span exists count: `{sum(1 for r in rows if r["affected_time_span"])}`',
        f'- affected_region exists count: `{sum(1 for r in rows if r["affected_region"])}`',
        f'- affected_mask exists count: `{sum(1 for r in rows if r["affected_mask"])}`',
        f'- spatial mask ready count: `{spatial}`',
        f'- time-only count: `{time_only}`',
        f'- local_mask_ratio: `{(local / total) if total else 0.0}`',
        f'- next LocalDPO probe possible: `{local > 0}`',
    ]) + '\n'
    Path(args.summary).write_text(text, encoding='utf-8')
    print(text)

if __name__ == '__main__':
    main()
