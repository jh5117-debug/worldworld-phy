from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
DATA_EXTS = {".json", ".jsonl", ".npy", ".npz", ".pkl", ".csv"}
REQUIRED_SIGNALS = ("video", "action", "camera", "intrinsics", "gravity", "replay")
FALSE_POSITIVE_TOKENS = (
    ".conda_envs",
    "/world_model_phys/PHYS/world_model_phys/",
    "/reports/",
    "/docs/",
    "/tests/",
    "/scripts/",
    "/results/",
    "/checkpoint",
    "checkpoint-",
    "videophy",
    "wan-ti2v",
    "wan22",
    "wan2.2",
    "physical_ti2v",
    "physion",
    "physinone",
    "csgo",
    "lingbot_inputs",
    "antigravity.py",
)
ACTION_FILE_TOKENS = ("action", "actions", "act_trace", "action_trace", "controls", "control_trace")
CAMERA_FILE_TOKENS = ("camera", "camera_trajectory", "trajectory", "poses", "pose", "extrinsics")
INTRINSICS_FILE_TOKENS = ("intrinsic", "intrinsics", "calib", "camera_matrix")
GRAVITY_FILE_TOKENS = ("gravity", "grav", "gravity_label")
REPLAY_FILE_TOKENS = ("replay", "replay_group", "group", "episode_group", "matched_replay")
ACTION_DIR_TOKENS = {"action", "actions", "action_traces", "controls"}
CAMERA_DIR_TOKENS = {"camera", "cameras", "poses", "trajectories", "camera_trajectories"}
INTRINSICS_DIR_TOKENS = {"intrinsics", "calibration", "calib"}
GRAVITY_DIR_TOKENS = {"gravity", "gravities"}
REPLAY_DIR_TOKENS = {"replay", "replays", "replay_groups", "groups"}


@dataclass
class RootCandidate:
    root: str
    status: str
    score: int
    input_rows: int
    exists: bool
    is_dir: bool
    signals: str
    evidence: str
    penalty_reasons: str = ""
    next_action: str = ""


def read_lines(path: str | Path) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    return [line.strip() for line in p.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]


def candidate_root(raw: str) -> str:
    p = Path(raw)
    name = p.name.lower()
    if name in {"action.npy", "actions.npy", "poses.npy", "intrinsics.npy", "camera.npy", "camera.json", "metadata.json"}:
        return str(p.parent)
    if p.suffix.lower() in VIDEO_EXTS | DATA_EXTS:
        return str(p.parent)
    return str(p)


def path_signals(text: str) -> set[str]:
    """Return structural signals from a concrete file path.

    This intentionally avoids using arbitrary natural-language video filenames
    as evidence for action/camera/replay. Generated videos often contain words
    such as "camera captures" or "adventure action" in their prompt-derived
    filename; those are not PhysEditWorld schema signals.
    """
    p = Path(text)
    name = p.name.lower()
    stem = p.stem.lower()
    suffix = p.suffix.lower()
    parent_tokens = {part.lower() for part in p.parts[-4:-1]}
    signals: set[str] = set()
    if suffix in VIDEO_EXTS:
        signals.add("video")
        return signals
    if any(tok in stem for tok in ACTION_FILE_TOKENS) or parent_tokens & ACTION_DIR_TOKENS:
        signals.add("action")
    if any(tok in stem for tok in CAMERA_FILE_TOKENS) or parent_tokens & CAMERA_DIR_TOKENS:
        signals.add("camera")
    if any(tok in stem for tok in INTRINSICS_FILE_TOKENS) or parent_tokens & INTRINSICS_DIR_TOKENS:
        signals.add("intrinsics")
    if any(tok in stem for tok in GRAVITY_FILE_TOKENS) or parent_tokens & GRAVITY_DIR_TOKENS:
        signals.add("gravity")
    if any(tok in stem for tok in REPLAY_FILE_TOKENS) or parent_tokens & REPLAY_DIR_TOKENS:
        signals.add("replay")
    return signals


def root_name_bonus(root: str) -> tuple[int, list[str]]:
    t = root.lower()
    bonuses: list[str] = []
    score = 0
    if "physeditworld" in t or "physedit_world" in t:
        score += 8
        bonuses.append("physeditworld_name")
    elif "physedit" in t:
        score += 5
        bonuses.append("physedit_name")
    if "selected_50h" in t or "50h" in t:
        score += 2
        bonuses.append("selected_50h_name")
    return score, bonuses


def penalty_tokens(text: str) -> list[str]:
    t = text.lower()
    return [tok for tok in FALSE_POSITIVE_TOKENS if tok.lower() in t]


def scan_existing_root(root: Path, max_depth: int, max_files: int) -> tuple[set[str], list[str]]:
    if not root.exists() or not root.is_dir():
        return set(), []
    signals: set[str] = set()
    examples: list[str] = []
    base_depth = len(root.parts)
    seen = 0
    for cur, dirs, files in os.walk(root):
        depth = len(Path(cur).parts) - base_depth
        if depth >= max_depth:
            dirs[:] = []
        for name in files:
            seen += 1
            rel = str(Path(cur, name))
            s = path_signals(rel)
            if s:
                signals.update(s)
                if len(examples) < 8:
                    examples.append(rel)
            if seen >= max_files:
                return signals, examples
    return signals, examples


