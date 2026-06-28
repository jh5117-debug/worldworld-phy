from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.dpo.anchored_dpo_trainer import _grad_norm, _precompute_pairs, _prepared_from_cache
from cam_physgeo.dpo.full_real_energy_audit import _load_condition_index, _normalize_protocol_v1_pairs_for_loader
from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy
from cam_physgeo.dpo.objective_ablation import _energy_margin, _reward_margin
from cam_physgeo.dpo.prefix5_dpo_dataset import Prefix5DpoDataset


def _load_yaml(path: str | Path) -> dict[str, Any]:
    import yaml

    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise TypeError(f"expected mapping config in {path}")
    return dict(data)


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _nested_get(data: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _safe_float(value: Any, default: float = float("nan")) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed"}


def _normalize_pairs(rows: list[dict[str, Any]], condition_manifest: str | Path) -> list[dict[str, Any]]:
    out = [json.loads(json.dumps(row)) for row in rows]
    _normalize_protocol_v1_pairs_for_loader(out, _load_condition_index(condition_manifest))
    expected = list(range(5, 81))
    for pair in out:
        pair.setdefault("loss_frame_indices", expected)
        pair.setdefault("reward_frame_indices", expected)
        pair.setdefault("same_prefix", True)
        pair.setdefault("same_prompt", True)
        pair.setdefault("same_poses", True)
        pair.setdefault("same_intrinsics", True)
        pair.setdefault("condition", {}).setdefault("prefix_len", 5)
        pair.setdefault("condition", {}).setdefault("prediction_start_frame", 5)
        pair.setdefault("winner", {}).setdefault("future_frame_indices", expected)
        pair.setdefault("loser", {}).setdefault("future_frame_indices", expected)
    return out


def _summary_row(name: str, pair: dict[str, Any]) -> dict[str, Any]:
    return {
        "subset": name,
        "pair_id": pair.get("pair_id"),
        "pair_type": pair.get("pair_type"),
        "corruption_type": _nested_get(pair, "loser.corruption_type", ""),
        "Delta_ref": _energy_margin(pair),
        "reward_margin": _reward_margin(pair),
        "reference_relative_margin": _safe_float(pair.get("reference_relative_margin"), _safe_float((pair.get("energy_audit") or {}).get("reference_relative_margin"), 0.0)),
        "visual_valid": _boolish(_nested_get(pair, "codex_audit.valid_preference", True)),
        "medium_hard": _boolish(pair.get("medium_hard", True)),
        "winner_source": _nested_get(pair, "winner.source", ""),
        "loser_source": _nested_get(pair, "loser.source", ""),
    }


def build_subsets(args: argparse.Namespace) -> None:
    rows = _normalize_pairs(_load_jsonl(args.ready_pairs), args.condition_manifest)
    type_a = [row for row in rows if row.get("pair_type") == "local_corruption"]
    type_b = [row for row in rows if row.get("pair_type") == "gt_vs_medium_hard_rollout"]
    key = lambda row: (_energy_margin(row), _reward_margin(row))
    type_a = sorted(type_a, key=key, reverse=True)
    type_b = sorted(type_b, key=key, reverse=True)
    subsets = {
        "d0_one_pair_typeB": type_b[:1],
        "d1_five_typeB": type_b[:5],
        "d2_five_typeA": type_a[:5],
        "d3_mixed8": type_b[:4] + type_a[:4],
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary: list[dict[str, Any]] = []
    for name, subset in subsets.items():
        _write_jsonl(out_dir / f"{name}.jsonl", subset)
        summary.extend(_summary_row(name, pair) for pair in subset)
    _write_csv(args.summary_csv, summary)
    print(json.dumps({k: len(v) for k, v in subsets.items()}, indent=2, sort_keys=True))


def _config(args: argparse.Namespace, *, rank: int | None = None, target_groups: list[str] | None = None, block_end: int | None = None) -> dict[str, Any]:
    cfg = _load_yaml(args.config)
    cfg["num_frames"] = int(args.num_frames)
    cfg["height"] = int(args.height)
    cfg["width"] = int(args.width)
    cfg["dpo_runtime_device"] = args.runtime_device or args.device
    cfg["dpo_skip_runtime_components_on_load"] = True
    if rank is not None:
        cfg["student_lora_rank"] = int(rank)
        cfg["student_lora_alpha"] = int(rank)
    if target_groups:
        cfg["student_lora_target_groups"] = target_groups
        cfg["student_lora_required_groups"] = target_groups
    if block_end is not None:
        cfg["student_lora_block_start"] = 0
        cfg["student_lora_block_end"] = int(block_end)
    return cfg


def _device(value: str) -> str:
    if value == "cuda" and torch.cuda.is_available():
        return "cuda:0"
    return value


def _dataset(path: str, args: argparse.Namespace, *, limit_pairs: int = 0) -> Prefix5DpoDataset:
    return Prefix5DpoDataset(
        path,
        repo_root=args.repo_root,
        limit_pairs=limit_pairs,
        num_frames=int(args.num_frames),
        height=int(args.height),
        width=int(args.width),
        min_margin=0.0,
    )


def _pair_meta(path: str | Path) -> dict[str, dict[str, Any]]:
    return {str(row.get("pair_id")): row for row in _load_jsonl(path)}


def _lora_norm(params: list[torch.nn.Parameter]) -> float:
    total = 0.0
    with torch.no_grad():
        for p in params:
            total += float(p.detach().float().norm().cpu()) ** 2
    return math.sqrt(total)


def _flat_grad(params: list[torch.nn.Parameter]) -> torch.Tensor:
    chunks = []
    for p in params:
        if p.grad is None:
            chunks.append(torch.zeros(p.numel(), dtype=torch.float32))
        else:
            chunks.append(p.grad.detach().float().flatten().cpu())
    return torch.cat(chunks) if chunks else torch.zeros(1)


def run_overfit(args: argparse.Namespace) -> None:
    out = Path(args.out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    cfg = _config(args, rank=args.rank, target_groups=args.target_groups.split(",") if args.target_groups else None, block_end=args.block_end)
    dev = _device(args.device)
    dataset = _dataset(args.pair_manifest, args, limit_pairs=1)
    cache = _precompute_pairs(dataset, cfg=cfg, device=dev, out_dir=out.parent)[0]
    backend = LingBotFastDpoEnergy(cfg, device=dev, prefix_len=5)
    params = backend.trainable_parameters()
    optimizer = torch.optim.AdamW(params, lr=float(args.learning_rate), betas=(0.9, 0.95), weight_decay=float(args.weight_decay))
    rows: list[dict[str, Any]] = []
    for step in range(int(args.max_steps)):
        started = time.time()
        optimizer.zero_grad(set_to_none=True)
        ts, noise = backend.sample_timestep_and_noise(tuple(cache.winner_latent.shape), seed=int(args.seed) + step)
        if args.mode == "winner_only":
            prepared = _prepared_from_cache(cache, side="winner", backend=backend, timestep_sample=ts, noise=noise)
            policy = backend.energy(prepared, ts)
            with backend.reference_mode():
                ref = backend.energy(prepared, ts).detach()
            loss = policy
            winner_improvement = float((ref - policy.detach()).cpu())
            loser_degradation = float("nan")
            energy = float(policy.detach().cpu())
            ref_energy = float(ref.cpu())
        elif args.mode == "loser_only":
            prepared = _prepared_from_cache(cache, side="loser", backend=backend, timestep_sample=ts, noise=noise)
            policy = backend.energy(prepared, ts)
            with backend.reference_mode():
                ref = backend.energy(prepared, ts).detach()
            loss = -policy
            winner_improvement = float("nan")
            loser_degradation = float((policy.detach() - ref).cpu())
            energy = float(policy.detach().cpu())
            ref_energy = float(ref.cpu())
        else:
            raise ValueError(args.mode)
        if not torch.isfinite(loss).all().item():
            break
        before = _lora_norm(params)
        loss.backward()
        grad = _grad_norm(params)
        optimizer.step()
        after = _lora_norm(params)
        rows.append({
            "mode": args.mode,
            "step": step + 1,
            "pair_id": cache.pair_id,
            "loss": float(loss.detach().cpu()),
            "policy_energy": energy,
            "ref_energy": ref_energy,
            "winner_improvement": winner_improvement,
            "loser_degradation": loser_degradation,
            "grad_norm": grad,
            "lora_param_norm": after,
            "update_norm_proxy": abs(after - before),
            "timestep_index": int(ts.index),
            "sigma": float(ts.sigma),
            "step_time_sec": time.time() - started,
            "cuda_memory_gb": torch.cuda.memory_allocated() / (1024 ** 3) if torch.cuda.is_available() else 0.0,
            "target_groups": ",".join(cfg.get("student_lora_target_groups", [])),
            "rank": cfg.get("student_lora_rank"),
            "block_end": cfg.get("student_lora_block_end"),
            "policy_trainable_params": getattr(backend, "policy_trainable_params", 0),
        })
    _write_csv(out, rows)
    print(out)


def run_gradient_decomp(args: argparse.Namespace) -> None:
    out = Path(args.out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    cfg = _config(args)
    dev = _device(args.device)
    dataset = _dataset(args.pair_manifest, args, limit_pairs=int(args.limit_pairs))
    caches = _precompute_pairs(dataset, cfg=cfg, device=dev, out_dir=out.parent)
    backend = LingBotFastDpoEnergy(cfg, device=dev, prefix_len=5)
    params = backend.trainable_parameters()
    rows = []
    for idx, cache in enumerate(caches):
        ts, noise = backend.sample_timestep_and_noise(tuple(cache.winner_latent.shape), seed=int(args.seed) + idx)
        winner = _prepared_from_cache(cache, side="winner", backend=backend, timestep_sample=ts, noise=noise)
        loser = _prepared_from_cache(cache, side="loser", backend=backend, timestep_sample=ts, noise=noise)
        backend.model.zero_grad(set_to_none=True)
        e_w = backend.energy(winner, ts)
        e_w.backward()
        g_w = _flat_grad(params)
        backend.model.zero_grad(set_to_none=True)
        e_l = backend.energy(loser, ts)
        e_l.backward()
        g_l = _flat_grad(params)
        norm_w = float(g_w.norm())
        norm_l = float(g_l.norm())
        cos = float(torch.nn.functional.cosine_similarity(g_w, g_l, dim=0, eps=1e-12))
        cos_minus = float(torch.nn.functional.cosine_similarity(-g_w, g_l, dim=0, eps=1e-12))
        rows.append({
            "pair_id": cache.pair_id,
            "E_policy_winner": float(e_w.detach().cpu()),
            "E_policy_loser": float(e_l.detach().cpu()),
            "grad_norm_winner": norm_w,
            "grad_norm_loser": norm_l,
            "winner_loser_grad_ratio": norm_w / max(norm_l, 1e-12),
            "cosine_gw_gl": cos,
            "cosine_minus_gw_plus_gl": cos_minus,
            "conflict_score": max(0.0, cos),
            "timestep_index": int(ts.index),
            "sigma": float(ts.sigma),
        })
    _write_csv(out, rows)
    print(out)


def _make_timestep_sample(backend: LingBotFastDpoEnergy, target_sigma: float):
    from physical_consistency.trainers.stage1_components import TimestepSample

    sigmas = backend.helper.sigmas.detach().float().cpu()
    indices = getattr(backend.helper, "high_noise_indices", torch.arange(len(sigmas))).detach().long().cpu()
    best = min(indices.tolist(), key=lambda idx: abs(float(sigmas[int(idx)]) - float(target_sigma)))
    timestep = backend.helper.timesteps_schedule[int(best)].to(backend.device).unsqueeze(0)
    sigma = float(backend.helper.sigmas[int(best)].item())
    return TimestepSample(index=int(best), sigma=sigma, timestep=timestep, weight=1.0, branch=backend.helper.branch_for_timestep_index(int(best)))


def run_sigma_sensitivity(args: argparse.Namespace) -> None:
    out = Path(args.out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    cfg = _config(args)
    dev = _device(args.device)
    dataset = _dataset(args.pair_manifest, args, limit_pairs=int(args.limit_pairs))
    caches = _precompute_pairs(dataset, cfg=cfg, device=dev, out_dir=out.parent)
    backend = LingBotFastDpoEnergy(cfg, device=dev, prefix_len=5)
    rows = []
    bins = [(0.05, 0.20), (0.20, 0.50), (0.50, 0.80), (0.80, 0.95)]
    for idx, cache in enumerate(caches):
        for lo, hi in bins:
            target = (lo + hi) / 2.0
            ts = _make_timestep_sample(backend, target)
            gen = torch.Generator(device=backend.device)
            gen.manual_seed(int(args.seed) + idx * 100 + int(target * 1000))
            noise = torch.randn(tuple(cache.winner_latent.shape), device=backend.device, dtype=backend.lowp_dtype, generator=gen)
            winner = _prepared_from_cache(cache, side="winner", backend=backend, timestep_sample=ts, noise=noise)
            loser = _prepared_from_cache(cache, side="loser", backend=backend, timestep_sample=ts, noise=noise)
            with torch.no_grad():
                pw = backend.energy(winner, ts)
                pl = backend.energy(loser, ts)
                with backend.reference_mode():
                    rw = backend.energy(winner, ts)
                    rl = backend.energy(loser, ts)
            dp = float((pl - pw).detach().cpu())
            dr = float((rl - rw).detach().cpu())
            rows.append({
                "pair_id": cache.pair_id,
                "sigma_bin": f"{lo:.2f}-{hi:.2f}",
                "target_sigma": target,
                "actual_sigma": float(ts.sigma),
                "timestep_index": int(ts.index),
                "E_policy_winner": float(pw.detach().cpu()),
                "E_policy_loser": float(pl.detach().cpu()),
                "Delta_policy": dp,
                "E_ref_winner": float(rw.detach().cpu()),
                "E_ref_loser": float(rl.detach().cpu()),
                "Delta_ref": dr,
                "reference_relative_margin": dp - dr,
            })
    _write_csv(out, rows)
    print(out)


def run_beta_utility(args: argparse.Namespace) -> None:
    rows_in = []
    for p in args.inputs.split(","):
        path = Path(p)
        if path.suffix == ".jsonl":
            rows_in.extend(_load_jsonl(path))
        elif path.exists():
            with path.open(newline="", encoding="utf-8") as f:
                rows_in.extend(csv.DictReader(f))
    betas = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
    rows = []
    for i, row in enumerate(rows_in):
        pair_id = row.get("pair_id", f"row_{i}")
        delta_policy = _safe_float(row.get("Delta_policy"), _safe_float(row.get("delta_policy"), _energy_margin(row)))
        delta_ref = _safe_float(row.get("Delta_ref"), _safe_float(row.get("delta_ref"), _energy_margin(row)))
        u = delta_policy - delta_ref
        for beta in betas:
            z = beta * u
            sig = 1.0 / (1.0 + math.exp(-max(min(z, 60.0), -60.0)))
            grad_scale = beta * (1.0 / (1.0 + math.exp(max(min(z, 60.0), -60.0))))
            rows.append({
                "pair_id": pair_id,
                "pair_type": row.get("pair_type", ""),
                "beta": beta,
                "Delta_policy": delta_policy,
                "Delta_ref": delta_ref,
                "u": u,
                "sigmoid_beta_u": sig,
                "gradient_scale": grad_scale,
                "near_zero": abs(u) < 1e-4,
                "saturated": sig < 0.01 or sig > 0.99,
            })
    _write_csv(args.out_csv, rows)
    print(args.out_csv)


def run_local_mask_audit(args: argparse.Namespace) -> None:
    rows = []
    for pair in _load_jsonl(args.pair_manifest):
        span = _nested_get(pair, "loser.affected_time_span")
        region = _nested_get(pair, "loser.affected_region")
        mask = _nested_get(pair, "loser.affected_mask_path")
        rows.append({
            "pair_id": pair.get("pair_id"),
            "pair_type": pair.get("pair_type"),
            "corruption_type": _nested_get(pair, "loser.corruption_type", ""),
            "affected_time_span_exists": span is not None and span != "",
            "affected_region_exists": region is not None and region != "",
            "affected_mask_exists": mask is not None and mask != "",
            "affected_time_span": span,
            "affected_region": region,
            "affected_mask_path": mask,
            "localdpo_complete_spatial_mask": bool(mask),
            "current_localdpo_level": "spatial_region" if mask else ("metadata_region_only" if region else ("time_only" if span else "missing")),
        })
    _write_csv(args.out_csv, rows)
    print(args.out_csv)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build-subsets")
    b.add_argument("--ready_pairs", default="reports/dpo_preference_protocol_v1/dpo_ready_pairs.jsonl")
    b.add_argument("--condition_manifest", default="manifests/screen16_v2v5.jsonl")
    b.add_argument("--out_dir", default="manifests/dpo_diagnostics")
    b.add_argument("--summary_csv", default="reports/dpo_failure_diagnostics/subset_summary.csv")
    b.set_defaults(func=build_subsets)

    def add_common(p):
        p.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
        p.add_argument("--repo_root", default=".")
        p.add_argument("--device", default="cuda")
        p.add_argument("--runtime_device", default="cuda")
        p.add_argument("--num_frames", type=int, default=81)
        p.add_argument("--height", type=int, default=480)
        p.add_argument("--width", type=int, default=832)
        p.add_argument("--seed", type=int, default=123)

    o = sub.add_parser("overfit")
    add_common(o)
    o.add_argument("--mode", choices=["winner_only", "loser_only"], required=True)
    o.add_argument("--pair_manifest", required=True)
    o.add_argument("--out_csv", required=True)
    o.add_argument("--max_steps", type=int, default=10)
    o.add_argument("--learning_rate", type=float, default=1e-6)
    o.add_argument("--weight_decay", type=float, default=0.01)
    o.add_argument("--rank", type=int, default=None)
    o.add_argument("--target_groups", default="")
    o.add_argument("--block_end", type=int, default=None)
    o.set_defaults(func=run_overfit)

    g = sub.add_parser("gradient-decomp")
    add_common(g)
    g.add_argument("--pair_manifest", required=True)
    g.add_argument("--out_csv", required=True)
    g.add_argument("--limit_pairs", type=int, default=5)
    g.set_defaults(func=run_gradient_decomp)

    s = sub.add_parser("sigma-sensitivity")
    add_common(s)
    s.add_argument("--pair_manifest", required=True)
    s.add_argument("--out_csv", required=True)
    s.add_argument("--limit_pairs", type=int, default=5)
    s.set_defaults(func=run_sigma_sensitivity)

    u = sub.add_parser("beta-utility")
    u.add_argument("--inputs", required=True)
    u.add_argument("--out_csv", required=True)
    u.set_defaults(func=run_beta_utility)

    m = sub.add_parser("local-mask-audit")
    m.add_argument("--pair_manifest", required=True)
    m.add_argument("--out_csv", required=True)
    m.set_defaults(func=run_local_mask_audit)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
