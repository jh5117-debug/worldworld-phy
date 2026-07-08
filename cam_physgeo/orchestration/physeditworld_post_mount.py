from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PASS_BACKEND_READINESS = "PHYS_EDITWORLD_BACKEND_READY_FOR_BASELINE_WARMUP"


@dataclass
class StepResult:
    step: str
    status: str
    command: str
    exit_code: int | None = None
    decision: str = ""
    output_path: str = ""
    error_reason: str = ""


def split_roots(value: str) -> list[str]:
    return [part for part in value.replace(",", ":").split(":") if part]


def count_jsonl(path: str | Path) -> int | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def norm_path(path: str | Path) -> str:
    return str(Path(path).expanduser().resolve(strict=False))


def read_json_decision(path: str | Path) -> tuple[str, str]:
    p = Path(path)
    if not p.exists():
        return "MISSING", "file missing"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return "UNREADABLE", repr(exc)
    return str(obj.get("decision") or obj.get("status") or "UNKNOWN"), str(obj.get("error_reason") or "")


def validate_root_lock(roots: list[str], lock_path: str | Path, allow_unlocked_roots: bool = False) -> StepResult:
    command = f"validate selected-root lock {lock_path}"
    if allow_unlocked_roots:
        return StepResult(
            "root_lock",
            "PASS",
            command,
            decision="POST_MOUNT_ROOT_LOCK_BYPASSED_FOR_MANUAL_REVIEW",
            output_path=str(lock_path),
            error_reason="allow_unlocked_roots=true; do not train/rollout from this path",
        )
    p = Path(lock_path)
    if not p.exists():
        return StepResult(
            "root_lock",
            "BLOCKED",
            command,
            decision="POST_MOUNT_BLOCKED_NO_ROOT_LOCK",
            output_path=str(lock_path),
            error_reason="run scripts/migration/select_physeditworld_root.sh with a strong PHYS_EDITWORLD_ROOTS path before post-mount continuation",
        )
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return StepResult(
            "root_lock",
            "BLOCKED",
            command,
            decision="POST_MOUNT_BLOCKED_UNREADABLE_ROOT_LOCK",
            output_path=str(lock_path),
            error_reason=repr(exc),
        )
    decision = str(obj.get("decision") or "")
    if decision != "PHYS_EDITWORLD_ROOT_SELECTION_LOCKED":
        return StepResult(
            "root_lock",
            "BLOCKED",
            command,
            decision="POST_MOUNT_BLOCKED_ROOT_LOCK_NOT_PASS",
            output_path=str(lock_path),
            error_reason=f"root lock decision is {decision or 'missing'}, expected PHYS_EDITWORLD_ROOT_SELECTION_LOCKED",
        )
    locked_roots = {
        norm_path(row.get("root", ""))
        for row in obj.get("roots", [])
        if row.get("root") and row.get("status") == "LOCKED"
    }
    requested_roots = {norm_path(root) for root in roots}
    if not locked_roots:
        return StepResult(
            "root_lock",
            "BLOCKED",
            command,
            decision="POST_MOUNT_BLOCKED_ROOT_LOCK_EMPTY",
            output_path=str(lock_path),
            error_reason="lock has no LOCKED roots",
        )
    if requested_roots != locked_roots:
        return StepResult(
            "root_lock",
            "BLOCKED",
            command,
            decision="POST_MOUNT_BLOCKED_ROOT_LOCK_MISMATCH",
            output_path=str(lock_path),
            error_reason=f"requested roots {sorted(requested_roots)} do not match locked roots {sorted(locked_roots)}",
        )
    return StepResult(
        "root_lock",
        "PASS",
        command,
        decision="POST_MOUNT_ROOT_LOCK_PASS",
        output_path=str(lock_path),
    )


def run(cmd: list[str], dry_run: bool) -> tuple[int, str]:
    printable = " ".join(shlex.quote(x) for x in cmd)
    if dry_run:
        return 0, "DRY_RUN: " + printable
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return proc.returncode, proc.stdout[-4000:]


def write_csv(rows: list[StepResult], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = ["step", "status", "command", "exit_code", "decision", "output_path", "error_reason"]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: asdict(row).get(k, "") for k in keys})


