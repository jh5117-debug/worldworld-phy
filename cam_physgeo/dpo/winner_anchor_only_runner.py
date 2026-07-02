from __future__ import annotations

import argparse
import csv
import json
import math
import os
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import torch

from cam_physgeo.dpo.anchored_dpo_trainer import _grad_norm, _scalar
from cam_physgeo.dpo.failure_diagnostics import _make_timestep_sample
from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy, PreparedEnergyInput, strict_future_latent_indices
from cam_physgeo.dpo.prefix5_dpo_dataset import decode_video_tensor, load_array, normalize_intrinsics, read_prompt


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _load_yaml(path: str | Path) -> dict[str, Any]:
    import yaml

    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise TypeError(f"expected mapping config in {path}")
    return dict(data)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed"}


def is_reviewed_dpo_pair(pair: dict[str, Any]) -> bool:
    audit = pair.get("codex_visual_audit") or pair.get("codex_audit") or {}
    reviewed = audit.get("reviewed", audit.get("valid_preference", False))
    ready = audit.get("is_dpo_ready", pair.get("medium_hard", False))
    return _boolish(reviewed) and _boolish(ready)


def reviewed_pairs(path: str | Path, limit: int) -> list[dict[str, Any]]:
    rows = [row for row in _load_jsonl(path) if is_reviewed_dpo_pair(row)]
    if limit > 0:
        rows = rows[: int(limit)]
    return rows


def window_sequence(start: int | None = None) -> list[int]:
    order = [81, 49, 33, 25]
    if start is None or int(start) <= 0:
        return order
    start = int(start)
    if start in order:
        return order[order.index(start) :]
    return [start] + [value for value in order if value < start]


def _cfg(config: str | Path, *, frames: int, height: int, width: int, runtime_device: str, gradient_checkpointing: bool) -> dict[str, Any]:
    cfg = _load_yaml(config)
    cfg["num_frames"] = int(frames)
    cfg["height"] = int(height)
    cfg["width"] = int(width)
    cfg["dpo_runtime_device"] = str(runtime_device)
    cfg["dpo_skip_runtime_components_on_load"] = True
    cfg["gradient_checkpointing"] = bool(gradient_checkpointing or cfg.get("gradient_checkpointing", True))
    return cfg



def ensure_runtime_ready(backend: LingBotFastDpoEnergy) -> None:
    if not hasattr(backend.helper, "vae") or not hasattr(backend.helper, "t5"):
        backend.helper.ensure_runtime_components(backend.runtime_device)
        backend._move_runtime_components(backend.runtime_device)



def offload_runtime_after_cache(backend: LingBotFastDpoEnergy) -> None:
    backend.runtime_device = torch.device("cpu")
    backend._move_runtime_components(torch.device("cpu"))
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _load_winner_inputs(pair: dict[str, Any], *, repo_root: str | Path, frames: int, height: int, width: int, prefix_len: int, prediction_start_frame: int):
    if not is_reviewed_dpo_pair(pair):
        raise ValueError(f"pair is not reviewed DPO-ready: {pair.get('pair_id')}")
    condition = pair.get("condition") or {}
    winner = pair.get("winner") or {}
    if int(condition.get("prefix_len", prefix_len)) != int(prefix_len):
        raise ValueError("prefix_len mismatch; refusing silent fallback")
    if int(condition.get("prediction_start_frame", prediction_start_frame)) != int(prediction_start_frame):
        raise ValueError("prediction_start_frame mismatch; refusing silent fallback")
    if int(frames) <= int(prefix_len):
        raise ValueError("used_window_frames must include prefix and future frames")
    video_path = winner.get("full_video_path") or winner.get("video")
    if not video_path:
        raise ValueError("winner full_video_path missing; refusing image-only path")
    video, meta = decode_video_tensor(video_path, repo_root=repo_root, num_frames=int(frames), height=int(height), width=int(width))
    source_height = int(meta.get("source_height") or height)
    source_width = int(meta.get("source_width") or width)
    poses = torch.from_numpy(load_array(condition["poses"], repo_root=repo_root, num_frames=int(frames)).astype("float32")).float()
    intrinsics = torch.from_numpy(
        normalize_intrinsics(
            load_array(condition["intrinsics"], repo_root=repo_root, num_frames=int(frames)),
            source_width=source_width,
            source_height=source_height,
        )
    ).float()
    prompt = read_prompt(condition.get("prompt_path") or condition.get("prompt"), repo_root=repo_root)
    if not prompt.strip():
        raise ValueError("empty prompt")
    return video, prompt, poses, intrinsics, source_height, source_width


