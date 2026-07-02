
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.dpo.failure_diagnostics import _make_timestep_sample
from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy, PreparedEnergyInput
from cam_physgeo.dpo.winner_anchor_only_runner import (
    _cfg,
    _load_winner_inputs,
    _prepare_winner_cached,
    cuda_stats,
    ensure_runtime_ready,
    reviewed_pairs,
)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def to_cpu(obj: Any) -> Any:
    if torch.is_tensor(obj):
        return obj.detach().cpu()
    if isinstance(obj, dict):
        return {k: to_cpu(v) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return tuple(to_cpu(v) for v in obj)
    if isinstance(obj, list):
        return [to_cpu(v) for v in obj]
    return obj


def tensor_tree_finite(obj: Any) -> bool:
    if torch.is_tensor(obj):
        return bool(torch.isfinite(obj.float()).all().item())
    if isinstance(obj, dict):
        return all(tensor_tree_finite(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return all(tensor_tree_finite(v) for v in obj)
    return True


def tensor_tree_shapes(obj: Any) -> Any:
    if torch.is_tensor(obj):
        return {"shape": list(obj.shape), "dtype": str(obj.dtype)}
    if isinstance(obj, dict):
        return {k: tensor_tree_shapes(v) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return [tensor_tree_shapes(v) for v in obj]
    if isinstance(obj, list):
        return [tensor_tree_shapes(v) for v in obj]
    return str(type(obj).__name__)


def append_csv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
        f.flush()


def write_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
        f.flush()


def _progress(path: Path, **row: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"time": time.time(), **row}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
        f.flush()


def build_cache(args: argparse.Namespace) -> dict[str, Any]:
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)
    report = Path(args.report)
    progress_path = Path(args.progress) if args.progress else report.with_name(report.stem + "_progress.jsonl")
    if report.exists():
        report.unlink()
    if progress_path.exists():
        progress_path.unlink()
    index_path = out_root / "cache_index.jsonl"
    if index_path.exists():
        index_path.unlink()
    if torch.cuda.is_available():
        torch.cuda.set_device(int(args.gpu))
        torch.cuda.reset_peak_memory_stats()
    device = f"cuda:{int(args.gpu)}" if torch.cuda.is_available() else "cpu"
    pairs = reviewed_pairs(args.pair_manifest, int(args.num_pairs))
    fieldnames = [
        "pair_id", "cache_status", "cache_tensor_path", "sha256", "E_ref_winner_cached",
        "timestep", "timestep_index", "actual_sigma", "used_window_frames", "prefix_len",
        "prediction_start_frame", "latent_loss_indices", "target_shape", "noisy_latent_shape",
        "context_shapes", "y_shape", "dit_cond_shapes", "finite", "seconds", "allocated_gb",
        "reserved_gb", "max_allocated_gb", "max_reserved_gb", "error_reason",
    ]
    _progress(progress_path, stage="start", requested_pairs=int(args.num_pairs), output_root=str(out_root))
    cfg = _cfg(
        args.config,
        frames=int(args.used_window_frames),
        height=int(args.height),
        width=int(args.width),
        runtime_device=str(args.runtime_device),
        gradient_checkpointing=True,
    )
    _progress(progress_path, stage="before_backend_load", device=device)
    backend = LingBotFastDpoEnergy(cfg, device=device, prefix_len=int(args.prefix_len))
    _progress(progress_path, stage="after_policy_load", **cuda_stats())
    ensure_runtime_ready(backend)
    _progress(progress_path, stage="after_runtime_ready", **cuda_stats())
    success = 0
    fail = 0
    for idx, pair in enumerate(pairs):
        start = time.time()
        pair_id = str(pair.get("pair_id") or f"pair_{idx:04d}")
        row: dict[str, Any] = {
            "pair_id": pair_id,
            "cache_status": "FAILED",
            "cache_tensor_path": "",
            "sha256": "",
            "E_ref_winner_cached": "",
            "timestep": "",
            "timestep_index": "",
            "actual_sigma": "",
            "used_window_frames": int(args.used_window_frames),
            "prefix_len": int(args.prefix_len),
            "prediction_start_frame": int(args.prediction_start_frame),
            "latent_loss_indices": "",
            "target_shape": "",
            "noisy_latent_shape": "",
            "context_shapes": "",
            "y_shape": "",
            "dit_cond_shapes": "",
            "finite": False,
            "seconds": "",
            "allocated_gb": "",
            "reserved_gb": "",
            "max_allocated_gb": "",
            "max_reserved_gb": "",
            "error_reason": "",
        }
        try:
            _progress(progress_path, stage="pair_start", pair_id=pair_id, pair_index=idx, **cuda_stats())
            video, prompt, poses, intrinsics, sh, sw = _load_winner_inputs(
                pair,
                repo_root=args.repo_root,
                frames=int(args.used_window_frames),
                height=int(args.height),
                width=int(args.width),
                prefix_len=int(args.prefix_len),
                prediction_start_frame=int(args.prediction_start_frame),
            )
            _progress(progress_path, stage="after_load_winner_inputs", pair_id=pair_id, pair_index=idx, **cuda_stats())
            ts = _make_timestep_sample(backend, float(args.target_sigma))
            _progress(progress_path, stage="before_prepare_winner_cached", pair_id=pair_id, pair_index=idx, **cuda_stats())
            prepared = _prepare_winner_cached(
                backend,
                video=video,
                prompt=prompt,
                poses=poses,
                intrinsics=intrinsics,
                source_height=sh,
                source_width=sw,
                timestep_sample=ts,
                seed=int(args.seed) + idx * 997,
                total_frames=int(args.used_window_frames),
            )
            _progress(progress_path, stage="after_prepare_winner_cached", pair_id=pair_id, pair_index=idx, **cuda_stats())
            with torch.no_grad(), backend.reference_mode():
                ref_energy = backend.energy(prepared, ts).detach()
            _progress(progress_path, stage="after_ref_energy", pair_id=pair_id, pair_index=idx, E_ref_winner_cached=float(ref_energy.detach().float().cpu().item()), **cuda_stats())
            cache_payload = {
                "target": to_cpu(prepared.target),
                "noisy_latent": to_cpu(prepared.noisy_latent),
                "context": to_cpu(prepared.context),
                "y": to_cpu(prepared.y),
                "dit_cond": to_cpu(prepared.dit_cond),
                "seq_len": int(prepared.seq_len),
                "latent_loss_indices": list(prepared.latent_loss_indices),
                "timestep_tensor": to_cpu(ts.timestep),
                "timestep_index": int(ts.index),
                "actual_sigma": float(ts.sigma),
                "timestep_weight": float(ts.weight),
            }
            finite = tensor_tree_finite(cache_payload) and bool(torch.isfinite(ref_energy.float()).all().item())
            if not finite:
                raise FloatingPointError("nonfinite tensor or E_ref_winner")
            tensor_name = f"{idx:03d}_{pair_id.replace('/', '_')}.pt"
            tensor_path = out_root / tensor_name
            torch.save(cache_payload, tensor_path)
            digest = sha256_file(tensor_path)
            index_row = {
                "pair_id": pair_id,
                "condition_hash": hashlib.sha256(json.dumps(pair.get("condition", {}), sort_keys=True).encode("utf-8")).hexdigest(),
                "prompt": (pair.get("condition") or {}).get("prompt", ""),
                "prompt_path": (pair.get("condition") or {}).get("prompt_path", ""),
                "poses": (pair.get("condition") or {}).get("poses", ""),
                "intrinsics": (pair.get("condition") or {}).get("intrinsics", ""),
                "prefix_video_path": (pair.get("condition") or {}).get("prefix_video_path", ""),
                "winner_future_video_path": (pair.get("winner") or {}).get("future_video_path", ""),
                "winner_full_video_path": (pair.get("winner") or {}).get("full_video_path", ""),
                "cache_tensor_path": str(tensor_path.relative_to(out_root)),
                "cached_winner_latent_tensor_path": str(tensor_path.relative_to(out_root)),
                "future_loss_mask_tensor_path": str(tensor_path.relative_to(out_root)),
                "latent_temporal_index_mapping": list(prepared.latent_loss_indices),
                "used_window_frames": int(args.used_window_frames),
                "selected_raw_frame_indices": list(range(int(args.used_window_frames))),
                "prefix_len": int(args.prefix_len),
                "prediction_start_frame": int(args.prediction_start_frame),
                "E_ref_winner_cached": float(ref_energy.detach().float().cpu().item()),
                "timestep": float(ts.timestep.detach().flatten()[0].item()) if hasattr(ts.timestep, "detach") else float(ts.timestep),
                "timestep_index": int(ts.index),
                "actual_sigma": float(ts.sigma),
                "same_seed_noise_id": int(args.seed) + idx * 997,
                "shape_dtype": tensor_tree_shapes(cache_payload),
                "finite": True,
                "sha256": digest,
                "status": "PASS",
                "error_reason": "",
            }
            write_jsonl(index_path, index_row)
            row.update(
                {
                    "cache_status": "PASS",
                    "cache_tensor_path": str(tensor_path),
                    "sha256": digest,
                    "E_ref_winner_cached": index_row["E_ref_winner_cached"],
                    "timestep": index_row["timestep"],
                    "timestep_index": index_row["timestep_index"],
                    "actual_sigma": index_row["actual_sigma"],
                    "latent_loss_indices": json.dumps(list(prepared.latent_loss_indices)),
                    "target_shape": json.dumps(list(prepared.target.shape)),
                    "noisy_latent_shape": json.dumps(list(prepared.noisy_latent.shape)),
                    "context_shapes": json.dumps(tensor_tree_shapes(prepared.context)),
                    "y_shape": json.dumps(list(prepared.y.shape)),
                    "dit_cond_shapes": json.dumps(tensor_tree_shapes(prepared.dit_cond)),
                    "finite": True,
                }
            )
            success += 1
            _progress(progress_path, stage="pair_cache_pass", pair_id=pair_id, pair_index=idx, cache_tensor_path=str(tensor_path), **cuda_stats())
            del video, poses, intrinsics, prepared, cache_payload, ref_energy
        except Exception as exc:  # noqa: BLE001 - row-level cache failure must be recorded
            fail += 1
            row["error_reason"] = repr(exc)
            _progress(progress_path, stage="pair_cache_fail", pair_id=pair_id, pair_index=idx, error_reason=repr(exc), **cuda_stats())
            write_jsonl(index_path, {"pair_id": pair_id, "status": "FAILED", "error_reason": repr(exc)})
        row.update({"seconds": time.time() - start, **cuda_stats()})
        append_csv(report, row, fieldnames)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        _progress(progress_path, stage="pair_done", pair_id=pair_id, pair_index=idx, cache_status=row.get("cache_status"), **cuda_stats())
    summary = {
        "status": "CACHE_BUILD_PASS" if success == len(pairs) and success > 0 else "CACHE_INCOMPLETE",
        "requested_pairs": int(args.num_pairs),
        "reviewed_pairs_loaded": len(pairs),
        "success": success,
        "fail": fail,
        "cache_root": str(out_root),
        "cache_index": str(index_path),
        "report": str(report),
        "progress": str(progress_path),
    }
    (out_root / "cache_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    summary_md = Path(args.report).with_name("cache_build_summary.md")
    summary_md.write_text(
        "Current Status:\n" + summary["status"] + "\n\n"
        "# v8d Winner-Anchor Cache Build Summary\n\n"
        f"- Reviewed pairs loaded: {len(pairs)}\n"
        f"- Cache success: {success}\n"
        f"- Cache fail: {fail}\n"
        f"- Cache root: `{out_root}`\n"
        f"- Cache index: `{index_path}`\n"
        f"- Report: `{report}`\n"
        "- Loser cached: no.\n"
        "- Reference graph cached: no; only scalar E_ref_winner_cached is stored.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build reusable v8d winner-anchor cache.")
    parser.add_argument("--pair_manifest", required=True)
    parser.add_argument("--num_pairs", type=int, default=10)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--prefix_len", type=int, default=5)
    parser.add_argument("--prediction_start_frame", type=int, default=5)
    parser.add_argument("--future_only", default="true")
    parser.add_argument("--used_window_frames", type=int, default=49)
    parser.add_argument("--output_root", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--progress", default="")
    parser.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    parser.add_argument("--repo_root", default=".")
    parser.add_argument("--runtime_device", default="cuda")
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--target_sigma", type=float, default=0.35)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args(argv)
    if str(args.future_only).lower() not in {"1", "true", "yes"}:
        raise ValueError("future_only must be true")
    build_cache(args)


if __name__ == "__main__":
    main()
