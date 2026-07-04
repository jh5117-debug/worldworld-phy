from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REMOVED_TOO_SUBTLE = {
    "protocol_v4_TypeAplus_022_s4_strong_pass_object_identity_change_local",
    "protocol_v4_TypeAplus_024_s4_strong_pass_partial_freeze",
    "protocol_v4_TypeAplus_028_s4_strong_pass_partial_freeze",
}

REPLACEMENTS = {
    "v11_SYN_0006_02200_collision_orbit_right_64_seed41200_object_identity_color_shift",
    "v11_SYN_0010_02202_collision_orbit_right_64_seed41202_local_scene_patch_drift",
    "v11_SYN_0012_02202_collision_orbit_right_64_seed41202_object_identity_color_shift",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def truth(v: Any) -> bool:
    return v is True or str(v).strip().lower() in {"true", "1", "yes", "y"}


def nested(d: dict[str, Any], *keys: str) -> Any:
    cur: Any = d
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def condition_id(row: dict[str, Any]) -> str:
    return str(nested(row, "condition", "condition_id") or row.get("condition_id") or row.get("pair_id"))


def pair_source(row: dict[str, Any]) -> str:
    if row.get("pair_source"):
        return str(row["pair_source"])
    ptype = row.get("pair_type")
    if ptype == "GT_C" or "rollout" in str(row.get("_manifest_source", "")):
        return "rollout_derived"
    if ptype == "TypeA_plus":
        return "TypeA_plus"
    return "synthetic_controlled"


def failure(row: dict[str, Any]) -> str:
    return str(row.get("failure_tag") or nested(row, "loser", "failure_type") or nested(row, "loser", "corruption_type") or "unknown")


def written_reason(row: dict[str, Any]) -> str:
    return str(nested(row, "codex_visual_audit", "written_reason") or nested(row, "codex_audit", "written_reason") or "")


def load_visual_rows() -> dict[str, dict[str, str]]:
    path = Path("reports/dpo_pair_factory_v11/visual_audit/pair_visual_audit.csv")
    if not path.exists():
        return {}
    with path.open(newline="") as f:
        return {r.get("pair_id", ""): r for r in csv.DictReader(f)}


def normalize_rows(rows: list[dict[str, Any]], visual_rows: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row0 in rows:
        row = dict(row0)
        pid = str(row.get("pair_id", ""))
        vis = visual_rows.get(pid, {})
        cva = dict(row.get("codex_visual_audit") or {})
        if vis:
            cva.setdefault("reviewed", truth(vis.get("reviewed")))
            cva.setdefault("reviewer", vis.get("reviewer") or "codex")
            cva.setdefault("human_visible", truth(vis.get("human_visible")))
            cva.setdefault("medium_hard", truth(vis.get("medium_hard")))
            cva.setdefault("is_dpo_ready", truth(vis.get("is_dpo_ready")))
            cva.setdefault("too_blurry", truth(vis.get("too_blurry")))
            cva.setdefault("too_collapsed", truth(vis.get("too_collapsed")))
            cva.setdefault("too_subtle", truth(vis.get("too_subtle")))
            cva.setdefault("winner_bad", truth(vis.get("winner_bad")))
            cva.setdefault("written_reason", vis.get("written_reason") or "")
            if vis.get("contact_sheet_path") and not row.get("contact_sheet_path"):
                row["contact_sheet_path"] = vis["contact_sheet_path"]
        if cva:
            row["codex_visual_audit"] = cva
        if "medium_hard" not in row and cva.get("medium_hard") is not None:
            row["medium_hard"] = cva.get("medium_hard")
        if vis and not row.get("failure_tag"):
            row["failure_tag"] = vis.get("failure_type") or row.get("failure_tag")
        normalized.append(row)
    return normalized


def validate(rows: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, str]]]:
    errors: list[str] = []
    detail: list[dict[str, str]] = []
    ids = [str(r.get("pair_id", "")) for r in rows]
    counts = Counter(ids)
    for pid, count in counts.items():
        if not pid:
            errors.append("empty_pair_id")
        if count > 1:
            errors.append(f"duplicate_pair_id:{pid}")
    for row in rows:
        pid = str(row.get("pair_id", ""))
        reasons = []
        if pid in REMOVED_TOO_SUBTLE:
            reasons.append("removed_too_subtle_present")
        if not truth(nested(row, "codex_visual_audit", "reviewed")):
            reasons.append("not_reviewed")
        if not written_reason(row):
            reasons.append("missing_written_reason")
        if not truth(row.get("medium_hard", nested(row, "codex_visual_audit", "medium_hard"))):
            reasons.append("not_medium_hard")
        if reasons:
            errors.extend([f"{pid}:{r}" for r in reasons])
            detail.append({"pair_id": pid, "status": "FAIL", "reasons": ";".join(reasons)})
        else:
            detail.append({"pair_id": pid, "status": "PASS", "reasons": ""})
    return errors, detail


