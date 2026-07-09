from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ALLOWED_PHYSICAL_GPUS = {"4", "5", "6", "7"}
FORBIDDEN_PHYSICAL_GPUS = {"0", "1", "2", "3"}
DEFAULT_GLOBS = [
    "scripts/continue_physeditworld_after_mount.sh",
    "scripts/migration/*physeditworld*.sh",
    "configs/cam_physgeo/physeditworld*.yaml",
    "cam_physgeo/eval/physeditworld*.py",
    "cam_physgeo/training/train_physeditworld*.py",
    "cam_physgeo/orchestration/physeditworld*.py",
    "docs/physeditworld*.md",
    "docs/experiments/EXP_physeditworld*.md",
]
CUDA_ASSIGN_RE = re.compile(r"(?:^|[\s;&(])(?:export\s+)?CUDA_VISIBLE_DEVICES\s*=\s*([^\s#;&)]+)")


@dataclass
class AssignmentRow:
    path: str
    line_number: int
    assignment: str
    visible_devices: str
    status: str
    detail: str = ""


def iter_target_files(globs: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for pattern in globs:
        matches = sorted(Path().glob(pattern))
        for match in matches:
            if match.is_file():
                files.add(match)
    return sorted(files)


def split_visible_devices(raw: str) -> list[str]:
    value = raw.strip().strip('"').strip("'")
    if not value or "$" in value or "<" in value or ">" in value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def classify_visible_devices(raw: str) -> tuple[str, str]:
    devices = split_visible_devices(raw)
    if not devices:
        return "DYNAMIC_OR_EMPTY_ASSIGNMENT", "cannot statically prove literal physical GPU ids"
    forbidden = [d for d in devices if d in FORBIDDEN_PHYSICAL_GPUS or d not in ALLOWED_PHYSICAL_GPUS]
    if forbidden:
        return "FORBIDDEN_GPU_ASSIGNMENT", "forbidden_or_not_allowed=" + ",".join(forbidden)
    return "GPU_POLICY_PASS", "allowed=" + ",".join(devices)


def scan_file(path: Path) -> list[AssignmentRow]:
    rows: list[AssignmentRow] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in CUDA_ASSIGN_RE.finditer(line):
            visible = match.group(1)
            status, detail = classify_visible_devices(visible)
            rows.append(
                AssignmentRow(
                    path=str(path),
                    line_number=lineno,
                    assignment=match.group(0).strip(),
                    visible_devices=visible.strip().strip('"').strip("'"),
                    status=status,
                    detail=detail,
                )
            )
    return rows


def decide(rows: list[AssignmentRow], scanned_files: int) -> str:
    if scanned_files == 0:
        return "PHYS_EDITWORLD_GPU_COMMAND_POLICY_BLOCKED_NO_FILES"
    if any(row.status == "FORBIDDEN_GPU_ASSIGNMENT" for row in rows):
        return "PHYS_EDITWORLD_GPU_COMMAND_POLICY_BLOCKED_FORBIDDEN_ASSIGNMENT"
    if any(row.status == "DYNAMIC_OR_EMPTY_ASSIGNMENT" for row in rows):
        return "PHYS_EDITWORLD_GPU_COMMAND_POLICY_NEEDS_DYNAMIC_REVIEW"
    return "PHYS_EDITWORLD_GPU_COMMAND_POLICY_PASS"


def write_csv(rows: list[AssignmentRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = ["path", "line_number", "assignment", "visible_devices", "status", "detail"]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(decision: str, rows: list[AssignmentRow], files: list[Path], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "decision": decision,
        "allowed_physical_gpus": sorted(ALLOWED_PHYSICAL_GPUS),
        "forbidden_physical_gpus": sorted(FORBIDDEN_PHYSICAL_GPUS),
        "scanned_files": len(files),
        "cuda_assignments": len(rows),
        "forbidden_assignments": sum(1 for row in rows if row.status == "FORBIDDEN_GPU_ASSIGNMENT"),
        "dynamic_or_empty_assignments": sum(1 for row in rows if row.status == "DYNAMIC_OR_EMPTY_ASSIGNMENT"),
        "rows": [asdict(row) for row in rows],
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(decision: str, rows: list[AssignmentRow], files: list[Path], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    lines = [
        "# PhysEditWorld GPU Command Policy Audit",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Allowed physical GPUs: `{','.join(sorted(ALLOWED_PHYSICAL_GPUS))}`",
        f"- Forbidden physical GPUs: `{','.join(sorted(FORBIDDEN_PHYSICAL_GPUS))}`",
        f"- Scanned files: `{len(files)}`",
        f"- CUDA_VISIBLE_DEVICES assignments: `{len(rows)}`",
        f"- Status counts: `{counts}`",
        "",
        "This audit is CPU/IO only. It statically scans PhysEditWorld-related runnable artifacts for explicit CUDA_VISIBLE_DEVICES assignments and does not launch GPU work.",
    ]
    if rows:
        lines.extend(["", "## Assignments"])
        for row in rows:
            lines.append(f"- `{row.path}:{row.line_number}` `{row.visible_devices}` -> `{row.status}` ({row.detail})")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Static PhysEditWorld GPU command policy audit")
    ap.add_argument("--glob", action="append", default=[], help="Additional glob to scan; defaults are PhysEditWorld artifacts")
    ap.add_argument("--json", default="reports/physeditworld_50h/gpu_policy/gpu_command_policy_audit.json")
    ap.add_argument("--csv", default="reports/physeditworld_50h/gpu_policy/gpu_command_policy_audit.csv")
    ap.add_argument("--summary", default="reports/physeditworld_50h/gpu_policy/gpu_command_policy_audit.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    globs = DEFAULT_GLOBS + list(args.glob)
    files = iter_target_files(globs)
    rows: list[AssignmentRow] = []
    for path in files:
        rows.extend(scan_file(path))
    decision = decide(rows, len(files))
    write_csv(rows, args.csv)
    write_json(decision, rows, files, args.json)
    write_summary(decision, rows, files, args.summary)
    print(json.dumps({"decision": decision, "scanned_files": len(files), "cuda_assignments": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
