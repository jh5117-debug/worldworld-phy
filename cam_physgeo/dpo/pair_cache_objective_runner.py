from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import torch
import torch.nn.functional as F

from cam_physgeo.dpo.anchored_dpo_trainer import _grad_norm
from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy, PreparedEnergyInput, extract_lora_state, load_lora_state
from cam_physgeo.dpo.lora_scope_config_v12 import apply_scope_to_cfg
from cam_physgeo.dpo.winner_anchor_only_runner import _cfg, _param_norm, _param_update_norm, cuda_stats

FIELDNAMES = [
    "step", "pair_id", "scope", "objective", "used_window_frames", "timestep", "actual_sigma", "pair_weight",
    "E_ref_winner_cached", "E_ref_loser_cached", "Delta_ref", "E_policy_winner_pre", "E_policy_loser_pre",
    "Delta_policy_pre", "E_policy_winner_post", "E_policy_loser_post", "Delta_policy_post",
    "winner_improvement_pre", "winner_improvement_post", "loser_degradation_pre", "loser_degradation_post",
    "reference_relative_margin_pre", "reference_relative_margin_post", "winner_contribution_ratio_pre",
    "winner_contribution_ratio_post", "u_raw_pre", "u_raw_post", "u_clipped", "lambda_loser",
    "lambda_winner_anchor", "lambda_pref", "dpo_loss", "objective_loss", "grad_norm", "update_norm", "lora_param_norm",
    "lr", "allocated_gb", "reserved_gb", "max_allocated_gb", "step_time", "finite", "status", "error_reason",
]


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def winner_contribution_ratio(winner_improvement: float, loser_degradation: float) -> float:
    wi = max(float(winner_improvement), 0.0)
    ld = max(float(loser_degradation), 0.0)
    denom = wi + ld
    return 0.0 if denom <= 0.0 else wi / denom


def _to_device(value: Any, device: torch.device) -> Any:
    if torch.is_tensor(value):
        return value.to(device)
    if isinstance(value, list):
        return [_to_device(v, device) for v in value]
    if isinstance(value, tuple):
        return tuple(_to_device(v, device) for v in value)
    if isinstance(value, dict):
        return {k: _to_device(v, device) for k, v in value.items()}
    return value


def _prepared(branch: dict[str, Any], device: torch.device) -> PreparedEnergyInput:
    return PreparedEnergyInput(
        target=_to_device(branch["target"], device),
        noisy_latent=_to_device(branch["noisy_latent"], device),
        context=_to_device(branch["context"], device),
        y=_to_device(branch["y"], device),
        dit_cond=_to_device(branch["dit_cond"], device),
        seq_len=int(branch["seq_len"]),
        latent_loss_indices=list(branch["latent_loss_indices"]),
    )


def _load_payload(cache_root: Path, row: dict[str, Any], device: torch.device) -> tuple[PreparedEnergyInput, PreparedEnergyInput, Any]:
    payload = torch.load(cache_root / str(row["cache_tensor_path"]), map_location="cpu")
    winner = _prepared(payload["winner"], device)
    loser = _prepared(payload["loser"], device)
    timestep = payload["timestep_tensor"]
    if not torch.is_tensor(timestep):
        timestep = torch.tensor([float(timestep)], dtype=torch.float32)
    ts = SimpleNamespace(
        timestep=timestep.to(device),
        index=int(payload.get("timestep_index", row.get("timestep_index", 0))),
        sigma=float(payload.get("actual_sigma", row.get("actual_sigma", 0.0))),
        weight=float(payload.get("timestep_weight", 1.0)),
    )
    return winner, loser, ts


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in FIELDNAMES})
        f.flush()


def _safe_float(value: Any) -> float:
    if torch.is_tensor(value):
        return float(value.detach().float().mean().cpu())
    return float(value)


def _parse_checkpoint_steps(raw: str) -> set[int]:
    steps: set[int] = set()
    for part in str(raw or '').split(','):
        part = part.strip()
        if not part:
            continue
        steps.add(int(part))
    return steps


