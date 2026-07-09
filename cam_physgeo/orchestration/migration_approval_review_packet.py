from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

DISALLOWED_MARKERS = (
    "local_assets",
    "contact_sheet",
    "contact-sheets",
    "contact_sheets",
    "/wandb",
    "/outputs/",
    "/output/",
    "failed_checkpoint",
    "failed-checkpoint",
)
WEIGHT_KEYWORDS = (
    "lingbot",
    "wan",
    "fast",
    "vae",
    "t5",
    "tokenizer",
    "scheduler",
    "adapter",
    "lora",
    "checkpoint",
    "model",
    "weight",
)
PHYS_EDIT_KEYWORDS = (
    "physedit",
    "gravity",
    "action",
    "camera",
    "pose",
    "poses",
    "intrinsic",
    "replay",
    "trajectory",
    "video",
    "frames",
)
LOW_VALUE_MARKERS = (
    "/__pycache__/",
    ".pyc",
    "/logs/",
    "/tmp/",
    "/cache/",
    "/.conda_envs/",
    "/code/",
    "/scripts/",
    "/tools/",
    "/legacy/",
    "/external/",
    "/requirements/",
    "videophy",
    "diffueraser_dpo_log",
    "/share/zoneinfo/",
    "/include/",
    ".jpg",
    ".jpeg",
    ".png",
)
MODEL_PAYLOAD_MARKERS = (
    "/checkpoints/",
    "/checkpoint/",
    "/weights/",
    "/weight/",
    "/tokenizer/",
    "/vae/",
    "/adapter/",
    ".safetensors",
    ".bin",
    ".pt",
    ".pth",
    ".ckpt",
)


@dataclass
class ReviewRow:
    row_index: int
    manifest_kind: str
    category: str
    copy_source: str
    destination_subdir: str
    exists: str
    file_type: str
    size_bytes: str
    sha256_status: str
    copy_recommendation: str
    copy_status: str
    current_approved: str
    review_priority: str
    review_score: int
    recommended_review_action: str
    review_reason: str
    safety_note: str


