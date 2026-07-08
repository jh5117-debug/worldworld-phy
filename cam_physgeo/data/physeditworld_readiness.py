from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REQUIRED_SAMPLE_KEYS = (
    "sample_id",
    "replay_group_id",
    "gravity_value",
    "video_path",
    "action_trace_path",
    "camera_trajectory_path",
    "intrinsics_path",
)


@dataclass
class CheckResult:
    name: str
    status: str
    path: str = ""
    rows: int | None = None
    error_reason: str = ""
    next_action: str = ""


def count_jsonl(path: str | Path) -> int | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def read_first_jsonl(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                return json.loads(line)
    return None


def check_nas_mount(path: str | Path) -> CheckResult:
    p = Path(path)
    if not p.exists():
        return CheckResult("nas_mount", "BLOCKED", str(p), None, "path does not exist", "mount or expose the PAI/NAS target path")
    if not p.is_dir():
        return CheckResult("nas_mount", "BLOCKED", str(p), None, "path is not a directory", "fix NAS target path")
    if not os.access(p, os.R_OK):
        return CheckResult("nas_mount", "BLOCKED", str(p), None, "directory is not readable", "fix NAS permissions")
    writable = os.access(p, os.W_OK)
    return CheckResult("nas_mount", "PASS" if writable else "READ_ONLY", str(p), None, "" if writable else "directory is not writable", "run rsync dry-run" if writable else "fix write permission or choose writable target")


def check_manifest(path: str | Path, name: str, require_rows: bool = True) -> CheckResult:
    p = Path(path)
    if not p.exists():
        return CheckResult(name, "BLOCKED", str(p), None, "manifest missing", "run the prior phase that creates this manifest")
    rows = count_jsonl(p)
    if rows is None:
        return CheckResult(name, "BLOCKED", str(p), None, "manifest unreadable", "inspect path")
    if require_rows and rows == 0:
        return CheckResult(name, "BLOCKED", str(p), rows, "manifest has zero rows", "mount selected PhysEditWorld 50h root and rerun audit/conversion")
    return CheckResult(name, "PASS", str(p), rows, next_action="continue next phase")


def check_sample_schema(path: str | Path) -> CheckResult:
    p = Path(path)
    first = read_first_jsonl(p)
    if first is None:
        return CheckResult("sample_schema", "BLOCKED", str(p), 0, "no sample row available", "requires non-empty strict manifest")
    missing = [k for k in REQUIRED_SAMPLE_KEYS if first.get(k) in (None, "")]
    if missing:
        return CheckResult("sample_schema", "BLOCKED", str(p), None, "missing keys: " + ",".join(missing), "fix manifest schema before conversion")
    return CheckResult("sample_schema", "PASS", str(p), None, next_action="run LingBot conversion smoke")


def check_root_candidates(candidate_file: str | Path) -> CheckResult:
    p = Path(candidate_file)
    if not p.exists():
        return CheckResult("physeditworld_root_candidates", "BLOCKED", str(p), None, "candidate file missing", "run bounded PhysEditWorld root search")
    rows = [line.strip() for line in p.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    likely = [r for r in rows if "physedit" in r.lower() and "reports/" not in r and "world_model_phys" not in r]
    status = "PASS" if likely else "BLOCKED"
    return CheckResult(
        "physeditworld_root_candidates",
        status,
        str(p),
        len(rows),
        "no external-looking PhysEditWorld root candidate" if not likely else "",
        "provide/mount selected PhysEditWorld 50h root" if not likely else "inspect candidates and rerun manifest audit",
    )


def overall_decision(results: list[CheckResult]) -> str:
    by_name = {r.name: r for r in results}
    if by_name.get("strict_manifest", CheckResult("", "BLOCKED")).status != "PASS":
        return "PHYS_EDIT_WORLD_ROOT_OR_MANIFEST_BLOCKED"
    if by_name.get("lingbot_train_manifest", CheckResult("", "BLOCKED")).status != "PASS":
        return "PHYS_EDIT_WORLD_CONVERSION_BLOCKED"
    if by_name.get("nas_mount", CheckResult("", "BLOCKED")).status not in {"PASS", "READ_ONLY"}:
        return "PAI_NAS_MOUNT_BLOCKED"
    return "READY_FOR_BASELINE_ROLLOUT_PREFLIGHT"


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = ["name", "status", "path", "rows", "error_reason", "next_action"]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in keys})


def write_summary(results: list[CheckResult], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# PhysEditWorld PAI Readiness Preflight", "", f"Decision: `{decision}`", "", "## Checks", ""]
    for r in results:
        row_part = "" if r.rows is None else f", rows={r.rows}"
        lines.append(f"- `{r.name}`: `{r.status}` ({r.path}{row_part})")
        if r.error_reason:
            lines.append(f"  - blocker: {r.error_reason}")
        if r.next_action:
            lines.append(f"  - next: {r.next_action}")
    lines.extend([
        "",
        "## Policy",
        "",
        "This preflight is CPU/IO only. It does not launch rollout, training, DPO, StageB, GRPO, or checkpoint deletion.",
        "It is intended to be rerun on H20 or PAI after the selected PhysEditWorld 50h root and NAS mount become visible.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_preflight(args: argparse.Namespace) -> tuple[str, list[CheckResult]]:
    results = [
        check_nas_mount(args.nas_path),
        check_root_candidates(args.candidate_file),
        check_manifest(args.strict_manifest, "strict_manifest", require_rows=True),
        check_manifest(args.train_manifest, "train_manifest", require_rows=True),
        check_manifest(args.lingbot_train_manifest, "lingbot_train_manifest", require_rows=True),
        check_sample_schema(args.strict_manifest),
    ]
    decision = overall_decision(results)
    return decision, results


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="PhysEditWorld 50h H20/PAI readiness preflight")
    ap.add_argument("--nas_path", default="/mnt/workspace/hj/nas_hj")
    ap.add_argument("--candidate_file", default="reports/migration/physeditworld_candidates_raw.txt")
    ap.add_argument("--strict_manifest", default="manifests/physeditworld_50h_all.jsonl")
    ap.add_argument("--train_manifest", default="manifests/physeditworld_50h_train.jsonl")
    ap.add_argument("--lingbot_train_manifest", default="manifests/physeditworld_50h_lingbot_train.jsonl")
    ap.add_argument("--output_csv", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--json", default="")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    decision, results = run_preflight(args)
    rows = [asdict(r) for r in results]
    write_csv(rows, args.output_csv)
    write_summary(results, decision, args.summary)
    if args.json:
        p = Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"decision": decision, "checks": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "checks": len(results)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