def _write_checkpoint_manifest(root: Path, rows: list[dict[str, Any]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / 'checkpoint_manifest.json').write_text(json.dumps(rows, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _save_lora_checkpoint(backend: LingBotFastDpoEnergy, root: Path, *, objective: str, scope: str, step: int) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    ckpt = root / f'{objective}_{scope}_step{step:03d}_lora_state.pt'
    torch.save(extract_lora_state(backend.model), ckpt)
    return {'step': int(step), 'objective': objective, 'scope': scope, 'path': str(ckpt), 'kind': 'lora_state'}


def _metrics(ref_w: float, ref_l: float, pol_w: torch.Tensor | float, pol_l: torch.Tensor | float) -> dict[str, float]:
    ew = _safe_float(pol_w)
    el = _safe_float(pol_l)
    delta_ref = float(ref_l) - float(ref_w)
    delta_policy = el - ew
    winner_improvement = float(ref_w) - ew
    loser_degradation = el - float(ref_l)
    margin = delta_policy - delta_ref
    return {
        "E_policy_winner": ew,
        "E_policy_loser": el,
        "Delta_policy": delta_policy,
        "winner_improvement": winner_improvement,
        "loser_degradation": loser_degradation,
        "reference_relative_margin": margin,
        "winner_contribution_ratio": winner_contribution_ratio(winner_improvement, loser_degradation),
    }


def _make_backend(args: argparse.Namespace, output: Path) -> LingBotFastDpoEnergy:
    cfg = _cfg(
        args.config,
        frames=int(args.used_window_frames),
        height=int(args.height),
        width=int(args.width),
        runtime_device="cpu",
        gradient_checkpointing=bool(args.gradient_checkpointing),
    )
    cfg = apply_scope_to_cfg(cfg, str(getattr(args, "scope", "L0_camera_r4")))
    cfg["dpo_policy_loader_mode"] = "safe_wan_policy_only"
    cfg["dpo_safe_loader_heartbeat_path"] = str(output.with_name(output.stem + "_safe_loader.jsonl"))
    return LingBotFastDpoEnergy(cfg, device=f"cuda:{int(args.gpu)}" if torch.cuda.is_available() else "cpu", prefix_len=5)


def _finite_values(*values: Any) -> bool:
    for value in values:
        if value == "":
            continue
        try:
            if not math.isfinite(float(value)):
                return False
        except Exception:
            return False
    return True


def _mean(values: list[Any]) -> float | str:
    vals = []
    for value in values:
        try:
            vals.append(float(value))
        except Exception:
            pass
    return "" if not vals else sum(vals) / len(vals)


def decide_status(objective: str, rows: list[dict[str, Any]], steps_requested: int) -> str:
    pass_rows = [r for r in rows if r.get("status") == "PASS"]
    if objective == "forward_sanity":
        return "FORWARD_SANITY_PASS" if pass_rows and len(pass_rows) == len(rows) else "FORWARD_SANITY_FAIL"
    if len(pass_rows) < int(steps_requested):
        if rows and rows[-1].get("status") == "OOM":
            return f"{objective.upper()}_OOM"
        return f"{objective.upper()}_INCOMPLETE"
    mean_wi = _mean([r.get("winner_improvement_post") for r in pass_rows])
    final_wi = float(pass_rows[-1].get("winner_improvement_post", 0.0))
    mean_ratio = _mean([r.get("winner_contribution_ratio_post") for r in pass_rows])
    if objective == "winner_anchor_repeat":
        return "WINNER_ANCHOR_REPEAT_PASS" if mean_wi != "" and float(mean_wi) > 0.0 and final_wi > 0.0 else "WINNER_ANCHOR_REPEAT_FAIL"
    if objective == "winner_detached_preference":
        return "WINNER_DETACHED_PREFERENCE_PASS" if mean_wi != "" and float(mean_wi) > 0.0 and final_wi > 0.0 else "WINNER_DETACHED_PREFERENCE_SIGNAL_FAIL"
    if objective == "tiny_loser_gradient_preference":
        return "TINY_LOSER_GRADIENT_PREFERENCE_PASS" if mean_wi != "" and float(mean_wi) > 0.0 and final_wi > 0.0 and mean_ratio != "" and float(mean_ratio) >= 0.30 else "TINY_LOSER_GRADIENT_PREFERENCE_SIGNAL_FAIL"
    if objective == "linear_winner_detached":
        return "LINEAR_WINNER_DETACHED_PASS" if mean_wi != "" and float(mean_wi) > 0.0 and final_wi > 0.0 else "LINEAR_WINNER_DETACHED_SIGNAL_FAIL"
    if objective == "standard_dpo_baseline":
        return "STANDARD_DPO_BASELINE_DIAGNOSTIC_COMPLETE"
    if mean_wi != "" and float(mean_wi) > 0.0 and final_wi > 0.0 and mean_ratio != "" and float(mean_ratio) >= 0.30:
        return objective.upper() + "_SIGNAL_HEALTHY"
    return objective.upper() + "_SIGNAL_FAIL"


def run_objective(args: argparse.Namespace) -> dict[str, Any]:
    output = Path(args.output)
    if output.exists():
        output.unlink()
    if torch.cuda.is_available():
        torch.cuda.set_device(int(args.gpu))
        torch.cuda.reset_peak_memory_stats()
    cache_root = Path(args.cache_root)
    rows = _read_jsonl(args.pair_subset)
    if not rows:
        raise RuntimeError(f"empty pair subset: {args.pair_subset}")
    steps = len(rows) if str(args.objective) == "forward_sanity" else int(args.steps)
    backend = _make_backend(args, output)
    init_lora_state = str(getattr(args, "init_lora_state", "") or "")
    if init_lora_state:
        state = torch.load(init_lora_state, map_location="cpu")
        load_lora_state(backend.model, state)
    params = backend.trainable_parameters()
    optim = torch.optim.AdamW(params, lr=float(args.lr))
    checkpoint_steps = _parse_checkpoint_steps(getattr(args, 'checkpoint_steps', ''))
    checkpoint_root = Path(args.checkpoint_root) if getattr(args, 'checkpoint_root', '') else None
    checkpoint_rows: list[dict[str, Any]] = []
    if checkpoint_root is not None and 0 in checkpoint_steps and str(args.objective) != 'forward_sanity':
        checkpoint_rows.append(_save_lora_checkpoint(backend, checkpoint_root, objective=str(args.objective), scope=str(getattr(args, 'scope', '')), step=0))
        _write_checkpoint_manifest(checkpoint_root, checkpoint_rows)
    history_winner_positive: list[bool] = []
    written: list[dict[str, Any]] = []
    start_all = time.time()
    for step in range(max(steps, 1)):
        start = time.time()
        row = rows[step % len(rows)]
        ref_w = float(row["E_ref_winner_cached"])
        ref_l = float(row["E_ref_loser_cached"])
        delta_ref = float(row["Delta_ref"])
        pair_weight = float(row.get("pair_weight", 1.0))
        lambda_loser = 0.0
        if str(args.objective) in {"strict_sdpo", "linear_dpo_anchor", "safe_linear"} and len(history_winner_positive) >= 3 and all(history_winner_positive[-3:]):
            lambda_loser = float(args.max_lambda_loser)
        if str(args.objective) == "tiny_loser_gradient_preference" and len(history_winner_positive) >= 3 and all(history_winner_positive[-3:]):
            lambda_loser = min(float(args.max_lambda_loser), 0.01)
        base = {
            "step": step,
            "pair_id": row.get("pair_id", ""),
            "scope": getattr(args, "scope", "L0_camera_r4"),
            "objective": args.objective,
            "used_window_frames": args.used_window_frames,
            "timestep": row.get("timestep", ""),
            "actual_sigma": row.get("actual_sigma", ""),
            "pair_weight": pair_weight,
            "E_ref_winner_cached": ref_w,
            "E_ref_loser_cached": ref_l,
            "Delta_ref": delta_ref,
            "lambda_loser": lambda_loser,
            "lambda_winner_anchor": float(args.lambda_winner_anchor),
            "lambda_pref": float(getattr(args, "lambda_pref", 1.0)),
            "lr": float(args.lr),
        }
        try:
            winner, loser, ts = _load_payload(cache_root, row, backend.device)
            with torch.no_grad():
                ew_pre = backend.energy(winner, ts).detach()
                el_pre = backend.energy(loser, ts).detach()
            pre = _metrics(ref_w, ref_l, ew_pre, el_pre)
            if args.objective == "forward_sanity":
                post = dict(pre)
                result = {**base, "status": "PASS", "finite": True, "dpo_loss": "", "objective_loss": "", "grad_norm": "", "update_norm": "", "lora_param_norm": _param_norm(params)}
            else:
                optim.zero_grad(set_to_none=True)
                before = [p.detach().float().cpu().clone() for p in params]
                ew_loss = backend.energy(winner, ts)
                need_loser_grad = args.objective == "standard_dpo_baseline" or lambda_loser > 0.0
                if need_loser_grad:
                    el_loss = backend.energy(loser, ts)
                else:
                    with torch.no_grad():
                        el_loss = backend.energy(loser, ts).detach()
                winner_improvement_tensor = float(ref_w) - ew_loss
                loser_degradation_tensor = el_loss - float(ref_l)
                delta_policy_tensor = el_loss - ew_loss
                u_raw = delta_policy_tensor - float(delta_ref)
                if args.objective == "winner_anchor_repeat":
                    dpo_loss = torch.zeros((), device=backend.device, dtype=ew_loss.dtype)
                    loss = ew_loss
                elif args.objective == "standard_dpo_baseline":
                    dpo_loss = -F.logsigmoid(float(args.beta) * u_raw)
                    loss = dpo_loss
                elif args.objective == "strict_sdpo":
                    safe_margin = winner_improvement_tensor + float(lambda_loser) * loser_degradation_tensor
                    dpo_loss = -F.logsigmoid(float(args.beta) * safe_margin)
                    loss = dpo_loss + float(args.lambda_winner_anchor) * ew_loss
                elif args.objective == "winner_detached_preference":
                    u_winner_only = (el_loss.detach() - ew_loss) - float(delta_ref)
                    dpo_loss = -F.logsigmoid(float(args.beta) * u_winner_only)
                    loss = float(args.lambda_winner_anchor) * ew_loss + float(getattr(args, "lambda_pref", 0.02)) * dpo_loss
                elif args.objective == "tiny_loser_gradient_preference":
                    safe_margin = winner_improvement_tensor + float(lambda_loser) * loser_degradation_tensor
                    dpo_loss = -F.logsigmoid(float(args.beta) * safe_margin)
                    loss = float(args.lambda_winner_anchor) * ew_loss + float(getattr(args, "lambda_pref", 0.02)) * dpo_loss
                elif args.objective == "linear_winner_detached":
                    u_winner_only = (el_loss.detach() - ew_loss) - float(delta_ref)
                    utility = torch.clamp(u_winner_only, -float(args.u_clip), float(args.u_clip))
                    dpo_loss = -float(pair_weight) * utility
                    loss = dpo_loss + float(args.lambda_winner_anchor) * ew_loss
                elif args.objective in {"linear_dpo_anchor", "safe_linear"}:
                    safe_margin = winner_improvement_tensor + float(lambda_loser) * loser_degradation_tensor
                    utility = torch.clamp(safe_margin, -float(args.u_clip), float(args.u_clip))
                    dpo_loss = -float(pair_weight) * utility
                    loss = dpo_loss + float(args.lambda_winner_anchor) * ew_loss
                else:
                    raise ValueError(f"unsupported objective={args.objective}")
                loss.backward()
                grad_norm = _grad_norm(params)
                optim.step()
                update_norm = _param_update_norm(before, params)
                with torch.no_grad():
                    ew_post = backend.energy(winner, ts).detach()
                    el_post = backend.energy(loser, ts).detach()
                post = _metrics(ref_w, ref_l, ew_post, el_post)
                history_winner_positive.append(post["winner_improvement"] > 0.0)
                result = {
                    **base,
                    "status": "PASS",
                    "finite": _finite_values(_safe_float(loss), grad_norm, update_norm, post["winner_improvement"]),
                    "dpo_loss": _safe_float(dpo_loss),
                    "objective_loss": _safe_float(loss),
                    "grad_norm": grad_norm,
                    "update_norm": update_norm,
                    "lora_param_norm": _param_norm(params),
                }
            result.update({
                "E_policy_winner_pre": pre["E_policy_winner"],
                "E_policy_loser_pre": pre["E_policy_loser"],
                "Delta_policy_pre": pre["Delta_policy"],
                "winner_improvement_pre": pre["winner_improvement"],
                "loser_degradation_pre": pre["loser_degradation"],
                "reference_relative_margin_pre": pre["reference_relative_margin"],
                "winner_contribution_ratio_pre": pre["winner_contribution_ratio"],
                "E_policy_winner_post": post["E_policy_winner"],
                "E_policy_loser_post": post["E_policy_loser"],
                "Delta_policy_post": post["Delta_policy"],
                "winner_improvement_post": post["winner_improvement"],
                "loser_degradation_post": post["loser_degradation"],
                "reference_relative_margin_post": post["reference_relative_margin"],
                "winner_contribution_ratio_post": post["winner_contribution_ratio"],
                "u_raw_pre": pre["reference_relative_margin"],
                "u_raw_post": post["reference_relative_margin"],
                "u_clipped": min(float(args.u_clip), max(-float(args.u_clip), post["reference_relative_margin"])),
                "step_time": time.time() - start,
                "error_reason": "",
                **cuda_stats(),
            })
            _append(output, result)
            written.append(result)
            completed_step = int(step) + 1
            if (
                result.get('status') == 'PASS'
                and checkpoint_root is not None
                and completed_step in checkpoint_steps
                and str(args.objective) != 'forward_sanity'
            ):
                checkpoint_rows.append(_save_lora_checkpoint(backend, checkpoint_root, objective=str(args.objective), scope=str(getattr(args, 'scope', '')), step=completed_step))
                _write_checkpoint_manifest(checkpoint_root, checkpoint_rows)
        except torch.cuda.OutOfMemoryError as exc:
            result = {**base, "status": "OOM", "finite": False, "error_reason": repr(exc), "step_time": time.time() - start, **cuda_stats()}
            _append(output, result)
            written.append(result)
            break
        except Exception as exc:  # noqa: BLE001
            result = {**base, "status": "FAIL", "finite": False, "error_reason": repr(exc), "step_time": time.time() - start, **cuda_stats()}
            _append(output, result)
            written.append(result)
            break
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    status = decide_status(str(args.objective), written, int(args.steps))
    summary = {
        "status": status,
        "objective": args.objective,
        "rows_written": len(written),
        "steps_requested": int(args.steps),
        "seconds": time.time() - start_all,
        "mean_winner_improvement_post": _mean([r.get("winner_improvement_post") for r in written if r.get("status") == "PASS"]),
        "final_winner_improvement_post": written[-1].get("winner_improvement_post") if written else "",
        "mean_loser_degradation_post": _mean([r.get("loser_degradation_post") for r in written if r.get("status") == "PASS"]),
        "mean_winner_contribution_ratio_post": _mean([r.get("winner_contribution_ratio_post") for r in written if r.get("status") == "PASS"]),
        "output": str(output),
        "checkpoint_manifest": str(checkpoint_root / 'checkpoint_manifest.json') if checkpoint_root is not None and checkpoint_rows else "",
        "checkpoints_saved": len(checkpoint_rows),
    }
    output.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output.with_suffix(".summary.md").write_text(
        "Current Status:\n" + status + "\n\n"
        f"# v8n {args.objective} Summary\n\n"
        f"- Rows written: {summary['rows_written']}\n"
        f"- Mean winner_improvement_post: {summary['mean_winner_improvement_post']}\n"
        f"- Final winner_improvement_post: {summary['final_winner_improvement_post']}\n"
        f"- Mean loser_degradation_post: {summary['mean_loser_degradation_post']}\n"
        f"- Mean winner_contribution_ratio_post: {summary['mean_winner_contribution_ratio_post']}\n"
        f"- Decision: `{status}`\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run tiny v8n objectives on validated v8m winner+loser pair cache.")
    parser.add_argument("--cache_root", required=True)
    parser.add_argument("--pair_subset", required=True)
    parser.add_argument("--objective", required=True, choices=["forward_sanity", "winner_anchor_repeat", "strict_sdpo", "linear_dpo_anchor", "safe_linear", "standard_dpo_baseline", "winner_detached_preference", "tiny_loser_gradient_preference", "linear_winner_detached"])
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scope", default="L0_camera_r4")
    parser.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--used_window_frames", type=int, default=49)
    parser.add_argument("--lr", type=float, default=1e-6)
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--u_clip", type=float, default=1.0)
    parser.add_argument("--lambda_winner_anchor", type=float, default=1.0)
    parser.add_argument("--lambda_pref", type=float, default=1.0)
    parser.add_argument("--max_lambda_loser", type=float, default=0.25)
    parser.add_argument("--init_lora_state", default="")
    parser.add_argument("--checkpoint_root", default="")
    parser.add_argument("--checkpoint_steps", default="0,5,10,20")
    parser.add_argument("--gradient_checkpointing", action="store_true", default=True)
    args = parser.parse_args(argv)
    run_objective(args)


if __name__ == "__main__":
    main()

