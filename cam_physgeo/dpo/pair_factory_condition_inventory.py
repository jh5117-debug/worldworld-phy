
from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

PATTERNS = [
    '*screen16*v2v5*.jsonl', '*prefix5*.jsonl', '*quant*benchmark*.jsonl',
    '*stageA*v2v5*.jsonl', '*dpo*pair*.jsonl', '*dpo_ready*.jsonl',
    '*conditions*.jsonl', '*generated_manifest*.csv',
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_path(value: Any, root: Path) -> str:
    if value is None:
        return ''
    text = str(value).strip()
    if not text:
        return ''
    if text.startswith('file://'):
        text = text[7:]
    p = Path(text)
    return str(p if p.is_absolute() else root / p)


def exists_path(value: Any, root: Path) -> bool:
    text = resolve_path(value, root)
    return bool(text) and Path(text).exists()


def looks_like_path(text: Any) -> bool:
    if text is None:
        return False
    s = str(text)
    return '/' in s or s.endswith(('.txt', '.json', '.mp4', '.npy', '.jpg', '.png'))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
    return rows


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open('r', encoding='utf-8', newline='') as f:
        return [dict(r) for r in csv.DictReader(f)]


def find_manifests(roots: list[str]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        base = Path(root)
        if not base.exists():
            continue
        if base.is_file():
            names = [base]
        else:
            names = []
            for dirpath, dirnames, filenames in os.walk(base):
                # Avoid descending into obvious binary-heavy output trees unless files match at this level.
                dirnames[:] = [d for d in dirnames if d not in {'__pycache__', '.git'}]
                for name in filenames:
                    if any(fnmatch.fnmatch(name, pat) for pat in PATTERNS):
                        names.append(Path(dirpath) / name)
        out.extend(names)
    return sorted(set(out))


def nested(row: dict[str, Any], key: str) -> dict[str, Any]:
    val = row.get(key)
    return val if isinstance(val, dict) else {}


def first(*values: Any) -> Any:
    for v in values:
        if v is not None and str(v) != '':
            return v
    return ''


def infer_seed(sample_id: str, row: dict[str, Any]) -> str:
    for key in ('seed', 'simulator_seed', 'scene_group_id'):
        if row.get(key) not in (None, ''):
            return str(row.get(key))
    if '_seed' in sample_id:
        return sample_id.rsplit('_seed', 1)[-1]
    return ''


def normalize_row(row: dict[str, Any], source_manifest: str) -> dict[str, Any] | None:
    cond = nested(row, 'condition')
    winner = nested(row, 'winner')
    sample_id = str(first(row.get('sample_id'), cond.get('sample_id'), row.get('benchmark_id'), row.get('condition_id'), row.get('pair_id')))
    if not sample_id:
        return None
    condition_id = str(first(row.get('condition_id'), cond.get('condition_id'), cond.get('full_condition_hash'), sample_id))
    template = str(first(row.get('template'), row.get('benchmark_template'), cond.get('template'), row.get('model_template'), 'unknown'))
    camera_motion = str(first(row.get('camera_motion'), row.get('camera_variant'), cond.get('camera_motion'), cond.get('camera_variant'), 'unknown'))
    prefix_len = int(first(row.get('prefix_len'), cond.get('prefix_len'), 5) or 5)
    prediction_start = int(first(row.get('prediction_start_frame'), cond.get('prediction_start_frame'), 5) or 5)
    prompt = first(row.get('prompt'), row.get('prompt_path'), cond.get('prompt'), cond.get('prompt_path'))
    prompt_path = first(row.get('prompt_path'), cond.get('prompt_path'), prompt if looks_like_path(prompt) else '')
    image_path = first(row.get('image_path'), row.get('condition_image_path'), row.get('image'), cond.get('image_path'), cond.get('image'))
    poses_path = first(row.get('poses_path'), row.get('poses'), cond.get('poses_path'), cond.get('poses'))
    intrinsics_path = first(row.get('intrinsics_path'), row.get('intrinsics'), cond.get('intrinsics_path'), cond.get('intrinsics'))
    prefix_video = first(row.get('prefix_video_path'), row.get('prefix_video'), cond.get('prefix_video_path'))
    gt_full = first(row.get('gt_full_video_path'), row.get('target_video'), row.get('full_target_video_path'), row.get('video'), cond.get('gt_full_video_path'), winner.get('full_video_path'), winner.get('video'))
    gt_future = first(row.get('gt_future_video_path'), row.get('gt_future'), cond.get('gt_future_video_path'), winner.get('future_video_path'))
    fps = first(row.get('fps'), cond.get('fps'), 16.0)
    height = first(row.get('height'), cond.get('height'), 480)
    width = first(row.get('width'), cond.get('width'), 832)
    num_frames = first(row.get('num_frames'), cond.get('num_frames'), 81)
    return {
        'condition_id': condition_id,
        'sample_id': sample_id,
        'template': template,
        'camera_motion': camera_motion,
        'prefix_len': prefix_len,
        'prediction_start_frame': prediction_start,
        'prefix_video_path': prefix_video,
        'image_path': image_path,
        'prompt': prompt,
        'prompt_path': prompt_path,
        'poses_path': poses_path,
        'intrinsics_path': intrinsics_path,
        'gt_full_video_path': gt_full,
        'gt_future_video_path': gt_future,
        'source_manifest': source_manifest,
        'source_pair_id': str(row.get('pair_id', row.get('old_pair_id', ''))),
        'seed': infer_seed(sample_id, row),
        'fps': float(fps or 16.0),
        'num_frames': int(float(num_frames or 81)),
        'height': int(float(height or 480)),
        'width': int(float(width or 832)),
    }


def ffprobe_frames(path: str, timeout: int = 8) -> int | None:
    if not path or not Path(path).exists():
        return None
    cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames',
        '-show_entries', 'stream=nb_read_frames', '-of', 'default=nokey=1:noprint_wrappers=1', path,
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=timeout, text=True).strip().splitlines()
        for line in out:
            if line and line != 'N/A':
                return int(float(line))
    except Exception:
        return None
    return None


def cut_video(full: str, out: str, start_frame: int, frames: int, fps: float) -> bool:
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    if Path(out).exists() and Path(out).stat().st_size > 0:
        return True
    if shutil.which('ffmpeg'):
        expr = f"select='between(n,{start_frame},{start_frame + frames - 1})',setpts=N/FRAME_RATE/TB"
        cmd = ['ffmpeg', '-y', '-v', 'error', '-i', full, '-vf', expr, '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', str(fps), out]
        try:
            subprocess.check_call(cmd, timeout=60)
            return Path(out).exists() and Path(out).stat().st_size > 0
        except Exception:
            pass
    try:
        import cv2

        cap = cv2.VideoCapture(full)
        if not cap.isOpened():
            return False
        src_fps = cap.get(cv2.CAP_PROP_FPS) or fps or 16.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        if width <= 0 or height <= 0:
            cap.release()
            return False
        writer = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*'mp4v'), float(fps or src_fps), (width, height))
        if not writer.isOpened():
            cap.release()
            return False
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_frame))
        written = 0
        for _ in range(int(frames)):
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(frame)
            written += 1
        writer.release()
        cap.release()
        return written > 0 and Path(out).exists() and Path(out).stat().st_size > 0
    except Exception:
        return False


