from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

EXPECTED_JSONL = [
    "manifests/physeditworld_50h_all.jsonl",
    "manifests/physeditworld_50h_train.jsonl",
    "manifests/physeditworld_50h_val.jsonl",
    "manifests/physeditworld_50h_test.jsonl",
    "manifests/physeditworld_50h_gravity_ood.jsonl",
    "manifests/physeditworld_50h_scene_ood.jsonl",
    "manifests/physeditworld_50h_action_ood.jsonl",
    "manifests/physeditworld_50h_lingbot_all.jsonl",
    "manifests/physeditworld_50h_lingbot_train.jsonl",
    "manifests/physeditworld_50h_lingbot_val.jsonl",
    "manifests/physeditworld_50h_lingbot_test.jsonl",
    "manifests/physeditworld_dpo_pairs_anchored_v0.jsonl",
]


@dataclass
class ManifestInitRow:
    path: str
    existed_before: bool
    rows: int
    status: str
    action: str
    error_reason: str = ""


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def init_manifest(path: str | Path, dry_run: bool = False) -> ManifestInitRow:
    p = Path(path)
    existed = p.exists()
    if existed and p.is_dir():
        return ManifestInitRow(str(p), True, 0, "FAIL", "none", "path is a directory")
    if not existed:
        if not dry_run:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
        return ManifestInitRow(str(p), False, 0, "CREATED" if not dry_run else "DRY_RUN_CREATE", "create_empty_jsonl")
    rows = count_jsonl(p)
    return ManifestInitRow(str(p), True, rows, "EXISTS", "keep_existing")


def write_csv(rows: list[ManifestInitRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(ManifestInitRow.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[ManifestInitRow], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"decision": decision, "manifests": [asdict(row) for row in rows]}
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[ManifestInitRow], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    created = [row for row in rows if row.status == "CREATED"]
    existing = [row for row in rows if row.status == "EXISTS"]
    failed = [row for row in rows if row.status == "FAIL"]
    lines = [
        "# PhysEditWorld Empty Manifest Initializer",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Created empty manifests: {len(created)}",
        f"- Existing manifests kept: {len(existing)}",
        f"- Failed manifests: {len(failed)}",
        "",
        "## Manifests",
        "",
    ]
    for row in rows:
        lines.append(f"- `{row.path}`: `{row.status}` rows={row.rows} action={row.action}")
        if row.error_reason:
            lines.append(f"  - error: {row.error_reason}")
    lines.extend([
        "",
        "## Safety",
        "",
        "This initializer only creates missing lightweight JSONL manifest placeholders. It does not overwrite non-empty manifests, copy data, delete files, use GPUs, train, rollout, or run DPO.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def decision_for(rows: list[ManifestInitRow]) -> str:
    if any(row.status == "FAIL" for row in rows):
        return "PHYS_EDITWORLD_EMPTY_MANIFEST_INIT_FAILED"
    if any(row.status == "CREATED" for row in rows):
        return "PHYS_EDITWORLD_EMPTY_MANIFESTS_INITIALIZED"
    if any(row.status == "DRY_RUN_CREATE" for row in rows):
        return "PHYS_EDITWORLD_EMPTY_MANIFESTS_DRY_RUN"
    return "PHYS_EDITWORLD_EMPTY_MANIFESTS_ALREADY_PRESENT"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Create missing lightweight PhysEditWorld JSONL manifest placeholders")
    ap.add_argument("--manifests", nargs="*", default=EXPECTED_JSONL)
    ap.add_argument("--report", default="reports/physeditworld_50h/manifest_init/empty_manifest_init.csv")
    ap.add_argument("--json", default="reports/physeditworld_50h/manifest_init/empty_manifest_init.json")
    ap.add_argument("--summary", default="reports/physeditworld_50h/manifest_init/empty_manifest_init.md")
    ap.add_argument("--dry_run", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = [init_manifest(path, dry_run=args.dry_run) for path in args.manifests]
    decision = decision_for(rows)
    write_csv(rows, args.report)
    write_json(rows, decision, args.json)
    write_summary(rows, decision, args.summary)
    print(json.dumps({"decision": decision, "manifests": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