def score_candidate(root: str, raw_rows: list[str], max_depth: int, max_files: int) -> RootCandidate:
    root_path = Path(root)
    text = "\n".join([root, *raw_rows])
    signals: set[str] = set()
    for raw in raw_rows:
        raw_path = Path(raw)
        if raw == root and raw_path.exists() and raw_path.is_dir():
            continue
        signals.update(path_signals(raw))
    fs_signals, examples = scan_existing_root(root_path, max_depth=max_depth, max_files=max_files)
    signals.update(fs_signals)
    penalties = penalty_tokens(text)
    score, _name_bonuses = root_name_bonus(root)
    score += 3 * len(signals & {"action", "camera", "intrinsics", "gravity", "replay"})
    if "video" in signals:
        score += 1
    if root_path.exists():
        score += 1
    if root_path.is_dir():
        score += 1
    score -= 5 * len(penalties)
    has_core_schema = {"video", "action", "gravity"}.issubset(signals) and ("camera" in signals or "intrinsics" in signals)
    has_matched_replay_schema = has_core_schema and "replay" in signals
    if score >= 16 and has_matched_replay_schema and not penalties:
        status = "STRONG_CANDIDATE"
        next_action = f"Set PHYS_EDITWORLD_ROOTS={root} and rerun post-mount continuation."
    elif score >= 8 and has_core_schema and not penalties:
        status = "WEAK_CANDIDATE"
        next_action = "Inspect manually; root lacks enough action/camera/gravity evidence for automatic selection."
    else:
        status = "REJECT_LIKELY_FALSE_POSITIVE"
        next_action = "Do not use as PhysEditWorld selected 50h root."
    evidence = ";".join(examples[:8])
    return RootCandidate(
        root=root,
        status=status,
        score=score,
        input_rows=len(raw_rows),
        exists=root_path.exists(),
        is_dir=root_path.is_dir(),
        signals=",".join(sorted(signals)),
        evidence=evidence,
        penalty_reasons=",".join(penalties),
        next_action=next_action,
    )


def rank_candidates(lines: list[str], explicit_roots: list[str], max_depth: int = 3, max_files: int = 500) -> list[RootCandidate]:
    grouped: dict[str, list[str]] = {}
    for line in lines:
        grouped.setdefault(candidate_root(line), []).append(line)
    for root in explicit_roots:
        if root:
            grouped.setdefault(root, []).append(root)
    rows = [score_candidate(root, raw, max_depth=max_depth, max_files=max_files) for root, raw in grouped.items()]
    rows.sort(key=lambda r: (r.status != "STRONG_CANDIDATE", -r.score, r.root))
    return rows


def overall_decision(rows: list[RootCandidate]) -> str:
    if any(r.status == "STRONG_CANDIDATE" for r in rows):
        return "PHYS_EDITWORLD_ROOT_CANDIDATES_STRONG"
    if any(r.status == "WEAK_CANDIDATE" for r in rows):
        return "PHYS_EDITWORLD_ROOT_CANDIDATES_WEAK_ONLY"
    if rows:
        return "PHYS_EDITWORLD_ROOT_CANDIDATES_NONE_STRONG"
    return "PHYS_EDITWORLD_ROOT_CANDIDATES_EMPTY"


def write_csv(rows: list[RootCandidate], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(RootCandidate.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[RootCandidate], decision: str, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"decision": decision, "candidates": [asdict(r) for r in rows]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[RootCandidate], decision: str, path: str | Path, top_k: int) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    lines = ["# PhysEditWorld Root Candidate Ranking", "", f"Decision: `{decision}`", "", "## Status Counts", ""]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    lines.extend(["", f"## Top {min(top_k, len(rows))} Candidates", ""])
    for row in rows[:top_k]:
        lines.append(f"- `{row.status}` score={row.score}: `{row.root}`")
        lines.append(f"  - signals: {row.signals or 'none'}")
        if row.penalty_reasons:
            lines.append(f"  - penalties: {row.penalty_reasons}")
        if row.evidence:
            lines.append(f"  - evidence: {row.evidence}")
        lines.append(f"  - next: {row.next_action}")
    lines.extend([
        "",
        "## Safety",
        "",
        "This ranking is CPU/IO only. It reads the bounded candidate list and limited directory samples; it does not train, rollout, copy, delete, or use GPUs.",
    ])
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_roots(raw: str) -> list[str]:
    if not raw.strip():
        return []
    return [part.strip() for part in raw.replace(",", os.pathsep).split(os.pathsep) if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rank candidate PhysEditWorld selected-50h roots")
    ap.add_argument("--candidate_file", default="reports/migration/physeditworld_candidates_raw.txt")
    ap.add_argument("--explicit_roots", default="")
    ap.add_argument("--max_depth", type=int, default=3)
    ap.add_argument("--max_files_per_root", type=int, default=500)
    ap.add_argument("--top_k", type=int, default=25)
    ap.add_argument("--output_csv", default="reports/migration/physeditworld_root_candidates_ranked.csv")
    ap.add_argument("--output_json", default="reports/migration/physeditworld_root_candidates_ranked.json")
    ap.add_argument("--summary", default="reports/migration/physeditworld_root_candidates_ranked.md")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    lines = read_lines(args.candidate_file)
    rows = rank_candidates(lines, parse_roots(args.explicit_roots), max_depth=args.max_depth, max_files=args.max_files_per_root)
    decision = overall_decision(rows)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json)
    write_summary(rows, decision, args.summary, args.top_k)
    print(json.dumps({"decision": decision, "candidates": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
