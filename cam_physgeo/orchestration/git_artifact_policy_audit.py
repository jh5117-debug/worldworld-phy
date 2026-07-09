from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

FORBIDDEN_RE = re.compile(
    r"(^local_assets/|\.(mp4|jpg|jpeg|png|hdf5|h5|npy|npz|pt|pth|safetensors|ckpt|bin|tar|zip|log)$)",
    re.IGNORECASE,
)
DEFAULT_LARGE_WARN_BYTES = 10 * 1024 * 1024


@dataclass
class ArtifactRow:
    path: str
    size_bytes: int
    status: str
    reason: str


def parse_ls_tree(output: str) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    for line in output.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        size_text = parts[3]
        path = parts[4]
        if size_text == "-":
            size = 0
        else:
            try:
                size = int(size_text)
            except ValueError:
                size = 0
        rows.append((path, size))
    return rows


def git_ls_tree(treeish: str) -> str:
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "-l", treeish],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout[-2000:])
    return proc.stdout


def classify_artifacts(paths: list[tuple[str, int]], large_warn_bytes: int = DEFAULT_LARGE_WARN_BYTES) -> list[ArtifactRow]:
    rows: list[ArtifactRow] = []
    for path, size in paths:
        if FORBIDDEN_RE.search(path):
            rows.append(ArtifactRow(path, size, "BLOCKED_FORBIDDEN_TRACKED_ARTIFACT", "forbidden path or extension is tracked in git"))
        elif size > large_warn_bytes:
            rows.append(ArtifactRow(path, size, "WARN_LARGE_TRACKED_FILE", f"tracked file exceeds {large_warn_bytes} bytes"))
    return rows


def decide(rows: list[ArtifactRow]) -> str:
    if any(row.status == "BLOCKED_FORBIDDEN_TRACKED_ARTIFACT" for row in rows):
        return "GIT_ARTIFACT_POLICY_BLOCKED_FORBIDDEN_TRACKED_ARTIFACTS"
    if any(row.status == "WARN_LARGE_TRACKED_FILE" for row in rows):
        return "GIT_ARTIFACT_POLICY_PASS_WITH_SIZE_WARNINGS"
    return "GIT_ARTIFACT_POLICY_PASS"


def write_csv(rows: list[ArtifactRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = ["path", "size_bytes", "status", "reason"]
    with p.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(decision: str, rows: list[ArtifactRow], path: str | Path, treeish: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "decision": decision,
        "treeish": treeish,
        "forbidden_count": sum(1 for row in rows if row.status == "BLOCKED_FORBIDDEN_TRACKED_ARTIFACT"),
        "large_warning_count": sum(1 for row in rows if row.status == "WARN_LARGE_TRACKED_FILE"),
        "rows": [asdict(row) for row in rows],
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(decision: str, rows: list[ArtifactRow], path: str | Path, treeish: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    forbidden = [row for row in rows if row.status == "BLOCKED_FORBIDDEN_TRACKED_ARTIFACT"]
    warnings = [row for row in rows if row.status == "WARN_LARGE_TRACKED_FILE"]
    lines = [
        "# Git Artifact Policy Audit",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Treeish: `{treeish}`",
        f"- Forbidden tracked artifacts: `{len(forbidden)}`",
        f"- Large tracked file warnings: `{len(warnings)}`",
        "",
        "This audit checks tracked Git artifacts only. It does not delete files, copy files, use GPUs, train, rollout, or run DPO.",
    ]
    if forbidden:
        lines.extend(["", "## Forbidden Tracked Artifacts"])
        for row in forbidden:
            lines.append(f"- `{row.path}` ({row.size_bytes} bytes): {row.reason}")
    if warnings:
        lines.extend(["", "## Large Tracked File Warnings"])
        for row in warnings:
            lines.append(f"- `{row.path}` ({row.size_bytes} bytes): {row.reason}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Audit tracked Git artifacts against no-video/no-weight/no-log policy")
    ap.add_argument("--treeish", default="HEAD")
    ap.add_argument("--large_warn_mb", type=float, default=10.0)
    ap.add_argument("--json", default="reports/migration/git_artifact_policy_audit.json")
    ap.add_argument("--csv", default="reports/migration/git_artifact_policy_audit.csv")
    ap.add_argument("--summary", default="reports/migration/git_artifact_policy_audit.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = git_ls_tree(args.treeish)
    rows = classify_artifacts(parse_ls_tree(output), int(args.large_warn_mb * 1024 * 1024))
    decision = decide(rows)
    write_csv(rows, args.csv)
    write_json(decision, rows, args.json, args.treeish)
    write_summary(decision, rows, args.summary, args.treeish)
    print(json.dumps({"decision": decision, "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
