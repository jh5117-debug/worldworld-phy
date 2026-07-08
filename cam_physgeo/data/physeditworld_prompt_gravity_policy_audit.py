from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from cam_physgeo.data.prompt_gravity import build_prompt_gravity, validate_prompt


FORBIDDEN_GRAVITY_CONDITION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bgravity[_-]?mlp\b",
        r"\bgravity[_-]?embedding\b",
        r"\bgravity[_-]?emb\b",
        r"\bgravity[_-]?encoder\b",
        r"\bgravity[_-]?project(or|ion)\b",
        r"\bcontinuous[_-]?gravity\b",
    ]
]

DEFAULT_POLICY_FILES = [
    "cam_physgeo/data/prompt_gravity.py",
    "cam_physgeo/data/physeditworld_to_lingbot.py",
    "cam_physgeo/data/lingbot_condition_schema.py",
    "configs/cam_physgeo/physeditworld_50h_warmup_rank32.yaml",
]


@dataclass
class PolicyAuditRow:
    check: str
    status: str
    evidence: str
    detail: str = ""
    next_action: str = ""


def scan_text_for_forbidden(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in FORBIDDEN_GRAVITY_CONDITION_PATTERNS:
        if pattern.search(text):
            hits.append(pattern.pattern)
    return hits


def audit_prompt_samples() -> list[PolicyAuditRow]:
    rows: list[PolicyAuditRow] = []
    samples = [0.25, 1.0, 4.0]
    for value in samples:
        prompt = build_prompt_gravity(value)
        errors = validate_prompt(prompt)
        expected = f"gravity: {value:.1f}g" if float(value).is_integer() else f"gravity: {value:g}g"
        status = "PASS" if not errors and expected in prompt else "FAIL"
        detail = f"value={value}; expected_token={expected}; errors={errors}; prompt={prompt!r}"
        rows.append(PolicyAuditRow("prompt_sample", status, "cam_physgeo/data/prompt_gravity.py", detail, "fix prompt template" if status != "PASS" else ""))
    leak_prompt = "gravity: 1.0g and will land at frame 20"
    leak_errors = validate_prompt(leak_prompt)
    rows.append(PolicyAuditRow(
        "future_leak_detector",
        "PASS" if "future_answer_leak" in leak_errors else "FAIL",
        "cam_physgeo/data/prompt_gravity.py",
        f"errors={leak_errors}",
        "extend FUTURE_LEAK_PATTERNS" if "future_answer_leak" not in leak_errors else "",
    ))
    return rows


def audit_policy_file(path: str | Path) -> list[PolicyAuditRow]:
    p = Path(path)
    if not p.exists():
        return [PolicyAuditRow("policy_file_exists", "MISSING", str(p), "file missing", "restore or regenerate policy file")]
    text = p.read_text(encoding="utf-8", errors="ignore")
    forbidden = scan_text_for_forbidden(text)
    rows = [
        PolicyAuditRow(
            "no_gravity_mlp_or_embedding",
            "PASS" if not forbidden else "FAIL",
            str(p),
            "no forbidden gravity conditioning symbols" if not forbidden else "forbidden_patterns=" + ",".join(forbidden),
            "remove gravity MLP/embedding from first prompt-only version" if forbidden else "",
        )
    ]
    if p.name == "physeditworld_to_lingbot.py":
        status = "PASS" if '"prompt_only"' in text and "gravity_condition_type" in text else "FAIL"
        rows.append(PolicyAuditRow(
            "conversion_writes_prompt_only_metadata",
            status,
            str(p),
            "conversion records gravity_condition_type=prompt_only" if '"prompt_only"' in text else "prompt_only marker missing",
            "ensure conversion metadata and gravity.json use prompt_only" if status != "PASS" else "",
        ))
    if p.name == "physeditworld_50h_warmup_rank32.yaml":
        status = "PASS" if re.search(r"gravity:\s*prompt_only", text) else "FAIL"
        rows.append(PolicyAuditRow(
            "warmup_config_prompt_only",
            status,
            str(p),
            "warmup config keeps gravity: prompt_only",
            "set condition.gravity to prompt_only" if status != "PASS" else "",
        ))
    return rows


def decision_for_rows(rows: list[PolicyAuditRow]) -> str:
    if any(row.status == "FAIL" for row in rows):
        return "PHYS_EDITWORLD_PROMPT_GRAVITY_POLICY_FAIL"
    if any(row.status == "MISSING" for row in rows):
        return "PHYS_EDITWORLD_PROMPT_GRAVITY_POLICY_MISSING"
    return "PHYS_EDITWORLD_PROMPT_GRAVITY_POLICY_PASS"


def write_csv(rows: list[PolicyAuditRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(PolicyAuditRow.__dataclass_fields__.keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[PolicyAuditRow], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "rows": [asdict(row) for row in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[PolicyAuditRow], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    lines = [
        "# PhysEditWorld Prompt-Gravity Policy Audit",
        "",
        f"Decision: `{decision}`",
        "",
        "## Policy",
        "",
        "- First version uses gravity in text prompt only.",
        "- No gravity MLP, embedding, encoder, projector, or continuous gravity conditioning is allowed.",
        "- Prompt must include a `gravity: {value}g` token and must not leak future outcomes.",
        "",
        "## Status Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    lines.extend(["", "## Checks", ""])
    for row in rows:
        lines.append(f"- `{row.check}`: `{row.status}`")
        lines.append(f"  - evidence: `{row.evidence}`")
        if row.detail:
            lines.append(f"  - detail: {row.detail}")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    lines.extend([
        "",
        "## Safety",
        "",
        "This audit is CPU/IO only. It does not use GPUs, train, rollout, copy data, delete files, or inspect local_assets.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Audit prompt-only gravity policy for PhysEditWorld LingBot entry")
    ap.add_argument("--files", nargs="*", default=DEFAULT_POLICY_FILES)
    ap.add_argument("--output_csv", default="reports/physeditworld_50h/prompt_gravity_policy/prompt_gravity_policy_audit.csv")
    ap.add_argument("--output_json", default="reports/physeditworld_50h/prompt_gravity_policy/prompt_gravity_policy_audit.json")
    ap.add_argument("--summary", default="reports/physeditworld_50h/prompt_gravity_policy/prompt_gravity_policy_audit.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = audit_prompt_samples()
    for path in args.files:
        rows.extend(audit_policy_file(path))
    decision = decision_for_rows(rows)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json)
    write_summary(rows, decision, args.summary)
    print(json.dumps({"decision": decision, "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
