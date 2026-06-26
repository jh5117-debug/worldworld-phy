from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.dpo.dpo_loss import dpo_energy_diagnostics, dpo_loss
from cam_physgeo.dpo.lingbot_fast_energy import (
    LingBotFastDpoEnergy,
    PreparedEnergyInput,
    build_stage1_args,
    extract_lora_state,
    load_lora_state,
    strict_future_latent_indices,
)
from cam_physgeo.dpo.prefix5_dpo_dataset import Prefix5DpoDataset


def _scalar(value: torch.Tensor | float) -> float:
    if torch.is_tensor(value):
        return float(value.detach().float().mean().cpu())
    return float(value)


def _grad_norm(parameters) -> float:
    total = 0.0
    for parameter in parameters:
        if parameter.grad is None:
            continue
        total += float(parameter.grad.detach().float().norm().cpu()) ** 2
    return math.sqrt(total)


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _ensure_src_path() -> None:
    src = Path(__file__).resolve().parents[2] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _to_cpu_tree(value):
    if torch.is_tensor(value):
        return value.detach().cpu()
    if isinstance(value, tuple):
        return tuple(_to_cpu_tree(v) for v in value)
    if isinstance(value, list):
        return [_to_cpu_tree(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_cpu_tree(v) for k, v in value.items()}
    return value


def _to_device_tree(value, device: torch.device):
    if torch.is_tensor(value):
        return value.to(device)
    if isinstance(value, tuple):
        return tuple(_to_device_tree(v, device) for v in value)
    if isinstance(value, list):
        return [_to_device_tree(v, device) for v in value]
    if isinstance(value, dict):
        return {k: _to_device_tree(v, device) for k, v in value.items()}
    return value


@dataclass(slots=True)
class PrecomputedPair:
    pair_id: str
    prompt: str
    winner_latent: torch.Tensor
    loser_latent: torch.Tensor
    context: list[torch.Tensor]
    y: torch.Tensor
    dit_cond: dict[str, tuple[torch.Tensor, ...]]
    seq_len: int
    latent_loss_indices: list[int]
    prefix_len: int = 5
    prediction_start_frame: int = 5


def _precompute_pairs(
    dataset: Prefix5DpoDataset,
    *,
    cfg: dict[str, Any],
    device: str,
    out_dir: Path,
) -> list[PrecomputedPair]:
    _ensure_src_path()
    from physical_consistency.trainers.stage1_components import (
        LingBotStage1Helper,
        configure_stage1_precision_env,
    )

    configure_stage1_precision_env(
        str(cfg.get("student_precision_profile", "mixed_safe")),
        str(cfg.get("student_low_precision_dtype", "bf16")),
    )
    dev = torch.device(device)
    args = build_stage1_args(cfg)
    helper = LingBotStage1Helper(args)
    helper.ensure_runtime_components(dev)
    rows: list[dict[str, Any]] = []
    out: list[PrecomputedPair] = []
    try:
        for index, example in enumerate(dataset):
            start = time.time()
            winner_video = example.winner_video.to(dev)
            loser_video = example.loser_video.to(dev)
            poses = example.poses.to(dev)
            intrinsics = example.intrinsics.to(dev)
            with torch.no_grad():
                winner_latent = helper.encode_video(winner_video)
                loser_latent = helper.encode_video(loser_video)
                context = helper.encode_text(example.prompt)
                y = helper.prepare_y(winner_video, winner_latent, prefix_len=example.prefix_len)
                lat_f, lat_h, lat_w = int(winner_latent.shape[1]), int(winner_latent.shape[2]), int(winner_latent.shape[3])
                seq_len = lat_f * lat_h * lat_w // (helper.patch_size[1] * helper.patch_size[2])
                dit_cond = helper.prepare_control_signal(
                    poses,
                    None,
                    intrinsics,
                    int(winner_video.shape[2]),
                    int(winner_video.shape[3]),
                    lat_f,
                    lat_h,
                    lat_w,
                    control_type="cam",
                    source_height=int(example.source_height),
                    source_width=int(example.source_width),
                )
                latent_loss_indices = strict_future_latent_indices(
                    total_frames=int(cfg.get("num_frames", 81) or 81),
                    prefix_len=example.prefix_len,
                    latent_frames=lat_f,
                    temporal_compression=int(cfg.get("temporal_compression", 4) or 4),
                )
            out.append(
                PrecomputedPair(
                    pair_id=example.pair_id,
                    prompt=example.prompt,
                    winner_latent=winner_latent.detach().cpu(),
                    loser_latent=loser_latent.detach().cpu(),
                    context=_to_cpu_tree(context),
                    y=y.detach().cpu(),
                    dit_cond=_to_cpu_tree(dit_cond),
                    seq_len=int(seq_len),
                    latent_loss_indices=latent_loss_indices,
                )
            )
            rows.append({"pair_id": example.pair_id, "index": index, "elapsed_sec": time.time() - start, "latent_shape": str(tuple(winner_latent.shape))})
    finally:
        helper.release_runtime_components()
        if dev.type == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
    _write_rows(out_dir / "precompute_latents.csv", rows)
    return out


def _prepared_from_cache(cache: PrecomputedPair, *, side: str, backend: LingBotFastDpoEnergy, timestep_sample: Any, noise: torch.Tensor) -> PreparedEnergyInput:
    latent = (cache.winner_latent if side == "winner" else cache.loser_latent).to(backend.device, dtype=backend.lowp_dtype)
    noise = noise.to(device=backend.device, dtype=latent.dtype)
    noisy = (1.0 - float(timestep_sample.sigma)) * latent + float(timestep_sample.sigma) * noise
    target = noise - latent
    return PreparedEnergyInput(
        target=target,
        noisy_latent=noisy,
        context=_to_device_tree(cache.context, backend.device),
        y=cache.y.to(backend.device, dtype=backend.lowp_dtype),
        dit_cond=_to_device_tree(cache.dit_cond, backend.device),
        seq_len=cache.seq_len,
        latent_loss_indices=list(cache.latent_loss_indices),
    )


def run_lingbot_fast_preflight(
    *,
    pair_manifest: str,
    out_dir: str,
    cfg: dict[str, Any],
    limit_pairs: int,
    max_steps: int,
    beta: float,
    seed: int,
    device: str,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    started = time.time()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if device == "cuda" and torch.cuda.is_available():
        device = "cuda:0"
    dataset = Prefix5DpoDataset(
        pair_manifest,
        repo_root=repo_root,
        limit_pairs=limit_pairs,
        num_frames=int(cfg.get("num_frames", 81) or 81),
        height=int(cfg.get("height", 480) or 480),
        width=int(cfg.get("width", 832) or 832),
        min_margin=0.0,
    )
    if len(dataset) <= 0:
        result = {"status": "BLOCKED_NO_PREFIX5_PAIRS", "pair_manifest": pair_manifest}
        (out / "preflight_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        return result

    precomputed = _precompute_pairs(dataset, cfg=cfg, device=device, out_dir=out)
    model_cfg = dict(cfg)
    model_cfg["dpo_skip_runtime_components_on_load"] = True
    backend = LingBotFastDpoEnergy(model_cfg, device=device, prefix_len=5)
    params = backend.trainable_parameters()
    optimizer = torch.optim.AdamW(
        params,
        lr=float(cfg.get("dpo_learning_rate", cfg.get("learning_rate", 1.0e-6)) or 1.0e-6),
        betas=(0.9, 0.95),
        weight_decay=float(cfg.get("weight_decay", 0.01) or 0.01),
    )
    rows: list[dict[str, Any]] = []
    finite = True
    nonzero_grad = False
    same_noise = True
    same_timestep = True
    error = ""
    for step in range(max(1, int(max_steps))):
        step_start = time.time()
        try:
            cache = precomputed[step % len(precomputed)]
            optimizer.zero_grad(set_to_none=True)
            timestep_sample, noise = backend.sample_timestep_and_noise(tuple(cache.winner_latent.shape), seed=int(seed) + step)
            winner = _prepared_from_cache(cache, side="winner", backend=backend, timestep_sample=timestep_sample, noise=noise)
            loser = _prepared_from_cache(cache, side="loser", backend=backend, timestep_sample=timestep_sample, noise=noise)
            policy_winner = backend.energy(winner, timestep_sample)
            policy_loser = backend.energy(loser, timestep_sample)
            with backend.reference_mode():
                ref_winner = backend.energy(winner, timestep_sample).detach()
                ref_loser = backend.energy(loser, timestep_sample).detach()
            loss = dpo_loss(policy_winner, policy_loser, ref_winner, ref_loser, beta=float(beta))
            if not torch.isfinite(loss).all().item():
                finite = False; error = "nonfinite_dpo_loss"; break
            loss.backward()
            grad_norm = _grad_norm(params)
            nonzero_grad = nonzero_grad or grad_norm > 0.0
            optimizer.step()
            diag = dpo_energy_diagnostics(policy_winner.detach(), policy_loser.detach(), ref_winner.detach(), ref_loser.detach(), beta=float(beta))
            winner_improvement = _scalar(ref_winner - policy_winner.detach())
            loser_degradation = _scalar(policy_loser.detach() - ref_loser)
            rows.append({
                **diag,
                "step": step + 1,
                "pair_id": cache.pair_id,
                "grad_norm": grad_norm,
                "winner_improvement": winner_improvement,
                "loser_degradation": loser_degradation,
                "same_noise": True,
                "same_timestep": True,
                "prefix_len": int(cache.prefix_len),
                "prediction_start_frame": int(cache.prediction_start_frame),
                "timestep_index": int(timestep_sample.index),
                "sigma": float(timestep_sample.sigma),
                "latent_loss_indices": " ".join(map(str, cache.latent_loss_indices)),
                "policy_trainable_params": int(backend.policy_trainable_params),
                "reference_trainable_params": 0,
                "step_time_sec": time.time() - step_start,
                "cuda_memory_allocated_gb": (torch.cuda.memory_allocated() / (1024**3) if torch.cuda.is_available() else 0.0),
                "cuda_memory_reserved_gb": (torch.cuda.memory_reserved() / (1024**3) if torch.cuda.is_available() else 0.0),
            })
        except Exception as exc:
            finite = False; error = repr(exc); break

    _write_rows(out / "energy_checks.csv", rows)
    metrics_jsonl = out / "training_metrics.jsonl"
    with metrics_jsonl.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    save_load_ok = False
    ckpt = out / "lingbot_fast_dpo_lora_state.pt"
    if rows:
        torch.save(extract_lora_state(backend.model), ckpt)
        saved = torch.load(ckpt, map_location="cpu")
        before = extract_lora_state(backend.model)
        load_lora_state(backend.model, saved)
        after = extract_lora_state(backend.model)
        save_load_ok = bool(before.keys() == after.keys() and all(torch.equal(before[k], after[k]) for k in before))
    status = "PASS" if rows and finite and same_noise and same_timestep and nonzero_grad and save_load_ok else "FAILED"
    result = {
        "status": status,
        "backend": "lingbot_fast_flow_matching_energy_precomputed_latents",
        "pair_manifest": pair_manifest,
        "pair_count": len(dataset),
        "steps": len(rows),
        "same_noise": same_noise,
        "same_timestep": same_timestep,
        "finite": finite,
        "error": error,
        "nonzero_grad": nonzero_grad,
        "save_load_ok": save_load_ok,
        "policy_trainable_params": getattr(backend, "policy_trainable_params", 0),
        "lora_inventory": getattr(backend, "lora_inventory", {}),
        "final_dpo_loss": rows[-1]["dpo_loss"] if rows else None,
        "final_implicit_accuracy": rows[-1]["implicit_accuracy"] if rows else None,
        "final_winner_improvement": rows[-1]["winner_improvement"] if rows else None,
        "final_loser_degradation": rows[-1]["loser_degradation"] if rows else None,
        "checkpoint": str(ckpt) if rows else "",
        "metrics": str(metrics_jsonl),
        "elapsed_seconds": time.time() - started,
        "device": device,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
    }
    (out / "preflight_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result
