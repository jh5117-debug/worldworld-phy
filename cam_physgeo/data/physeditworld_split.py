from __future__ import annotations

import argparse
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from cam_physgeo.utils.io import read_jsonl, write_jsonl


def _bucket_id(group_id: str) -> float:
    return int(hashlib.sha1(group_id.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF


def split_by_replay_group(records: Iterable[dict], val_ratio: float = 0.05, test_ratio: float = 0.05) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in records:
        groups[str(row.get("replay_group_id") or row.get("sample_id") or "unknown")].append(row)
    out = {"train": [], "val": [], "test": []}
    for gid, rows in sorted(groups.items()):
        v = _bucket_id(gid)
        split = "test" if v < test_ratio else "val" if v < test_ratio + val_ratio else "train"
        out[split].extend(rows)
    return out


def leakage_rows(splits: dict[str, list[dict]]) -> list[dict]:
    seen: dict[str, set[str]] = defaultdict(set)
    for split, rows in splits.items():
        for row in rows:
            seen[str(row.get("replay_group_id") or row.get("sample_id") or "unknown")].add(split)
    return [
        {"replay_group_id": gid, "splits": ",".join(sorted(names)), "status": "LEAK" if len(names) > 1 else "OK"}
        for gid, names in sorted(seen.items())
    ]


def write_csv(rows: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for row in rows for k in row})
    with path.open("w", encoding="utf-8") as f:
        f.write(",".join(keys) + "\n")
        for row in rows:
            f.write(",".join(str(row.get(k, "")).replace("\n", " ").replace(",", ";") for k in keys) + "\n")


def summarize_distribution(rows: list[dict], key: str) -> list[dict]:
    counts = Counter(str(row.get(key) or "unknown") for row in rows)
    return [{key: name, "count": count} for name, count in sorted(counts.items())]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out_dir", default="manifests")
    ap.add_argument("--prefix", default="physeditworld_50h")
    ap.add_argument("--report_dir", default="reports/physeditworld_50h")
    ap.add_argument("--val-ratio", type=float, default=0.05)
    ap.add_argument("--test-ratio", type=float, default=0.05)
    args = ap.parse_args(argv)
    rows = list(read_jsonl(args.manifest))
    splits = split_by_replay_group(rows, args.val_ratio, args.test_ratio)
    out_dir = Path(args.out_dir)
    write_jsonl(splits["train"], out_dir / f"{args.prefix}_train.jsonl")
    write_jsonl(splits["val"], out_dir / f"{args.prefix}_val.jsonl")
    write_jsonl(splits["test"], out_dir / f"{args.prefix}_test.jsonl")
    # Conservative OOD placeholders: keep explicit manifests, but do not invent heldout semantics.
    write_jsonl([], out_dir / f"{args.prefix}_gravity_ood.jsonl")
    write_jsonl([], out_dir / f"{args.prefix}_scene_ood.jsonl")
    write_jsonl([], out_dir / f"{args.prefix}_action_ood.jsonl")
    report = Path(args.report_dir)
    leaks = leakage_rows(splits)
    write_csv(leaks, report / "replay_group_leakage_check.csv")
    write_csv(summarize_distribution(rows, "gravity_label"), report / "gravity_distribution.csv")
    write_csv(summarize_distribution(rows, "scene_id"), report / "scene_distribution.csv")
    write_csv(summarize_distribution(rows, "action_trace_id"), report / "action_distribution.csv")
    leak_count = sum(1 for row in leaks if row["status"] == "LEAK")
    (report / "split_summary.md").write_text(
        "# PhysEditWorld Split Summary\n\n"
        f"- Total rows: {len(rows)}\n"
        f"- Train: {len(splits['train'])}\n"
        f"- Val: {len(splits['val'])}\n"
        f"- Test: {len(splits['test'])}\n"
        f"- Replay-group leakage rows: {leak_count}\n"
        "- OOD split manifests are placeholders until explicit heldout gravity/scene/action metadata is verified.\n"
    )
    print({"total": len(rows), "train": len(splits["train"]), "val": len(splits["val"]), "test": len(splits["test"]), "leaks": leak_count})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
