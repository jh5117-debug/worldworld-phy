from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.dpo.failure_diagnostics import _make_timestep_sample
from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy
from cam_physgeo.dpo.winner_anchor_only_runner import (
    _cfg,
    _load_winner_inputs,
    _prepare_winner_cached,
    cuda_stats,
    ensure_runtime_ready,
    offload_runtime_after_cache,
    reviewed_pairs,
)


STAGES = [
    "0_initial",
    "1_load_policy_only",
    "2_load_reference_only_if_needed",
    "3_precompute_ref_energy_no_grad",
    "4_unload_reference",
    "5_load_or_cache_winner_latents",
    "6_policy_forward_no_grad",
    "7_policy_forward_grad",
    "8_backward",
    "9_optimizer_step",
    "10_post_update_recompute_no_grad",
    "11_after_empty_cache",
]


def _record(path: Path, stage: str, notes: str) -> dict[str, Any]:
    row = {"stage": stage, **cuda_stats(), "notes": notes}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
        f.flush()
    return row


def run_memory_audit(args: argparse.Namespace) -> dict[str, Any]:
    out = Path(args.output)
    if out.exists():
        out.unlink()
    if torch.cuda.is_available():
        torch.cuda.set_device(int(args.gpu))
        torch.cuda.reset_peak_memory_stats()
    device = f"cuda:{int(args.gpu)}" if torch.cuda.is_available() else "cpu"
    rows: list[dict[str, Any]] = []
    rows.append(_record(out, "0_initial", "connected; no model loaded"))
    cfg = _cfg(args.config, frames=int(args.used_window_frames), height=int(args.height), width=int(args.width), runtime_device=str(args.runtime_device), gradient_checkpointing=True)
    backend = LingBotFastDpoEnergy(cfg, device=device, prefix_len=5)
    ensure_runtime_ready(backend)
    rows.append(_record(out, "1_load_policy_only", "policy loaded; LoRA trainables only; runtime ready for cache"))
    rows.append(_record(out, "2_load_reference_only_if_needed", "no separate reference model loaded; reference uses LoRA scaling zero under no_grad"))
    pairs = reviewed_pairs(args.pair_manifest, int(args.num_pairs))
    if not pairs:
        raise RuntimeError("no reviewed pairs found")
    video, prompt, poses, intrinsics, sh, sw = _load_winner_inputs(
        pairs[0],
        repo_root=args.repo_root,
        frames=int(args.used_window_frames),
        height=int(args.height),
        width=int(args.width),
        prefix_len=5,
        prediction_start_frame=5,
    )
    ts = _make_timestep_sample(backend, float(args.target_sigma))
    prepared = _prepare_winner_cached(
        backend,
        video=video,
        prompt=prompt,
        poses=poses,
        intrinsics=intrinsics,
        source_height=sh,
        source_width=sw,
        timestep_sample=ts,
        seed=int(args.seed),
        total_frames=int(args.used_window_frames),
    )
    offload_runtime_after_cache(backend)
    rows.append(_record(out, "5_load_or_cache_winner_latents", "winner-only fixed timestep/noise prepared; loser not decoded; runtime offloaded to CPU"))
    with torch.no_grad(), backend.reference_mode():
        ref_energy = backend.energy(prepared, ts).detach()
    rows.append(_record(out, "3_precompute_ref_energy_no_grad", f"E_ref_winner={float(ref_energy.detach().float().cpu())}"))
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    rows.append(_record(out, "4_unload_reference", "reference mode exited; no separate ref object exists; empty_cache called"))
    with torch.no_grad():
        policy_energy = backend.energy(prepared, ts).detach()
    rows.append(_record(out, "6_policy_forward_no_grad", f"E_policy_winner={float(policy_energy.detach().float().cpu())}"))
    rows.append(_record(out, "7_policy_forward_grad", "skipped in no-training audit; measured by winner_anchor_only_runner"))
    rows.append(_record(out, "8_backward", "skipped in no-training audit; measured by winner_anchor_only_runner"))
    rows.append(_record(out, "9_optimizer_step", "skipped in no-training audit; measured by winner_anchor_only_runner"))
    with torch.no_grad():
        post_energy = backend.energy(prepared, ts).detach()
    rows.append(_record(out, "10_post_update_recompute_no_grad", f"dry-run recompute E_policy_winner={float(post_energy.detach().float().cpu())}"))
    del prepared, backend, video, poses, intrinsics, policy_energy, post_energy, ref_energy
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    rows.append(_record(out, "11_after_empty_cache", "debug complete; cache emptied"))
    summary = {
        "status": "MEMORY_AUDIT_NO_TRAINING_PASS",
        "output": str(out),
        "separate_reference_loaded": False,
        "reference_removed_from_training_graph": True,
        "loser_branch_loaded": False,
        "cached_winner_input_used": True,
        "used_window_frames": int(args.used_window_frames),
    }
    summary_path = out.with_name("memory_audit_summary.md")
    summary_path.write_text(
        "Current Status:\nPASS_DIAGNOSTIC_NO_TRAINING\n\n"
        "# v8c Winner-Anchor Memory Audit\n\n"
        "- Separate reference model loaded: no.\n"
        "- Reference in training graph: no; reference energy is no_grad with LoRA scaling zero.\n"
        "- Loser branch loaded: no.\n"
        "- Cached winner input used: yes.\n"
        f"- Used window frames: {args.used_window_frames}.\n"
        "- Backward/optimizer stages: skipped in this no-training audit and measured by the runner.\n"
        "- Preliminary conclusion: v8c removes the separate reference and loser branches; remaining risk is policy forward/backward activation cost.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="No-training memory audit for v8c winner-anchor path.")
    parser.add_argument("--pair_manifest", required=True)
    parser.add_argument("--num_pairs", type=int, default=1)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    parser.add_argument("--repo_root", default=".")
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--used_window_frames", type=int, default=81)
    parser.add_argument("--target_sigma", type=float, default=0.35)
    parser.add_argument("--runtime_device", default="cuda")
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args(argv)
    run_memory_audit(args)


if __name__ == "__main__":
    main()
