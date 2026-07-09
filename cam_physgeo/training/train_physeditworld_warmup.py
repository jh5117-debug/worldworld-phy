from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Any

ALLOWED_PHYSICAL_GPUS = {"4", "5", "6", "7"}
FORBIDDEN_PHYSICAL_GPUS = {"0", "1", "2", "3"}


def count_jsonl(path: str | Path) -> int | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def read_validation_decision(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return "MISSING"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return "UNREADABLE"
    return str(obj.get("decision") or obj.get("status") or "UNKNOWN")


def parse_simple_config(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    rank_match = re.search(r"lora_rank:\s*([0-9]+)", text)
    max_steps_match = re.search(r"max_steps:\s*([0-9]+)", text)
    return {
        "exists": Path(path).exists(),
        "gravity_prompt_only": "gravity: prompt_only" in text,
        "lora_rank": int(rank_match.group(1)) if rank_match else None,
        "max_steps_config": int(max_steps_match.group(1)) if max_steps_match else None,
        "allowed_gpus_declared": "allowed_physical_gpus: [4, 5, 6, 7]" in text,
        "forbidden_gpus_declared": "forbidden_physical_gpus: [0, 1, 2, 3]" in text,
    }


def visible_gpu_status() -> tuple[str, str]:
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    devices = [d.strip() for d in visible.split(",") if d.strip()]
    if not devices:
        return visible, "NO_VISIBLE_GPU_SET"
    forbidden = [d for d in devices if d in FORBIDDEN_PHYSICAL_GPUS or d not in ALLOWED_PHYSICAL_GPUS]
    if forbidden:
        return visible, "FORBIDDEN_GPU_VISIBLE:" + ",".join(forbidden)
    return visible, "GPU_POLICY_PASS"


def write_csv(row: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = [
        "decision",
        "status",
        "error_reason",
        "config",
        "manifest",
        "val_manifest",
        "manifest_rows",
        "val_rows",
        "manifest_validation",
        "manifest_validation_decision",
        "val_manifest_validation",
        "val_manifest_validation_decision",
        "max_steps_requested",
        "gravity_prompt_only",
        "lora_rank",
        "cuda_visible_devices",
        "gpu_policy",
        "output_root",
    ]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in keys})


def write_summary(row: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PhysEditWorld Warm-Up Gate Summary",
        "",
        f"Decision: `{row['decision']}`",
        "",
        f"- Status: `{row['status']}`",
        f"- Error reason: {row.get('error_reason') or 'none'}",
        f"- Config: `{row['config']}`",
        f"- Manifest: `{row['manifest']}` rows={row.get('manifest_rows')}",
        f"- Val manifest: `{row['val_manifest']}` rows={row.get('val_rows')}",
        f"- Manifest validation: `{row.get('manifest_validation')}` decision=`{row.get('manifest_validation_decision')}`",
        f"- Val manifest validation: `{row.get('val_manifest_validation')}` decision=`{row.get('val_manifest_validation_decision')}`",
        f"- Gravity prompt-only: `{row.get('gravity_prompt_only')}`",
        f"- LoRA rank: `{row.get('lora_rank')}`",
        f"- CUDA_VISIBLE_DEVICES: `{row.get('cuda_visible_devices')}`",
        f"- GPU policy: `{row.get('gpu_policy')}`",
        "",
        "This command is a safety gate for the PhysEditWorld 50h rank32 warm-up. It does not perform training unless prerequisites are present and the backend is explicitly connected in a later implementation.",
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="PhysEditWorld prompt-gravity rank32 warm-up gate")
    ap.add_argument("--config", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--val_manifest", required=True)
    ap.add_argument("--manifest_validation", default="reports/physeditworld_50h/conversion_validation/lingbot_train_manifest_validation.json")
    ap.add_argument("--val_manifest_validation", default="reports/physeditworld_50h/conversion_validation/lingbot_val_manifest_validation.json")
    ap.add_argument("--max_steps", type=int, required=True)
    ap.add_argument("--save_steps", default="")
    ap.add_argument("--eval_every", type=int, default=0)
    ap.add_argument("--output_root", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--report_root", default="")
    ap.add_argument("--dry_run", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = parse_simple_config(args.config)
    rows = count_jsonl(args.manifest)
    val_rows = count_jsonl(args.val_manifest)
    manifest_validation_decision = read_validation_decision(args.manifest_validation)
    val_manifest_validation_decision = read_validation_decision(args.val_manifest_validation)
    visible, gpu_policy = visible_gpu_status()
    decision = "WARMUP_PREFLIGHT_READY"
    status = "PASS"
    error = ""

    if not cfg["exists"]:
        decision, status, error = "WARMUP_BLOCKED_CONFIG_MISSING", "BLOCKED", "config missing"
    elif not cfg["gravity_prompt_only"] or cfg["lora_rank"] != 32:
        decision, status, error = "WARMUP_BLOCKED_CONFIG_INVALID", "BLOCKED", "config must be prompt-only gravity and rank32"
    elif gpu_policy.startswith("FORBIDDEN_GPU_VISIBLE"):
        decision, status, error = "WARMUP_BLOCKED_FORBIDDEN_GPU", "BLOCKED", gpu_policy
    elif rows is None:
        decision, status, error = "WARMUP_BLOCKED_MANIFEST_MISSING", "BLOCKED", "train manifest missing"
    elif rows == 0:
        decision, status, error = "WARMUP_BLOCKED_EMPTY_MANIFEST", "BLOCKED", "train manifest has zero rows"
    elif val_rows is None:
        decision, status, error = "WARMUP_BLOCKED_VAL_MANIFEST_MISSING", "BLOCKED", "val manifest missing"
    elif val_rows == 0:
        decision, status, error = "WARMUP_BLOCKED_EMPTY_VAL_MANIFEST", "BLOCKED", "val manifest has zero rows"
    elif manifest_validation_decision != "LINGBOT_MANIFEST_SCHEMA_PASS":
        decision, status, error = "WARMUP_BLOCKED_MANIFEST_VALIDATION", "BLOCKED", f"train validation decision is {manifest_validation_decision}"
    elif val_manifest_validation_decision != "LINGBOT_MANIFEST_SCHEMA_PASS":
        decision, status, error = "WARMUP_BLOCKED_VAL_MANIFEST_VALIDATION", "BLOCKED", f"val validation decision is {val_manifest_validation_decision}"
    elif gpu_policy == "NO_VISIBLE_GPU_SET" and not args.dry_run:
        decision, status, error = "WARMUP_BLOCKED_NO_VISIBLE_GPU", "BLOCKED", "real warm-up requires explicit CUDA_VISIBLE_DEVICES in allowed physical GPU4-7"
    elif args.dry_run:
        decision, status = "WARMUP_DRY_RUN_READY", "PASS"
    else:
        decision, status, error = "WARMUP_BACKEND_NOT_CONNECTED", "BLOCKED", "real LingBot-Fast training backend not connected in this gate scaffold"

    report = args.report or str(Path(args.report_root or "reports/physeditworld_50h_warmup_rank32") / "preflight.csv")
    summary = str(Path(args.report_root or Path(report).parent) / "preflight_summary.md")
    row = {
        "decision": decision,
        "status": status,
        "error_reason": error,
        "config": args.config,
        "manifest": args.manifest,
        "val_manifest": args.val_manifest,
        "manifest_rows": rows,
        "val_rows": val_rows,
        "manifest_validation": args.manifest_validation,
        "manifest_validation_decision": manifest_validation_decision,
        "val_manifest_validation": args.val_manifest_validation,
        "val_manifest_validation_decision": val_manifest_validation_decision,
        "max_steps_requested": args.max_steps,
        "gravity_prompt_only": cfg["gravity_prompt_only"],
        "lora_rank": cfg["lora_rank"],
        "cuda_visible_devices": visible,
        "gpu_policy": gpu_policy,
        "output_root": args.output_root,
    }
    write_csv(row, report)
    write_summary(row, summary)
    print(json.dumps({"decision": decision, "status": status, "report": report, "summary": summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
