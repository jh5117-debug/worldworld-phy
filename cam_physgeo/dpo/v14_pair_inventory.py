
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    rows: list[dict[str, Any]] = []
    if not p.exists():
        return rows
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                keys.append(key)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def nested_get(row: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        cur: Any = row
        ok = True
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return cur
    return default


def pair_id(row: dict[str, Any]) -> str:
    return str(nested_get(row, "pair_id", "id", default=""))


def is_synthetic(row: dict[str, Any]) -> bool:
    value = nested_get(row, "is_synthetic", "synthetic_visible", "loser.synthetic_visible", default="")
    if isinstance(value, bool):
        return value
    text = str(value).lower()
    source = str(nested_get(row, "pair_source", "source", "loser_source", default="")).lower()
    ptype = str(nested_get(row, "pair_type", default="")).lower()
    return text in {"true", "1", "yes"} or "synthetic" in source or "typem" in ptype or "controlled" in source


def is_rollout(row: dict[str, Any]) -> bool:
    value = nested_get(row, "is_rollout_derived", default="")
    if isinstance(value, bool):
        return value
    text = str(value).lower()
    source = str(nested_get(row, "pair_source", "source", "loser_source", default="")).lower()
    ptype = str(nested_get(row, "pair_type", default="")).lower()
    return text in {"true", "1", "yes"} or "rollout" in source or "gt>c" in ptype or "b>c" in ptype


def local_ready(row: dict[str, Any]) -> bool:
    return bool(
        nested_get(row, "affected_region", "affected_mask", "loser.affected_region", "loser.affected_mask", default="")
        or nested_get(row, "affected_time_span", "loser.affected_time_span", default="")
    )


def failure_type(row: dict[str, Any]) -> str:
    return str(nested_get(row, "failure_type", "failure_tag", "main_failure", "loser.failure_type", "loser.main_failure", default="unknown"))


def source_label(row: dict[str, Any]) -> str:
    if is_rollout(row):
        return "rollout_derived"
    if is_synthetic(row):
        return "synthetic_controlled"
    return str(nested_get(row, "pair_source", "source", default="other")) or "other"


def reward_margin(row: dict[str, Any]) -> float:
    for key in ("reward_margin", "margin", "score_margin"):
        try:
            return float(nested_get(row, key, default=""))
        except Exception:
            pass
    try:
        return float(nested_get(row, "winner_reward", "reward_winner", default=0.0)) - float(nested_get(row, "loser_reward", "reward_loser", default=0.0))
    except Exception:
        return 0.0


def reviewed(row: dict[str, Any]) -> bool:
    value = nested_get(row, "codex_visual_audit.reviewed", "reviewed", default="")
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}


def enrich(row: dict[str, Any], subset_hint: str = "") -> dict[str, Any]:
    out = dict(row)
    out.setdefault("pair_id", pair_id(row))
    out["v14_pair_source"] = source_label(row)
    out["v14_is_synthetic"] = is_synthetic(row)
    out["v14_is_rollout_derived"] = is_rollout(row)
    out["v14_failure_type"] = failure_type(row)
    out["v14_reward_margin"] = reward_margin(row)
    out["v14_local_mask_ready"] = local_ready(row)
    out["v14_reviewed"] = reviewed(row)
    if subset_hint:
        out["v14_subset_hint"] = subset_hint
    return out


