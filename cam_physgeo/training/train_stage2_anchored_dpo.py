from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path
from typing import Iterable

from cam_physgeo.dpo.anchored_dataset import AnchoredPreferenceDataset
from cam_physgeo.dpo.dpo_loss import dpo_energy_diagnostics, dpo_loss
from cam_physgeo.training.train_utils import load_training_config


def _read_config(path: str | None) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return load_training_config(str(p))


def same_noise_timestep(
    *,
    batch_size: int,
    latent_shape: tuple[int, ...] = (4, 8, 16, 16),
    seed: int = 123,
    timestep: int = 799,
    device: str = "cpu",
):
    """Create paired winner/loser noise and timestep tensors.

    DPO comparisons are only meaningful when winner and loser share the same
    stochastic diffusion condition.  This helper is intentionally exported for
    tests and for preflight bookkeeping.
    """

    import torch

    gen = torch.Generator(device="cpu")
    gen.manual_seed(int(seed))
    noise = torch.randn((int(batch_size),) + tuple(latent_shape), generator=gen)
    noise = noise.to(device)
    timesteps = torch.full((int(batch_size),), int(timestep), dtype=torch.long, device=device)
    return {
        "winner_noise": noise.clone(),
        "loser_noise": noise.clone(),
        "winner_timestep": timesteps.clone(),
        "loser_timestep": timesteps.clone(),
    }


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value == "":
            return default
        out = float(value)
        if not math.isfinite(out):
            return default
        return out
    except Exception:
        return default


def _pair_base_energies(pair: dict) -> tuple[float, float]:
    """Map existing reward/metric scores to deterministic diagnostic energies."""

    winner_score = _safe_float(pair.get("winner", {}).get("score"), 1.0)
    loser_score = _safe_float(pair.get("loser", {}).get("score"), 0.0)
    return 1.0 - winner_score, 1.0 - loser_score


def _path_exists(path: str | None, root: Path) -> bool:
    if not path:
        return False
    p = Path(path)
    if p.exists():
        return True
    return (root / path).exists()


def validate_pair_assets(pair: dict, *, repo_root: str | Path = ".") -> list[str]:
    root = Path(repo_root)
    errors: list[str] = []
    condition = pair.get("condition") or {}
    for key in ["image", "poses", "intrinsics", "prompt"]:
        if not _path_exists(condition.get(key), root):
            errors.append(f"missing_condition_{key}")
    if condition.get("use_action") not in (False, "false", "False", 0):
        errors.append("condition_use_action_not_false")
    for side in ["winner", "loser"]:
        video = (pair.get(side) or {}).get("video")
        if not _path_exists(video, root):
            errors.append(f"missing_{side}_video")
    return errors


class DiagnosticEnergyPolicy:
    """Tiny differentiable DPO probe used before LingBot energy wiring.

    This module does not replace the LingBot-Fast backend.  It verifies pair
    loading, same-noise/timestep bookkeeping, DPO loss direction, optimizer
    updates, checkpoint save/load, and metric logging on real anchored pairs.
    """

    def __init__(self, *, device: str = "cpu") -> None:
        import torch

        self.torch = torch
        self.margin_gain = torch.nn.Parameter(torch.zeros((), dtype=torch.float32, device=device))
        self.optimizer = torch.optim.AdamW([self.margin_gain], lr=1e-2)

    def energies(self, winner_base, loser_base):
        gain = self.margin_gain
        return winner_base - 0.5 * gain, loser_base + 0.5 * gain

    def state_dict(self):
        return {"margin_gain": self.margin_gain.detach().cpu()}

    def load_state_dict(self, state: dict) -> None:
        with self.torch.no_grad():
            self.margin_gain.copy_(state["margin_gain"].to(self.margin_gain.device))


def _iter_limited(dataset: Iterable[dict], limit: int) -> list[dict]:
    rows = list(dataset)
    if limit > 0:
        rows = rows[:limit]
    return rows


