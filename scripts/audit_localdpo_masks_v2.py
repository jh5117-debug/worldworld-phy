from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from cam_physgeo.dpo.localdpo_mask import audit_pairs_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', default='reports/dpo_preference_protocol_v2/localdpo_ready_pairs_v2.jsonl')
    parser.add_argument('--out_dir', default='reports/localdpo_mask_v2')
    args = parser.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = audit_pairs_jsonl(args.pairs)
    keys = sorted({k for r in rows for k in r})
    with (out / 'mask_audit.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(rows)
    usable = [r for r in rows if r['status'] == 'ok' and r['spatial_mask_available'] and not r['fallback_time_only']]
    time_only = [r for r in rows if r['fallback_time_only']]
    summary = {
        'input_pairs': args.pairs,
        'total_pairs': len(rows),
        'usable_spatial_time_masks': len(usable),
        'time_only_fallback': len(time_only),
        'invalid': sum(1 for r in rows if r['status'] != 'ok'),
        'mean_local_mask_ratio': sum(float(r['local_mask_ratio']) for r in rows) / max(1, len(rows)),
        'min_local_mask_ratio': min([float(r['local_mask_ratio']) for r in rows] or [0.0]),
        'max_local_mask_ratio': max([float(r['local_mask_ratio']) for r in rows] or [0.0]),
    }
    (out / 'localdpo_ready_pairs_spatial_v2.jsonl').write_text(Path(args.pairs).read_text(encoding='utf-8'), encoding='utf-8')
    (out / 'mask_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True), encoding='utf-8')
    lines = [
        '# LocalDPO Spatial Mask v2 Summary',
        '',
        'Current Status: {}'.format('PASS' if summary['usable_spatial_time_masks'] >= 20 else 'BLOCKED'),
        '',
        '- Total Type A pairs audited: {}'.format(summary['total_pairs']),
        '- Usable spatial+time masks: {}'.format(summary['usable_spatial_time_masks']),
        '- Time-only fallbacks: {}'.format(summary['time_only_fallback']),
        '- Invalid masks: {}'.format(summary['invalid']),
        '- Mean local mask ratio: {:.6f}'.format(summary['mean_local_mask_ratio']),
        '- Min local mask ratio: {:.6f}'.format(summary['min_local_mask_ratio']),
        '- Max local mask ratio: {:.6f}'.format(summary['max_local_mask_ratio']),
        '',
        'Mask mapping uses raw frames 5-80 as future and maps them to latent temporal slots using stride 4. Prefix frames are excluded.',
    ]
    (out / 'mask_summary.md').write_text('
'.join(lines) + '
', encoding='utf-8')
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