def boolish(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def read_tsv(path: str | Path) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def has_marker(text: str, markers: Iterable[str]) -> str:
    normalized = text.lower().replace("\\", "/")
    for marker in markers:
        if marker in normalized:
            return marker
    return ""


def score_row(row: dict[str, str]) -> tuple[str, int, str, str, str]:
    source = row.get("copy_source", "") or row.get("resolved_target", "") or row.get("manifest_path", "")
    exists = boolish(row.get("exists", ""))
    file_type = row.get("file_type", "")
    copy_status = row.get("copy_status", "")
    manifest_kind = row.get("manifest_kind", "")
    category = row.get("category", "")
    score = 0
    reasons: list[str] = []
    safety_note = "keep approved=false until explicit review"

    marker = has_marker(source, DISALLOWED_MARKERS)
    if marker:
        return (
            "blocked",
            -100,
            "DO_NOT_APPROVE",
            f"disallowed payload marker `{marker}`",
            "blocked by migration artifact policy",
        )
    if not exists or copy_status.startswith("BLOCKED"):
        return (
            "blocked",
            -80,
            "DO_NOT_APPROVE_UNTIL_SOURCE_EXISTS",
            copy_status or "source missing",
            "source must exist on H20 before any approval",
        )
    low_marker = has_marker(source, LOW_VALUE_MARKERS)
    model_payload_marker = has_marker(source, MODEL_PAYLOAD_MARKERS)
    if low_marker and not model_payload_marker:
        return (
            "low",
            0,
            "KEEP_UNAPPROVED_UNLESS_NEEDED",
            f"code/env/example artifact marker `{low_marker}`; prefer git/env export over raw copy",
            "not a primary migration payload; keep approved=false unless explicitly required",
        )
    if manifest_kind == "weights":
        score += 30
        reasons.append("weight/model candidate")
        if model_payload_marker:
            score += 20
            reasons.append(f"model payload marker `{model_payload_marker}`")
        matched = [kw for kw in WEIGHT_KEYWORDS if kw in source.lower()]
        if matched:
            score += min(16, 4 * len(matched))
            reasons.append("weight keywords: " + ",".join(matched[:5]))
    elif manifest_kind == "data":
        score += 10
        reasons.append("data candidate")
        matched = [kw for kw in PHYS_EDIT_KEYWORDS if kw in source.lower()]
        if matched:
            score += min(30, 5 * len(matched))
            reasons.append("PhysEditWorld schema keywords: " + ",".join(matched[:6]))
    if file_type == "file":
        score += 5
        reasons.append("file can be byte-counted/hash-reviewed")
    elif file_type == "dir":
        score += 2
        reasons.append("directory requires recursive human review before approval")
    if row.get("sha256_status") == "SHA256_OK":
        score += 5
        reasons.append("sha256 available")
    if "PENDING" in row.get("sha256_status", ""):
        reasons.append("hash pending because directory/large asset")
    if category:
        reasons.append(f"category={category}")

    if score >= 35:
        priority = "high"
        action = "REVIEW_FOR_APPROVAL"
    elif score >= 15:
        priority = "medium"
        action = "REVIEW_IF_NEEDED"
    else:
        priority = "low"
        action = "KEEP_UNAPPROVED_UNLESS_NEEDED"
    return priority, score, action, "; ".join(reasons) or "no strong migration signal", safety_note


def build_review_rows(copy_plan: str | Path) -> list[ReviewRow]:
    rows: list[ReviewRow] = []
    for idx, row in enumerate(read_tsv(copy_plan), start=1):
        priority, score, action, reason, safety = score_row(row)
        rows.append(ReviewRow(
            row_index=idx,
            manifest_kind=row.get("manifest_kind", ""),
            category=row.get("category", ""),
            copy_source=row.get("copy_source", ""),
            destination_subdir=row.get("destination_subdir", ""),
            exists=row.get("exists", ""),
            file_type=row.get("file_type", ""),
            size_bytes=row.get("size_bytes", ""),
            sha256_status=row.get("sha256_status", ""),
            copy_recommendation=row.get("copy_recommendation", ""),
            copy_status=row.get("copy_status", ""),
            current_approved=row.get("approved", "false"),
            review_priority=priority,
            review_score=score,
            recommended_review_action=action,
            review_reason=reason,
            safety_note=safety,
        ))
    rows.sort(key=lambda r: (r.review_priority == "blocked", -r.review_score, r.manifest_kind, r.copy_source))
    return rows


def summarize(rows: list[ReviewRow], top_n: int) -> dict[str, object]:
    by_priority: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    by_action: dict[str, int] = {}
    present_file_bytes_by_priority: dict[str, int] = {}
    for row in rows:
        by_priority[row.review_priority] = by_priority.get(row.review_priority, 0) + 1
        by_kind[row.manifest_kind] = by_kind.get(row.manifest_kind, 0) + 1
        by_action[row.recommended_review_action] = by_action.get(row.recommended_review_action, 0) + 1
        if row.exists == "True" and row.file_type == "file":
            try:
                size = int(float(row.size_bytes or 0))
            except ValueError:
                size = 0
            present_file_bytes_by_priority[row.review_priority] = present_file_bytes_by_priority.get(row.review_priority, 0) + size
    high_rows = [row for row in rows if row.review_priority == "high"]
    decision = "MIGRATION_APPROVAL_REVIEW_PACKET_READY" if rows else "MIGRATION_APPROVAL_REVIEW_PACKET_EMPTY"
    return {
        "decision": decision,
        "rows": len(rows),
        "top_n": top_n,
        "high_priority_rows": len(high_rows),
        "by_priority": by_priority,
        "by_kind": by_kind,
        "by_action": by_action,
        "present_file_bytes_by_priority": present_file_bytes_by_priority,
        "top_review_sources": [asdict(row) for row in rows[:top_n]],
        "safety": {
            "copied_files": False,
            "deleted_files": False,
            "approved_rows_modified": False,
            "default_approved": False,
            "requires_explicit_human_or_codex_approval": True,
        },
    }


def write_csv(rows: list[ReviewRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(ReviewRow.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(summary: dict[str, object], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(summary: dict[str, object], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Migration Approval Review Packet",
        "",
        f"Decision: `{summary['decision']}`",
        "",
        "## Purpose",
        "",
        "This packet ranks the no-default-approval copy-plan rows so a reviewer can decide which assets should become approved later. It does not approve, copy, delete, or recursively size any payload.",
        "",
        "## Counts",
        "",
        f"- Rows: `{summary['rows']}`",
        f"- High-priority rows: `{summary['high_priority_rows']}`",
        f"- Top rows shown in JSON: `{summary['top_n']}`",
        "",
        "### By Priority",
        "",
    ]
    for key, value in sorted(summary["by_priority"].items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "### By Action", ""])
    for key, value in sorted(summary["by_action"].items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend([
        "",
        "## Reviewer Rule",
        "",
        "Only after NAS/root are visible should a reviewer edit `reports/migration/approved_copy_manifest_template.tsv` and set `approved=true` for a minimal restore payload. Do not approve old outputs, contact sheets, broad `local_assets/`, failed checkpoints, or logs.",
        "",
        "## Top Review Sources",
        "",
    ])
    for row in summary["top_review_sources"][:20]:
        lines.append(f"- `{row['review_priority']}` score={row['review_score']} `{row['manifest_kind']}` `{row['copy_source']}`")
        lines.append(f"  - action: `{row['recommended_review_action']}`; reason: {row['review_reason']}")
    lines.extend([
        "",
        "## Safety",
        "",
        "- Copied files: `False`",
        "- Deleted files: `False`",
        "- Approved rows modified: `False`",
        "- Default approved: `False`",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rank migration copy-plan rows for explicit approval review without approving or copying files.")
    ap.add_argument("--copy_plan", default="reports/migration/approved_copy_manifest_template.tsv")
    ap.add_argument("--output_csv", default="reports/migration/migration_approval_review_packet.csv")
    ap.add_argument("--output_json", default="reports/migration/migration_approval_review_packet.json")
    ap.add_argument("--summary", default="reports/migration/migration_approval_review_packet.md")
    ap.add_argument("--top_n", type=int, default=50)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = build_review_rows(args.copy_plan)
    summary = summarize(rows, args.top_n)
    write_csv(rows, args.output_csv)
    write_json(summary, args.output_json)
    write_markdown(summary, args.summary)
    print(json.dumps({"decision": summary["decision"], "rows": summary["rows"], "high_priority_rows": summary["high_priority_rows"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
