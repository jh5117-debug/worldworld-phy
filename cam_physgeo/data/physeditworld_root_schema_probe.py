from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from cam_physgeo.data.physeditworld_root_candidates import FALSE_POSITIVE_TOKENS, parse_roots, path_signals

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}
MANIFEST_HINTS = ("manifest", "dataset", "split", "metadata", "samples")
METADATA_HINTS = ("metadata", "meta", "scene", "episode", "sample")


@dataclass
class RootSchemaProbe:
    root: str
    status: str
    decision: str
    exists: bool
    is_dir: bool
    files_scanned: int = 0
    dirs_scanned: int = 0
    video_files: int = 0
    action_files: int = 0
    camera_files: int = 0
    intrinsics_files: int = 0
    gravity_files: int = 0
    replay_files: int = 0
    manifest_files: int = 0
    metadata_files: int = 0
    sample_dir_candidates: int = 0
    signals: str = ""
    likely_layouts: str = ""
    evidence: str = ""
    blockers: str = ""
    next_action: str = ""


def is_false_positive_path(path: str | Path) -> list[str]:
    text = str(path).lower()
    return [tok for tok in FALSE_POSITIVE_TOKENS if tok.lower() in text]


def bounded_walk(root: Path, max_depth: int, max_files: int):
    root = root.resolve()
    dirs_scanned = 0
    files_scanned = 0
    for cur, dirs, files in os.walk(root):
        cur_path = Path(cur)
        dirs_scanned += 1
        depth = len(cur_path.relative_to(root).parts)
        if depth >= max_depth:
            dirs[:] = []
        file_paths = [cur_path / name for name in files]
        files_scanned += len(file_paths)
        yield cur_path, file_paths, dirs_scanned, files_scanned
        if files_scanned >= max_files:
            return


def classify_root(root: str, max_depth: int, max_files: int) -> RootSchemaProbe:
    root_path = Path(root)
    exists = root_path.exists()
    is_dir = root_path.is_dir()
    if not root.strip():
        return RootSchemaProbe(
            root="",
            status="BLOCKED",
            decision="PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT",
            exists=False,
            is_dir=False,
            blockers="PHYS_EDITWORLD_ROOTS is empty",
            next_action="export PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h",
        )
    if not exists or not is_dir:
        return RootSchemaProbe(
            root=root,
            status="BLOCKED",
            decision="PHYS_EDITWORLD_SCHEMA_PROBE_ROOT_MISSING",
            exists=exists,
            is_dir=is_dir,
            blockers="root missing or not a directory",
            next_action="mount/provide this root path",
        )

    signals: set[str] = set()
    evidence: list[str] = []
    sample_dirs: set[str] = set()
    counts = {
        "video_files": 0,
        "action_files": 0,
        "camera_files": 0,
        "intrinsics_files": 0,
        "gravity_files": 0,
        "replay_files": 0,
        "manifest_files": 0,
        "metadata_files": 0,
    }
    dirs_scanned = 0
    files_scanned = 0

    for cur, files, dirs_seen, files_seen in bounded_walk(root_path, max_depth=max_depth, max_files=max_files):
        dirs_scanned = dirs_seen
        files_scanned = files_seen
        dir_signals: set[str] = set()
        for file in files:
            low = file.name.lower()
            suffix = file.suffix.lower()
            file_signals = path_signals(str(file))
            signals.update(file_signals)
            dir_signals.update(file_signals)
            if suffix in VIDEO_EXTS:
                counts["video_files"] += 1
            if "action" in file_signals:
                counts["action_files"] += 1
            if "camera" in file_signals:
                counts["camera_files"] += 1
            if "intrinsics" in file_signals:
                counts["intrinsics_files"] += 1
            if "gravity" in file_signals:
                counts["gravity_files"] += 1
            if "replay" in file_signals:
                counts["replay_files"] += 1
            if suffix in {".json", ".jsonl", ".csv", ".tsv", ".parquet"} and any(h in low for h in MANIFEST_HINTS):
                counts["manifest_files"] += 1
                if len(evidence) < 12:
                    evidence.append(str(file))
            if suffix in {".json", ".jsonl", ".yaml", ".yml"} and any(h in low for h in METADATA_HINTS):
                counts["metadata_files"] += 1
            if file_signals and len(evidence) < 12:
                evidence.append(str(file))
        if {"video", "action"}.issubset(dir_signals) and ("camera" in dir_signals or "intrinsics" in dir_signals):
            sample_dirs.add(str(cur))

    layouts: list[str] = []
    if sample_dirs:
        layouts.append("sample_dir")
    if counts["manifest_files"]:
        layouts.append("manifest_driven")
    if counts["replay_files"] or counts["gravity_files"]:
        layouts.append("matched_replay_or_gravity_grouped")
    if counts["video_files"] and not layouts:
        layouts.append("video_only_or_result_folder")

    penalties = is_false_positive_path(root_path)
    blockers: list[str] = []
    if not counts["video_files"]:
        blockers.append("missing_video_or_frames")
    if not counts["action_files"]:
        blockers.append("missing_action_trace")
    if not (counts["camera_files"] or counts["intrinsics_files"]):
        blockers.append("missing_camera_or_intrinsics")
    if not counts["gravity_files"]:
        blockers.append("missing_gravity_label")
    if not counts["replay_files"]:
        blockers.append("missing_replay_group_metadata")
    if penalties:
        blockers.append("false_positive_path_tokens=" + ",".join(penalties))

    has_core = counts["video_files"] and counts["action_files"] and counts["gravity_files"] and (counts["camera_files"] or counts["intrinsics_files"])
    has_replay = has_core and counts["replay_files"]
    if penalties:
        decision = "PHYS_EDITWORLD_SCHEMA_PROBE_REJECT_FALSE_POSITIVE"
        status = "BLOCKED"
        next_action = "do not use this path as selected PhysEditWorld 50h root"
    elif has_replay:
        decision = "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"
        status = "PASS"
        next_action = "run locked handoff sequence and Phase 1 manifest audit"
    elif has_core:
        decision = "PHYS_EDITWORLD_SCHEMA_PROBE_PARTIAL_NEEDS_REPLAY_MAPPING"
        status = "BLOCKED"
        next_action = "provide/identify replay_group metadata or explicit grouping manifest"
    else:
        decision = "PHYS_EDITWORLD_SCHEMA_PROBE_INCOMPLETE"
        status = "BLOCKED"
        next_action = "provide root with action/camera/intrinsics/gravity/replay/video schema"

    return RootSchemaProbe(
        root=root,
        status=status,
        decision=decision,
        exists=exists,
        is_dir=is_dir,
        files_scanned=files_scanned,
        dirs_scanned=dirs_scanned,
        sample_dir_candidates=len(sample_dirs),
        signals=",".join(sorted(signals)),
        likely_layouts=",".join(layouts),
        evidence=";".join(evidence[:12]),
        blockers=";".join(blockers),
        next_action=next_action,
        **counts,
    )


