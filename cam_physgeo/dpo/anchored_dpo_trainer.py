from __future__ import annotations

import csv
import json
import math
import os
import time
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.dpo.dpo_loss import dpo_energy_diagnostics, dpo_loss
from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy, extract_lora_state, load_lora_state
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

    backend = LingBotFastDpoEnergy(cfg, device=device, prefix_len=5)
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
            example = dataset[step % len(dataset)]
            optimizer.zero_grad(set_to_none=True)
            energies = backend.pair_energies(example, seed=int(seed) + step)
            loss = dpo_loss(
                energies.policy_winner_energy,
                energies.policy_loser_energy,
                energies.ref_winner_energy,
                energies.ref_loser_energy,
                beta=float(beta),
            )
            if not torch.isfinite(loss).all().item():
                finite = False
                error = "nonfinite_dpo_loss"
                break
            loss.backward()
            grad_norm = _grad_norm(params)
            nonzero_grad = nonzero_grad or grad_norm > 0.0
            optimizer.step()
            diag = dpo_energy_diagnostics(
                energies.policy_winner_energy.detach(),
                energies.policy_loser_energy.detach(),
                energies.ref_winner_energy.detach(),
                energies.ref_loser_energy.detach(),
                beta=float(beta),
            )
            same_noise = same_noise and bool(energies.same_noise)
            same_timestep = same_timestep and bool(energies.same_timestep)
            winner_improvement = _scalar(energies.ref_winner_energy - energies.policy_winner_energy.detach())
            loser_degradation = _scalar(energies.policy_loser_energy.detach() - energies.ref_loser_energy)
            rows.append(
                {
                    **diag,
                    "step": step + 1,
                    "pair_id": example.pair_id,
                    "grad_norm": grad_norm,
                    "winner_improvement": winner_improvement,
                    "loser_degradation": loser_degradation,
                    "same_noise": bool(energies.same_noise),
                    "same_timestep": bool(energies.same_timestep),
                    "prefix_len": int(energies.prefix_len),
                    "prediction_start_frame": int(energies.prediction_start_frame),
                    "timestep_index": int(energies.timestep_index),
                    "sigma": float(energies.sigma),
                    "latent_loss_indices": " ".join(map(str, energies.latent_loss_indices)),
                    "policy_trainable_params": int(energies.policy_trainable_params),
                    "reference_trainable_params": int(energies.reference_trainable_params),
                    "step_time_sec": time.time() - step_start,
                    "cuda_memory_allocated_gb": (torch.cuda.memory_allocated() / (1024**3) if torch.cuda.is_available() else 0.0),
                    "cuda_memory_reserved_gb": (torch.cuda.memory_reserved() / (1024**3) if torch.cuda.is_available() else 0.0),
                }
            )
        except Exception as exc:
            finite = False
            error = repr(exc)
            break

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
        "backend": "lingbot_fast_flow_matching_energy",
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
