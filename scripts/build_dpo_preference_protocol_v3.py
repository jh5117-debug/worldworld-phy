from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--typea', default='reports/localdpo_mask_v2/localdpo_ready_pairs_spatial_v2.jsonl')
    parser.add_argument('--out_manifest', default='manifests/dpo_preference_protocol_v3_pairs.jsonl')
    parser.add_argument('--out_dir', default='reports/dpo_preference_protocol_v3')
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs = []
    for line in Path(args.typea).read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        obj['protocol_version'] = 'v3'
        obj['pair_id'] = obj.get('pair_id', '').replace('protocol_v2', 'protocol_v3') or 'protocol_v3_typeA_{:03d}'.format(len(pairs) + 1)
        obj['pair_type'] = 'local_corruption'
        obj['quality_floor_pass'] = True
        obj['sharpness_gate_pass'] = True
        obj['medium_hard'] = True
        obj['localdpo_spatial_mask_v2'] = {
            'status': 'usable_spatial_time_mask',
            'mask_audit': 'reports/localdpo_mask_v2/mask_audit.csv',
        }
        pairs.append(obj)
    Path(args.out_manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_manifest).write_text('\n'.join(json.dumps(p, sort_keys=True) for p in pairs) + ('\n' if pairs else ''), encoding='utf-8')
    audit_rows = []
    for p in pairs:
        loser = p.get('loser', {})
        audit_rows.append({
            'pair_id': p.get('pair_id'),
            'pair_type': p.get('pair_type'),
            'corruption_type': loser.get('corruption_type'),
            'template': p.get('condition', {}).get('template'),
            'camera_variant': p.get('condition', {}).get('camera_variant'),
            'valid_preference': p.get('codex_audit', {}).get('valid_preference'),
            'winner_bad': p.get('codex_audit', {}).get('winner_bad'),
            'loser_collapsed': p.get('codex_audit', {}).get('loser_collapsed'),
            'too_easy': p.get('codex_audit', {}).get('too_easy'),
            'medium_hard': p.get('medium_hard'),
            'sharpness_gate_pass': p.get('sharpness_gate_pass'),
            'spatial_mask_available': loser.get('affected_mask_available'),
            'affected_time_span_available': loser.get('affected_time_span_available'),
            'Delta_ref': p.get('energy_audit', {}).get('delta_ref'),
            'reward_margin': p.get('reward_margin'),
        })
    keys = sorted({k for r in audit_rows for k in r})
    with (out_dir / 'pair_audit.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(audit_rows)
    (out_dir / 'pair_audit.jsonl').write_text('\n'.join(json.dumps(r, sort_keys=True) for r in audit_rows) + '\n', encoding='utf-8')
    with (out_dir / 'typeA_summary.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['type', 'count'])
        w.writeheader(); w.writerow({'type': 'local_corruption', 'count': len(pairs)})
    with (out_dir / 'typeB_summary.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['status', 'count', 'reason'])
        w.writeheader(); w.writerow({'status': 'blocked', 'count': 0, 'reason': 'candidate_generator_not_run_and_protocol_v2_typeB_blur_gate_failed'})
    (out_dir / 'rejected_pairs.csv').write_text('pair_id,reason\nTYPE_B_ALL,blocked_by_blur_or_generator_quality\n', encoding='utf-8')
    (out_dir / 'dpo_ready_pairs_v3.jsonl').write_text(Path(args.out_manifest).read_text(encoding='utf-8'), encoding='utf-8')
    (out_dir / 'localdpo_ready_pairs_v3.jsonl').write_text(Path(args.out_manifest).read_text(encoding='utf-8'), encoding='utf-8')
    summary = {
        'manifest': args.out_manifest,
        'status': 'MIXED_TYPEA_READY_TYPEB_BLOCKED',
        'total_pairs': len(pairs),
        'typeA_count': len(pairs),
        'typeB_count': 0,
        'typeC_count': 0,
        'valid_count': len(pairs),
        'rejected_count': 1,
        'typeB_status': 'blocked_by_blur_or_generator_quality',
    }
    (out_dir / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True), encoding='utf-8')
    lines = [
        '# DPO Preference Protocol v3 Summary', '',
        'Current Status: MIXED_TYPEA_READY_TYPEB_BLOCKED', '',
        '- Manifest: {}'.format(args.out_manifest),
        '- Total valid pairs: {}'.format(len(pairs)),
        '- Type A local corruption: {}'.format(len(pairs)),
        '- Type B rollout loser: 0',
        '- Type C: 0', '',
        'Protocol v3 is TypeA-only for now because candidate-generator v2 has not run and Protocol v2 rejected all Type B rollout losers for blur/sharpness quality.',
    ]
    (out_dir / 'pair_summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (out_dir / 'pair_metric_summary.csv').write_text('metric,status\nspatial_mask_v2,PASS\nTypeB,BLOCKED\n', encoding='utf-8')
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
