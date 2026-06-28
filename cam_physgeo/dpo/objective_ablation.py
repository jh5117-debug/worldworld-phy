from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.dpo.anchored_dpo_trainer import (
    _grad_norm,
    _precompute_pairs,
    _prepared_from_cache,
    _scalar,
    _write_rows,
)
from cam_physgeo.dpo.dpo_loss import dpo_energy_diagnostics, dpo_loss
from cam_physgeo.dpo.full_real_energy_audit import (
    _load_condition_index,
    _normalize_protocol_v1_pairs_for_loader,
)
from cam_physgeo.dpo.lingbot_fast_energy import (
    LingBotFastDpoEnergy,
    extract_lora_state,
    load_lora_state,
)
from cam_physgeo.dpo.prefix5_dpo_dataset import Prefix5DpoDataset


OBJECTIVES = {"standard", "sdpo", "linear", "localdpo"}


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return rows
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
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_yaml(path: str | Path) -> dict[str, Any]:
    import yaml

    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise TypeError(f"expected mapping config in {path}")
    return dict(data)


def _safe_float(value: Any, default: float = float("nan")) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _nested_get(data: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed"}


def _reward_margin(pair: dict[str, Any]) -> float:
    direct = _safe_float(pair.get("reward_margin"))
    if math.isfinite(direct):
        return direct
    direct = _safe_float(pair.get("margin"))
    if math.isfinite(direct):
        return direct
    winner = pair.get("winner", {}).get("reward", {}) or {}
    loser = pair.get("loser", {}).get("reward", {}) or {}
    return _safe_float(winner.get("R_total"), 0.0) - _safe_float(loser.get("R_total"), 0.0)


def _energy_margin(pair: dict[str, Any]) -> float:
    for key in ("Delta_ref", "delta_ref", "energy_margin"):
        value = _safe_float(pair.get(key))
        if math.isfinite(value):
            return value
    audit = pair.get("energy_audit", {}) or {}
    for key in ("Delta_ref", "delta_ref", "energy_margin"):
        value = _safe_float(audit.get(key))
        if math.isfinite(value):
            return value
    return 0.0


def _reference_relative_margin(pair: dict[str, Any]) -> float:
    for key in ("reference_relative_margin", "ref_relative_margin"):
        value = _safe_float(pair.get(key))
        if math.isfinite(value):
            return value
    audit = pair.get("energy_audit", {}) or {}
    value = _safe_float(audit.get("reference_relative_margin"))
    if math.isfinite(value):
        return value
    return 0.0


def _normalize_pairs(rows: list[dict[str, Any]], condition_manifest: str | Path) -> list[dict[str, Any]]:
    normalized = [json.loads(json.dumps(row)) for row in rows]
    condition_index = _load_condition_index(condition_manifest)
    _normalize_protocol_v1_pairs_for_loader(normalized, condition_index)
    expected = list(range(5, 81))
    for pair in normalized:
        pair.setdefault("loss_frame_indices", expected)
        pair.setdefault("reward_frame_indices", expected)
        pair.setdefault("same_prefix", True)
        pair.setdefault("same_prompt", True)
        pair.setdefault("same_poses", True)
        pair.setdefault("same_intrinsics", True)
        condition = pair.setdefault("condition", {})
        condition.setdefault("prefix_len", 5)
        condition.setdefault("prediction_start_frame", 5)
        pair.setdefault("winner", {}).setdefault("future_frame_indices", expected)
        pair.setdefault("loser", {}).setdefault("future_frame_indices", expected)
    return normalized


def _pair_summary_row(pair: dict[str, Any], subset: str) -> dict[str, Any]:
    return {
        "subset": subset,
        "pair_id": pair.get("pair_id"),
        "pair_type": pair.get("pair_type"),
        "corruption_type": _nested_get(pair, "loser.corruption_type", ""),
        "reward_margin": _reward_margin(pair),
        "Delta_ref": _energy_margin(pair),
        "Delta_policy": _safe_float(pair.get("Delta_policy"), _safe_float((pair.get("energy_audit") or {}).get("Delta_policy"), 0.0)),
        "reference_relative_margin": _reference_relative_margin(pair),
        "visual_valid": _boolish(_nested_get(pair, "codex_audit.valid_preference", True)),
        "medium_hard": _boolish(pair.get("medium_hard", True)),
        "winner_quality": _safe_float(_nested_get(pair, "winner.quality.visual_quality", ""), ""),
        "loser_quality": _safe_float(_nested_get(pair, "loser.quality.visual_quality", ""), ""),
        "winner_source": _nested_get(pair, "winner.source", ""),
        "loser_source": _nested_get(pair, "loser.source", ""),
    }


def _top_by_energy(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (_energy_margin(row), _reward_margin(row)), reverse=True)[:count]


def _round_robin_corruption(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(rows, key=lambda r: (_energy_margin(r), _reward_margin(r)), reverse=True):
        key = str(_nested_get(row, "loser.corruption_type", "unknown") or "unknown")
        buckets.setdefault(key, []).append(row)
    selected: list[dict[str, Any]] = []
    while len(selected) < count and any(buckets.values()):
        for key in sorted(buckets):
            if buckets[key]:
                selected.append(buckets[key].pop(0))
                if len(selected) >= count:
                    break
    return selected


def build_subsets(args: argparse.Namespace) -> None:
    ready = _normalize_pairs(_load_jsonl(args.ready_pairs), args.condition_manifest)
    local = _normalize_pairs(_load_jsonl(args.localdpo_pairs), args.condition_manifest)
    type_a = [row for row in ready if str(row.get("pair_type")) == "local_corruption"]
    type_b = [row for row in ready if str(row.get("pair_type")) == "gt_vs_medium_hard_rollout"]
    s0 = _top_by_energy(type_b, 4) + _top_by_energy(type_a, 4)
    s1 = _top_by_energy(type_b, 16) + _top_by_energy(type_a, 4)
    s2 = _top_by_energy(type_b, 16) + _top_by_energy(type_a, 16)
    local_candidates = [
        row for row in local
        if _nested_get(row, "loser.affected_region", None) is not None
        or _nested_get(row, "loser.affected_time_span", None) is not None
        or _nested_get(row, "loser.affected_mask_path", None) is not None
    ]
    s_local = _round_robin_corruption(local_candidates or local, 16)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subsets = {
        "s0_sanity_8": s0,
        "s1_probe_20": s1,
        "s2_probe_32_optional": s2,
        "s_localdpo_16": s_local,
    }
    summary: list[dict[str, Any]] = []
    for name, rows in subsets.items():
        _write_jsonl(out_dir / f"{name}.jsonl", rows)
        summary.extend(_pair_summary_row(row, name) for row in rows)
    _write_csv(args.summary_csv, summary)
    print(json.dumps({name: len(rows) for name, rows in subsets.items()}, indent=2, sort_keys=True))


def winner_contribution_ratio(winner_improvement: torch.Tensor | float, loser_degradation: torch.Tensor | float, eps: float = 1e-8) -> torch.Tensor:
    if not torch.is_tensor(winner_improvement):
        winner_improvement = torch.tensor(float(winner_improvement))
    if not torch.is_tensor(loser_degradation):
        loser_degradation = torch.tensor(float(loser_degradation), device=winner_improvement.device)
    positive_winner = torch.clamp(winner_improvement, min=0.0)
    positive_loser = torch.clamp(loser_degradation, min=0.0)
    return positive_winner / (positive_winner + positive_loser + float(eps))


def reward_to_pair_weight(reward_margin: float, min_margin: float = 0.10, max_margin: float = 0.45) -> float:
    if not math.isfinite(reward_margin):
        return 1.0
    if max_margin <= min_margin:
        return 1.0
    x = (float(reward_margin) - min_margin) / (max_margin - min_margin)
    x = max(0.0, min(1.0, x))
    return 0.5 + 1.5 * x


@dataclass(slots=True)
class ObjectiveResult:
    loss: torch.Tensor
    lambda_loser: float = 1.0
    pair_weight: float = 1.0
    u_raw: float = 0.0
    u_clipped: float = 0.0
    winner_contribution_ratio: float = 0.0
    local_mask_ratio: float = 1.0
    affected_tokens_count: int = 0
    full_future_tokens_count: int = 0


def compute_objective_loss(
    objective: str,
    policy_winner: torch.Tensor,
    policy_loser: torch.Tensor,
    ref_winner: torch.Tensor,
    ref_loser: torch.Tensor,
    *,
    beta: float,
    reward_margin: float = 0.0,
    u_clip: float = 1.0,
) -> ObjectiveResult:
    objective = objective.lower()
    delta_policy = policy_loser - policy_winner
    delta_ref = ref_loser - ref_winner
    u = delta_policy - delta_ref
    winner_improvement = ref_winner - policy_winner
    loser_degradation = policy_loser - ref_loser
    ratio = winner_contribution_ratio(winner_improvement, loser_degradation)
    if objective in {"standard", "localdpo"}:
        return ObjectiveResult(
            loss=dpo_loss(policy_winner, policy_loser, ref_winner, ref_loser, beta=beta),
            u_raw=_scalar(u.detach()),
            u_clipped=_scalar(torch.clamp(u.detach(), -float(u_clip), float(u_clip))),
            winner_contribution_ratio=_scalar(ratio.detach()),
        )
    if objective == "sdpo":
        winner_bad = bool((winner_improvement.detach() <= 0).all().item())
        ratio_value = _scalar(ratio.detach())
        if winner_bad:
            lambda_loser = 0.0
        elif ratio_value < 0.30:
            lambda_loser = 0.25
        else:
            lambda_loser = 1.0
        effective_loser = ref_loser + float(lambda_loser) * (policy_loser - ref_loser)
        return ObjectiveResult(
            loss=dpo_loss(policy_winner, effective_loser, ref_winner, ref_loser, beta=beta),
            lambda_loser=lambda_loser,
            u_raw=_scalar(u.detach()),
            u_clipped=_scalar(torch.clamp(u.detach(), -float(u_clip), float(u_clip))),
            winner_contribution_ratio=ratio_value,
        )
    if objective == "linear":
        pair_weight = reward_to_pair_weight(float(reward_margin))
        u_clipped = torch.clamp(u, -float(u_clip), float(u_clip))
        return ObjectiveResult(
            loss=-float(pair_weight) * float(beta) * u_clipped.mean(),
            pair_weight=pair_weight,
            u_raw=_scalar(u.detach()),
            u_clipped=_scalar(u_clipped.detach()),
            winner_contribution_ratio=_scalar(ratio.detach()),
        )
    raise ValueError(f"unsupported objective: {objective}")


def parse_affected_time_span(value: Any) -> tuple[int, int] | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        if value == "future_frames_5_80":
            return (5, 80)
        value = value.replace("frames", "").replace("frame", "").replace("_", "-")
        parts = [p for p in value.replace(":", "-").split("-") if p.strip().isdigit()]
        if len(parts) >= 2:
            return (int(parts[0]), int(parts[1]))
        return None
    if isinstance(value, dict):
        start = value.get("start_frame", value.get("start"))
        end = value.get("end_frame", value.get("end"))
        if start is not None and end is not None:
            return (int(start), int(end))
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return (int(value[0]), int(value[1]))
    return None


def affected_latent_indices(
    affected_span: Any,
    *,
    total_frames: int = 81,
    prefix_len: int = 5,
    latent_frames: int,
    temporal_compression: int = 4,
) -> list[int]:
    future_indices = []
    for latent_idx in range(latent_frames):
        start = latent_idx * temporal_compression
        end = min(total_frames - 1, (latent_idx + 1) * temporal_compression - 1)
        if end >= prefix_len:
            future_indices.append(latent_idx)
    span = parse_affected_time_span(affected_span)
    if span is None:
        return future_indices
    start, end = span
    selected = [
        idx for idx in future_indices
        if min(total_frames - 1, (idx + 1) * temporal_compression - 1) >= start
        and idx * temporal_compression <= end
    ]
    return selected or future_indices


def _apply_local_mask(prepared, cache, affected_span: Any, temporal_compression: int, total_frames: int) -> ObjectiveResult:
    original = list(prepared.latent_loss_indices)
    selected = affected_latent_indices(
        affected_span,
        total_frames=total_frames,
        prefix_len=cache.prefix_len,
        latent_frames=int(cache.winner_latent.shape[1]),
        temporal_compression=temporal_compression,
    )
    selected = [idx for idx in selected if idx in original]
    if selected:
        prepared.latent_loss_indices = selected
    result = ObjectiveResult(
        loss=torch.tensor(0.0),
        local_mask_ratio=(len(selected) / max(1, len(original))) if selected else 1.0,
        affected_tokens_count=len(selected),
        full_future_tokens_count=len(original),
    )
    return result


def _pair_lookup(path: str | Path) -> dict[str, dict[str, Any]]:
    return {str(row.get("pair_id")): row for row in _load_jsonl(path)}


def _save_lora_checkpoint(backend: LingBotFastDpoEnergy, out: Path, objective: str, step: int) -> str:
    ckpt = out / "checkpoints" / f"{objective}_step{step:03d}_lora_state.pt"
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    torch.save(extract_lora_state(backend.model), ckpt)
    return str(ckpt)


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    objective = str(args.objective).lower()
    if objective not in OBJECTIVES:
        raise ValueError(f"unsupported objective {objective}")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cfg = _load_yaml(args.config)
    cfg["num_frames"] = int(args.num_frames)
    cfg["height"] = int(args.height)
    cfg["width"] = int(args.width)
    cfg["dpo_runtime_device"] = args.runtime_device or args.device
    cfg["dpo_skip_runtime_components_on_load"] = True
    if args.device.startswith("cuda") and torch.cuda.is_available() and args.device == "cuda":
        device = "cuda:0"
    else:
        device = args.device
    dataset = Prefix5DpoDataset(
        args.pair_manifest,
        repo_root=args.repo_root,
        limit_pairs=int(args.limit_pairs),
        num_frames=int(args.num_frames),
        height=int(args.height),
        width=int(args.width),
        min_margin=0.0,
    )
    if len(dataset) <= 0:
        result = {"status": "BLOCKED_NO_PREFIX5_PAIRS", "pair_manifest": args.pair_manifest}
        (out / "probe_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        return result
    pair_meta = _pair_lookup(args.pair_manifest)
    precomputed = _precompute_pairs(dataset, cfg=cfg, device=device, out_dir=out)
    backend = LingBotFastDpoEnergy(cfg, device=device, prefix_len=5)
    params = backend.trainable_parameters()
    optimizer = torch.optim.AdamW(params, lr=float(args.learning_rate), betas=(0.9, 0.95), weight_decay=float(args.weight_decay))
    checkpoints: list[dict[str, Any]] = [{"step": 0, "path": _save_lora_checkpoint(backend, out, objective, 0)}]
    rows: list[dict[str, Any]] = []
    finite = True
    error = ""
    nonzero_grad = False
    save_load_ok = False
    temporal_compression = int(cfg.get("temporal_compression", 4) or 4)
    for step in range(max(1, int(args.max_steps))):
        step_start = time.time()
        try:
            cache = precomputed[step % len(precomputed)]
            meta = pair_meta.get(cache.pair_id, {})
            optimizer.zero_grad(set_to_none=True)
            timestep_sample, noise = backend.sample_timestep_and_noise(tuple(cache.winner_latent.shape), seed=int(args.seed) + step)
            winner = _prepared_from_cache(cache, side="winner", backend=backend, timestep_sample=timestep_sample, noise=noise)
            loser = _prepared_from_cache(cache, side="loser", backend=backend, timestep_sample=timestep_sample, noise=noise)
            local_mask = ObjectiveResult(loss=torch.tensor(0.0), local_mask_ratio=1.0, affected_tokens_count=len(winner.latent_loss_indices), full_future_tokens_count=len(winner.latent_loss_indices))
            if objective == "localdpo":
                span = _nested_get(meta, "loser.affected_time_span", None)
                local_mask = _apply_local_mask(winner, cache, span, temporal_compression, int(args.num_frames))
                _apply_local_mask(loser, cache, span, temporal_compression, int(args.num_frames))
            policy_winner = backend.energy(winner, timestep_sample)
            policy_loser = backend.energy(loser, timestep_sample)
            with backend.reference_mode():
                ref_winner = backend.energy(winner, timestep_sample).detach()
                ref_loser = backend.energy(loser, timestep_sample).detach()
            objective_result = compute_objective_loss(
                objective,
                policy_winner,
                policy_loser,
                ref_winner,
                ref_loser,
                beta=float(args.beta),
                reward_margin=_reward_margin(meta),
                u_clip=float(args.u_clip),
            )
            loss = objective_result.loss
            if not torch.isfinite(loss).all().item():
                finite = False
                error = "nonfinite_objective_loss"
                break
            loss.backward()
            grad_norm = _grad_norm(params)
            nonzero_grad = nonzero_grad or grad_norm > 0.0
            optimizer.step()
            diag = dpo_energy_diagnostics(policy_winner.detach(), policy_loser.detach(), ref_winner.detach(), ref_loser.detach(), beta=float(args.beta))
            winner_improvement = _scalar(ref_winner - policy_winner.detach())
            loser_degradation = _scalar(policy_loser.detach() - ref_loser)
            ratio = _scalar(winner_contribution_ratio(winner_improvement, loser_degradation))
            row = {
                **diag,
                "objective": objective,
                "objective_loss": _scalar(loss.detach()),
                "step": step + 1,
                "pair_id": cache.pair_id,
                "pair_type": meta.get("pair_type", ""),
                "corruption_type": _nested_get(meta, "loser.corruption_type", ""),
                "reward_margin": _reward_margin(meta),
                "grad_norm": grad_norm,
                "winner_improvement": winner_improvement,
                "loser_degradation": loser_degradation,
                "winner_contribution_ratio": ratio,
                "lambda_loser": objective_result.lambda_loser,
                "pair_weight": objective_result.pair_weight,
                "linear_utility": objective_result.u_raw,
                "u_raw": objective_result.u_raw,
                "u_clipped": objective_result.u_clipped,
                "local_mask_ratio": local_mask.local_mask_ratio,
                "affected_tokens_count": local_mask.affected_tokens_count,
                "full_future_tokens_count": local_mask.full_future_tokens_count,
                "same_noise": True,
                "same_timestep": True,
                "prefix_len": int(cache.prefix_len),
                "prediction_start_frame": int(cache.prediction_start_frame),
                "timestep_index": int(timestep_sample.index),
                "sigma": float(timestep_sample.sigma),
                "latent_loss_indices": " ".join(map(str, winner.latent_loss_indices)),
                "policy_trainable_params": int(backend.policy_trainable_params),
                "reference_trainable_params": 0,
                "step_time_sec": time.time() - step_start,
                "cuda_memory_allocated_gb": (torch.cuda.memory_allocated() / (1024**3) if torch.cuda.is_available() else 0.0),
                "cuda_memory_reserved_gb": (torch.cuda.memory_reserved() / (1024**3) if torch.cuda.is_available() else 0.0),
            }
            rows.append(row)
            if (step + 1) in {5, 10, 20, 50}:
                checkpoints.append({"step": step + 1, "path": _save_lora_checkpoint(backend, out, objective, step + 1)})
        except Exception as exc:
            finite = False
            error = repr(exc)
            break
    _write_rows(out / f"training_metrics_{objective}.csv", rows)
    with (out / f"training_metrics_{objective}.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    if rows:
        ckpt = Path(checkpoints[-1]["path"])
        saved = torch.load(ckpt, map_location="cpu")
        before = extract_lora_state(backend.model)
        load_lora_state(backend.model, saved)
        after = extract_lora_state(backend.model)
        save_load_ok = bool(before.keys() == after.keys() and all(torch.equal(before[k], after[k]) for k in before))
    final = rows[-1] if rows else {}
    status = "PASS" if rows and finite and nonzero_grad and save_load_ok else "FAILED"
    result = {
        "status": status,
        "objective": objective,
        "pair_manifest": args.pair_manifest,
        "pair_count": len(dataset),
        "steps": len(rows),
        "finite": finite,
        "error": error,
        "nonzero_grad": nonzero_grad,
        "save_load_ok": save_load_ok,
        "policy_trainable_params": getattr(backend, "policy_trainable_params", 0),
        "lora_inventory": getattr(backend, "lora_inventory", {}),
        "final_objective_loss": final.get("objective_loss"),
        "final_dpo_loss": final.get("dpo_loss"),
        "final_implicit_accuracy": final.get("implicit_accuracy"),
        "final_winner_improvement": final.get("winner_improvement"),
        "final_loser_degradation": final.get("loser_degradation"),
        "final_winner_contribution_ratio": final.get("winner_contribution_ratio"),
        "checkpoints": checkpoints,
        "metrics_csv": str(out / f"training_metrics_{objective}.csv"),
        "elapsed_seconds": time.time() - started,
        "device": device,
        "cuda_visible_devices": __import__("os").environ.get("CUDA_VISIBLE_DEVICES", ""),
    }
    (out / "probe_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build-subsets")
    p.add_argument("--ready_pairs", default="reports/dpo_preference_protocol_v1/dpo_ready_pairs.jsonl")
    p.add_argument("--localdpo_pairs", default="reports/dpo_preference_protocol_v1/localdpo_ready_pairs.jsonl")
    p.add_argument("--condition_manifest", default="manifests/screen16_v2v5.jsonl")
    p.add_argument("--out_dir", default="manifests/dpo_probe_subsets")
    p.add_argument("--summary_csv", default="reports/dpo_objective_ablation/subset_summary.csv")
    p.set_defaults(func=build_subsets)

    r = sub.add_parser("run-probe")
    r.add_argument("--objective", required=True, choices=sorted(OBJECTIVES))
    r.add_argument("--pair_manifest", required=True)
    r.add_argument("--out_dir", required=True)
    r.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    r.add_argument("--repo_root", default=".")
    r.add_argument("--limit_pairs", type=int, default=0)
    r.add_argument("--max_steps", type=int, default=20)
    r.add_argument("--beta", type=float, default=0.1)
    r.add_argument("--u_clip", type=float, default=1.0)
    r.add_argument("--learning_rate", type=float, default=1e-6)
    r.add_argument("--weight_decay", type=float, default=0.01)
    r.add_argument("--seed", type=int, default=123)
    r.add_argument("--device", default="cuda")
    r.add_argument("--runtime_device", default="cuda")
    r.add_argument("--num_frames", type=int, default=81)
    r.add_argument("--height", type=int, default=480)
    r.add_argument("--width", type=int, default=832)
    r.set_defaults(func=run_probe)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
