
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import cv2
import time
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.dpo.failure_diagnostics import _make_timestep_sample
from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy
from cam_physgeo.dpo.prefix5_dpo_dataset import decode_video_tensor, load_array, normalize_intrinsics, read_prompt
from cam_physgeo.dpo.winner_anchor_cache_builder import (
    _progress,
    append_csv,
    patch_t5_checkpoint_init,
    sha256_file,
    tensor_tree_finite,
    tensor_tree_shapes,
    to_cpu,
    write_jsonl,
)
from cam_physgeo.dpo.winner_anchor_only_runner import (
    _cfg,
    _prepare_winner_cached,
    cuda_stats,
    ensure_runtime_ready,
    is_reviewed_dpo_pair,
    reviewed_pairs,
)


def _sanitize(name: str) -> str:
    return ''.join(ch if ch.isalnum() or ch in {'-', '_', '.'} else '_' for ch in name)




def _resolve_repo_path(path: str | Path, repo_root: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(repo_root) / p


def _ensure_full_from_prefix_future(pair: dict[str, Any], *, role: str, repo_root: str | Path) -> str | None:
    condition = pair.get('condition') or {}
    branch = pair.get(role) or {}
    prefix = condition.get('prefix_video_path')
    future = branch.get('future_video_path')
    if not prefix or not future:
        return None
    pair_id = _sanitize(str(pair.get('pair_id') or 'pair'))
    out_dir = Path(repo_root) / 'local_assets' / 'dpo_training_sanity_v12' / 'recovered_full_videos'
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f'{pair_id}_{role}_full_from_prefix_future.mp4'
    if out.exists() and out.stat().st_size > 0:
        return str(out)
    prefix_path = _resolve_repo_path(prefix, repo_root)
    future_path = _resolve_repo_path(future, repo_root)
    if not prefix_path.exists() or not future_path.exists():
        return None

    fps = 16.0
    writer = None
    frame_size: tuple[int, int] | None = None
    frames_written = 0
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    try:
        for video_path in (prefix_path, future_path):
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise RuntimeError(f'cannot decode {video_path}')
            candidate_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            if candidate_fps > 1.0:
                fps = candidate_fps
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if writer is None:
                    height, width = frame.shape[:2]
                    frame_size = (width, height)
                    writer = cv2.VideoWriter(str(out), fourcc, fps, frame_size)
                    if not writer.isOpened():
                        raise RuntimeError(f'cannot open video writer for {out}')
                elif frame_size is not None and (frame.shape[1], frame.shape[0]) != frame_size:
                    frame = cv2.resize(frame, frame_size, interpolation=cv2.INTER_AREA)
                writer.write(frame)
                frames_written += 1
            cap.release()
        if writer is not None:
            writer.release()
        if frames_written <= 0 or not out.exists() or out.stat().st_size <= 0:
            raise RuntimeError('prefix+future reconstruction wrote no frames')
    except Exception:
        if writer is not None:
            writer.release()
        if out.exists():
            out.unlink()
        raise
    return str(out)

def _load_role_inputs(
    pair: dict[str, Any],
    *,
    role: str,
    repo_root: str | Path,
    frames: int,
    height: int,
    width: int,
    prefix_len: int,
    prediction_start_frame: int,
):
    if role not in {'winner', 'loser'}:
        raise ValueError(f'unsupported role={role}')
    if not is_reviewed_dpo_pair(pair):
        raise ValueError(f'pair is not reviewed DPO-ready: {pair.get("pair_id")}')
    audit = pair.get('codex_visual_audit') or pair.get('codex_audit') or {}
    if not audit.get('reviewed', audit.get('valid_preference', False)):
        raise ValueError(f'pair has no reviewed visual audit: {pair.get("pair_id")}')
    condition = pair.get('condition') or {}
    branch = pair.get(role) or {}
    if int(condition.get('prefix_len', prefix_len)) != int(prefix_len):
        raise ValueError('prefix_len mismatch; refusing silent fallback')
    if int(condition.get('prediction_start_frame', prediction_start_frame)) != int(prediction_start_frame):
        raise ValueError('prediction_start_frame mismatch; refusing silent fallback')
    if int(frames) <= int(prefix_len):
        raise ValueError('used_window_frames must include prefix and future frames')
    video_path = branch.get('full_video_path') or branch.get('video')
    if role == 'winner' and not video_path:
        video_path = condition.get('gt_full_video_path') or condition.get('full_video_path')
    if not video_path:
        video_path = _ensure_full_from_prefix_future(pair, role=role, repo_root=repo_root)
    if not video_path:
        raise ValueError(f'{role} full_video_path missing and prefix+future reconstruction unavailable; refusing image-only path')
    video, meta = decode_video_tensor(video_path, repo_root=repo_root, num_frames=int(frames), height=int(height), width=int(width))
    source_height = int(meta.get('source_height') or height)
    source_width = int(meta.get('source_width') or width)
    poses_path = condition.get('poses') or condition.get('poses_path')
    intrinsics_path = condition.get('intrinsics') or condition.get('intrinsics_path')
    if not poses_path or not intrinsics_path:
        raise KeyError('poses/intrinsics')
    poses = torch.from_numpy(load_array(poses_path, repo_root=repo_root, num_frames=int(frames)).astype('float32')).float()
    intrinsics = torch.from_numpy(
        normalize_intrinsics(
            load_array(intrinsics_path, repo_root=repo_root, num_frames=int(frames)),
            source_width=source_width,
            source_height=source_height,
        )
    ).float()
    prompt = read_prompt(condition.get('prompt_path') or condition.get('prompt'), repo_root=repo_root)
    if not prompt.strip():
        raise ValueError('empty prompt')
    return video, prompt, poses, intrinsics, source_height, source_width


def _payload_for(prepared: Any) -> dict[str, Any]:
    return {
        'target': to_cpu(prepared.target),
        'noisy_latent': to_cpu(prepared.noisy_latent),
        'context': to_cpu(prepared.context),
        'y': to_cpu(prepared.y),
        'dit_cond': to_cpu(prepared.dit_cond),
        'seq_len': int(prepared.seq_len),
        'latent_loss_indices': list(prepared.latent_loss_indices),
    }


def _load_reviewed_pairs(path: str | Path, limit: int) -> list[dict[str, Any]]:
    pairs = reviewed_pairs(path, limit)
    if not pairs:
        raise RuntimeError(f'no reviewed pairs found in {path}')
    return pairs


def build_pair_cache(args: argparse.Namespace) -> dict[str, Any]:
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)
    report = Path(args.report)
    progress_path = Path(args.progress) if args.progress else report.with_name(report.stem + '_progress.jsonl')
    for path in [report, progress_path, out_root / 'cache_index.jsonl']:
        if path.exists():
            path.unlink()
    if torch.cuda.is_available():
        torch.cuda.set_device(int(args.gpu))
        torch.cuda.reset_peak_memory_stats()
    device = f'cuda:{int(args.gpu)}' if torch.cuda.is_available() else 'cpu'
    pairs = _load_reviewed_pairs(args.pair_manifest, int(args.num_pairs))
    fieldnames = [
        'pair_id', 'cache_status', 'cache_tensor_path', 'sha256', 'E_ref_winner_cached', 'E_ref_loser_cached',
        'Delta_ref', 'timestep', 'timestep_index', 'actual_sigma', 'same_seed_noise_id', 'used_window_frames',
        'prefix_len', 'prediction_start_frame', 'winner_latent_loss_indices', 'loser_latent_loss_indices',
        'winner_target_shape', 'loser_target_shape', 'finite', 'reviewed', 'seconds', 'allocated_gb', 'reserved_gb',
        'max_allocated_gb', 'max_reserved_gb', 'error_reason',
    ]
    _progress(progress_path, stage='start', requested_pairs=int(args.num_pairs), output_root=str(out_root))
    cfg = _cfg(
        args.config,
        frames=int(args.used_window_frames),
        height=int(args.height),
        width=int(args.width),
        runtime_device=str(args.runtime_device),
        gradient_checkpointing=True,
    )
    cfg['dpo_policy_loader_mode'] = str(getattr(args, 'loader_mode', 'safe_wan_policy_only'))
    if cfg['dpo_policy_loader_mode'] == 'safe_wan_policy_only':
        cfg['dpo_safe_loader_heartbeat_path'] = str(progress_path.with_name(progress_path.stem + '_safe_loader.jsonl'))
    _progress(progress_path, stage='before_backend_load', device=device)
    backend = LingBotFastDpoEnergy(cfg, device=device, prefix_len=int(args.prefix_len))
    _progress(progress_path, stage='after_policy_load', **cuda_stats())
    patch_t5_checkpoint_init(progress_path)
    _progress(progress_path, stage='before_runtime_ready_fastinit', **cuda_stats())
    ensure_runtime_ready(backend)
    _progress(progress_path, stage='after_runtime_ready', **cuda_stats())
    index_path = out_root / 'cache_index.jsonl'
    success = 0
    fail = 0
    for idx, pair in enumerate(pairs):
        start = time.time()
        pair_id = str(pair.get('pair_id') or f'pair_{idx:04d}')
        row: dict[str, Any] = {name: '' for name in fieldnames}
        row.update({
            'pair_id': pair_id,
            'cache_status': 'FAILED',
            'used_window_frames': int(args.used_window_frames),
            'prefix_len': int(args.prefix_len),
            'prediction_start_frame': int(args.prediction_start_frame),
            'finite': False,
            'reviewed': False,
        })
        try:
            _progress(progress_path, stage='pair_start', pair_id=pair_id, pair_index=idx, **cuda_stats())
            w_video, prompt, poses, intrinsics, sh, sw = _load_role_inputs(
                pair,
                role='winner',
                repo_root=args.repo_root,
                frames=int(args.used_window_frames),
                height=int(args.height),
                width=int(args.width),
                prefix_len=int(args.prefix_len),
                prediction_start_frame=int(args.prediction_start_frame),
            )
            l_video, _prompt2, poses2, intrinsics2, sh2, sw2 = _load_role_inputs(
                pair,
                role='loser',
                repo_root=args.repo_root,
                frames=int(args.used_window_frames),
                height=int(args.height),
                width=int(args.width),
                prefix_len=int(args.prefix_len),
                prediction_start_frame=int(args.prediction_start_frame),
            )
            _progress(progress_path, stage='after_load_pair_inputs', pair_id=pair_id, pair_index=idx, **cuda_stats())
            ts = _make_timestep_sample(backend, float(args.target_sigma))
            seed = int(args.seed) + idx * 997
            _progress(progress_path, stage='before_prepare_winner', pair_id=pair_id, pair_index=idx, **cuda_stats())
            winner_prepared = _prepare_winner_cached(
                backend,
                video=w_video,
                prompt=prompt,
                poses=poses,
                intrinsics=intrinsics,
                source_height=sh,
                source_width=sw,
                timestep_sample=ts,
                seed=seed,
                total_frames=int(args.used_window_frames),
            )
            _progress(progress_path, stage='after_prepare_winner', pair_id=pair_id, pair_index=idx, **cuda_stats())
            _progress(progress_path, stage='before_prepare_loser', pair_id=pair_id, pair_index=idx, **cuda_stats())
            loser_prepared = _prepare_winner_cached(
                backend,
                video=l_video,
                prompt=prompt,
                poses=poses2,
                intrinsics=intrinsics2,
                source_height=sh2,
                source_width=sw2,
                timestep_sample=ts,
                seed=seed,
                total_frames=int(args.used_window_frames),
            )
            _progress(progress_path, stage='after_prepare_loser', pair_id=pair_id, pair_index=idx, **cuda_stats())
            _progress(progress_path, stage='before_ref_energies', pair_id=pair_id, pair_index=idx, **cuda_stats())
            with torch.no_grad(), backend.reference_mode():
                e_ref_w = backend.energy(winner_prepared, ts).detach()
                e_ref_l = backend.energy(loser_prepared, ts).detach()
            e_ref_w_f = float(e_ref_w.float().cpu().item())
            e_ref_l_f = float(e_ref_l.float().cpu().item())
            _progress(progress_path, stage='after_ref_energies', pair_id=pair_id, pair_index=idx, E_ref_winner=e_ref_w_f, E_ref_loser=e_ref_l_f, **cuda_stats())
            payload = {
                'winner': _payload_for(winner_prepared),
                'loser': _payload_for(loser_prepared),
                'timestep_tensor': to_cpu(ts.timestep),
                'timestep_index': int(ts.index),
                'actual_sigma': float(ts.sigma),
                'timestep_weight': float(ts.weight),
                'same_seed_noise_id': seed,
                'pair_id': pair_id,
            }
            finite = tensor_tree_finite(payload) and all(torch.isfinite(x.float()).all().item() for x in [e_ref_w, e_ref_l])
            if not finite:
                raise FloatingPointError('nonfinite pair cache tensor or reference energy')
            tensor_name = f'{idx:03d}_{_sanitize(pair_id)}.pt'
            tensor_path = out_root / tensor_name
            torch.save(payload, tensor_path)
            digest = sha256_file(tensor_path)
            audit = pair.get('codex_visual_audit') or pair.get('codex_audit') or {}
            index_row = {
                'pair_id': pair_id,
                'condition_hash': hashlib.sha256(json.dumps(pair.get('condition', {}), sort_keys=True).encode('utf-8')).hexdigest(),
                'prompt': (pair.get('condition') or {}).get('prompt', ''),
                'prompt_path': (pair.get('condition') or {}).get('prompt_path', ''),
                'poses': (pair.get('condition') or {}).get('poses', ''),
                'intrinsics': (pair.get('condition') or {}).get('intrinsics', ''),
                'prefix_video_path': (pair.get('condition') or {}).get('prefix_video_path', ''),
                'winner_future_video_path': (pair.get('winner') or {}).get('future_video_path', ''),
                'winner_full_video_path': (pair.get('winner') or {}).get('full_video_path', ''),
                'loser_future_video_path': (pair.get('loser') or {}).get('future_video_path', ''),
                'loser_full_video_path': (pair.get('loser') or {}).get('full_video_path', ''),
                'cache_tensor_path': str(tensor_path.relative_to(out_root)),
                'cached_winner_latent_tensor_path': str(tensor_path.relative_to(out_root)),
                'cached_loser_latent_tensor_path': str(tensor_path.relative_to(out_root)),
                'future_loss_mask_tensor_path': str(tensor_path.relative_to(out_root)),
                'winner_latent_temporal_index_mapping': list(winner_prepared.latent_loss_indices),
                'loser_latent_temporal_index_mapping': list(loser_prepared.latent_loss_indices),
                'used_window_frames': int(args.used_window_frames),
                'selected_raw_frame_indices': list(range(int(args.used_window_frames))),
                'prefix_len': int(args.prefix_len),
                'prediction_start_frame': int(args.prediction_start_frame),
                'E_ref_winner_cached': e_ref_w_f,
                'E_ref_loser_cached': e_ref_l_f,
                'E_ref_winner': e_ref_w_f,
                'E_ref_loser': e_ref_l_f,
                'Delta_ref': e_ref_l_f - e_ref_w_f,
                'cache_level': 'pair_with_ref_energy',
                'timestep': float(ts.timestep.detach().flatten()[0].item()) if hasattr(ts.timestep, 'detach') else float(ts.timestep),
                'timestep_index': int(ts.index),
                'actual_sigma': float(ts.sigma),
                'same_seed_noise_id': seed,
                'shape_dtype': tensor_tree_shapes(payload),
                'finite': True,
                'sha256': digest,
                'codex_visual_audit_reviewed': bool(audit.get('reviewed', audit.get('valid_preference', False))),
                'codex_visual_audit_is_dpo_ready': bool(audit.get('is_dpo_ready', audit.get('valid_preference', False))),
                'codex_visual_audit_main_failure': audit.get('main_failure_tag') or (pair.get('loser') or {}).get('failure_type', ''),
                'codex_visual_audit_written_reason': audit.get('written_reason', ''),
                'status': 'PASS',
                'error_reason': '',
            }
            write_jsonl(index_path, index_row)
            row.update({
                'cache_status': 'PASS',
                'cache_tensor_path': str(tensor_path),
                'sha256': digest,
                'E_ref_winner_cached': e_ref_w_f,
                'E_ref_loser_cached': e_ref_l_f,
                'Delta_ref': e_ref_l_f - e_ref_w_f,
                'timestep': index_row['timestep'],
                'timestep_index': index_row['timestep_index'],
                'actual_sigma': index_row['actual_sigma'],
                'same_seed_noise_id': seed,
                'winner_latent_loss_indices': json.dumps(list(winner_prepared.latent_loss_indices)),
                'loser_latent_loss_indices': json.dumps(list(loser_prepared.latent_loss_indices)),
                'winner_target_shape': json.dumps(list(winner_prepared.target.shape)),
                'loser_target_shape': json.dumps(list(loser_prepared.target.shape)),
                'finite': True,
                'reviewed': True,
            })
            success += 1
            _progress(progress_path, stage='pair_cache_pass', pair_id=pair_id, pair_index=idx, cache_tensor_path=str(tensor_path), **cuda_stats())
            del w_video, l_video, poses, poses2, intrinsics, intrinsics2, winner_prepared, loser_prepared, payload, e_ref_w, e_ref_l
        except Exception as exc:  # noqa: BLE001
            fail += 1
            row['error_reason'] = repr(exc)
            _progress(progress_path, stage='pair_cache_fail', pair_id=pair_id, pair_index=idx, error_reason=repr(exc), **cuda_stats())
            write_jsonl(index_path, {'pair_id': pair_id, 'status': 'FAILED', 'error_reason': repr(exc)})
        row.update({'seconds': time.time() - start, **cuda_stats()})
        append_csv(report, row, fieldnames)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        _progress(progress_path, stage='pair_done', pair_id=pair_id, pair_index=idx, cache_status=row.get('cache_status'), **cuda_stats())
    summary_status = 'PAIR_CACHE_BUILD_PASS' if success == len(pairs) and success > 0 else ('PAIR_CACHE_PARTIAL' if success else 'PAIR_CACHE_FAILED')
    summary = {
        'status': summary_status,
        'requested_pairs': int(args.num_pairs),
        'reviewed_pairs_loaded': len(pairs),
        'success': success,
        'fail': fail,
        'cache_root': str(out_root),
        'cache_index': str(index_path),
        'report': str(report),
        'progress': str(progress_path),
    }
    (out_root / 'cache_summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True), encoding='utf-8')
    Path(args.report).with_name('pair_cache_build_summary.md').write_text(
        'Current Status:\n' + summary_status + '\n\n'
        '# v8m Reviewed Pair Cache Build Summary\n\n'
        f'- Reviewed pairs loaded: {len(pairs)}\n'
        f'- Cache success: {success}\n'
        f'- Cache fail: {fail}\n'
        f'- Cache root: `{out_root}`\n'
        f'- Cache index: `{index_path}`\n'
        f'- Report: `{report}`\n'
        '- Winner cached: yes.\n'
        '- Loser cached: yes.\n'
        '- Reference graph cached: no; only scalar E_ref_winner_cached and E_ref_loser_cached are stored.\n',
        encoding='utf-8',
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Build v8m reviewed winner+loser pair cache.')
    parser.add_argument('--pair_manifest', required=True)
    parser.add_argument('--num_pairs', type=int, default=10)
    parser.add_argument('--gpu', type=int, default=0)
    parser.add_argument('--prefix_len', type=int, default=5)
    parser.add_argument('--prediction_start_frame', type=int, default=5)
    parser.add_argument('--future_only', default='true')
    parser.add_argument('--used_window_frames', type=int, default=49)
    parser.add_argument('--output_root', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--progress', default='')
    parser.add_argument('--heartbeat_seconds', type=float, default=15.0)
    parser.add_argument('--per_stage_timeout_seconds', type=float, default=180.0)
    parser.add_argument('--per_pair_timeout_seconds', type=float, default=600.0)
    parser.add_argument('--config', default='configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml')
    parser.add_argument('--repo_root', default='.')
    parser.add_argument('--runtime_device', default='cuda')
    parser.add_argument('--height', type=int, default=480)
    parser.add_argument('--width', type=int, default=832)
    parser.add_argument('--target_sigma', type=float, default=0.35)
    parser.add_argument('--seed', type=int, default=1234)
    parser.add_argument('--loader_mode', default='safe_wan_policy_only', choices=['stage1_helper', 'safe_wan_policy_only'])
    args = parser.parse_args(argv)
    if str(args.future_only).lower() not in {'1', 'true', 'yes'}:
        raise ValueError('future_only must be true')
    build_pair_cache(args)


if __name__ == '__main__':
    main()
