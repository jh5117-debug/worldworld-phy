from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy
from cam_physgeo.dpo.prefix5_dpo_dataset import Prefix5DpoDataset


def _load_yaml(path: str | Path) -> dict[str, Any]:
    import yaml

    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise TypeError(f"expected mapping config in {path}")
    return dict(data)


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
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _append_jsonl(path: str | Path, row: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()


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


def _pair_reward_margin(pair: dict[str, Any]) -> float:
    direct = _safe_float(pair.get("margin"))
    if math.isfinite(direct):
        return direct
    winner = pair.get("winner", {}).get("reward", {}) or {}
    loser = pair.get("loser", {}).get("reward", {}) or {}
    return _safe_float(winner.get("R_total"), 0.0) - _safe_float(loser.get("R_total"), 0.0)


def _nested_get(data: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _energy_row_from_result(
    *,
    pair: dict[str, Any],
    pair_index: int,
    result: Any,
    seed: int,
    shard_index: int,
    num_shards: int,
    elapsed: float,
    device: str,
) -> dict[str, Any]:
    policy_w = float(result.policy_winner_energy.detach().float().cpu().item())
    policy_l = float(result.policy_loser_energy.detach().float().cpu().item())
    ref_w = float(result.ref_winner_energy.detach().float().cpu().item())
    ref_l = float(result.ref_loser_energy.detach().float().cpu().item())
    delta_policy = policy_l - policy_w
    delta_ref = ref_l - ref_w
    memory_allocated = 0.0
    memory_reserved = 0.0
    memory_peak = 0.0
    if torch.cuda.is_available() and str(device).startswith("cuda"):
        memory_allocated = torch.cuda.memory_allocated() / (1024**3)
        memory_reserved = torch.cuda.memory_reserved() / (1024**3)
        memory_peak = torch.cuda.max_memory_allocated() / (1024**3)
    return {
        "pair_index": pair_index,
        "pair_id": pair.get("pair_id"),
        "pair_type": pair.get("pair_type"),
        "protocol_version": pair.get("protocol_version"),
        "corruption_type": _nested_get(pair, "loser.corruption_type", ""),
        "winner_source": _nested_get(pair, "winner.source", ""),
        "loser_source": _nested_get(pair, "loser.source", ""),
        "reward_margin": _pair_reward_margin(pair),
        "policy_winner_energy": policy_w,
        "policy_loser_energy": policy_l,
        "E_policy_winner": policy_w,
        "E_policy_loser": policy_l,
        "delta_policy": delta_policy,
        "Delta_policy": delta_policy,
        "ref_winner_energy": ref_w,
        "ref_loser_energy": ref_l,
        "E_ref_winner": ref_w,
        "E_ref_loser": ref_l,
        "delta_ref": delta_ref,
        "Delta_ref": delta_ref,
        "energy_margin": delta_ref,
        "reference_relative_margin": delta_policy - delta_ref,
        "same_noise": bool(result.same_noise),
        "same_timestep": bool(result.same_timestep),
        "prefix_len": int(result.prefix_len),
        "prediction_start_frame": int(result.prediction_start_frame),
        "latent_loss_indices": ",".join(str(x) for x in result.latent_loss_indices),
        "timestep_index": int(result.timestep_index),
        "sigma": float(result.sigma),
        "timestep": float(result.timestep),
        "timestep_weight": float(result.timestep_weight),
        "policy_trainable_params": int(result.policy_trainable_params),
        "reference_trainable_params": int(result.reference_trainable_params),
        "affected_region_available": bool(_nested_get(pair, "loser.affected_region")),
        "affected_time_span_available": bool(_nested_get(pair, "loser.affected_time_span")),
        "affected_mask_available": bool(_nested_get(pair, "loser.affected_mask_path")),
        "same_prefix": bool(pair.get("same_prefix")),
        "same_prompt": bool(pair.get("same_prompt")),
        "same_poses": bool(pair.get("same_poses")),
        "same_intrinsics": bool(pair.get("same_intrinsics")),
        "quality_floor_pass": bool(pair.get("quality_floor_pass")),
        "medium_hard": bool(pair.get("medium_hard")),
        "codex_valid_preference": bool(_nested_get(pair, "codex_audit.valid_preference", False)),
        "codex_too_easy": bool(_nested_get(pair, "codex_audit.too_easy", False)),
        "codex_winner_bad": bool(_nested_get(pair, "codex_audit.winner_bad", False)),
        "codex_loser_collapsed": bool(_nested_get(pair, "codex_audit.loser_collapsed", False)),
        "seed": seed,
        "device": device,
        "shard_index": shard_index,
        "num_shards": num_shards,
        "energy_seconds": elapsed,
        "cuda_memory_allocated_gb": memory_allocated,
        "cuda_memory_reserved_gb": memory_reserved,
        "cuda_peak_memory_gb": memory_peak,
        "status": "ok",
        "error_reason": "",
    }


def _load_condition_index(path: str | Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    p = Path(path)
    if not p.exists():
        return index
    for row in _load_jsonl(p):
        condition = row.get("condition", row)
        if not isinstance(condition, dict):
            continue
        sample_id = str(condition.get("sample_id") or row.get("sample_id") or "")
        if sample_id:
            index[sample_id] = dict(condition)
    return index


def _sample_id_from_winner_path(pair: dict[str, Any]) -> str:
    value = str(_nested_get(pair, "winner.full_video_path", "") or _nested_get(pair, "winner.future_video_path", ""))
    parts = Path(value).parts
    if "conditions" in parts:
        idx = parts.index("conditions")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return ""


def _normalize_protocol_v1_pairs_for_loader(rows: list[dict[str, Any]], condition_index: dict[str, dict[str, Any]]) -> None:
    expected = list(range(5, 81))
    required_condition_keys = ("image", "prompt", "poses", "intrinsics")
    for pair in rows:
        pair.setdefault("winner", {}).setdefault("future_frame_indices", expected)
        pair.setdefault("loser", {}).setdefault("future_frame_indices", expected)
        condition = pair.setdefault("condition", {})
        if not isinstance(condition, dict):
            continue
        needs_backfill = any(not condition.get(key) for key in required_condition_keys)
        if not needs_backfill:
            continue
        sample_id = _sample_id_from_winner_path(pair) or str(condition.get("sample_id") or "")
        source = condition_index.get(sample_id)
        if not source:
            continue
        for key, value in source.items():
            current = condition.get(key)
            if key not in condition or current is None or current == "" or current == []:
                condition[key] = value


def run_shard(args: argparse.Namespace) -> None:
    cfg = _load_yaml(args.config)
    cfg["num_frames"] = int(args.num_frames)
    cfg["height"] = int(args.height)
    cfg["width"] = int(args.width)
    if args.runtime_device:
        cfg["dpo_runtime_device"] = args.runtime_device
    dataset = Prefix5DpoDataset(
        args.pair_manifest,
        repo_root=args.repo_root,
        limit_pairs=0,
        num_frames=args.num_frames,
        height=args.height,
        width=args.width,
    )
    out_jsonl = Path(args.out_dir) / f"shard_{args.shard_index:02d}_of_{args.num_shards:02d}.jsonl"
    out_csv = Path(args.out_dir) / f"shard_{args.shard_index:02d}_of_{args.num_shards:02d}.csv"
    done = {
        str(row.get("pair_id"))
        for row in _load_jsonl(out_jsonl)
        if str(row.get("status")) == "ok" and row.get("pair_id")
    }
    rows = _load_jsonl(out_jsonl)
    condition_index = _load_condition_index(args.condition_manifest)
    _normalize_protocol_v1_pairs_for_loader(dataset.rows, condition_index)
    energy = LingBotFastDpoEnergy(cfg, device=args.device, prefix_len=args.prefix_len)
    processed_seen = 0
    for idx, pair in enumerate(dataset.rows):
        if idx % int(args.num_shards) != int(args.shard_index):
            continue
        pair_id = str(pair.get("pair_id") or f"pair_{idx}")
        if args.limit > 0 and processed_seen >= args.limit:
            break
        if args.resume and pair_id in done:
            continue
        seed = int(args.seed_base) + idx
        started = time.time()
        try:
            if torch.cuda.is_available() and args.device.startswith("cuda"):
                torch.cuda.reset_peak_memory_stats()
            example = dataset[idx]
            with torch.no_grad():
                result = energy.pair_energies(example, seed=seed)
            row = _energy_row_from_result(
                pair=pair,
                pair_index=idx,
                result=result,
                seed=seed,
                shard_index=args.shard_index,
                num_shards=args.num_shards,
                elapsed=time.time() - started,
                device=args.device,
            )
        except Exception as exc:
            row = {
                "pair_index": idx,
                "pair_id": pair_id,
                "pair_type": pair.get("pair_type"),
                "corruption_type": _nested_get(pair, "loser.corruption_type", ""),
                "reward_margin": _pair_reward_margin(pair),
                "seed": seed,
                "device": args.device,
                "shard_index": args.shard_index,
                "num_shards": args.num_shards,
                "energy_seconds": time.time() - started,
                "status": "failed",
                "error_reason": f"{type(exc).__name__}: {exc}",
            }
        _append_jsonl(out_jsonl, row)
        rows.append(row)
        processed_seen += 1
        _write_csv(out_csv, rows)
        print(json.dumps({"pair_id": pair_id, "status": row["status"], "seconds": row["energy_seconds"]}, sort_keys=True), flush=True)


def _read_csv_by_pair(path: str | Path) -> dict[str, dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8", newline="") as f:
        return {str(row.get("pair_id")): dict(row) for row in csv.DictReader(f) if row.get("pair_id")}


@dataclass(slots=True)
class SelectionResult:
    row: dict[str, Any]
    selected: bool
    reasons: list[str]
    localdpo_ready: bool


def _select_pair(row: dict[str, Any], pair: dict[str, Any], audit: dict[str, Any], *, energy_threshold: float) -> SelectionResult:
    reasons: list[str] = []
    status_ok = row.get("status") == "ok"
    visual_valid = _boolish(audit.get("is_valid_preference", _nested_get(pair, "codex_audit.valid_preference", False)))
    winner_bad = _boolish(audit.get("is_winner_bad", _nested_get(pair, "codex_audit.winner_bad", False)))
    loser_collapsed = _boolish(audit.get("is_loser_collapsed", _nested_get(pair, "codex_audit.loser_collapsed", False)))
    too_easy = _boolish(audit.get("is_too_easy", _nested_get(pair, "codex_audit.too_easy", False)))
    medium_hard = _boolish(audit.get("is_medium_hard", pair.get("medium_hard", False)))
    quality_floor = _boolish(pair.get("quality_floor_pass", True))
    reward_margin = _safe_float(row.get("reward_margin"), _pair_reward_margin(pair))
    energy_margin = _safe_float(row.get("delta_ref"), _safe_float(row.get("Delta_ref"), 0.0))
    same_condition = all(bool(pair.get(k)) for k in ("same_prefix", "same_prompt", "same_poses", "same_intrinsics"))
    if not status_ok:
        reasons.append("energy_failed")
    if not visual_valid:
        reasons.append("visual_invalid")
    if winner_bad:
        reasons.append("winner_bad")
    if loser_collapsed:
        reasons.append("loser_collapsed")
    if too_easy:
        reasons.append("too_easy")
    if not medium_hard:
        reasons.append("not_medium_hard")
    if not quality_floor:
        reasons.append("quality_floor_failed")
    if not same_condition:
        reasons.append("condition_mismatch")
    if not math.isfinite(reward_margin) or reward_margin <= 0:
        reasons.append("nonpositive_reward_margin")
    if not math.isfinite(energy_margin) or energy_margin <= energy_threshold:
        reasons.append("weak_or_negative_energy_margin")
    selected = not reasons
    localdpo_ready = (
        selected
        and str(pair.get("pair_type")) == "local_corruption"
        and bool(_nested_get(pair, "loser.affected_region"))
        and bool(_nested_get(pair, "loser.affected_time_span"))
        and bool(_nested_get(pair, "loser.affected_mask_path"))
    )
    out = dict(row)
    out.update(
        {
            "visual_validity": visual_valid,
            "winner_bad": winner_bad,
            "loser_collapsed": loser_collapsed,
            "too_easy": too_easy,
            "too_hard": False,
            "medium_hard_score": 1.0 if medium_hard else 0.0,
            "winner_quality": _nested_get(pair, "winner.quality.visual_quality", ""),
            "loser_quality": _nested_get(pair, "loser.quality.visual_quality", ""),
            "local_corruption_available": str(pair.get("pair_type")) == "local_corruption",
            "affected_region_available": bool(_nested_get(pair, "loser.affected_region")),
            "affected_time_span_available": bool(_nested_get(pair, "loser.affected_time_span")),
            "selected_dpo_ready": selected,
            "localdpo_ready": localdpo_ready,
            "selection_reasons": ";".join(reasons),
        }
    )
    return SelectionResult(row=out, selected=selected, reasons=reasons, localdpo_ready=localdpo_ready)


def _summary_stats(values: list[float]) -> dict[str, Any]:
    vals = [v for v in values if math.isfinite(v)]
    if not vals:
        return {"count": 0, "mean": "", "median": "", "min": "", "max": "", "positive": 0}
    return {
        "count": len(vals),
        "mean": statistics.fmean(vals),
        "median": statistics.median(vals),
        "min": min(vals),
        "max": max(vals),
        "positive": sum(v > 0 for v in vals),
    }


def summarize(args: argparse.Namespace) -> None:
    pair_rows = _load_jsonl(args.pair_manifest)
    pairs = {str(row.get("pair_id")): row for row in pair_rows}
    energy_rows: dict[str, dict[str, Any]] = {}
    for path in glob.glob(args.energy_jsonl_glob):
        for row in _load_jsonl(path):
            pair_id = str(row.get("pair_id"))
            if not pair_id:
                continue
            if pair_id not in energy_rows or row.get("status") == "ok":
                energy_rows[pair_id] = row
    ordered = [energy_rows.get(str(pair.get("pair_id")), {"pair_id": pair.get("pair_id"), "status": "missing"}) for pair in pair_rows]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(out_dir / "full_real_energy_audit.jsonl", ordered)
    _write_csv(out_dir / "full_real_energy_audit.csv", ordered)

    ok_rows = [r for r in ordered if r.get("status") == "ok"]
    positive = sorted(abs(_safe_float(r.get("delta_ref"), 0.0)) for r in ok_rows if _safe_float(r.get("delta_ref"), 0.0) > 0)
    if positive:
        dynamic_threshold = max(1e-6, positive[max(0, int(0.10 * (len(positive) - 1)))])
    else:
        dynamic_threshold = 1e-6
    energy_threshold = max(float(args.min_energy_margin), dynamic_threshold)
    audit_rows = _read_csv_by_pair(args.pair_audit)
    selections: list[SelectionResult] = []
    for row in ordered:
        pair_id = str(row.get("pair_id"))
        pair = pairs.get(pair_id, {})
        selections.append(_select_pair(row, pair, audit_rows.get(pair_id, {}), energy_threshold=energy_threshold))
    selected = [sel for sel in selections if sel.selected]
    if len(selected) > args.max_ready_pairs:
        selected = sorted(selected, key=lambda s: (_safe_float(s.row.get("delta_ref"), 0.0), _safe_float(s.row.get("reward_margin"), 0.0)), reverse=True)[: args.max_ready_pairs]
        selected_ids = {str(sel.row.get("pair_id")) for sel in selected}
        for sel in selections:
            if sel.row.get("selected_dpo_ready") and str(sel.row.get("pair_id")) not in selected_ids:
                sel.row["selected_dpo_ready"] = False
                sel.row["localdpo_ready"] = False
                sel.row["selection_reasons"] = (str(sel.row.get("selection_reasons") or "") + ";capped_by_top_energy_margin").strip(";")
    _write_csv(out_dir / "dpo_ready_pair_selection.csv", [sel.row for sel in selections])
    ready_pairs = []
    for sel in selections:
        if sel.row.get("selected_dpo_ready"):
            pair = dict(pairs[str(sel.row["pair_id"])])
            pair["energy_audit"] = {k: sel.row.get(k) for k in sel.row if "energy" in k or k in {"delta_ref", "delta_policy", "reference_relative_margin"}}
            pair["selection"] = {"dpo_ready": True, "energy_threshold": energy_threshold}
            ready_pairs.append(pair)
    _write_jsonl(out_dir / "dpo_ready_pairs.jsonl", ready_pairs)
    local_ready = []
    for sel in selections:
        if sel.row.get("localdpo_ready") and sel.row.get("selected_dpo_ready"):
            pair = dict(pairs[str(sel.row["pair_id"])])
            pair["energy_audit"] = {k: sel.row.get(k) for k in sel.row if "energy" in k or k in {"delta_ref", "delta_policy", "reference_relative_margin"}}
            pair["selection"] = {"localdpo_ready": True, "energy_threshold": energy_threshold}
            local_ready.append(pair)
    _write_jsonl(out_dir / "localdpo_ready_pairs.jsonl", local_ready)

    by_type: dict[str, list[dict[str, Any]]] = {}
    for row in ok_rows:
        by_type.setdefault(str(row.get("pair_type")), []).append(row)
    lines = [
        "# Full Real-Energy Audit Summary",
        "",
        f"Pair manifest: `{args.pair_manifest}`",
        f"Total pairs: {len(pair_rows)}",
        f"Real-energy ok: {len(ok_rows)}",
        f"Real-energy failed/missing: {len(pair_rows) - len(ok_rows)}",
        f"Energy threshold for DPO-ready selection: {energy_threshold:.8f}",
        f"DPO-ready pairs: {sum(1 for sel in selections if sel.row.get('selected_dpo_ready'))}",
        f"LocalDPO-ready pairs: {len(local_ready)}",
        "",
        "## Energy Margin By Type",
        "",
    ]
    for pair_type, rows in sorted(by_type.items()):
        stats = _summary_stats([_safe_float(row.get("delta_ref"), 0.0) for row in rows])
        reward_stats = _summary_stats([_safe_float(row.get("reward_margin"), 0.0) for row in rows])
        lines += [
            f"### {pair_type}",
            f"- count: {stats['count']}",
            f"- Delta_ref mean/median/min/max: {stats['mean']}/{stats['median']}/{stats['min']}/{stats['max']}",
            f"- positive Delta_ref: {stats['positive']} / {stats['count']}",
            f"- reward_margin mean/median: {reward_stats['mean']}/{reward_stats['median']}",
            "",
        ]
    reason_counts: dict[str, int] = {}
    for sel in selections:
        reasons = str(sel.row.get("selection_reasons") or "")
        if not reasons:
            continue
        for reason in reasons.split(";"):
            if reason:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
    lines += ["## Selection Rejection Reasons", ""]
    for key, count in sorted(reason_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- {key}: {count}")
    lines += [
        "",
        "## Training Recommendation",
        "",
        "This file is an audit-only artifact: no DPO optimizer step was run.",
        "Use `dpo_ready_pairs.jsonl` only if the ready count is at least 20; otherwise treat the protocol as blocked by weak real-energy margin.",
    ]
    (out_dir / "full_real_energy_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    local_lines = [
        "# LocalDPO-Ready Pair Summary",
        "",
        f"LocalDPO-ready pairs: {len(local_ready)}",
        "Criteria: Type A local corruption, affected region/time/mask present, Codex-valid, medium-hard, quality-floor pass, and positive real-energy margin.",
    ]
    (out_dir / "localdpo_ready_summary.md").write_text("\n".join(local_lines) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": len(pair_rows), "ok": len(ok_rows), "dpo_ready": len(ready_pairs), "localdpo_ready": len(local_ready)}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Full real LingBot-Fast energy audit for V2V-5 DPO pairs")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run-shard")
    run.add_argument("--pair_manifest", required=True)
    run.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    run.add_argument("--out_dir", required=True)
    run.add_argument("--repo_root", default=".")
    run.add_argument("--device", default="cuda")
    run.add_argument("--runtime_device", default="cpu")
    run.add_argument("--condition_manifest", default="manifests/screen16_v2v5.jsonl")
    run.add_argument("--prefix_len", type=int, default=5)
    run.add_argument("--num_frames", type=int, default=81)
    run.add_argument("--height", type=int, default=480)
    run.add_argument("--width", type=int, default=832)
    run.add_argument("--seed_base", type=int, default=91000)
    run.add_argument("--shard_index", type=int, default=0)
    run.add_argument("--num_shards", type=int, default=1)
    run.add_argument("--limit", type=int, default=0)
    run.add_argument("--resume", action="store_true")
    run.set_defaults(func=run_shard)

    summ = sub.add_parser("summarize")
    summ.add_argument("--pair_manifest", required=True)
    summ.add_argument("--energy_jsonl_glob", required=True)
    summ.add_argument("--pair_audit", default="reports/dpo_preference_protocol_v1/pair_audit.csv")
    summ.add_argument("--out_dir", default="reports/dpo_preference_protocol_v1")
    summ.add_argument("--min_energy_margin", type=float, default=1e-6)
    summ.add_argument("--max_ready_pairs", type=int, default=50)
    summ.set_defaults(func=summarize)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
