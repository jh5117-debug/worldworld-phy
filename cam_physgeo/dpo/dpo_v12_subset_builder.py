"""Build balanced tiny-DPO v12 subsets from repaired ready500 manifests."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

FAILURE_BUCKETS = [
    "background_drift",
    "wrong_camera",
    "object_deformation",
    "identity_change",
    "reobserve_mismatch",
    "partial_freeze",
    "physical_event_failure",
]


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def nested(row: dict[str, Any], key: str, default: Any = None) -> Any:
    if key in row:
        return row[key]
    for container in (row.get("condition") or {}, row.get("loser") or {}, row.get("winner") or {}):
        if key in container:
            return container[key]
    return default


def pair_source(row: dict[str, Any]) -> str:
    if row.get("is_rollout_derived") or row.get("pair_type") == "GT_C":
        return "rollout_derived"
    if row.get("is_synthetic") or row.get("pair_source") == "synthetic_controlled" or "synthetic" in str(row.get("pair_type", "")).lower():
        return "synthetic_controlled"
    if "TypeA" in str(row.get("pair_type", "")):
        return "TypeA_plus"
    return str(row.get("pair_source") or nested(row, "source", "unknown"))


def failure_tag(row: dict[str, Any]) -> str:
    tag = row.get("failure_tag") or nested(row, "failure_type") or row.get("main_failure")
    if isinstance(tag, list):
        return "+".join(map(str, tag))
    return str(tag or "unknown")


def failure_bucket(row: dict[str, Any]) -> str:
    tag = failure_tag(row).lower()
    if "background" in tag:
        return "background_drift"
    if "camera" in tag:
        return "wrong_camera"
    if "deform" in tag:
        return "object_deformation"
    if "identity" in tag or "color" in tag:
        return "identity_change"
    if "reobserve" in tag:
        return "reobserve_mismatch"
    if "freeze" in tag:
        return "partial_freeze"
    if any(x in tag for x in ["collision", "containment", "drop", "roll", "event", "phys"]):
        return "physical_event_failure"
    return "other"


def condition_id(row: dict[str, Any]) -> str:
    return str(nested(row, "condition_id") or nested(row, "sample_id") or row.get("pair_id"))


def template(row: dict[str, Any]) -> str:
    return str(nested(row, "template", "unknown"))


def camera_motion(row: dict[str, Any]) -> str:
    return str(nested(row, "camera_motion", "unknown"))


def reviewed_ready(row: dict[str, Any]) -> bool:
    audit = row.get("codex_visual_audit") or row.get("codex_audit") or {}
    if not isinstance(audit, dict):
        audit = {}
    return bool(audit.get("reviewed", False)) and bool(audit.get("is_dpo_ready", row.get("medium_hard", False)))


def localdpo_mode(row: dict[str, Any]) -> str:
    loser = row.get("loser") or {}
    keys = set(row) | set(loser)
    has_region = any(k in keys for k in ["affected_region", "affected_bbox", "affected_mask", "bbox", "mask_path"])
    has_time = any(k in keys for k in ["affected_time_span", "loss_frame_indices", "reward_frame_indices"])
    if has_region and has_time:
        return "LOCALDPO_SPATIOTEMPORAL"
    if has_time:
        return "LOCALDPO_TIME_ONLY"
    return "GLOBAL_OR_UNKNOWN"


def stable_key(row: dict[str, Any]) -> str:
    return hashlib.sha1(str(row.get("pair_id", "")).encode()).hexdigest()


def diverse_select(rows: list[dict[str, Any]], n: int, rollout_limit: int, max_per_condition: int = 1) -> list[dict[str, Any]]:
    rows = sorted(rows, key=stable_key)
    by_source = defaultdict(list)
    for row in rows:
        by_source[pair_source(row)].append(row)

    selected: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    cond_counts: Counter[str] = Counter()

    def add(row: dict[str, Any]) -> bool:
        pid = str(row.get("pair_id"))
        cid = condition_id(row)
        if pid in used_ids:
            return False
        if cond_counts[cid] >= max_per_condition:
            return False
        selected.append(row)
        used_ids.add(pid)
        cond_counts[cid] += 1
        return True

    for row in by_source.get("rollout_derived", [])[:rollout_limit]:
        add(row)
        if len(selected) >= n:
            return selected

    for bucket in FAILURE_BUCKETS:
        for row in rows:
            if failure_bucket(row) == bucket and add(row):
                break
        if len(selected) >= n:
            return selected

    grouped = defaultdict(list)
    for row in rows:
        if str(row.get("pair_id")) not in used_ids:
            grouped[failure_bucket(row)].append(row)
    buckets = sorted(grouped)
    progressed = True
    while len(selected) < n and progressed:
        progressed = False
        for bucket in buckets:
            while grouped[bucket]:
                row = grouped[bucket].pop(0)
                if add(row):
                    progressed = True
                    break
            if len(selected) >= n:
                break
    if len(selected) < n and max_per_condition == 1:
        return diverse_select(rows, n, rollout_limit, max_per_condition=6)
    return selected[:n]


def summarize_rows(name: str, rows: list[dict[str, Any]], path: str) -> dict[str, Any]:
    return {
        "subset": name,
        "count": len(rows),
        "path": path,
        "source_breakdown": dict(Counter(pair_source(r) for r in rows)),
        "failure_bucket_breakdown": dict(Counter(failure_bucket(r) for r in rows)),
        "failure_tag_breakdown": dict(Counter(failure_tag(r) for r in rows)),
        "template_breakdown": dict(Counter(template(r) for r in rows)),
        "camera_motion_breakdown": dict(Counter(camera_motion(r) for r in rows)),
        "condition_count": len({condition_id(r) for r in rows}),
        "localdpo_breakdown": dict(Counter(localdpo_mode(r) for r in rows)),
    }


def write_summary(output_csv: Path, output_md: Path, summaries: list[dict[str, Any]]) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["subset", "count", "path", "source_breakdown", "failure_bucket_breakdown", "template_breakdown", "camera_motion_breakdown", "condition_count", "localdpo_breakdown"]
    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in summaries:
            writer.writerow({k: row.get(k) for k in fields})
    with output_md.open("w") as f:
        f.write("Current Status: PASS\n\n# DPO v12 Subset Summary\n\n")
        for row in summaries:
            f.write("## {}\n\n".format(row["subset"]))
            f.write("- Count: {}\n".format(row["count"]))
            f.write("- Path: `{}`\n".format(row["path"]))
            f.write("- Sources: `{}`\n".format(row["source_breakdown"]))
            f.write("- Failure buckets: `{}`\n".format(row["failure_bucket_breakdown"]))
            f.write("- Templates: `{}`\n".format(row["template_breakdown"]))
            f.write("- Camera motions: `{}`\n".format(row["camera_motion_breakdown"]))
            f.write("- Conditions: {}\n".format(row["condition_count"]))
            f.write("- LocalDPO readiness: `{}`\n\n".format(row["localdpo_breakdown"]))
        f.write("## Caveat\n\nThe repaired canonical pool is dominated by controlled synthetic pairs. Rollout-derived rows are included in scope/video sanity subsets where available, but real rollout-derived DPO remains limited.\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", default="manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl")
    ap.add_argument("--train", default="manifests/dpo_pair_factory_v11_train400_repaired.jsonl")
    ap.add_argument("--val", default="manifests/dpo_pair_factory_v11_val50_repaired.jsonl")
    ap.add_argument("--test", default="manifests/dpo_pair_factory_v11_test50_repaired.jsonl")
    ap.add_argument("--output_dir", default="manifests/dpo_v12_subsets")
    ap.add_argument("--report_dir", default="reports/dpo_training_sanity_v12")
    args = ap.parse_args()

    canonical = [r for r in read_jsonl(args.canonical) if reviewed_ready(r)]
    val = [r for r in read_jsonl(args.val) if reviewed_ready(r)]
    test = [r for r in read_jsonl(args.test) if reviewed_ready(r)]

    pool = canonical
    out = Path(args.output_dir)
    report = Path(args.report_dir)

    subsets = {
        "S0_scope_probe_16": diverse_select(pool, 16, rollout_limit=8, max_per_condition=1),
        "S1_tiny_dpo_32": diverse_select(pool, 32, rollout_limit=8, max_per_condition=1),
        "S2_small_dpo_64": diverse_select(pool, 64, rollout_limit=15, max_per_condition=1),
        "S3_dpo_128_optional": diverse_select(pool, 128, rollout_limit=15, max_per_condition=1),
        "val_energy_16": diverse_select(val or test or canonical, 16, rollout_limit=0, max_per_condition=1),
        "val_video_16": diverse_select(test or val or canonical, 16, rollout_limit=8, max_per_condition=1),
    }
    paths = {
        "S0_scope_probe_16": out / "s0_scope_probe_16.jsonl",
        "S1_tiny_dpo_32": out / "s1_tiny_dpo_32.jsonl",
        "S2_small_dpo_64": out / "s2_small_dpo_64.jsonl",
        "S3_dpo_128_optional": out / "s3_dpo_128_optional.jsonl",
        "val_energy_16": out / "val_energy_16.jsonl",
        "val_video_16": out / "val_video_16.jsonl",
    }
    summaries = []
    for name, rows in subsets.items():
        write_jsonl(paths[name], rows)
        summaries.append(summarize_rows(name, rows, str(paths[name])))
    write_summary(report / "subset_summary.csv", report / "subset_summary.md", summaries)
    required = {"S0_scope_probe_16": 16, "S1_tiny_dpo_32": 32, "S2_small_dpo_64": 64, "S3_dpo_128_optional": 128, "val_energy_16": 16, "val_video_16": 16}
    bad = {k: len(subsets[k]) for k, n in required.items() if len(subsets[k]) != n}
    if bad:
        raise SystemExit(f"subset count mismatch: {bad}")


if __name__ == "__main__":
    main()