def _prepare_winner_cached(
    backend: LingBotFastDpoEnergy,
    *,
    video: torch.Tensor,
    prompt: str,
    poses: torch.Tensor,
    intrinsics: torch.Tensor,
    source_height: int,
    source_width: int,
    timestep_sample: Any,
    seed: int,
    total_frames: int,
) -> PreparedEnergyInput:
    video = video.to(backend.device)
    poses = poses.to(backend.device)
    intrinsics = intrinsics.to(backend.device)
    height, width = int(video.shape[2]), int(video.shape[3])
    with torch.no_grad():
        latent = backend._encode_video(video)
        context = backend._encode_text(prompt)
        y = backend._prepare_y(video, latent)
        lat_f, lat_h, lat_w = int(latent.shape[1]), int(latent.shape[2]), int(latent.shape[3])
        seq_len = lat_f * lat_h * lat_w // (backend.helper.patch_size[1] * backend.helper.patch_size[2])
        dit_cond = backend.helper.prepare_control_signal(
            poses,
            None,
            intrinsics,
            height,
            width,
            lat_f,
            lat_h,
            lat_w,
            control_type="cam",
            source_height=int(source_height),
            source_width=int(source_width),
        )
        generator = torch.Generator(device=backend.device)
        generator.manual_seed(int(seed))
        noise = torch.randn(tuple(latent.shape), device=backend.device, dtype=backend.lowp_dtype, generator=generator)
        noise = noise.to(device=backend.device, dtype=latent.dtype)
        noisy = (1.0 - float(timestep_sample.sigma)) * latent + float(timestep_sample.sigma) * noise
        target = noise - latent
        latent_loss_indices = strict_future_latent_indices(
            total_frames=int(total_frames),
            prefix_len=int(backend.prefix_len),
            latent_frames=lat_f,
            temporal_compression=int(backend.temporal_compression),
        )
    return PreparedEnergyInput(
        target=target.detach(),
        noisy_latent=noisy.detach(),
        context=[tensor.detach() for tensor in context],
        y=y.detach(),
        dit_cond=dit_cond,
        seq_len=int(seq_len),
        latent_loss_indices=list(latent_loss_indices),
    )


def cuda_stats() -> dict[str, float]:
    if not torch.cuda.is_available():
        return {"allocated_gb": 0.0, "reserved_gb": 0.0, "max_allocated_gb": 0.0, "max_reserved_gb": 0.0}
    return {
        "allocated_gb": torch.cuda.memory_allocated() / (1024**3),
        "reserved_gb": torch.cuda.memory_reserved() / (1024**3),
        "max_allocated_gb": torch.cuda.max_memory_allocated() / (1024**3),
        "max_reserved_gb": torch.cuda.max_memory_reserved() / (1024**3),
    }


def _param_norm(params: list[torch.nn.Parameter]) -> float:
    total = 0.0
    for param in params:
        total += float(torch.sum(param.detach().float().cpu() ** 2).item())
    return math.sqrt(total)


def _param_update_norm(before: list[torch.Tensor], params: list[torch.nn.Parameter]) -> float:
    total = 0.0
    for old, param in zip(before, params):
        diff = param.detach().float().cpu() - old
        total += float(torch.sum(diff * diff).item())
    return math.sqrt(total)


