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
    "physion",
    "physinone",
    "csgo",
    "lingbot_inputs",
    "antigravity.py",
)


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
    t = text.lower()
    signals: set[str] = set()
    if any(ext in t for ext in VIDEO_EXTS):
        signals.add("video")
    if "action" in t:
        signals.add("action")
    if "camera" in t or "pose" in t or "trajectory" in t:
        signals.add("camera")
    if "intrinsic" in t:
        signals.add("intrinsics")
    if "gravity" in t:
        signals.add("gravity")
    if "replay" in t or "group" in t:
        signals.add("replay")
    return signals


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
    signals = path_signals(text)
    fs_signals, examples = scan_existing_root(root_path, max_depth=max_depth, max_files=max_files)
    signals.update(fs_signals)
    penalties = penalty_tokens(text)
    score = 0
    tlow = text.lower()
    if "physedit" in tlow:
        score += 8
    if "gravity" in tlow:
        score += 3
    if "replay" in tlow:
        score += 2
    score += 2 * len(signals)
    if root_path.exists():
        score += 1
    if root_path.is_dir():
        score += 1
    score -= 5 * len(penalties)
    if score >= 12 and "gravity" in signals and "action" in signals and ("camera" in signals or "intrinsics" in signals):
        status = "STRONG_CANDIDATE"
        next_action = f"Set PHYS_EDITWORLD_ROOTS={root} and rerun post-mount continuation."
    elif score >= 4 and not penalties:
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