def assess_condition(cond: dict[str, Any], root: Path, recover_root: Path, do_recover: bool) -> tuple[dict[str, Any], dict[str, Any] | None]:
    row = dict(cond)
    errors: list[str] = []
    prefix_abs = resolve_path(row.get('prefix_video_path'), root)
    future_abs = resolve_path(row.get('gt_future_video_path'), root)
    full_abs = resolve_path(row.get('gt_full_video_path'), root)
    prompt_exists = True if row.get('prompt') and not looks_like_path(row.get('prompt')) else exists_path(row.get('prompt_path') or row.get('prompt'), root)
    checks = {
        'prefix_exists': Path(prefix_abs).exists() if prefix_abs else False,
        'gt_full_exists': Path(full_abs).exists() if full_abs else False,
        'gt_future_exists': Path(future_abs).exists() if future_abs else False,
        'image_exists': exists_path(row.get('image_path'), root),
        'prompt_exists': prompt_exists,
        'poses_exists': exists_path(row.get('poses_path'), root),
        'intrinsics_exists': exists_path(row.get('intrinsics_path'), root),
    }
    for key, ok in checks.items():
        if not ok:
            errors.append(key.replace('_exists', '_missing'))
    recover_method = 'existing'
    if (not checks['prefix_exists'] or not checks['gt_future_exists']) and checks['gt_full_exists']:
        recover_method = 'cut_from_full'
        sample = ''.join(ch if ch.isalnum() or ch in {'-', '_'} else '_' for ch in str(row['sample_id']))
        out_dir = recover_root / sample
        if not checks['prefix_exists']:
            row['prefix_video_path'] = str((out_dir / 'prefix_len5.mp4').relative_to(root))
        if not checks['gt_future_exists']:
            row['gt_future_video_path'] = str((out_dir / 'clean_future_5_80.mp4').relative_to(root))
        if do_recover:
            prefix_ok = cut_video(full_abs, resolve_path(row['prefix_video_path'], root), 0, 5, float(row.get('fps') or 16.0))
            future_ok = cut_video(full_abs, resolve_path(row['gt_future_video_path'], root), 5, 76, float(row.get('fps') or 16.0))
            checks['prefix_exists'] = prefix_ok
            checks['gt_future_exists'] = future_ok
        else:
            checks['prefix_exists'] = Path(resolve_path(row['prefix_video_path'], root)).exists()
            checks['gt_future_exists'] = Path(resolve_path(row['gt_future_video_path'], root)).exists()
        errors = [e for e in errors if e not in {'prefix_missing', 'gt_future_missing'}]
        if not checks['prefix_exists']:
            errors.append('prefix_missing')
        if not checks['gt_future_exists']:
            errors.append('gt_future_missing')
    prefix_frames = ffprobe_frames(resolve_path(row.get('prefix_video_path'), root)) if checks['prefix_exists'] else None
    future_frames = ffprobe_frames(resolve_path(row.get('gt_future_video_path'), root)) if checks['gt_future_exists'] else None
    full_frames = ffprobe_frames(resolve_path(row.get('gt_full_video_path'), root)) if checks['gt_full_exists'] else None
    if prefix_frames is not None and prefix_frames < 5:
        errors.append('prefix_frame_count_lt5')
    if future_frames is not None and future_frames < 70:
        errors.append('future_frame_count_lt70')
    runnable = not errors and int(row.get('prefix_len', 5)) == 5 and int(row.get('prediction_start_frame', 5)) == 5
    row.update({
        'recover_method': recover_method,
        'status': 'runnable' if runnable else ('recoverable' if checks['gt_full_exists'] else 'not_runnable'),
        'prefix_frame_count': prefix_frames if prefix_frames is not None else '',
        'future_frame_count': future_frames if future_frames is not None else '',
        'full_frame_count': full_frames if full_frames is not None else '',
        'not_runnable_reason': ';'.join(dict.fromkeys(errors)),
    })
    recoverable = row if row['status'] == 'recoverable' else None
    return row, recoverable