def _append_csv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
        f.flush()


def _write_summary(path: Path, status: str, rows: list[dict[str, Any]], *, frames: int, output: Path) -> None:
    completed = len([row for row in rows if row.get("status") == "PASS"])
    final_improvement = rows[-1].get("winner_improvement_post") if rows else None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Current Status:\n"
        f"{status}\n\n"
        "# Winner-Anchor-Only v8c Summary\n\n"
        f"- Steps completed: {completed}\n"
        f"- Used window frames: {frames}\n"
        f"- Final winner_improvement_post: {final_improvement}\n"
        f"- CSV: `{output}`\n"
        f"- Decision: `{status}`\n",
        encoding="utf-8",
    )


def _status(rows: list[dict[str, Any]], requested_steps: int) -> str:
    pass_rows = [row for row in rows if row.get("status") == "PASS"]
    if len(pass_rows) < int(requested_steps):
        if rows and rows[-1].get("status") == "OOM":
            return "WINNER_ANCHOR_1PAIR_OOM"
        return "WINNER_ANCHOR_1PAIR_INCOMPLETE"
    final = float(pass_rows[-1].get("winner_improvement_post", 0.0))
    mean = sum(float(row.get("winner_improvement_post", 0.0)) for row in pass_rows) / len(pass_rows)
    if final > 0.0 and mean > 0.0:
        return "WINNER_ANCHOR_1PAIR_MEMORY_SAFE_PASS"
    return "WINNER_ANCHOR_1PAIR_OBJECTIVE_FAIL"



def _load_cache_index(cache_root: str | Path, limit: int) -> list[dict[str, Any]]:
    root = Path(cache_root)
    index = root / "cache_index.jsonl"
    rows: list[dict[str, Any]] = []
    with index.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("status") == "PASS":
                rows.append(row)
    if limit > 0:
        rows = rows[: int(limit)]
    if not rows:
        raise RuntimeError(f"no PASS cache rows found in {index}")
    return rows


def _tree_to_device(obj: Any, device: torch.device) -> Any:
    if torch.is_tensor(obj):
        return obj.to(device)
    if isinstance(obj, dict):
        return {k: _tree_to_device(v, device) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return tuple(_tree_to_device(v, device) for v in obj)
    if isinstance(obj, list):
        return [_tree_to_device(v, device) for v in obj]
    return obj


def _load_prepared_from_cache(cache_root: str | Path, row: dict[str, Any], device: torch.device) -> tuple[PreparedEnergyInput, Any]:
    payload = torch.load(Path(cache_root) / str(row["cache_tensor_path"]), map_location="cpu")
    prepared = PreparedEnergyInput(
        target=_tree_to_device(payload["target"], device),
        noisy_latent=_tree_to_device(payload["noisy_latent"], device),
        context=_tree_to_device(payload["context"], device),
        y=_tree_to_device(payload["y"], device),
        dit_cond=_tree_to_device(payload["dit_cond"], device),
        seq_len=int(payload["seq_len"]),
        latent_loss_indices=list(payload["latent_loss_indices"]),
    )
    timestep_tensor = payload["timestep_tensor"].to(device) if torch.is_tensor(payload["timestep_tensor"]) else torch.as_tensor(payload["timestep_tensor"], device=device)
    ts = SimpleNamespace(
        timestep=timestep_tensor,
        index=int(payload["timestep_index"]),
        sigma=float(payload["actual_sigma"]),
        weight=float(payload["timestep_weight"]),
    )
    return prepared, ts


def _cache_train_status(rows: list[dict[str, Any]], requested_steps: int) -> str:
    pass_rows = [row for row in rows if row.get("status") == "PASS"]
    if len(pass_rows) < int(requested_steps):
        if rows and rows[-1].get("status") == "OOM":
            return "WINNER_ANCHOR_CACHE10_OOM"
        return "WINNER_ANCHOR_CACHE10_TOO_SLOW"
    final = float(pass_rows[-1].get("winner_improvement_post", 0.0))
    mean = sum(float(row.get("winner_improvement_post", 0.0)) for row in pass_rows) / len(pass_rows)
    if final > 0.0 and mean > 0.0:
        return "WINNER_ANCHOR_CACHE10_PASS"
    return "WINNER_ANCHOR_CACHE10_OBJECTIVE_FAIL"


def _write_cache_train_summary(path: Path, status: str, rows: list[dict[str, Any]], *, output: Path) -> None:
    pass_rows = [row for row in rows if row.get("status") == "PASS"]
    mean = ""
    final = ""
    if pass_rows:
        vals = [float(row.get("winner_improvement_post", 0.0)) for row in pass_rows]
        mean = sum(vals) / len(vals)
        final = vals[-1]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Current Status:\n"
        f"{status}\n\n"
        "# v8d Cache-Only Winner-Anchor Summary\n\n"
        f"- Steps completed: {len(pass_rows)}\n"
        f"- Mean winner_improvement_post: {mean}\n"
        f"- Final winner_improvement_post: {final}\n"
        f"- CSV: `{output}`\n"
        f"- Decision: `{status}`\n",
        encoding="utf-8",
    )