def subset_sum_groups(groups: list[tuple[str, list[dict[str, Any]]]], target: int) -> tuple[set[str], int]:
    dp: dict[int, list[str]] = {0: []}
    for gid, rows in groups:
        size = len(rows)
        for total, chosen in list(dp.items())[::-1]:
            nt = total + size
            if nt <= target and nt not in dp:
                dp[nt] = chosen + [gid]
        if target in dp:
            return set(dp[target]), target
    best = max(dp)
    return set(dp[best]), best


def split_no_condition_leak(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_cond[condition_id(row)].append(row)
    groups = sorted(by_cond.items(), key=lambda kv: (len(kv[1]), kv[0]))
    val_ids, val_count = subset_sum_groups(groups, 50)
    remaining = [(gid, rs) for gid, rs in groups if gid not in val_ids]
    test_ids, test_count = subset_sum_groups(remaining, 50)
    train: list[dict[str, Any]] = []
    val: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    for gid, rs in groups:
        if gid in val_ids:
            val.extend(rs)
        elif gid in test_ids:
            test.extend(rs)
        else:
            train.extend(rs)
    train_c, val_c, test_c = set(map(condition_id, train)), set(map(condition_id, val)), set(map(condition_id, test))
    meta = {
        "condition_groups": len(groups),
        "no_condition_leakage": not (train_c & val_c or train_c & test_c or val_c & test_c),
        "exact_counts": len(train) == 400 and len(val) == 50 and len(test) == 50,
        "val_dp_count": val_count,
        "test_dp_count": test_count,
    }
    return train, val, test, meta


def diverse_top50(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    for row in rows:
        if pair_source(row) == "rollout_derived" and row.get("pair_id") not in used:
            selected.append(row); used.add(row["pair_id"])
            if len(selected) == 50:
                return selected
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("pair_id") not in used:
            buckets[(pair_source(row), failure(row))].append(row)
    keys = sorted(buckets)
    while len(selected) < 50 and keys:
        progressed = False
        for key in list(keys):
            bucket = buckets[key]
            if bucket:
                row = bucket.pop(0)
                selected.append(row); used.add(row["pair_id"]); progressed = True
                if len(selected) == 50:
                    return selected
            if not bucket and key in keys:
                keys.remove(key)
        if not progressed:
            break
    return selected


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repaired_manifest", required=True)
    ap.add_argument("--old_manifest", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--canonical_out", required=True)
    ap.add_argument("--train_out", required=True)
    ap.add_argument("--val_out", required=True)
    ap.add_argument("--test_out", required=True)
    ap.add_argument("--top50_out", required=True)
    args = ap.parse_args()
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    repaired = normalize_rows(read_jsonl(Path(args.repaired_manifest)), load_visual_rows())
    old = read_jsonl(Path(args.old_manifest))
    errors, detail = validate(repaired)
    if len(repaired) != 500:
        errors.append(f"repaired_count_not_500:{len(repaired)}")
    repaired_ids = {str(r.get("pair_id")) for r in repaired}
    old_ids = {str(r.get("pair_id")) for r in old}
    if REMOVED_TOO_SUBTLE & repaired_ids:
        errors.append("removed_too_subtle_ids_present")
    if not REPLACEMENTS <= repaired_ids:
        errors.append("replacement_ids_missing:" + ",".join(sorted(REPLACEMENTS - repaired_ids)))
    train, val, test, split_meta = split_no_condition_leak(repaired)
    top50 = diverse_top50(repaired)
    paths = {
        "canonical": Path(args.canonical_out),
        "train": Path(args.train_out),
        "val": Path(args.val_out),
        "test": Path(args.test_out),
        "top50": Path(args.top50_out),
    }
    for path, rows in [(paths["canonical"], repaired), (paths["train"], train), (paths["val"], val), (paths["test"], test), (paths["top50"], top50)]:
        write_jsonl(path, rows)
    with (out / "repaired_pair_diff.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pair_id", "old", "repaired", "kind"])
        w.writeheader()
        for pid in sorted((old_ids | repaired_ids)):
            kind = "unchanged"
            if pid in old_ids and pid not in repaired_ids:
                kind = "removed"
            elif pid in repaired_ids and pid not in old_ids:
                kind = "added"
            w.writerow({"pair_id": pid, "old": pid in old_ids, "repaired": pid in repaired_ids, "kind": kind})
    with (out / "repaired_schema_audit.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pair_id", "status", "reasons"]); w.writeheader(); w.writerows(detail)
    split_rows = []
    for name, rows in [("canonical", repaired), ("train", train), ("val", val), ("test", test), ("top50", top50)]:
        p = paths[name]
        split_rows.append({
            "split": name,
            "count": len(rows),
            "sha256": sha256(p),
            "source_breakdown": dict(Counter(pair_source(r) for r in rows)),
            "pair_type_breakdown": dict(Counter(str(r.get("pair_type", "")) for r in rows)),
            "failure_breakdown": dict(Counter(failure(r) for r in rows)),
            "path": str(p),
        })
    with (out / "repaired_split_summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(split_rows[0].keys())); w.writeheader(); w.writerows(split_rows)
    status = "PASS" if not errors and len(train) == 400 and len(val) == 50 and len(test) == 50 and split_meta["no_condition_leakage"] else "MIXED"
    md = [
        f"Current Status: {status}",
        "",
        "# Repaired Ready500 Freeze Summary",
        "",
        f"- Repaired input count: {len(repaired)}",
        f"- Canonical output: {paths['canonical']}",
        f"- Train/val/test/top50 counts: {len(train)} / {len(val)} / {len(test)} / {len(top50)}",
        f"- Removed too-subtle IDs absent: {not bool(REMOVED_TOO_SUBTLE & repaired_ids)}",
        f"- Replacement IDs present: {REPLACEMENTS <= repaired_ids}",
        f"- No duplicate pair IDs: {len(repaired_ids) == len(repaired)}",
        f"- Condition groups: {split_meta['condition_groups']}",
        f"- No condition leakage: {split_meta['no_condition_leakage']}",
        f"- Exact split counts: {split_meta['exact_counts']}",
        f"- Errors: {errors}",
        "",
        "## Source Breakdown",
        "",
        f"{dict(Counter(pair_source(r) for r in repaired))}",
        "",
        "## Pair Type Breakdown",
        "",
        f"{dict(Counter(str(r.get('pair_type', '')) for r in repaired))}",
    ]
    (out / "repaired_freeze_summary.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"status": status, "errors": errors, "counts": {"canonical": len(repaired), "train": len(train), "val": len(val), "test": len(test), "top50": len(top50)}, "split_meta": split_meta}, indent=2))


if __name__ == "__main__":
    main()
