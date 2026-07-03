
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.dpo.winner_anchor_cache_builder import sha256_file, tensor_tree_finite


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        f.flush()


def _load_index(cache_root: Path) -> list[dict[str, Any]]:
    index = cache_root / 'cache_index.jsonl'
    if not index.exists():
        raise FileNotFoundError(index)
    return [json.loads(line) for line in index.read_text().splitlines() if line.strip()]


def validate_cache(cache_root: str | Path, output: str | Path) -> dict[str, Any]:
    root = Path(cache_root)
    rows = _load_index(root)
    out_rows: list[dict[str, Any]] = []
    fieldnames = [
        'pair_id', 'status', 'tensor_exists', 'sha256_match', 'payload_loads', 'winner_present', 'loser_present',
        'winner_finite', 'loser_finite', 'E_ref_winner_finite', 'E_ref_loser_finite', 'same_seed_noise_id_present',
        'actual_sigma_present', 'used_window_frames', 'prefix_len', 'prediction_start_frame', 'future_mask_nonempty',
        'reviewed', 'error_reason',
    ]
    pass_count = 0
    fail_count = 0
    seen: set[str] = set()
    for row in rows:
        pair_id = str(row.get('pair_id', ''))
        result: dict[str, Any] = {name: '' for name in fieldnames}
        result.update({'pair_id': pair_id, 'status': 'FAIL', 'error_reason': ''})
        errors: list[str] = []
        payload = None
        try:
            if not pair_id or pair_id in seen:
                errors.append('missing_or_duplicate_pair_id')
            seen.add(pair_id)
            tensor_rel = row.get('cache_tensor_path', '')
            tensor_path = root / str(tensor_rel)
            result['tensor_exists'] = tensor_path.exists()
            if not tensor_path.exists():
                errors.append('missing_tensor')
            else:
                result['sha256_match'] = sha256_file(tensor_path) == row.get('sha256')
                if not result['sha256_match']:
                    errors.append('sha256_mismatch')
                payload = torch.load(tensor_path, map_location='cpu')
                result['payload_loads'] = True
            if payload is not None:
                result['winner_present'] = 'winner' in payload
                result['loser_present'] = 'loser' in payload
                if not result['winner_present']:
                    errors.append('winner_missing')
                if not result['loser_present']:
                    errors.append('loser_missing')
                result['winner_finite'] = tensor_tree_finite(payload.get('winner', {}))
                result['loser_finite'] = tensor_tree_finite(payload.get('loser', {}))
                if not result['winner_finite']:
                    errors.append('winner_nonfinite')
                if not result['loser_finite']:
                    errors.append('loser_nonfinite')
                result['same_seed_noise_id_present'] = 'same_seed_noise_id' in payload or bool(row.get('same_seed_noise_id') != '')
                result['actual_sigma_present'] = 'actual_sigma' in payload or bool(row.get('actual_sigma') != '')
                future_masks = []
                if isinstance(payload.get('winner'), dict):
                    future_masks.append(payload['winner'].get('latent_loss_indices', []))
                if isinstance(payload.get('loser'), dict):
                    future_masks.append(payload['loser'].get('latent_loss_indices', []))
                result['future_mask_nonempty'] = all(len(x) > 0 for x in future_masks) if future_masks else False
                if not result['future_mask_nonempty']:
                    errors.append('future_mask_empty')
            for key in ['E_ref_winner_cached', 'E_ref_loser_cached']:
                try:
                    val = float(row.get(key, 'nan'))
                    finite = bool(torch.isfinite(torch.tensor(val)).item())
                except Exception:
                    finite = False
                result[key.replace('_cached', '_finite')] = finite
                if not finite:
                    errors.append(f'{key}_nonfinite')
            result['used_window_frames'] = row.get('used_window_frames')
            result['prefix_len'] = row.get('prefix_len')
            result['prediction_start_frame'] = row.get('prediction_start_frame')
            if int(row.get('used_window_frames', -1)) != 49:
                errors.append('used_window_frames_not_49')
            if int(row.get('prefix_len', -1)) != 5:
                errors.append('prefix_len_not_5')
            if int(row.get('prediction_start_frame', -1)) != 5:
                errors.append('prediction_start_frame_not_5')
            reviewed = bool(row.get('codex_visual_audit_reviewed')) and bool(row.get('codex_visual_audit_is_dpo_ready'))
            result['reviewed'] = reviewed
            if not reviewed:
                errors.append('visual_review_missing')
        except Exception as exc:  # noqa: BLE001
            errors.append(repr(exc))
        if errors:
            fail_count += 1
            result['error_reason'] = ';'.join(errors)
        else:
            pass_count += 1
            result['status'] = 'PASS'
        out_rows.append(result)
    _write_csv(Path(output), out_rows, fieldnames)
    status = 'PAIR_CACHE_VALIDATION_PASS' if pass_count == len(rows) and pass_count > 0 else 'PAIR_CACHE_VALIDATION_FAIL'
    summary = {'status': status, 'rows': len(rows), 'pass': pass_count, 'fail': fail_count, 'cache_root': str(root), 'output': str(output)}
    summary_path = Path(output).with_name(Path(output).stem + '_summary.md')
    summary_path.write_text(
        'Current Status:\n' + status + '\n\n'
        '# v8m Pair Cache Validation Summary\n\n'
        f'- Rows: {len(rows)}\n'
        f'- PASS: {pass_count}\n'
        f'- FAIL: {fail_count}\n'
        f'- Cache root: `{root}`\n'
        f'- CSV: `{output}`\n',
        encoding='utf-8',
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Validate v8m reviewed pair cache.')
    parser.add_argument('--cache_root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    validate_cache(args.cache_root, args.output)


if __name__ == '__main__':
    main()