def run_cache_only_winner_anchor(args: argparse.Namespace) -> dict[str, Any]:
    output = Path(args.output)
    if output.exists():
        output.unlink()
    if torch.cuda.is_available():
        torch.cuda.set_device(int(args.gpu))
        torch.cuda.reset_peak_memory_stats()
    device = torch.device(f"cuda:{int(args.gpu)}" if torch.cuda.is_available() else "cpu")
    cache_rows = _load_cache_index(args.cache_root, int(args.num_pairs))
    first_frames = int(cache_rows[0].get("used_window_frames", args.used_window_frames or 49))
    cfg = _cfg(args.config, frames=first_frames, height=int(args.height), width=int(args.width), runtime_device="cpu", gradient_checkpointing=bool(args.gradient_checkpointing))
    backend = LingBotFastDpoEnergy(cfg, device=str(device), prefix_len=int(args.prefix_len))
    params = backend.trainable_parameters()
    optimizer = torch.optim.AdamW(params, lr=float(args.learning_rate), betas=(0.9, 0.95), weight_decay=float(args.weight_decay))
    fieldnames = [
        "step", "used_window_frames", "pair_id", "timestep", "timestep_index", "actual_sigma",
        "E_ref_winner_cached", "E_policy_winner_pre_update", "E_policy_winner_post_update",
        "winner_improvement_pre", "winner_improvement_post", "loss", "grad_norm", "update_norm",
        "lora_param_norm", "lr", "allocated_gb", "reserved_gb", "max_allocated_gb", "max_reserved_gb",
        "step_time", "finite", "status", "error_reason",
    ]
    rows: list[dict[str, Any]] = []
    for step in range(int(args.steps)):
        step_start = time.time()
        cache_row = cache_rows[step % len(cache_rows)]
        pair_id = str(cache_row.get("pair_id"))
        used_frames = int(cache_row.get("used_window_frames", first_frames))
        ref_energy = float(cache_row["E_ref_winner_cached"])
        try:
            prepared, ts = _load_prepared_from_cache(args.cache_root, cache_row, device)
            optimizer.zero_grad(set_to_none=True)
            with torch.no_grad():
                pre_energy = backend.energy(prepared, ts).detach()
            loss = backend.energy(prepared, ts)
            finite = bool(torch.isfinite(loss).all().item())
            if not finite:
                raise FloatingPointError("nonfinite cache-only winner-anchor loss")
            loss.backward()
            grad_norm = _grad_norm(params)
            before = [param.detach().float().cpu().clone() for param in params]
            optimizer.step()
            update_norm = _param_update_norm(before, params)
            optimizer.zero_grad(set_to_none=True)
            with torch.no_grad():
                post_energy = backend.energy(prepared, ts).detach()
            row = {
                "step": step + 1,
                "used_window_frames": used_frames,
                "pair_id": pair_id,
                "timestep": float(ts.timestep.detach().flatten()[0].item()) if hasattr(ts.timestep, "detach") else float(ts.timestep),
                "timestep_index": int(ts.index),
                "actual_sigma": float(ts.sigma),
                "E_ref_winner_cached": ref_energy,
                "E_policy_winner_pre_update": _scalar(pre_energy),
                "E_policy_winner_post_update": _scalar(post_energy),
                "winner_improvement_pre": ref_energy - _scalar(pre_energy),
                "winner_improvement_post": ref_energy - _scalar(post_energy),
                "loss": _scalar(loss.detach()),
                "grad_norm": grad_norm,
                "update_norm": update_norm,
                "lora_param_norm": _param_norm(params),
                "lr": float(args.learning_rate),
                **cuda_stats(),
                "step_time": time.time() - step_start,
                "finite": finite,
                "status": "PASS",
                "error_reason": "",
            }
            _append_csv(output, row, fieldnames)
            rows.append(row)
            del prepared, ts, pre_energy, post_energy, loss, before
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except torch.cuda.OutOfMemoryError as exc:
            row = {
                "step": step + 1,
                "used_window_frames": used_frames,
                "pair_id": pair_id,
                "timestep": "",
                "timestep_index": "",
                "actual_sigma": "",
                "E_ref_winner_cached": ref_energy,
                "E_policy_winner_pre_update": "",
                "E_policy_winner_post_update": "",
                "winner_improvement_pre": "",
                "winner_improvement_post": "",
                "loss": "",
                "grad_norm": "",
                "update_norm": "",
                "lora_param_norm": "",
                "lr": float(args.learning_rate),
                **cuda_stats(),
                "step_time": time.time() - step_start,
                "finite": False,
                "status": "OOM",
                "error_reason": repr(exc),
            }
            _append_csv(output, row, fieldnames)
            rows.append(row)
            break
        except Exception as exc:  # noqa: BLE001
            row = {
                "step": step + 1,
                "used_window_frames": used_frames,
                "pair_id": pair_id,
                "timestep": "",
                "timestep_index": "",
                "actual_sigma": "",
                "E_ref_winner_cached": ref_energy,
                "E_policy_winner_pre_update": "",
                "E_policy_winner_post_update": "",
                "winner_improvement_pre": "",
                "winner_improvement_post": "",
                "loss": "",
                "grad_norm": "",
                "update_norm": "",
                "lora_param_norm": "",
                "lr": float(args.learning_rate),
                **cuda_stats(),
                "step_time": time.time() - step_start,
                "finite": False,
                "status": "ERROR",
                "error_reason": repr(exc),
            }
            _append_csv(output, row, fieldnames)
            rows.append(row)
            break
    final_status = _cache_train_status(rows, int(args.steps))
    summary_path = output.with_name(output.stem + "_summary.md")
    _write_cache_train_summary(summary_path, final_status, rows, output=output)
    pass_rows = [row for row in rows if row.get("status") == "PASS"]
    vals = [float(row.get("winner_improvement_post", 0.0)) for row in pass_rows]
    result = {
        "status": final_status,
        "output": str(output),
        "summary": str(summary_path),
        "steps_completed": len(pass_rows),
        "mean_winner_improvement_post": sum(vals) / len(vals) if vals else None,
        "final_winner_improvement_post": vals[-1] if vals else None,
        "cache_root": str(args.cache_root),
        "reference_loaded_in_training_loop": False,
        "loser_loaded_in_training_loop": False,
        "vae_used_in_training_loop": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result

def run_winner_anchor(args: argparse.Namespace) -> dict[str, Any]:
    if str(args.mode) == "cache_only_policy_train":
        return run_cache_only_winner_anchor(args)
    if str(args.mode) != "policy_only_cached_latents":
        raise ValueError("only policy_only_cached_latents and cache_only_policy_train are supported")
    output = Path(args.output)
    if output.exists():
        output.unlink()
    if torch.cuda.is_available():
        torch.cuda.set_device(int(args.gpu))
        torch.cuda.reset_peak_memory_stats()
    device = f"cuda:{int(args.gpu)}" if torch.cuda.is_available() else "cpu"
    pairs = reviewed_pairs(args.pair_manifest, int(args.num_pairs))
    if not pairs:
        raise RuntimeError("no reviewed=true DPO-ready pair found")
    fieldnames = [
        "step", "used_window_frames", "pair_id", "timestep", "timestep_index", "actual_sigma",
        "E_ref_winner_cached", "E_policy_winner_pre_update", "E_policy_winner_post_update",
        "winner_improvement_pre", "winner_improvement_post", "loss", "grad_norm", "update_norm",
        "lora_param_norm", "lr", "allocated_gb", "reserved_gb", "max_allocated_gb", "max_reserved_gb",
        "step_time", "finite", "status", "error_reason",
    ]
    rows: list[dict[str, Any]] = []
    final_status = "WINNER_ANCHOR_1PAIR_OOM"
    used_frames = 0
    for frames in window_sequence(args.used_window_frames):
        used_frames = int(frames)
        rows = []
        if output.exists():
            output.unlink()
        try:
            cfg = _cfg(args.config, frames=used_frames, height=int(args.height), width=int(args.width), runtime_device=args.runtime_device, gradient_checkpointing=bool(args.gradient_checkpointing))
            backend = LingBotFastDpoEnergy(cfg, device=device, prefix_len=int(args.prefix_len))
            ensure_runtime_ready(backend)
            params = backend.trainable_parameters()
            optimizer = torch.optim.AdamW(params, lr=float(args.learning_rate), betas=(0.9, 0.95), weight_decay=float(args.weight_decay))
            prepared_by_pair: list[tuple[dict[str, Any], PreparedEnergyInput, Any, float]] = []
            for idx, pair in enumerate(pairs):
                video, prompt, poses, intrinsics, sh, sw = _load_winner_inputs(pair, repo_root=args.repo_root, frames=used_frames, height=int(args.height), width=int(args.width), prefix_len=int(args.prefix_len), prediction_start_frame=int(args.prediction_start_frame))
                ts = _make_timestep_sample(backend, float(args.target_sigma))
                prepared = _prepare_winner_cached(backend, video=video, prompt=prompt, poses=poses, intrinsics=intrinsics, source_height=sh, source_width=sw, timestep_sample=ts, seed=int(args.seed) + idx * 997, total_frames=used_frames)
                with torch.no_grad(), backend.reference_mode():
                    ref_energy = backend.energy(prepared, ts).detach()
                prepared_by_pair.append((pair, prepared, ts, _scalar(ref_energy)))
                del video, poses, intrinsics, ref_energy
                offload_runtime_after_cache(backend)
            for step in range(int(args.steps)):
                step_start = time.time()
                pair, prepared, ts, ref_energy = prepared_by_pair[step % len(prepared_by_pair)]
                pair_id = str(pair.get("pair_id"))
                try:
                    optimizer.zero_grad(set_to_none=True)
                    with torch.no_grad():
                        pre_energy = backend.energy(prepared, ts).detach()
                    loss = backend.energy(prepared, ts)
                    finite = bool(torch.isfinite(loss).all().item())
                    if not finite:
                        raise FloatingPointError("nonfinite winner-anchor loss")
                    loss.backward()
                    grad_norm = _grad_norm(params)
                    before = [p.detach().float().cpu().clone() for p in params]
                    optimizer.step()
                    update_norm = _param_update_norm(before, params)
                    optimizer.zero_grad(set_to_none=True)
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    with torch.no_grad():
                        post_energy = backend.energy(prepared, ts).detach()
                    row = {
                        "step": step + 1,
                        "used_window_frames": used_frames,
                        "pair_id": pair_id,
                        "timestep": float(ts.timestep.detach().flatten()[0].item()) if hasattr(ts.timestep, "detach") else float(ts.timestep),
                        "timestep_index": int(ts.index),
                        "actual_sigma": float(ts.sigma),
                        "E_ref_winner_cached": ref_energy,
                        "E_policy_winner_pre_update": _scalar(pre_energy),
                        "E_policy_winner_post_update": _scalar(post_energy),
                        "winner_improvement_pre": ref_energy - _scalar(pre_energy),
                        "winner_improvement_post": ref_energy - _scalar(post_energy),
                        "loss": _scalar(loss.detach()),
                        "grad_norm": grad_norm,
                        "update_norm": update_norm,
                        "lora_param_norm": _param_norm(params),
                        "lr": float(args.learning_rate),
                        **cuda_stats(),
                        "step_time": time.time() - step_start,
                        "finite": finite,
                        "status": "PASS",
                        "error_reason": "",
                    }
                    _append_csv(output, row, fieldnames)
                    rows.append(row)
                    del pre_energy, post_energy, loss
                except torch.cuda.OutOfMemoryError as exc:
                    row = {
                        "step": step + 1,
                        "used_window_frames": used_frames,
                        "pair_id": pair_id,
                        "timestep": "",
                        "timestep_index": "",
                        "actual_sigma": "",
                        "E_ref_winner_cached": ref_energy,
                        "E_policy_winner_pre_update": "",
                        "E_policy_winner_post_update": "",
                        "winner_improvement_pre": "",
                        "winner_improvement_post": "",
                        "loss": "",
                        "grad_norm": "",
                        "update_norm": "",
                        "lora_param_norm": "",
                        "lr": float(args.learning_rate),
                        **cuda_stats(),
                        "step_time": time.time() - step_start,
                        "finite": False,
                        "status": "OOM",
                        "error_reason": repr(exc),
                    }
                    _append_csv(output, row, fieldnames)
                    rows.append(row)
                    raise
            final_status = _status(rows, int(args.steps))
            break
        except torch.cuda.OutOfMemoryError:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            if int(args.used_window_frames or 0) > 0:
                final_status = "WINNER_ANCHOR_1PAIR_OOM"
                break
            continue
    summary_path = output.with_name(output.stem + "_summary.md")
    _write_summary(summary_path, final_status, rows, frames=used_frames, output=output)
    result = {
        "status": final_status,
        "output": str(output),
        "summary": str(summary_path),
        "steps_completed": len([row for row in rows if row.get("status") == "PASS"]),
        "used_window_frames": used_frames,
        "final_winner_improvement_post": rows[-1].get("winner_improvement_post") if rows else None,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "local_gpu_arg": int(args.gpu),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Memory-safe winner-anchor-only runner for v8c.")
    parser.add_argument("--pair_manifest", default="")
    parser.add_argument("--cache_root", default="")
    parser.add_argument("--num_pairs", type=int, default=1)
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--mode", default="policy_only_cached_latents")
    parser.add_argument("--prefix_len", type=int, default=5)
    parser.add_argument("--prediction_start_frame", type=int, default=5)
    parser.add_argument("--future_only", default="true")
    parser.add_argument("--output", required=True)
    parser.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    parser.add_argument("--repo_root", default=".")
    parser.add_argument("--runtime_device", default="cuda")
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--used_window_frames", type=int, default=0)
    parser.add_argument("--gradient_checkpointing", action="store_true")
    parser.add_argument("--offload_reference", action="store_true")
    parser.add_argument("--cache_latents", default="true")
    parser.add_argument("--learning_rate", type=float, default=1e-6)
    parser.add_argument("--weight_decay", type=float, default=0.01)
    parser.add_argument("--target_sigma", type=float, default=0.35)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args(argv)
    if str(args.future_only).lower() not in {"1", "true", "yes"}:
        raise ValueError("future_only must be true")
    run_winner_anchor(args)


if __name__ == "__main__":
    main()