def overall_decision(rows: list[RootSchemaProbe]) -> str:
    if not rows:
        return "PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT"
    if any(row.decision == "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT" for row in rows):
        return "PHYS_EDITWORLD_SCHEMA_PROBE_READY_FOR_MANIFEST_AUDIT"
    if any(row.decision == "PHYS_EDITWORLD_SCHEMA_PROBE_PARTIAL_NEEDS_REPLAY_MAPPING" for row in rows):
        return "PHYS_EDITWORLD_SCHEMA_PROBE_PARTIAL_NEEDS_REPLAY_MAPPING"
    if all(row.decision == "PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT" for row in rows):
        return "PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT"
    if all(row.decision == "PHYS_EDITWORLD_SCHEMA_PROBE_ROOT_MISSING" for row in rows):
        return "PHYS_EDITWORLD_SCHEMA_PROBE_ROOT_MISSING"
    return "PHYS_EDITWORLD_SCHEMA_PROBE_BLOCKED"


def write_csv(path: str | Path, rows: list[RootSchemaProbe]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(RootSchemaProbe.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(path: str | Path, decision: str, rows: list[RootSchemaProbe]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "roots": [asdict(row) for row in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(path: str | Path, decision: str, rows: list[RootSchemaProbe]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# PhysEditWorld Root Schema Probe", "", f"Decision: `{decision}`", "", "## Roots", ""]
    for row in rows:
        loc = f" `{row.root}`" if row.root else ""
        lines.append(f"- `{row.status}` / `{row.decision}`{loc}")
        lines.append(f"  - files/dirs scanned: {row.files_scanned}/{row.dirs_scanned}")
        lines.append(f"  - counts: video={row.video_files}, action={row.action_files}, camera={row.camera_files}, intrinsics={row.intrinsics_files}, gravity={row.gravity_files}, replay={row.replay_files}, manifest={row.manifest_files}")
        lines.append(f"  - layouts: {row.likely_layouts or 'none'}")
        lines.append(f"  - signals: {row.signals or 'none'}")
        if row.evidence:
            lines.append(f"  - evidence: {row.evidence}")
        if row.blockers:
            lines.append(f"  - blockers: {row.blockers}")
        if row.next_action:
            lines.append(f"  - next: {row.next_action}")
    lines.extend([
        "",
        "## Safety",
        "",
        "This probe is CPU/IO only. It scans bounded filenames and shallow layout evidence; it does not decode videos, copy files, delete files, use GPUs, train, rollout, or run DPO.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Probe mounted PhysEditWorld root schema/layout readiness")
    ap.add_argument("--roots", default="", help="Colon/comma-separated roots. Defaults to PHYS_EDITWORLD_ROOTS.")
    ap.add_argument("--max_depth", type=int, default=5)
    ap.add_argument("--max_files_per_root", type=int, default=5000)
    ap.add_argument("--output_csv", default="reports/migration/physeditworld_root_schema_probe.csv")
    ap.add_argument("--output_json", default="reports/migration/physeditworld_root_schema_probe.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_root_schema_probe.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw_roots = args.roots or os.environ.get("PHYS_EDITWORLD_ROOTS", "")
    roots = parse_roots(raw_roots)
    if not roots:
        roots = [""]
    rows = [classify_root(root, args.max_depth, args.max_files_per_root) for root in roots]
    decision = overall_decision(rows)
    write_csv(args.output_csv, rows)
    write_json(args.output_json, decision, rows)
    write_summary(args.summary, decision, rows)
    print(json.dumps({"decision": decision, "roots": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