def run_diagnostic_preflight(
    *,
    pair_manifest: str,
    out_dir: str,
    limit_pairs: int,
    max_steps: int,
    beta: float,
    seed: int,
    device: str,
    repo_root: str | Path = ".",
) -> dict:
    import torch

    started = time.time()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dataset = AnchoredPreferenceDataset(pair_manifest, min_margin=0.0)
    pairs = _iter_limited(dataset, limit_pairs)
    asset_errors = {p.get("pair_id", f"pair_{i}"): validate_pair_assets(p, repo_root=repo_root) for i, p in enumerate(pairs)}
    bad = {k: v for k, v in asset_errors.items() if v}
    if not pairs:
        result = {
            "status": "BLOCKED_NO_PAIRS",
            "pair_manifest": pair_manifest,
            "pair_count": 0,
            "bad_assets": bad,
        }
        (out / "preflight_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    if bad:
        result = {
            "status": "BLOCKED_BAD_PAIR_ASSETS",
            "pair_manifest": pair_manifest,
            "pair_count": len(pairs),
            "bad_assets": bad,
        }
        (out / "preflight_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    same = same_noise_timestep(batch_size=len(pairs), seed=seed, device=device)
    same_noise_ok = bool(torch.equal(same["winner_noise"], same["loser_noise"]))
    same_timestep_ok = bool(torch.equal(same["winner_timestep"], same["loser_timestep"]))

    policy = DiagnosticEnergyPolicy(device=device)
    rows = []
    max_steps = max(1, int(max_steps))
    for step in range(max_steps):
        pair = pairs[step % len(pairs)]
        winner_base, loser_base = _pair_base_energies(pair)
        winner_base_t = torch.tensor(winner_base, dtype=torch.float32, device=device)
        loser_base_t = torch.tensor(loser_base, dtype=torch.float32, device=device)
        ref_winner = winner_base_t.detach()
        ref_loser = loser_base_t.detach()
        policy_winner, policy_loser = policy.energies(winner_base_t, loser_base_t)
        loss = dpo_loss(policy_winner, policy_loser, ref_winner, ref_loser, beta=beta)
        policy.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        grad = policy.margin_gain.grad.detach().clone()
        policy.optimizer.step()
        diag = dpo_energy_diagnostics(policy_winner, policy_loser, ref_winner, ref_loser, beta=beta)
        diag.update(
            {
                "step": step + 1,
                "pair_id": pair.get("pair_id"),
                "grad_norm": float(grad.abs().cpu()),
                "margin_gain": float(policy.margin_gain.detach().cpu()),
                "same_noise": same_noise_ok,
                "same_timestep": same_timestep_ok,
            }
        )
        rows.append(diag)

    ckpt = out / "diagnostic_adapter_state.pt"
    torch.save(policy.state_dict(), ckpt)
    reloaded = DiagnosticEnergyPolicy(device=device)
    reloaded.load_state_dict(torch.load(ckpt, map_location=device))
    save_load_ok = bool(torch.allclose(policy.margin_gain.detach(), reloaded.margin_gain.detach()))

    metrics_path = out / "training_metrics.jsonl"
    with metrics_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    result = {
        "status": "PASS" if same_noise_ok and same_timestep_ok and save_load_ok and rows[-1]["grad_norm"] > 0 else "FAILED",
        "backend": "diagnostic_energy",
        "pair_manifest": pair_manifest,
        "pair_count": len(pairs),
        "steps": len(rows),
        "same_noise": same_noise_ok,
        "same_timestep": same_timestep_ok,
        "save_load_ok": save_load_ok,
        "final_dpo_loss": rows[-1]["dpo_loss"],
        "final_implicit_accuracy": rows[-1]["implicit_accuracy"],
        "final_margin_gain": rows[-1]["margin_gain"],
        "final_grad_norm": rows[-1]["grad_norm"],
        "checkpoint": str(ckpt),
        "metrics": str(metrics_path),
        "elapsed_seconds": time.time() - started,
    }
    (out / "preflight_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def probe_lingbot_fast_backend(*, out_dir: str) -> dict:
    """Record the current real-backend state without pretending to train."""

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "BLOCKED_FAST_ENERGY_BACKEND",
        "backend": "lingbot_fast",
        "reason": (
            "LingBot-Fast rollout initialization is available in prior artifacts, "
            "but the anchored DPO energy path has not yet exposed a callable "
            "winner/loser flow-matching energy function with frozen reference."
        ),
    }
    (out / "lingbot_fast_backend_probe.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="")
    parser.add_argument("--pair_manifest", default="")
    parser.add_argument("--out", default="reports/dpo_bf16_preflight")
    parser.add_argument("--backend", choices=["diagnostic_energy", "lingbot_fast"], default="diagnostic_energy")
    parser.add_argument("--plan_only", action="store_true")
    parser.add_argument("--run_preflight", action="store_true")
    parser.add_argument("--limit_pairs", type=int, default=8)
    parser.add_argument("--max_steps", type=int, default=2)
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args(argv)

    cfg = _read_config(args.config)
    pair_manifest = args.pair_manifest or cfg.get("pair_manifest", "manifests/anchored_dpo_probe_pairs.jsonl")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    dataset_status = {}
    try:
        ds = AnchoredPreferenceDataset(pair_manifest, min_margin=0.0)
        dataset_status = {
            "pair_manifest": pair_manifest,
            "pair_count": len(ds),
            "first_pair_id": ds[0].get("pair_id") if len(ds) else None,
        }
    except Exception as exc:
        dataset_status = {
            "pair_manifest": pair_manifest,
            "pair_count": 0,
            "error": repr(exc),
        }

    plan = {
        "stage": "stage2_anchored_dpo",
        "backend": args.backend,
        "config": cfg,
        "dataset": dataset_status,
        "limit_pairs": args.limit_pairs,
        "max_steps": args.max_steps,
        "beta": args.beta,
        "device": args.device,
        "run_preflight_requested": bool(args.run_preflight),
        "plan_only": bool(args.plan_only),
    }
    (out / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(plan, indent=2, sort_keys=True))

    if args.plan_only or not args.run_preflight:
        return 0
    if args.backend == "lingbot_fast":
        result = probe_lingbot_fast_backend(out_dir=str(out))
    else:
        result = run_diagnostic_preflight(
            pair_manifest=pair_manifest,
            out_dir=str(out),
            limit_pairs=args.limit_pairs,
            max_steps=args.max_steps,
            beta=args.beta,
            seed=args.seed,
            device=args.device,
            repo_root=Path.cwd(),
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
