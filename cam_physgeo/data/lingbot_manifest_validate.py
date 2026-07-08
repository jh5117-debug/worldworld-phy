from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from cam_physgeo.data.lingbot_condition_schema import validate_condition_dir
from cam_physgeo.utils.io import read_jsonl


REQUIRED_MANIFEST_FIELDS = [
    "sample_id",
    "sample_dir",
    "prefix_path",
    "target_video_path",
    "action_path",
    "poses_path",
    "intrinsics_path",
    "prompt_path",
    "gravity_path",
    "metadata_path",
    "gravity_condition_type",
    "gravity_value",
    "replay_group_id",
    "action_trace_id",
    "camera_policy_id",
    "prediction_start_frame",
    "prefix_frame_count",
    "target_frame_count",
    "action_frame_count",
    "camera_frame_count",
]


def _exists(path_value: Any) -> bool:
    return bool(path_value) and Path(str(path_value)).exists()


def validate_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    pair_id = str(row.get("sample_id") or "")
    errors: list[str] = []
    for key in REQUIRED_MANIFEST_FIELDS:
        if row.get(key) in (None, ""):
            errors.append(f"missing_field:{key}")
    for key in [
        "sample_dir",
        "prefix_path",
        "target_video_path",
        "action_path",
        "poses_path",
        "intrinsics_path",
        "prompt_path",
        "gravity_path",
        "metadata_path",
    ]:
        if row.get(key) not in (None, "") and not _exists(row.get(key)):
            errors.append(f"missing_path:{key}")
    if row.get("gravity_condition_type") != "prompt_only":
        errors.append("invalid:gravity_condition_type")
    sample_dir = row.get("sample_dir")
    if sample_dir and Path(str(sample_dir)).exists():
        errors.extend(f"condition:{err}" for err in validate_condition_dir(sample_dir))
        try:
            meta = json.loads(Path(str(row.get("metadata_path"))).read_text(encoding="utf-8"))
            target_count = len(meta.get("target_frame_indices") or [])
            prefix_count = len(meta.get("prefix_frame_indices") or [])
            action_count = len(meta.get("frame_indices") or [])
            if row.get("target_frame_count") != target_count:
                errors.append("mismatch:target_frame_count")
            if row.get("prefix_frame_count") != prefix_count:
                errors.append("mismatch:prefix_frame_count")
            if row.get("action_frame_count") != action_count:
                errors.append("mismatch:action_frame_count")
            if row.get("camera_frame_count") != action_count:
                errors.append("mismatch:camera_frame_count")
        except Exception as exc:
            errors.append(f"metadata_validate_error:{exc}")
    return {
        "sample_id": pair_id,
        "sample_dir": row.get("sample_dir", ""),
        "status": "PASS" if not errors else "FAIL",
        "error_reason": ";".join(errors),
    }


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = ["sample_id", "sample_dir", "status", "error_reason"]
    with path.open("w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_summary(manifest: str, rows: list[dict[str, Any]], output_json: Path, summary: Path) -> str:
    total = len(rows)
    passed = sum(1 for row in rows if row["status"] == "PASS")
    failed = total - passed
    if total == 0:
        decision = "LINGBOT_MANIFEST_BLOCKED_EMPTY"
    elif failed:
        decision = "LINGBOT_MANIFEST_SCHEMA_FAIL"
    else:
        decision = "LINGBOT_MANIFEST_SCHEMA_PASS"
    payload = {"decision": decision, "manifest": manifest, "total": total, "passed": passed, "failed": failed}
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(
        "# LingBot Converted Manifest Validation\n\n"
        f"Decision: `{decision}`\n\n"
        f"- Manifest: `{manifest}`\n"
        f"- Rows: {total}\n"
        f"- PASS: {passed}\n"
        f"- FAIL: {failed}\n"
        "- Required semantics: prompt-only gravity, explicit prefix path, future-only target path, sampled action/camera paths, intrinsics path, and metadata path.\n",
        encoding="utf-8",
    )
    return decision


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate converted PhysEditWorld LingBot manifest rows")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output_csv", required=True)
    ap.add_argument("--output_json", required=True)
    ap.add_argument("--summary", required=True)
    args = ap.parse_args(argv)
    manifest_rows = list(read_jsonl(args.manifest))
    validation_rows = [validate_manifest_row(row) for row in manifest_rows]
    write_csv(validation_rows, Path(args.output_csv))
    decision = write_summary(args.manifest, validation_rows, Path(args.output_json), Path(args.summary))
    print(json.dumps({"decision": decision, "rows": len(validation_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