def write_json(rows: list[StepResult], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "steps": [asdict(r) for r in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[StepResult], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# PhysEditWorld Post-Mount Continuation Summary", "", f"Decision: `{decision}`", "", "## Steps", ""]
    for row in rows:
        lines.append(f"- `{row.step}`: `{row.status}`")
        lines.append(f"  - command: `{row.command}`")
        if row.decision:
            lines.append(f"  - decision: `{row.decision}`")
        if row.output_path:
            lines.append(f"  - output: `{row.output_path}`")
        if row.error_reason:
            lines.append(f"  - error: {row.error_reason}")
    lines.extend([
        "",
        "## Safety",
        "",
        "This continuation runs only Phase 1/2 CPU/IO preparation and safe gate collectors. It does not start warm-up training, checkpoint rollout, DPO, StageB, GRPO, broad-LoRA, or deletion.",
        "Smoke conversion writes a non-canonical smoke manifest. Canonical LingBot train/val/test manifests are written only when `--run_full_conversion` is explicitly set.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def overall(rows: list[StepResult]) -> str:
    if not rows:
        return "POST_MOUNT_NO_STEPS"
    first_bad = next((r for r in rows if r.status in {"BLOCKED", "FAIL"}), None)
    if first_bad:
        return "POST_MOUNT_BLOCKED_AT_" + first_bad.step.upper()
    return "POST_MOUNT_PHASE12_DONE_RUN_PIPELINE_GATE_NEXT"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Continue PhysEditWorld pipeline after selected root is mounted")
    ap.add_argument("--roots", nargs="*", default=None, help="PhysEditWorld roots. Defaults to PHYS_EDITWORLD_ROOTS colon/comma list.")
    ap.add_argument("--target_hours", type=float, default=50.0)
    ap.add_argument("--limit", type=int, default=32, help="Conversion smoke limit")
    ap.add_argument("--skip_video_probe", action="store_true")
    ap.add_argument("--run_full_conversion", action="store_true", help="After smoke conversion passes, write canonical all/train/val/test LingBot manifests.")
    ap.add_argument("--dry_run", action="store_true")
    ap.add_argument("--root_lock", default="reports/migration/physeditworld_selected_root.lock.json")
    ap.add_argument("--allow_unlocked_roots", action="store_true", help="Manual-inspection bypass only; never use for training/rollout.")
    ap.add_argument("--output_csv", default="reports/physeditworld_50h/post_mount/post_mount_status.csv")
    ap.add_argument("--output_json", default="reports/physeditworld_50h/post_mount/post_mount_status.json")
    ap.add_argument("--summary", default="reports/physeditworld_50h/post_mount/post_mount_summary.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    roots = args.roots if args.roots is not None else split_roots(os.environ.get("PHYS_EDITWORLD_ROOTS", ""))
    rows: list[StepResult] = []
    if not roots:
        rows.append(StepResult("root_input", "BLOCKED", "PHYS_EDITWORLD_ROOTS", decision="POST_MOUNT_BLOCKED_NO_ROOTS", error_reason="set PHYS_EDITWORLD_ROOTS=/path/to/selected_50h_root"))
        decision = overall(rows)
        write_csv(rows, args.output_csv)
        write_json(rows, decision, args.output_json)
        write_summary(rows, decision, args.summary)
        print(json.dumps({"decision": decision, "steps": len(rows)}, sort_keys=True))
        return 0

    lock_row = validate_root_lock(roots, args.root_lock, args.allow_unlocked_roots)
    rows.append(lock_row)
    if lock_row.status == "BLOCKED":
        decision = overall(rows)
        write_csv(rows, args.output_csv)
        write_json(rows, decision, args.output_json)
        write_summary(rows, decision, args.summary)
        print(json.dumps({"decision": decision, "steps": len(rows)}, sort_keys=True))
        return 0

    missing = [root for root in roots if not Path(root).exists()]
    if missing:
        rows.append(StepResult("root_input", "BLOCKED", " ".join(roots), decision="POST_MOUNT_BLOCKED_ROOT_MISSING", error_reason="missing roots: " + ",".join(missing)))
        decision = overall(rows)
        write_csv(rows, args.output_csv)
        write_json(rows, decision, args.output_json)
        write_summary(rows, decision, args.summary)
        print(json.dumps({"decision": decision, "steps": len(rows)}, sort_keys=True))
        return 0

    manifest_cmd = [
        "python3", "-m", "cam_physgeo.data.physeditworld_manifest",
        "--roots", *roots,
        "--target_hours", str(args.target_hours),
        "--output", "manifests/physeditworld_50h_all.jsonl",
        "--report", "reports/physeditworld_50h/data_audit.csv",
        "--summary", "reports/physeditworld_50h/data_audit_summary.md",
    ]
    if args.skip_video_probe:
        manifest_cmd.append("--skip_video_probe")
    code, out = run(manifest_cmd, args.dry_run)
    rows.append(StepResult("manifest_audit", "PASS" if code == 0 else "FAIL", " ".join(shlex.quote(x) for x in manifest_cmd), code, output_path="manifests/physeditworld_50h_all.jsonl", error_reason="" if code == 0 else out))
    if code != 0 or count_jsonl("manifests/physeditworld_50h_all.jsonl") == 0 and not args.dry_run:
        if code == 0:
            rows[-1].status = "BLOCKED"
            rows[-1].decision = "PHYS_EDIT_WORLD_DATA_NOT_FOUND"
            rows[-1].error_reason = "manifest audit produced zero rows"
        decision = overall(rows)
        write_csv(rows, args.output_csv)
        write_json(rows, decision, args.output_json)
        write_summary(rows, decision, args.summary)
        print(json.dumps({"decision": decision, "steps": len(rows)}, sort_keys=True))
        return 0

    commands = [
        ("split", ["python3", "-m", "cam_physgeo.data.physeditworld_split", "--manifest", "manifests/physeditworld_50h_all.jsonl", "--out_dir", "manifests", "--prefix", "physeditworld_50h", "--report_dir", "reports/physeditworld_50h"], "manifests/physeditworld_50h_train.jsonl"),
        (
            "conversion_smoke",
            [
                "python3", "-m", "cam_physgeo.data.physeditworld_to_lingbot",
                "--manifest", "manifests/physeditworld_50h_train.jsonl",
                "--limit", str(args.limit),
                "--output_root", "local_assets/physeditworld_50h_lingbot_smoke",
                "--num_frames", "81",
                "--fps", "16",
                "--height", "480",
                "--width", "832",
                "--gravity_prompt_style", "physeditworld_v0",
                "--report", "reports/physeditworld_50h/conversion_smoke.csv",
                "--summary", "reports/physeditworld_50h/conversion_smoke_summary.md",
                "--manifest_out", "manifests/physeditworld_50h_lingbot_smoke_train.jsonl",
            ],
            "manifests/physeditworld_50h_lingbot_smoke_train.jsonl",
        ),
        (
            "conversion_smoke_validation",
            [
                "python3", "-m", "cam_physgeo.data.lingbot_manifest_validate",
                "--manifest", "manifests/physeditworld_50h_lingbot_smoke_train.jsonl",
                "--output_csv", "reports/physeditworld_50h/conversion_validation/lingbot_smoke_train_manifest_validation.csv",
                "--output_json", "reports/physeditworld_50h/conversion_validation/lingbot_smoke_train_manifest_validation.json",
                "--summary", "reports/physeditworld_50h/conversion_validation/lingbot_smoke_train_manifest_validation.md",
            ],
            "reports/physeditworld_50h/conversion_validation/lingbot_smoke_train_manifest_validation.json",
        ),
    ]
    if args.run_full_conversion:
        for split_name, manifest_path in [
            ("all", "manifests/physeditworld_50h_all.jsonl"),
            ("train", "manifests/physeditworld_50h_train.jsonl"),
            ("val", "manifests/physeditworld_50h_val.jsonl"),
            ("test", "manifests/physeditworld_50h_test.jsonl"),
        ]:
            commands.append(
                (
                    f"conversion_{split_name}",
                    [
                        "python3", "-m", "cam_physgeo.data.physeditworld_to_lingbot",
                        "--manifest", manifest_path,
                        "--output_root", "local_assets/physeditworld_50h_lingbot_v0",
                        "--num_frames", "81",
                        "--fps", "16",
                        "--height", "480",
                        "--width", "832",
                        "--gravity_prompt_style", "physeditworld_v0",
                        "--report", f"reports/physeditworld_50h/conversion_{split_name}.csv",
                        "--summary", f"reports/physeditworld_50h/conversion_{split_name}_summary.md",
                        "--manifest_out", f"manifests/physeditworld_50h_lingbot_{split_name}.jsonl",
                    ],
                    f"manifests/physeditworld_50h_lingbot_{split_name}.jsonl",
                )
            )
        for split_name in ["train", "val", "test"]:
            commands.append(
                (
                    f"conversion_{split_name}_validation",
                    [
                        "python3", "-m", "cam_physgeo.data.lingbot_manifest_validate",
                        "--manifest", f"manifests/physeditworld_50h_lingbot_{split_name}.jsonl",
                        "--output_csv", f"reports/physeditworld_50h/conversion_validation/lingbot_{split_name}_manifest_validation.csv",
                        "--output_json", f"reports/physeditworld_50h/conversion_validation/lingbot_{split_name}_manifest_validation.json",
                        "--summary", f"reports/physeditworld_50h/conversion_validation/lingbot_{split_name}_manifest_validation.md",
                    ],
                    f"reports/physeditworld_50h/conversion_validation/lingbot_{split_name}_manifest_validation.json",
                )
            )
    else:
        commands.extend(
            [
                (
                    "conversion_train_validation",
                    [
                        "python3", "-m", "cam_physgeo.data.lingbot_manifest_validate",
                        "--manifest", "manifests/physeditworld_50h_lingbot_train.jsonl",
                        "--output_csv", "reports/physeditworld_50h/conversion_validation/lingbot_train_manifest_validation.csv",
                        "--output_json", "reports/physeditworld_50h/conversion_validation/lingbot_train_manifest_validation.json",
                        "--summary", "reports/physeditworld_50h/conversion_validation/lingbot_train_manifest_validation.md",
                    ],
                    "reports/physeditworld_50h/conversion_validation/lingbot_train_manifest_validation.json",
                ),
                (
                    "conversion_val_validation",
                    [
                        "python3", "-m", "cam_physgeo.data.lingbot_manifest_validate",
                        "--manifest", "manifests/physeditworld_50h_lingbot_val.jsonl",
                        "--output_csv", "reports/physeditworld_50h/conversion_validation/lingbot_val_manifest_validation.csv",
                        "--output_json", "reports/physeditworld_50h/conversion_validation/lingbot_val_manifest_validation.json",
                        "--summary", "reports/physeditworld_50h/conversion_validation/lingbot_val_manifest_validation.md",
                    ],
                    "reports/physeditworld_50h/conversion_validation/lingbot_val_manifest_validation.json",
                ),
            ]
        )
    for name, cmd, outpath in commands:
        code, out = run(cmd, args.dry_run)
        rows.append(StepResult(name, "PASS" if code == 0 else "FAIL", " ".join(shlex.quote(x) for x in cmd), code, output_path=outpath, error_reason="" if code == 0 else out))
        if code != 0:
            break

    if not any(row.status in {"BLOCKED", "FAIL"} for row in rows):
        backend_cmd = ["python3", "-m", "cam_physgeo.orchestration.physeditworld_backend_readiness"]
        backend_output = "reports/physeditworld_50h/backend_readiness/backend_readiness.json"
        code, out = run(backend_cmd, args.dry_run)
        backend_decision, backend_error = read_json_decision(backend_output)
        backend_status = "PASS" if code == 0 and backend_decision == PASS_BACKEND_READINESS else "BLOCKED"
        if code != 0:
            backend_status = "FAIL"
            backend_error = out
        rows.append(StepResult(
            "backend_readiness",
            backend_status,
            " ".join(shlex.quote(x) for x in backend_cmd),
            code,
            decision=backend_decision,
            output_path=backend_output,
            error_reason=backend_error if backend_error else ("backend readiness must pass before baseline/warm-up/checkpoint eval" if backend_status == "BLOCKED" else ""),
        ))

    if not any(row.status in {"BLOCKED", "FAIL"} for row in rows):
        final_commands = [
            ("pipeline_gate", ["bash", "scripts/run_physeditworld_pipeline_gates.sh"], "reports/physeditworld_50h/pipeline_gate/pipeline_gate_summary.md"),
            ("requirement_matrix", ["python3", "-m", "cam_physgeo.orchestration.physeditworld_requirement_matrix"], "reports/physeditworld_50h/requirement_matrix.md"),
        ]
        for name, cmd, outpath in final_commands:
            code, out = run(cmd, args.dry_run)
            rows.append(StepResult(name, "PASS" if code == 0 else "FAIL", " ".join(shlex.quote(x) for x in cmd), code, output_path=outpath, error_reason="" if code == 0 else out))
            if code != 0:
                break

    decision = overall(rows)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json)
    write_summary(rows, decision, args.summary)
    print(json.dumps({"decision": decision, "steps": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
