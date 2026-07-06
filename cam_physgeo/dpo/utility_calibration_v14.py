
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

EPS = 1e-8


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def get(row: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        cur: Any = row
        ok = True
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return cur
    return default


def fnum(value: Any, default: float = math.nan) -> float:
    try:
        return float(value)
    except Exception:
        return default


def reward_margin(row: dict[str, Any]) -> float:
    margin = fnum(get(row, "reward_margin", "v14_reward_margin", default=""))
    if math.isfinite(margin):
        return margin
    return fnum(get(row, "winner_reward", "reward_winner", default=0.0), 0.0) - fnum(get(row, "loser_reward", "reward_loser", default=0.0), 0.0)


def existing_energy(row: dict[str, Any]) -> tuple[float, float, float, float] | None:
    candidates = [
        ("m_w", "m_l", "m_w_ref", "m_l_ref"),
        ("E_policy_winner_post", "E_policy_loser_post", "E_ref_winner_cached", "E_ref_loser_cached"),
        ("E_policy_winner", "E_policy_loser", "E_ref_winner", "E_ref_loser"),
    ]
    for keys in candidates:
        vals = [fnum(get(row, k, default="")) for k in keys]
        if all(math.isfinite(v) for v in vals):
            return vals[0], vals[1], vals[2], vals[3]
    return None


def proxy_energy(row: dict[str, Any]) -> tuple[float, float, float, float]:
    # Explicit proxy for planning only; status marks it as not real energy.
    margin = max(reward_margin(row), 0.0)
    source = str(get(row, "v14_pair_source", "pair_source", default="")).lower()
    scale = 0.0015 if "rollout" in source else 0.0010
    m_w_ref = 1.0
    m_l_ref = 1.0 + margin * scale
    m_w = m_w_ref
    m_l = m_l_ref
    return m_w, m_l, m_w_ref, m_l_ref


def compute_metrics(m_w: float, m_l: float, m_w_ref: float, m_l_ref: float, *, local_gain: float = 1.0) -> dict[str, float]:
    win_gap = m_w - m_w_ref
    lose_gap = m_l - m_l_ref
    winner_improvement = -win_gap
    loser_degradation = lose_gap
    delta_policy = m_l - m_w
    delta_ref = m_l_ref - m_w_ref
    u_raw = delta_policy - delta_ref
    g_w_log = math.log((max(m_w, 0.0) + EPS) / (max(m_w_ref, 0.0) + EPS))
    g_l_log = math.log((max(m_l, 0.0) + EPS) / (max(m_l_ref, 0.0) + EPS))
    u_log = g_l_log - g_w_log
    local_u_raw = u_raw * local_gain
    local_u_log = u_log * local_gain
    return {
        "m_w": m_w,
        "m_l": m_l,
        "m_w_ref": m_w_ref,
        "m_l_ref": m_l_ref,
        "win_gap": win_gap,
        "lose_gap": lose_gap,
        "winner_improvement": winner_improvement,
        "loser_degradation": loser_degradation,
        "Delta_policy": delta_policy,
        "Delta_ref": delta_ref,
        "u_raw": u_raw,
        "g_w_log": g_w_log,
        "g_l_log": g_l_log,
        "u_log": u_log,
        "local_u_raw": local_u_raw,
        "local_u_log": local_u_log,
        "m_w_per_token": m_w,
        "m_l_per_token": m_l,
        "m_w_ref_per_token": m_w_ref,
        "m_l_ref_per_token": m_l_ref,
        "m_w_sum": m_w,
        "m_w_mean": m_w,
        "m_w_local_mean": m_w * local_gain,
        "m_w_full_future_mean": m_w,
    }


def add_normalization(rows: list[dict[str, Any]], keys: tuple[str, ...] = ("g_w_log", "g_l_log", "u_log", "u_raw")) -> None:
    for key in keys:
        vals = [fnum(r.get(key)) for r in rows if math.isfinite(fnum(r.get(key)))]
        if not vals:
            continue
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1)
        std = math.sqrt(var) or 1.0
        med = sorted(vals)[len(vals) // 2]
        mad_vals = sorted(abs(v - med) for v in vals)
        mad = mad_vals[len(mad_vals) // 2] or 1.0
        for row in rows:
            v = fnum(row.get(key))
            if math.isfinite(v):
                row[key.replace("_log", "").replace("u_raw", "u") + "_z"] = (v - mean) / std
                row[key.replace("_log", "").replace("u_raw", "u") + "_mad"] = (v - med) / mad


def calibrate(args: argparse.Namespace) -> dict[str, Any]:
    rows_in = read_jsonl(args.pair_manifest)
    out_csv = Path(args.output_csv)
    out_jsonl = Path(args.output_jsonl)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    rows_out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows_in[: args.limit or None]):
        status = "PASS_EXISTING_FIELDS"
        energies = existing_energy(row)
        if energies is None:
            if args.allow_proxy:
                energies = proxy_energy(row)
                status = "PROXY_NOT_REAL_ENERGY"
            else:
                energies = (math.nan, math.nan, math.nan, math.nan)
                status = "MISSING_REAL_ENERGY"
        local_gain = 1.0
        if get(row, "v14_local_mask_ready", "affected_time_span", "loser.affected_time_span", default=""):
            local_gain = float(args.local_gain)
        metrics = compute_metrics(*energies, local_gain=local_gain) if all(math.isfinite(v) for v in energies) else {}
        out = {
            "subset_name": args.subset_name,
            "row_idx": idx,
            "pair_id": get(row, "pair_id", default=f"row_{idx}"),
            "pair_source": get(row, "v14_pair_source", "pair_source", default=""),
            "pair_type": get(row, "pair_type", default=""),
            "failure_type": get(row, "v14_failure_type", "failure_type", "failure_tag", default=""),
            "reward_margin": reward_margin(row),
            "medium_hard": get(row, "medium_hard", "codex_visual_audit.medium_hard", default=""),
            "affected_region_available": bool(get(row, "affected_region", "loser.affected_region", default="")),
            "affected_time_span_available": bool(get(row, "affected_time_span", "loser.affected_time_span", default="")),
            "local_mask_ratio": "",
            "sigma": "",
            "timestep": "",
            "actual_sigma_bin": "unknown",
            "requested_sigma_bin": "unknown",
            "energy_backend": args.energy_backend,
            "status": status,
            "error_reason": "" if status != "MISSING_REAL_ENERGY" else "No real energy fields found; rerun with LingBot energy backend.",
        }
        out.update(metrics)
        rows_out.append(out)
    add_normalization(rows_out)
    keys: list[str] = []
    seen: set[str] = set()
    for row in rows_out:
        for key in row:
            if key not in seen:
                seen.add(key); keys.append(key)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows_out)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for row in rows_out:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    pass_count = sum(1 for r in rows_out if str(r.get("status", "")).startswith("PASS"))
    proxy_count = sum(1 for r in rows_out if r.get("status") == "PROXY_NOT_REAL_ENERGY")
    return {"rows": len(rows_out), "pass_existing_energy": pass_count, "proxy_not_real_energy": proxy_count, "output_csv": str(out_csv), "output_jsonl": str(out_jsonl)}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pair_manifest", required=True)
    p.add_argument("--subset_name", required=True)
    p.add_argument("--energy_backend", default="existing_fields", choices=["existing_fields", "manifest_proxy", "lingbot_pending"])
    p.add_argument("--allow_proxy", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--local_gain", type=float, default=4.0)
    p.add_argument("--output_csv", required=True)
    p.add_argument("--output_jsonl", required=True)
    print(json.dumps(calibrate(p.parse_args(argv)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
