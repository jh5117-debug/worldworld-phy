"""Generate v12 LoRA scope inventory and candidate summaries.

This command is intentionally non-training. It combines static target-group rules with
previous verified camera-condition LoRA inventory when present. Runtime winner-anchor
sanity remains the authority for actual scope acceptance.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from cam_physgeo.dpo.lora_scope_config_v12 import SCOPE_CANDIDATES, scope_summary_rows

HISTORICAL_CAMERA_INVENTORY = Path("reports/dpo_probe_v2v5_20260627/tiny1_step1_sanity/preflight_summary.json")


def load_historical_camera_modules() -> tuple[list[dict[str, Any]], int | None]:
    if not HISTORICAL_CAMERA_INVENTORY.exists():
        return [], None
    data = json.loads(HISTORICAL_CAMERA_INVENTORY.read_text())
    inv = data.get("lora_inventory") or {}
    modules = inv.get("modules") or []
    trainable = data.get("policy_trainable_params")
    return list(modules), int(trainable) if trainable is not None else None


def candidate_param_estimates(camera_r4_params: int | None) -> dict[str, str]:
    estimates: dict[str, str] = {}
    for scope, spec in SCOPE_CANDIDATES.items():
        rank = int(spec["rank"])
        groups = set(spec["target_groups"])
        if groups == {"camera_conditioning"} and camera_r4_params:
            estimates[scope] = str(int(camera_r4_params * rank / 4))
        else:
            estimates[scope] = "RUNTIME_SCOPE_SANITY_REQUIRED"
    return estimates


def write_inventory(output: Path, modules: list[dict[str, Any]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["module_name", "group", "rank_observed", "shape", "dtype", "requires_grad_default", "recommended_lora_group", "memory_risk", "module_regex", "status"]
    rows: list[dict[str, Any]] = []
    for mod in modules:
        name = str(mod.get("name", ""))
        group = str(mod.get("group", "camera_conditioning"))
        rows.append({
            "module_name": name,
            "group": group,
            "rank_observed": mod.get("rank", ""),
            "shape": "NOT_STORED_IN_HISTORICAL_INVENTORY",
            "dtype": "NOT_STORED_IN_HISTORICAL_INVENTORY",
            "requires_grad_default": "False after LoRA wrapping; LoRA A/B true",
            "recommended_lora_group": group,
            "memory_risk": "low" if group == "camera_conditioning" else "unknown",
            "module_regex": name.replace(".", "\\."),
            "status": "HISTORICAL_RUNTIME_VERIFIED",
        })
    for group, regex, risk in [
        ("self_attention", r"blocks\\.[0-3]\\..*(self_attn|attn1).*", "medium"),
        ("cross_attention", r"blocks\\.[0-3]\\..*(cross_attn|attn2).*", "medium_high"),
        ("adaln_camera_mod", r".*(ada|mod|scale|shift|cam).*", "unknown"),
        ("ffn", r".*(ffn|mlp|feed_forward).*", "forbidden"),
    ]:
        rows.append({
            "module_name": "RUNTIME_ENUM_REQUIRED",
            "group": group,
            "rank_observed": "",
            "shape": "RUNTIME_ENUM_REQUIRED",
            "dtype": "RUNTIME_ENUM_REQUIRED",
            "requires_grad_default": "False unless explicitly selected",
            "recommended_lora_group": group if group != "ffn" else "FORBIDDEN",
            "memory_risk": risk,
            "module_regex": regex,
            "status": "STATIC_RULE_ONLY",
        })
    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_candidates(path: Path, summary_md: Path, camera_params: int | None) -> None:
    estimates = candidate_param_estimates(camera_params)
    payload = {name: {**spec, "estimated_trainable_params": estimates[name]} for name, spec in SCOPE_CANDIDATES.items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with summary_md.open("w") as f:
        f.write("Current Status: PASS_WITH_RUNTIME_CAVEAT\n\n# v12 LoRA Scope Candidate Summary\n\n")
        for name, spec in payload.items():
            f.write(f"## {name}\n\n")
            f.write(f"- Description: {spec['description']}\n")
            f.write(f"- Target groups: `{spec['target_groups']}`\n")
            f.write(f"- Rank/alpha: {spec['rank']} / {spec['alpha']}\n")
            f.write(f"- Blocks: {spec['block_start']}..{spec['block_end']}\n")
            f.write(f"- Estimated trainable params: `{spec['estimated_trainable_params']}`\n")
            f.write(f"- Memory risk: {spec['memory_risk']}\n\n")
        f.write("## Caveat\n\nCamera-conditioning module count and params are from a historical runtime-verified preflight. Self/cross/AdaLN candidates still require winner-anchor runtime sanity before DPO. FFN/broad/all-block scopes remain forbidden.\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="lingbot_fast")
    ap.add_argument("--output", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--candidates", default="reports/dpo_training_sanity_v12/lora_scope_candidates.json")
    args = ap.parse_args()
    if args.model != "lingbot_fast":
        raise ValueError("v12 inventory currently supports --model lingbot_fast only")
    modules, camera_params = load_historical_camera_modules()
    write_inventory(Path(args.output), modules)
    write_candidates(Path(args.candidates), Path(args.summary), camera_params)


if __name__ == "__main__":
    main()
