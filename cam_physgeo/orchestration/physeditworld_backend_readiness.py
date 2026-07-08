from __future__ import annotations

import argparse
import csv
import importlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PASS_DECISION = "PHYS_EDITWORLD_BACKEND_READY_FOR_BASELINE_WARMUP"
SCAFFOLD_DECISION = "PHYS_EDITWORLD_BACKEND_BLOCKED_SCAFFOLD_ONLY"


@dataclass
class BackendCheck:
    name: str
    status: str
    evidence: str
    detail: str = ""
    next_action: str = ""


def check_path(name: str, path: str, next_action: str) -> BackendCheck:
    p = Path(path)
    if p.exists():
        detail = "exists"
        if p.is_symlink():
            detail += f"; symlink_target={p.resolve(strict=False)}"
        return BackendCheck(name, "PASS", path, detail)
    return BackendCheck(name, "BLOCKED", path, "missing", next_action)


def check_import(module: str) -> BackendCheck:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:
        return BackendCheck(f"import_{module}", "BLOCKED", module, repr(exc), f"fix import for {module}")
    return BackendCheck(f"import_{module}", "PASS", module, getattr(imported, "__file__", "built-in"))


def parse_warmup_config(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
    rank_match = re.search(r"lora_rank:\s*([0-9]+)", text)
    return {
        "exists": p.exists(),
        "gravity_prompt_only": "gravity: prompt_only" in text,
        "lora_rank": int(rank_match.group(1)) if rank_match else None,
        "allowed_gpus": "allowed_physical_gpus: [4, 5, 6, 7]" in text,
        "forbidden_gpus": "forbidden_physical_gpus: [0, 1, 2, 3]" in text,
    }


def check_warmup_config(path: str) -> list[BackendCheck]:
    cfg = parse_warmup_config(path)
    rows = [check_path("warmup_config_exists", path, "create PhysEditWorld rank32 warm-up config")]
    rows.append(
        BackendCheck(
            "warmup_config_prompt_only_gravity",
            "PASS" if cfg["gravity_prompt_only"] else "BLOCKED",
            path,
            f"gravity_prompt_only={cfg['gravity_prompt_only']}",
            "keep first version prompt-only; do not add gravity MLP/embedding",
        )
    )
    rows.append(
        BackendCheck(
            "warmup_config_lora_rank32",
            "PASS" if cfg["lora_rank"] == 32 else "BLOCKED",
            path,
            f"lora_rank={cfg['lora_rank']}",
            "set first warm-up LoRA rank to 32",
        )
    )
    rows.append(
        BackendCheck(
            "warmup_config_gpu_policy",
            "PASS" if cfg["allowed_gpus"] and cfg["forbidden_gpus"] else "BLOCKED",
            path,
            f"allowed_gpus={cfg['allowed_gpus']} forbidden_gpus={cfg['forbidden_gpus']}",
            "declare allowed GPU4-7 and forbidden GPU0-3",
        )
    )
    return rows


def tsv_has_existing_role(path: str, role_tokens: list[str]) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    text = p.read_text(encoding="utf-8", errors="ignore").lower()
    return any(token.lower() in text for token in role_tokens) and "\ttrue\t" in text


def check_manifest_role(name: str, path: str, tokens: list[str], next_action: str) -> BackendCheck:
    if not Path(path).exists():
        return BackendCheck(name, "BLOCKED", path, "manifest missing", next_action)
    ok = tsv_has_existing_role(path, tokens)
    return BackendCheck(name, "PASS" if ok else "REVIEW_REQUIRED", path, f"tokens={','.join(tokens)} found_existing={ok}", next_action)


def check_scaffold_backend(name: str, path: str, marker: str, next_action: str) -> BackendCheck:
    p = Path(path)
    if not p.exists():
        return BackendCheck(name, "BLOCKED", path, "file missing", next_action)
    text = p.read_text(encoding="utf-8", errors="ignore")
    if marker in text:
        return BackendCheck(name, "BLOCKED", path, f"found marker {marker}", next_action)
    return BackendCheck(name, "PASS", path, f"marker {marker} absent")


def build_rows(args: argparse.Namespace) -> list[BackendCheck]:
    rows: list[BackendCheck] = []
    rows.extend(
        [
            check_path("lingbot_code_link", args.lingbot_code, "restore or relink LingBot code before baseline/warm-up"),
            check_path("base_model_link", args.base_model, "restore or relink LingBot base/fast weights before baseline/warm-up"),
            check_path("weights_manifest", args.weights_manifest, "build required weights migration manifest"),
            check_path("data_manifest", args.data_manifest, "build required data migration manifest"),
        ]
    )
    rows.extend(check_warmup_config(args.warmup_config))
    rows.extend(
        [
            check_manifest_role("weights_manifest_lingbot_code", args.weights_manifest, ["links/lingbot_code", "lingbot_code"], "mark LingBot code as required for migration restore"),
            check_manifest_role("weights_manifest_base_model", args.weights_manifest, ["links/base_model", "lingbot-base", "lingbot-fast"], "mark LingBot base/fast weights as required for migration restore"),
            check_import("cam_physgeo.eval.physeditworld_baseline_rollout"),
            check_import("cam_physgeo.eval.physeditworld_checkpoint_eval"),
            check_import("cam_physgeo.training.train_physeditworld_warmup"),
            check_import("cam_physgeo.dpo.physeditworld_pair_manifest_validate"),
            check_scaffold_backend(
                "baseline_rollout_backend_connected",
                "cam_physgeo/eval/physeditworld_baseline_rollout.py",
                "BASELINE_BACKEND_NOT_CONNECTED",
                "wire real LingBot-Fast V2V-5 baseline rollout invocation with no image-only fallback",
            ),
            check_scaffold_backend(
                "checkpoint_eval_backend_connected",
                "cam_physgeo/eval/physeditworld_checkpoint_eval.py",
                "CHECKPOINT_EVAL_BACKEND_NOT_CONNECTED",
                "wire real checkpoint rollout, metrics, and Codex visual audit runner",
            ),
            check_scaffold_backend(
                "warmup_training_backend_connected",
                "cam_physgeo/training/train_physeditworld_warmup.py",
                "WARMUP_BACKEND_NOT_CONNECTED",
                "connect gated LingBot-Fast rank32 warm-up backend after manifest validation",
            ),
        ]
    )
    try:
        import torch

        rows.append(BackendCheck("torch_import", "PASS", "torch", f"torch={torch.__version__} cuda_available={torch.cuda.is_available()}"))
    except Exception as exc:
        rows.append(BackendCheck("torch_import", "BLOCKED", "torch", repr(exc), "fix torch import before any GPU preflight"))
    rows.append(BackendCheck("python_version", "PASS", sys.executable, sys.version.replace("\n", " ")))
    return rows


def overall_decision(rows: list[BackendCheck]) -> str:
    scaffold_blocks = [row for row in rows if row.status == "BLOCKED" and "BACKEND_NOT_CONNECTED" in row.detail]
    hard_blocks = [row for row in rows if row.status == "BLOCKED" and row not in scaffold_blocks]
    if hard_blocks:
        return "PHYS_EDITWORLD_BACKEND_BLOCKED_DEPENDENCY"
    if scaffold_blocks:
        return SCAFFOLD_DECISION
    if any(row.status == "REVIEW_REQUIRED" for row in rows):
        return "PHYS_EDITWORLD_BACKEND_REVIEW_REQUIRED"
    return PASS_DECISION


def write_csv(rows: list[BackendCheck], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(BackendCheck.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[BackendCheck], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "checks": [asdict(row) for row in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[BackendCheck], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    lines = ["# PhysEditWorld LingBot Backend Readiness", "", f"Decision: `{decision}`", "", "## Status Counts", ""]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    lines.extend(["", "## Checks", ""])
    for row in rows:
        lines.append(f"- `{row.name}`: `{row.status}`")
        lines.append(f"  - evidence: `{row.evidence}`")
        if row.detail:
            lines.append(f"  - detail: {row.detail}")
        if row.next_action and row.status != "PASS":
            lines.append(f"  - next: {row.next_action}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This audit is CPU/IO only. It imports lightweight Python modules and reads manifests/configs; it does not load model weights, use GPUs, train, rollout, copy, delete, or push local_assets.",
        ]
    )
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Audit LingBot/PhysEditWorld backend readiness before baseline and warm-up")
    ap.add_argument("--lingbot_code", default="links/lingbot_code")
    ap.add_argument("--base_model", default="links/base_model")
    ap.add_argument("--warmup_config", default="configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml")
    ap.add_argument("--weights_manifest", default="reports/migration/required_weights_manifest.tsv")
    ap.add_argument("--data_manifest", default="reports/migration/required_data_manifest.tsv")
    ap.add_argument("--output_csv", default="reports/physeditworld_50h/backend_readiness/backend_readiness.csv")
    ap.add_argument("--output_json", default="reports/physeditworld_50h/backend_readiness/backend_readiness.json")
    ap.add_argument("--summary", default="reports/physeditworld_50h/backend_readiness/backend_readiness.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = build_rows(args)
    decision = overall_decision(rows)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json)
    write_summary(rows, decision, args.summary)
    print(json.dumps({"decision": decision, "checks": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