def load_manifest(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == '.csv':
        return read_csv(path)
    return read_jsonl(path)


def run_inventory(args: argparse.Namespace) -> dict[str, Any]:
    root = repo_root()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    recover_root = root / 'local_assets/dpo_pair_factory_v10/recovered_conditions'
    manifest_paths = find_manifests(list(args.roots))
    inv_rows: list[dict[str, Any]] = []
    condition_rows: list[dict[str, Any]] = []
    recoverable_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in manifest_paths:
        try:
            raw_rows = load_manifest(path)
        except Exception as exc:
            inv_rows.append({'manifest_path': str(path), 'total_rows': 0, 'condition_like_rows': 0, 'pair_like_rows': 0, 'runnable_count': 0, 'recoverable_count': 0, 'not_runnable_reason': f'load_error:{exc!r}'})
            continue
        normalized = [normalize_row(r, str(path)) for r in raw_rows]
        normalized = [r for r in normalized if r is not None]
        runnable = 0
        recoverable = 0
        reasons: dict[str, int] = {}
        templates: dict[str, int] = {}
        cameras: dict[str, int] = {}
        for cond in normalized:
            assessed, rec = assess_condition(cond, root, recover_root, bool(args.recover))
            templates[str(assessed.get('template', 'unknown'))] = templates.get(str(assessed.get('template', 'unknown')), 0) + 1
            cameras[str(assessed.get('camera_motion', 'unknown'))] = cameras.get(str(assessed.get('camera_motion', 'unknown')), 0) + 1
            if assessed['status'] == 'runnable':
                runnable += 1
                key = str(assessed.get('sample_id'))
                if key not in seen:
                    seen.add(key)
                    condition_rows.append(assessed)
            elif rec:
                recoverable += 1
                recoverable_rows.append(rec)
            reason = assessed.get('not_runnable_reason') or 'ok'
            reasons[reason] = reasons.get(reason, 0) + 1
        inv_rows.append({
            'manifest_path': str(path),
            'total_rows': len(raw_rows),
            'condition_like_rows': len(normalized),
            'pair_like_rows': sum(1 for r in raw_rows if isinstance(r, dict) and ('winner' in r or 'loser' in r)),
            'runnable_count': runnable,
            'recoverable_count': recoverable,
            'template_distribution': json.dumps(templates, sort_keys=True),
            'camera_motion_distribution': json.dumps(cameras, sort_keys=True),
            'not_runnable_reason': json.dumps(reasons, sort_keys=True),
        })
    condition_rows = sorted(condition_rows, key=lambda r: (str(r.get('template')), str(r.get('sample_id'))))
    target = Path(args.target_manifest)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w', encoding='utf-8') as f:
        for row in condition_rows:
            f.write(json.dumps(row, sort_keys=True) + '\n')
    with (out_dir / 'recoverable_rows.jsonl').open('w', encoding='utf-8') as f:
        for row in recoverable_rows:
            f.write(json.dumps(row, sort_keys=True) + '\n')
    fieldnames = ['manifest_path','total_rows','condition_like_rows','pair_like_rows','runnable_count','recoverable_count','template_distribution','camera_motion_distribution','not_runnable_reason']
    with (out_dir / 'prefix5_condition_inventory.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator='\n')
        w.writeheader(); w.writerows(inv_rows)
    templates: dict[str, int] = {}
    cameras: dict[str, int] = {}
    for row in condition_rows:
        templates[str(row.get('template', 'unknown'))] = templates.get(str(row.get('template', 'unknown')), 0) + 1
        cameras[str(row.get('camera_motion', 'unknown'))] = cameras.get(str(row.get('camera_motion', 'unknown')), 0) + 1
    status = 'CONDITION_INVENTORY_READY_100' if len(condition_rows) >= 100 else ('CONDITION_INVENTORY_READY_50' if len(condition_rows) >= 50 else ('CONDITION_INVENTORY_PARTIAL' if condition_rows else 'CONDITION_INVENTORY_BLOCKED'))
    summary = {
        'status': status,
        'manifest_count': len(manifest_paths),
        'recovered_runnable_conditions': len(condition_rows),
        'recoverable_rows': len(recoverable_rows),
        'target_manifest': str(target),
        'templates': templates,
        'camera_motions': cameras,
    }
    (out_dir / 'prefix5_condition_inventory_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (out_dir / 'prefix5_condition_inventory.md').write_text(
        'Current Status:\n' + status + '\n\n'
        '# DPO Pair Factory v10 Condition Inventory\n\n'
        f"- Manifest files scanned: {len(manifest_paths)}\n"
        f"- Unique runnable prefix5 conditions: {len(condition_rows)}\n"
        f"- Recoverable rows not included: {len(recoverable_rows)}\n"
        f"- Target manifest: `{target}`\n"
        f"- Templates: `{json.dumps(templates, sort_keys=True)}`\n"
        f"- Camera motions: `{json.dumps(cameras, sort_keys=True)}`\n",
        encoding='utf-8',
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Recover runnable prefix5/V2V-5 conditions for DPO Pair Factory v10.')
    parser.add_argument('--roots', nargs='+', required=True)
    parser.add_argument('--output_dir', required=True)
    parser.add_argument('--target_manifest', required=True)
    parser.add_argument('--recover', action='store_true', default=True)
    args = parser.parse_args(argv)
    run_inventory(args)


if __name__ == '__main__':
    main()