def unique_by_pair(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        pid = pair_id(row)
        if not pid or pid in seen:
            continue
        seen.add(pid)
        out.append(row)
    return out


def stratified(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[(source_label(row), failure_type(row))].append(row)
    ordered_keys = sorted(buckets, key=lambda k: (k[0], k[1]))
    out: list[dict[str, Any]] = []
    while len(out) < n and ordered_keys:
        progressed = False
        for key in list(ordered_keys):
            bucket = buckets[key]
            if bucket:
                out.append(bucket.pop(0))
                progressed = True
                if len(out) >= n:
                    break
            else:
                ordered_keys.remove(key)
        if not progressed:
            break
    return out


def summarize(name: str, rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    return {
        "subset": name,
        "path": str(path),
        "count": len(rows),
        "source_distribution": json.dumps(dict(Counter(source_label(r) for r in rows)), sort_keys=True),
        "failure_distribution": json.dumps(dict(Counter(failure_type(r) for r in rows)), sort_keys=True),
        "reviewed_count": sum(1 for r in rows if reviewed(r)),
        "local_mask_count": sum(1 for r in rows if local_ready(r)),
        "reward_margin_mean": (sum(reward_margin(r) for r in rows) / len(rows)) if rows else 0.0,
        "reward_margin_min": min((reward_margin(r) for r in rows), default=0.0),
        "reward_margin_max": max((reward_margin(r) for r in rows), default=0.0),
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    out_manifest = Path(args.manifest_dir)
    out_report = Path(args.output_dir)
    out_manifest.mkdir(parents=True, exist_ok=True)
    out_report.mkdir(parents=True, exist_ok=True)
    all500 = unique_by_pair(read_jsonl(args.ready_manifest))
    train = unique_by_pair(read_jsonl(args.train_manifest))
    s_pass = unique_by_pair(read_jsonl(args.s_pass))
    s_fail = unique_by_pair(read_jsonl(args.s_fail))
    rollout_manifest = unique_by_pair(read_jsonl(args.rollout_manifest))
    rollout = rollout_manifest or [r for r in all500 if is_rollout(r)]
    synthetic = [r for r in all500 if is_synthetic(r)]
    local_mask = [r for r in all500 if local_ready(r)]
    strat100 = stratified(all500, min(int(args.stratified_count), len(all500)))
    outputs = {
        "all500": all500,
        "s_pass": s_pass,
        "s_fail": s_fail,
        "rollout_only": rollout,
        "synthetic_controlled": synthetic,
        "stratified100": strat100,
        "local_mask": local_mask,
    }
    summaries: list[dict[str, Any]] = []
    pair_cards: list[dict[str, Any]] = []
    for name, rows in outputs.items():
        enriched = [enrich(r, name) for r in rows]
        path = out_manifest / f"{name}.jsonl"
        write_jsonl(path, enriched)
        summaries.append(summarize(name, enriched, path))
        for r in enriched:
            pair_cards.append({
                "subset": name,
                "pair_id": r.get("pair_id", ""),
                "source": r.get("v14_pair_source", ""),
                "failure_type": r.get("v14_failure_type", ""),
                "reward_margin": r.get("v14_reward_margin", 0.0),
                "reviewed": r.get("v14_reviewed", False),
                "local_mask_ready": r.get("v14_local_mask_ready", False),
                "medium_hard": nested_get(r, "medium_hard", "codex_visual_audit.medium_hard", default=""),
                "winner_video_path": nested_get(r, "winner_video_path", "winner.path", "winner_video", default=""),
                "loser_video_path": nested_get(r, "loser_video_path", "loser.path", "loser_video", default=""),
            })
    write_csv(out_report / "pair_inventory.csv", pair_cards)
    write_csv(out_report / "pair_inventory_summary.csv", summaries)
    md = ["# v14 Pair Inventory Summary", ""]
    for row in summaries:
        md.append(f"- `{row['subset']}`: {row['count']} rows, reviewed={row['reviewed_count']}, local_mask={row['local_mask_count']}, source={row['source_distribution']}")
    (out_report / "pair_inventory_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"manifest_dir": str(out_manifest), "output_dir": str(out_report), "summaries": summaries}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ready_manifest", default="manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl")
    p.add_argument("--train_manifest", default="manifests/dpo_pair_factory_v11_train400_repaired.jsonl")
    p.add_argument("--val_manifest", default="manifests/dpo_pair_factory_v11_val50_repaired.jsonl")
    p.add_argument("--rollout_manifest", default="manifests/dpo_pair_factory_v11_rollout_only.jsonl")
    p.add_argument("--s_pass", default="manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl")
    p.add_argument("--s_fail", default="manifests/dpo_v12b_subsets/s_fail_winner_anchor.jsonl")
    p.add_argument("--manifest_dir", default="manifests/dpo_v14_subsets")
    p.add_argument("--output_dir", default="reports/dpo_utility_calibration_v14")
    p.add_argument("--stratified_count", type=int, default=100)
    print(json.dumps(build(p.parse_args(argv)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
