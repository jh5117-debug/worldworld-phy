
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

BETA_VALUES = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
UTILITY_KEYS = ["u_raw", "u_log", "u_z", "u_mad", "local_u_raw", "local_u_log", "local_u_z"]
UTILITY_ALIASES = {
    "u_raw": ("u_raw", "u_raw_post", "reference_relative_margin_post"),
    "u_log": ("u_log",),
    "u_z": ("u_z",),
    "u_mad": ("u_mad",),
    "local_u_raw": ("local_u_raw",),
    "local_u_log": ("local_u_log",),
    "local_u_z": ("local_u_z",),
}


def fnum(v: Any) -> float:
    try:
        x = float(v)
        return x if math.isfinite(x) else math.nan
    except Exception:
        return math.nan


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def softplus_neg(logit: float) -> float:
    # -log(sigmoid(logit)) = softplus(-logit)
    x = -logit
    if x > 50:
        return x
    return math.log1p(math.exp(x))


def quantile(vals: list[float], q: float) -> float:
    if not vals:
        return math.nan
    vals = sorted(vals)
    idx = min(max(int(round((len(vals) - 1) * q)), 0), len(vals) - 1)
    return vals[idx]


def read_values(paths: list[str]) -> dict[str, list[float]]:
    out = {k: [] for k in UTILITY_KEYS}
    for path in paths:
        p = Path(path)
        if not p.exists():
            continue
        with p.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("status") == "MISSING_REAL_ENERGY":
                    continue
                for key in UTILITY_KEYS:
                    val = math.nan
                    for alias in UTILITY_ALIASES.get(key, (key,)):
                        val = fnum(row.get(alias))
                        if math.isfinite(val):
                            break
                    if key == "u_log" and not math.isfinite(val):
                        g_w = fnum(row.get("g_w", row.get("g_w_log")))
                        g_l = fnum(row.get("g_l", row.get("g_l_log")))
                        if math.isfinite(g_w) and math.isfinite(g_l):
                            val = g_l - g_w
                    if math.isfinite(val):
                        out[key].append(val)
    return out


def sweep(args: argparse.Namespace) -> dict[str, Any]:
    values = read_values(args.input_csv)
    rows: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for utility, vals in values.items():
        if not vals:
            continue
        abs_vals = [abs(v) for v in vals]
        for beta in BETA_VALUES:
            logits = [beta * v for v in vals]
            abs_logits = [abs(x) for x in logits]
            losses = [softplus_neg(x) for x in logits]
            grad = [beta * sigmoid(-x) for x in logits]
            row = {
                "utility_type": utility,
                "count": len(vals),
                "beta": beta,
                "median_abs_u": quantile(abs_vals, 0.5),
                "median_abs_beta_u": quantile(abs_logits, 0.5),
                "p90_abs_beta_u": quantile(abs_logits, 0.9),
                "mean_dpo_loss": sum(losses) / len(losses),
                "mean_gradient_scale": sum(grad) / len(grad),
                "near_zero_ratio": sum(1 for x in abs_logits if x < 0.01) / len(abs_logits),
                "effective_ratio": sum(1 for x in abs_logits if 0.05 <= x <= 5.0) / len(abs_logits),
                "saturation_ratio": sum(1 for x in abs_logits if x > 10.0) / len(abs_logits),
            }
            rows.append(row)
            score = row["effective_ratio"] - row["near_zero_ratio"] - row["saturation_ratio"]
            if 0.1 <= row["median_abs_beta_u"] <= 1.0:
                score += 1.0
            if best is None or score > best["score"]:
                best = {"score": score, **row}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(rows[0].keys()) if rows else ["utility_type", "count", "beta"]
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    if best and float(best.get("median_abs_beta_u") or 0.0) == 0.0 and float(best.get("effective_ratio") or 0.0) == 0.0:
        rec = {
            "recommended_utility_type": "NONE_ZERO_UTILITY",
            "recommended_beta": None,
            "recommended_median_abs_beta_u": 0.0,
            "reason": "All observed utility values are zero at policy=reference; beta cannot create preference signal without a nonzero policy-reference utility change.",
            "input_csv": args.input_csv,
        }
    else:
        rec = {
            "recommended_utility_type": best.get("utility_type") if best else "NONE",
            "recommended_beta": best.get("beta") if best else None,
            "recommended_median_abs_beta_u": best.get("median_abs_beta_u") if best else None,
            "reason": "Choose utility/beta with median |beta*u| in 0.1-1.0 and high effective ratio." if best else "No finite utility values found.",
            "input_csv": args.input_csv,
        }
    Path(args.recommendation).parent.mkdir(parents=True, exist_ok=True)
    Path(args.recommendation).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    md = ["# Beta Loss Response Summary", "", f"Recommended utility: `{rec['recommended_utility_type']}`", f"Recommended beta: `{rec['recommended_beta']}`", "", "This sweep is only as real as its input utility CSVs. Rows marked `PROXY_NOT_REAL_ENERGY` must not be treated as real LingBot energy evidence."]
    Path(args.summary).write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"rows": len(rows), "output": str(out), "recommendation": rec}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input_csv", nargs="+", required=True)
    p.add_argument("--output", default="reports/dpo_utility_calibration_v14/beta_loss_response.csv")
    p.add_argument("--summary", default="reports/dpo_utility_calibration_v14/beta_loss_response_summary.md")
    p.add_argument("--recommendation", default="reports/dpo_utility_calibration_v14/recommended_dpo_scale.json")
    print(json.dumps(sweep(p.parse_args(argv)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
