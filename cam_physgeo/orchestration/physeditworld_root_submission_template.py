from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

FIELDS = (
    "candidate_root", "storage_location", "expected_hours", "dataset_version",
    "video_or_frames_glob", "action_trace_glob", "camera_trajectory_or_poses_glob",
    "intrinsics_glob", "gravity_label_or_metadata_glob", "replay_group_or_matched_replay_glob",
    "prompt_or_text_metadata_glob", "split_or_scene_manifest_glob", "notes", "submitter", "review_status",
)
REQUIRED_EVIDENCE = (
    "video_or_frames_glob", "action_trace_glob", "camera_trajectory_or_poses_glob",
    "intrinsics_glob", "gravity_label_or_metadata_glob", "replay_group_or_matched_replay_glob",
)
SAFE_RESUME_COMMANDS = (
    "export PHYS_EDITWORLD_ROOTS=/path/to/selected_physeditworld_50h_root",
    "bash scripts/migration/select_physeditworld_root.sh",
    "bash scripts/migration/probe_physeditworld_root_schema.sh",
    "bash scripts/migration/prepare_physeditworld_root_intake.sh",
    "bash scripts/migration/run_physeditworld_locked_handoff_sequence.sh",
)

@dataclass
class TemplateRow:
    candidate_root: str = "<absolute path to selected PhysEditWorld 50h root>"
    storage_location: str = "<H20 path, PAI path, or NAS path>"
    expected_hours: str = "50"
    dataset_version: str = "<version or export id>"
    video_or_frames_glob: str = "<relative glob for videos or frame directories>"
    action_trace_glob: str = "<relative glob for action traces>"
    camera_trajectory_or_poses_glob: str = "<relative glob for camera trajectory / poses>"
    intrinsics_glob: str = "<relative glob for intrinsics / calibration>"
    gravity_label_or_metadata_glob: str = "<relative glob for explicit gravity labels / metadata>"
    replay_group_or_matched_replay_glob: str = "<relative glob for replay groups / matched replays>"
    prompt_or_text_metadata_glob: str = "<relative glob for prompt/text metadata, if present>"
    split_or_scene_manifest_glob: str = "<relative glob for split, scene, or episode manifest, if present>"
    notes: str = "Do not point this at Physion, PhyInOne, VideoPHY, rollout outputs, contact sheets, or checkpoint folders."
    submitter: str = "<name or owner>"
    review_status: str = "PENDING_EXTERNAL_INPUT"

def default_rows() -> list[TemplateRow]:
    return [TemplateRow()]

def write_tsv(path: str | Path, rows: list[TemplateRow]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(FIELDS), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

def build_summary(rows: list[TemplateRow]) -> dict[str, object]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY",
        "template_rows": len(rows),
        "fields": list(FIELDS),
        "required_evidence": list(REQUIRED_EVIDENCE),
        "review_status_values": ["PENDING_EXTERNAL_INPUT", "READY_FOR_SCHEMA_PROBE", "REJECTED_NOT_PHYS_EDIT_WORLD", "REJECTED_INCOMPLETE_EVIDENCE"],
        "safe_resume_commands": list(SAFE_RESUME_COMMANDS),
        "safety": {"mode": "CPU/IO only", "does_not_scan_roots": True, "does_not_select_root": True, "does_not_approve_copy_rows": True, "does_not_copy_delete_train_or_use_gpu": True},
    }

def write_json(path: str | Path, summary: dict[str, object], rows: list[TemplateRow]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(summary)
    payload["template"] = [asdict(row) for row in rows]
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def write_markdown(path: str | Path, summary: dict[str, object], tsv_path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PhysEditWorld Root Submission Template", "", f"Decision: `{summary['decision']}`", "",
        "## Purpose", "",
        "This template is the external/PAI handoff form for the real PhysEditWorld selected 50h root. It does not select a root and it does not fabricate data. Fill one row per candidate root before rerunning the selected-root/schema gates.",
        "", "## Template File", "", f"- TSV: `{tsv_path}`", "", "## Required Evidence", "",
    ]
    for field in REQUIRED_EVIDENCE:
        lines.append(f"- `{field}`")
    lines.extend([
        "", "A valid first-root candidate must expose action traces, camera trajectory or poses, intrinsics/calibration, explicit gravity labels or metadata, replay-group or matched-replay metadata, and target videos or frames. Prompt/text metadata and split/scene manifests are strongly recommended when present.",
        "", "Do not point this template at Physion, PhyInOne, VideoPHY, Wan/LingBot rollout outputs, contact sheets, local_assets experiment folders, checkpoint folders, or prompt-derived MP4 folders. Those are not the selected PhysEditWorld 50h root.",
        "", "## Review Status Values", "",
    ])
    for value in summary["review_status_values"]:
        lines.append(f"- `{value}`")
    lines.extend(["", "## Safe Resume Commands After Filling", "", "```bash", "cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys"])
    lines.extend(SAFE_RESUME_COMMANDS)
    lines.extend(["```", "", "## Safety", "", "This generator is CPU/IO only. It does not scan candidate roots recursively, copy files, delete files, approve migration rows, use GPUs, train, rollout, evaluate videos, or run DPO."])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Write the external PhysEditWorld selected-root submission template")
    ap.add_argument("--output_tsv", default="reports/migration/physeditworld_root_submission_template.tsv")
    ap.add_argument("--output_json", default="reports/migration/physeditworld_root_submission_template.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_root_submission_template.md")
    return ap

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = default_rows()
    summary = build_summary(rows)
    write_tsv(args.output_tsv, rows)
    write_json(args.output_json, summary, rows)
    write_markdown(args.summary, summary, args.output_tsv)
    print(json.dumps({"decision": summary["decision"], "template_rows": len(rows)}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
