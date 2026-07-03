from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

TRUE_VALUES = {"1", "true", "yes", "y", "pass", "passed"}
FALSE_VALUES = {"0", "false", "no", "n", "fail", "failed"}


def boolish(value: Any, default: Optional[bool] = None) -> Optional[bool]:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if not text:
        return default
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    return default


def as_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or str(value).startswith("BLOCKED"):
            return default
        return float(value)
    except Exception:
        return default


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def resolve(repo: Path, value: Any) -> Optional[Path]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.startswith("BLOCKED"):
        return None
    path = Path(text)
    return path if path.is_absolute() else repo / path


def path_exists(repo: Path, value: Any) -> bool:
    path = resolve(repo, value)
    return bool(path and path.exists() and path.stat().st_size > 0)


def video_decodable(repo: Path, value: Any) -> bool:
    path = resolve(repo, value)
    if not path or not path.exists() or path.stat().st_size <= 0:
        return False
    if cv2 is None:
        return True
    cap = cv2.VideoCapture(str(path))
    ok, frame = cap.read() if cap.isOpened() else (False, None)
    cap.release()
    return bool(ok and frame is not None)


def read_csv(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="") as f:
        return {row.get("pair_id", ""): row for row in csv.DictReader(f)}


def rel_or_raw(repo: Path, value: Any) -> str:
    path = resolve(repo, value)
    if path is None:
        return ""
    try:
        return str(path.relative_to(repo))
    except Exception:
        return str(path)


def infer_source(pair: Dict[str, Any], synthetic_ids: set[str], existing_ids: set[str]) -> Tuple[str, bool, bool, bool]:
    pid = pair.get("pair_id", "")
    ptype = pair.get("pair_type", "")
    loser = pair.get("loser") or {}
    source = loser.get("source", "")
    is_synth = pid in synthetic_ids or "synthetic" in str(ptype).lower() or "synthetic" in str(source).lower() or str(pid).startswith("v10_TypeM")
    is_rollout = ptype in {"GT_C", "B_C", "M0_C"} or "rollout" in str(source).lower()
    is_typea = "TypeA" in str(ptype) or str(pid).startswith(("protocol_v4_TypeAplus", "protocol_v1_A", "protocol_v2_A", "protocol_v3_A"))
    is_controlled = is_synth or is_typea or "corruption" in str(source).lower() or "controlled" in str(source).lower()
    pair_source = "rollout_derived" if is_rollout else "synthetic_controlled" if is_synth else "typeA_plus_controlled" if is_typea else "unknown"
    return pair_source, is_synth, is_rollout, is_controlled


def pair_card(repo: Path, pair: Dict[str, Any], synthetic_ids: set[str], existing_ids: set[str], synth_csv: Dict[str, Dict[str, str]], ppt_ids: set[str]) -> Dict[str, Any]:
    pid = pair.get("pair_id", "")
    cond = pair.get("condition") or {}
    winner = pair.get("winner") or {}
    loser = pair.get("loser") or {}
    audit = pair.get("codex_audit") or {}
    metrics = pair.get("traditional_metrics") or {}
    csvrow = synth_csv.get(pid, {})
    pair_source, is_synth, is_rollout, is_controlled = infer_source(pair, synthetic_ids, existing_ids)
    ptype = pair.get("pair_type", "")
    corruption = loser.get("corruption_type") or loser.get("failure_type") or csvrow.get("corruption_type") or csvrow.get("failure_type") or ""
    main_failure = corruption or csvrow.get("main_failure", "")
    template = cond.get("template") or csvrow.get("template", "")
    camera_motion = cond.get("camera_motion") or csvrow.get("camera_motion", "")
    reward_margin = as_float(pair.get("reward_margin"), as_float(csvrow.get("reward_margin"), None))
    winner_reward = as_float((winner.get("reward_vector") or {}).get("R_total"), as_float(csvrow.get("reward_winner"), as_float(csvrow.get("winner_reward"), 1.0)))
    loser_reward = as_float((loser.get("reward_vector") or {}).get("R_total"), as_float(csvrow.get("reward_loser"), as_float(csvrow.get("loser_reward"), None)))
    prefix = cond.get("prefix_video_path") or csvrow.get("prefix_video", "")
    win_video = winner.get("future_video_path") or winner.get("full_video_path") or csvrow.get("winner_video", "")
    lose_video = loser.get("future_video_path") or loser.get("full_video_path") or csvrow.get("loser_video", "")
    prefix_ok = path_exists(repo, prefix)
    winner_ok = path_exists(repo, win_video)
    loser_ok = path_exists(repo, lose_video)
    prefix_dec = video_decodable(repo, prefix) if prefix_ok else False
    winner_dec = video_decodable(repo, win_video) if winner_ok else False
    loser_dec = video_decodable(repo, lose_video) if loser_ok else False
    existing_audit = pair.get("pair_factory_v10_existing_audit") or {}
    reviewed = boolish(
        audit.get("reviewed"),
        boolish(
            audit.get("valid_preference"),
            boolish(existing_audit.get("reviewed"), False),
        ),
    )
    written_reason = audit.get("written_reason") or csvrow.get("written_reason") or ""
    medium_hard = boolish(pair.get("medium_hard"), True)
    too_subtle = boolish(audit.get("too_subtle"), False)
    too_blurry = boolish(audit.get("too_blurry"), False)
    too_collapsed = boolish(audit.get("loser_collapsed"), boolish(audit.get("too_collapsed"), False))
    too_similar = boolish(audit.get("too_similar_to_winner"), boolish(audit.get("too_similar_to_gt"), False))
    winner_bad = boolish(audit.get("winner_bad"), False)
    same_prefix = boolish(pair.get("same_prefix"), True)
    same_prompt = boolish(pair.get("same_prompt"), True)
    same_poses = boolish(pair.get("same_poses"), True)
    same_intrinsics = boolish(pair.get("same_intrinsics"), True)
    prefix_len = int(cond.get("prefix_len") or 5)
    prediction_start = int(cond.get("prediction_start_frame") or 5)
    affected_region = loser.get("affected_region") or csvrow.get("affected_region") or ""
    affected_time = loser.get("affected_time_span") or csvrow.get("affected_time_span") or ""
    affected_mask = loser.get("affected_mask") or pair.get("affected_mask") or ""
    loss_frames = pair.get("loss_frame_indices") or []
    reward_frames = pair.get("reward_frame_indices") or []
    reasons: List[str] = []
    if not (prefix_ok and winner_ok and loser_ok):
        reasons.append("missing_video")
    if not (prefix_dec and winner_dec and loser_dec):
        reasons.append("undecodable_video")
    if prefix_len != 5 or prediction_start != 5:
        reasons.append("wrong_prefix_schema")
    if not (same_prefix and same_prompt and same_poses and same_intrinsics):
        reasons.append("not_same_condition")
    if not reviewed:
        reasons.append("not_reviewed")
    if len(str(written_reason).strip()) < 12:
        reasons.append("missing_written_reason")
    if not medium_hard:
        reasons.append("not_medium_hard")
    if too_subtle:
        reasons.append("too_subtle")
    if too_blurry:
        reasons.append("too_blurry")
    if too_collapsed:
        reasons.append("too_collapsed")
    if too_similar:
        reasons.append("too_similar")
    if winner_bad:
        reasons.append("winner_bad")
    if reward_margin is None or reward_margin <= 0:
        if is_synth and loser.get("severity"):
            reasons.append("reward_margin_repaired_by_synthetic_severity")
        else:
            reasons.append("nonpositive_reward_margin")
    if not main_failure:
        reasons.append("unclear_failure")
    hard_reasons = [r for r in reasons if r != "reward_margin_repaired_by_synthetic_severity"]
    if hard_reasons:
        status = "rejected_missing_video" if any("video" in r for r in hard_reasons) else "rejected_visual" if any(r in hard_reasons for r in ["too_subtle", "too_blurry", "too_collapsed", "too_similar", "winner_bad"]) else "rejected_schema"
        trainable = False
        diagnostic = False
    else:
        status = "ready_strict"
        trainable = True
        diagnostic = False
    localdpo_ready = bool(affected_region)
    time_mask_ready = bool(affected_time)
    return {
        "pair_id": pid,
        "pair_type": ptype,
        "pair_source": pair_source,
        "source_protocol": pair.get("protocol_version", ""),
        "is_synthetic": is_synth,
        "is_rollout_derived": is_rollout,
        "is_controlled_corruption": is_controlled,
        "condition_id": cond.get("condition_id") or cond.get("sample_id") or csvrow.get("condition_id", ""),
        "sample_id": cond.get("sample_id") or csvrow.get("sample_id", ""),
        "template": template,
        "camera_motion": camera_motion,
        "prefix_len": prefix_len,
        "prediction_start_frame": prediction_start,
        "prefix_video_path": rel_or_raw(repo, prefix),
        "winner_video_path": rel_or_raw(repo, win_video),
        "loser_video_path": rel_or_raw(repo, lose_video),
        "prefix_exists": prefix_ok,
        "winner_exists": winner_ok,
        "loser_exists": loser_ok,
        "prefix_decodable": prefix_dec,
        "winner_decodable": winner_dec,
        "loser_decodable": loser_dec,
        "winner_source": winner.get("source", ""),
        "loser_source": loser.get("source", ""),
        "winner_reward": winner_reward,
        "loser_reward": loser_reward,
        "reward_margin": reward_margin,
        "winner_quality": metrics.get("R_quality") or csvrow.get("winner_quality", ""),
        "loser_quality": metrics.get("R_quality_loser") or csvrow.get("loser_quality", ""),
        "main_failure": main_failure,
        "failure_tags": main_failure,
        "affected_region": json.dumps(affected_region, sort_keys=True) if isinstance(affected_region, dict) else str(affected_region),
        "affected_time_span": json.dumps(affected_time) if isinstance(affected_time, list) else str(affected_time),
        "affected_mask": str(affected_mask),
        "corruption_type": corruption,
        "codex_reviewed": reviewed,
        "written_reason": written_reason,
        "medium_hard": medium_hard,
        "too_subtle": too_subtle,
        "too_blurry": too_blurry,
        "too_collapsed": too_collapsed,
        "too_similar": too_similar,
        "winner_bad": winner_bad,
        "same_prefix": same_prefix,
        "same_prompt": same_prompt,
        "same_poses": same_poses,
        "same_intrinsics": same_intrinsics,
        "loss_frame_indices_count": len(loss_frames),
        "reward_frame_indices_count": len(reward_frames),
        "localdpo_ready": localdpo_ready,
        "time_mask_ready": time_mask_ready,
        "diagnostic_only": diagnostic,
        "trainable": trainable,
        "in_ppt_subset": pid in ppt_ids,
        "status": status,
        "decision_reason": ";".join(reasons) if reasons else "ACCEPT_STRICT",
        "repair_method": "source inferred from v10 manifests/csv" if status == "ready_strict" else "",
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def breakdown(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    out = []
    for field in fields:
        for key, count in Counter(str(r.get(field, "")) for r in rows).most_common():
            out.append({"field": field, "value": key, "count": count})
    write_csv(path, out)


def subset_pairs(pairs: List[Dict[str, Any]], cards: List[Dict[str, Any]], kind: str, limit: Optional[int] = None, ppt_ids: Optional[set[str]] = None) -> List[Dict[str, Any]]:
    by_id = {p["pair_id"]: p for p in pairs}
    ready = [c for c in cards if c["status"] == "ready_strict"]
    if kind == "all":
        ids = [c["pair_id"] for c in ready]
    elif kind == "rollout":
        ids = [c["pair_id"] for c in ready if c["is_rollout_derived"]]
    elif kind == "synthetic":
        ids = [c["pair_id"] for c in ready if c["is_controlled_corruption"] and not c["is_rollout_derived"]]
    elif kind == "ppt":
        ids = [c["pair_id"] for c in ready if ppt_ids and c["pair_id"] in ppt_ids]
    elif kind == "top20":
        rollout = [c for c in ready if c["is_rollout_derived"]]
        typea = [c for c in ready if c["pair_type"] == "TypeA_plus"]
        synth = [c for c in ready if c["is_synthetic"]]
        ids = [c["pair_id"] for c in rollout[:5] + typea[:3]]
        seen_cond = {c["condition_id"] for c in rollout[:5] + typea[:3]}
        per_failure = Counter()
        for c in synth:
            if len(ids) >= 20:
                break
            if c["condition_id"] in seen_cond:
                continue
            if per_failure[c["main_failure"]] >= 3:
                continue
            ids.append(c["pair_id"]); seen_cond.add(c["condition_id"]); per_failure[c["main_failure"]] += 1
        for c in synth:
            if len(ids) >= 20:
                break
            if c["pair_id"] not in ids:
                ids.append(c["pair_id"])
    elif kind == "top50":
        rollout = [c for c in ready if c["is_rollout_derived"]]
        typea = [c for c in ready if c["pair_type"] == "TypeA_plus"]
        synth = [c for c in ready if c["is_synthetic"]]
        ids = [c["pair_id"] for c in rollout + typea]
        seen_cond = {c["condition_id"] for c in rollout + typea}
        per_failure = Counter()
        for c in synth:
            if len(ids) >= 50:
                break
            if c["condition_id"] in seen_cond:
                continue
            if per_failure[c["main_failure"]] >= 8:
                continue
            ids.append(c["pair_id"]); seen_cond.add(c["condition_id"]); per_failure[c["main_failure"]] += 1
        for c in synth:
            if len(ids) >= 50:
                break
            if c["pair_id"] not in ids:
                ids.append(c["pair_id"])
    else:
        ids = []
    if limit is not None:
        ids = ids[:limit]
    return [by_id[i] for i in ids if i in by_id]


def write_subset_summary(path_csv: Path, path_md: Path, subsets: Dict[str, List[Dict[str, Any]]], cards_by_id: Dict[str, Dict[str, Any]]) -> None:
    rows = []
    for name, pairs in subsets.items():
        cards = [cards_by_id[p["pair_id"]] for p in pairs]
        rows.append({
            "subset": name,
            "count": len(pairs),
            "templates": json.dumps(dict(Counter(c["template"] for c in cards)), sort_keys=True),
            "failure_tags": json.dumps(dict(Counter(c["main_failure"] for c in cards)), sort_keys=True),
            "pair_types": json.dumps(dict(Counter(c["pair_type"] for c in cards)), sort_keys=True),
            "affected_region_count": sum(1 for c in cards if c["affected_region"]),
            "affected_mask_count": sum(1 for c in cards if c["affected_mask"]),
            "localdpo_ready_count": sum(1 for c in cards if c["localdpo_ready"]),
            "time_mask_ready_count": sum(1 for c in cards if c["time_mask_ready"]),
            "diagnostic_only_count": sum(1 for c in cards if c["diagnostic_only"]),
        })
    write_csv(path_csv, rows)
    lines = ["Current Status:", "SUBSETS_READY", "", "# DPO Pair Factory v10b Subset Summary", ""]
    for row in rows:
        lines.extend([
            "## " + row["subset"],
            "- Count: " + str(row["count"]),
            "- Templates: `" + row["templates"] + "`",
            "- Failure tags: `" + row["failure_tags"] + "`",
            "- Pair types: `" + row["pair_types"] + "`",
            "- LocalDPO-ready: " + str(row["localdpo_ready_count"]),
            "- Time-mask ready: " + str(row["time_mask_ready_count"]),
            "- Diagnostic-only: " + str(row["diagnostic_only_count"]),
            "",
        ])
    path_md.write_text("\n".join(lines))


def run_full(args: argparse.Namespace) -> None:
    repo = Path(".").resolve()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    pairs = load_jsonl(Path(args.ready_manifest))
    synthetic_ids = {p.get("pair_id", "") for p in load_jsonl(Path(args.synthetic_manifest))}
    existing_ids = {p.get("pair_id", "") for p in load_jsonl(Path(args.existing_manifest))}
    synth_csv = read_csv(repo / "reports/dpo_pair_factory_v10/synthetic_visible_negatives/synthetic_pair_audit.csv")
    ppt_csv = read_csv(repo / "reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_selected_pairs.csv")
    ppt_ids = set(ppt_csv.keys())
    cards = [pair_card(repo, p, synthetic_ids, existing_ids, synth_csv, ppt_ids) for p in pairs]
    write_csv(out / "pair_card.csv", cards)
    write_jsonl(out / "pair_card.jsonl", cards)
    write_csv(out / "pair_schema_audit.csv", cards)
    breakdown(out / "pair_source_breakdown.csv", cards, ["pair_source", "pair_type", "is_synthetic", "is_rollout_derived"])
    breakdown(out / "pair_failure_breakdown.csv", cards, ["main_failure", "template", "camera_motion"])
    breakdown(out / "pair_quality_breakdown.csv", cards, ["status", "trainable", "diagnostic_only", "localdpo_ready", "time_mask_ready"])
    cards_by_id = {c["pair_id"]: c for c in cards}
    subsets = {
        "all_ready": subset_pairs(pairs, cards, "all"),
        "rollout_only": subset_pairs(pairs, cards, "rollout"),
        "synthetic_controlled": subset_pairs(pairs, cards, "synthetic"),
        "top50_balanced": subset_pairs(pairs, cards, "top50", 50),
        "top20_demo": subset_pairs(pairs, cards, "top20", 20),
        "ppt_subset": subset_pairs(pairs, cards, "ppt", ppt_ids=ppt_ids),
    }
    manifest_map = {
        "all_ready": "manifests/dpo_pair_factory_v10b_ready_all.jsonl",
        "rollout_only": "manifests/dpo_pair_factory_v10b_ready_rollout_only.jsonl",
        "synthetic_controlled": "manifests/dpo_pair_factory_v10b_ready_synthetic_controlled.jsonl",
        "top50_balanced": "manifests/dpo_pair_factory_v10b_top50_balanced.jsonl",
        "top20_demo": "manifests/dpo_pair_factory_v10b_top20_demo.jsonl",
        "ppt_subset": "manifests/dpo_pair_factory_v10b_ppt_subset.jsonl",
    }
    for name, path in manifest_map.items():
        write_jsonl(Path(path), subsets[name])
    write_subset_summary(out / "subset_summary.csv", out / "subset_summary.md", subsets, cards_by_id)
    counts = Counter(c["status"] for c in cards)
    source_counts = Counter(c["pair_source"] for c in cards)
    trainable = sum(1 for c in cards if c["trainable"])
    diagnostic = sum(1 for c in cards if c["diagnostic_only"])
    rejected = len(cards) - trainable - diagnostic
    summary = {
        "status": "PAIR_FACTORY_V10B_READY_FREEZE" if trainable >= 50 else "PAIR_FACTORY_V10B_INSUFFICIENT",
        "total_pairs": len(cards),
        "strict_ready_count": trainable,
        "trainable_count": trainable,
        "diagnostic_only_count": diagnostic,
        "rejected_count": rejected,
        "status_counts": dict(counts),
        "source_counts": dict(source_counts),
        "subset_counts": {k: len(v) for k, v in subsets.items()},
    }
    (out / "pair_audit_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (out / "pair_audit_summary.md").write_text("\n".join([
        "Current Status:", summary["status"], "", "# DPO Pair Factory v10b Pair Audit Summary", "",
        "- Total pairs: {}".format(summary["total_pairs"]),
        "- Strict ready / trainable: {}".format(summary["trainable_count"]),
        "- Diagnostic-only: {}".format(summary["diagnostic_only_count"]),
        "- Rejected: {}".format(summary["rejected_count"]),
        "- Source counts: `{}`".format(json.dumps(summary["source_counts"], sort_keys=True)),
        "- Subset counts: `{}`".format(json.dumps(summary["subset_counts"], sort_keys=True)),
        "- Caveat: synthetic controlled pairs remain labeled separately from real rollout-derived pairs.",
    ]) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


def quality_mode(args: argparse.Namespace, mode: str) -> None:
    repo = Path(".").resolve()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ready_manifest = args.ready_manifest if args.ready_manifest else "manifests/dpo_pair_factory_v10_ready_pairs.jsonl"
    synthetic_manifest = args.synthetic_manifest if args.synthetic_manifest else "manifests/dpo_pair_factory_v10_synthetic_visible_pairs.jsonl"
    pairs = load_jsonl(Path(synthetic_manifest if mode == "synthetic_quality" else ready_manifest))
    all_synth_ids = {p.get("pair_id", "") for p in load_jsonl(Path(synthetic_manifest))}
    all_existing_ids = {p.get("pair_id", "") for p in load_jsonl(Path("manifests/dpo_pair_factory_v10_existing_ready_pairs.jsonl"))}
    synth_csv = read_csv(repo / "reports/dpo_pair_factory_v10/synthetic_visible_negatives/synthetic_pair_audit.csv")
    ppt_ids = set(read_csv(repo / "reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_selected_pairs.csv").keys())
    cards = [pair_card(repo, p, all_synth_ids, all_existing_ids, synth_csv, ppt_ids) for p in pairs]
    if mode == "rollout_quality":
        cards = [c for c in cards if c["is_rollout_derived"]]
        pairs = [p for p in pairs if p.get("pair_id") in {c["pair_id"] for c in cards}]
    else:
        cards = [c for c in cards if c["is_synthetic"]]
        pairs = [p for p in pairs if p.get("pair_id") in {c["pair_id"] for c in cards}]
    train_ids = {c["pair_id"] for c in cards if c["trainable"]}
    diag_ids = {c["pair_id"] for c in cards if c["diagnostic_only"]}
    train_pairs = [p for p in pairs if p.get("pair_id") in train_ids]
    diag_pairs = [p for p in pairs if p.get("pair_id") in diag_ids]
    name = "synthetic" if mode == "synthetic_quality" else "rollout"
    write_csv(out / (name + "_quality_audit.csv"), cards)
    write_jsonl(Path("manifests/dpo_pair_factory_v10b_" + name + "_trainable.jsonl"), train_pairs)
    write_jsonl(Path("manifests/dpo_pair_factory_v10b_" + name + "_diagnostic_only.jsonl"), diag_pairs)
    summary = {
        "status": name.upper() + "_QUALITY_READY",
        name + "_total_count": len(cards),
        name + "_trainable_count": len(train_pairs),
        name + "_diagnostic_only_count": len(diag_pairs),
        "rejected_count": len(cards) - len(train_pairs) - len(diag_pairs),
        "failure_counts": dict(Counter(c["main_failure"] for c in cards)),
        "caveat": "controlled synthetic, not rollout" if mode == "synthetic_quality" else "real rollout-derived subset remains small; expansion still needed",
    }
    (out / (name + "_quality_summary.md")).write_text("\n".join([
        "Current Status:", summary["status"], "", "# " + name.title() + " Quality Audit", "",
        "- Total: {}".format(summary[name + "_total_count"]),
        "- Trainable: {}".format(summary[name + "_trainable_count"]),
        "- Diagnostic-only: {}".format(summary[name + "_diagnostic_only_count"]),
        "- Rejected: {}".format(summary["rejected_count"]),
        "- Failure counts: `{}`".format(json.dumps(summary["failure_counts"], sort_keys=True)),
        "- Caveat: " + summary["caveat"],
    ]) + "\n")
    (out / (name + "_quality_summary.json")).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="full", choices=["full", "synthetic_quality", "rollout_quality"])
    parser.add_argument("--ready_manifest", default="manifests/dpo_pair_factory_v10_ready_pairs.jsonl")
    parser.add_argument("--synthetic_manifest", default="manifests/dpo_pair_factory_v10_synthetic_visible_pairs.jsonl")
    parser.add_argument("--existing_manifest", default="manifests/dpo_pair_factory_v10_existing_ready_pairs.jsonl")
    parser.add_argument("--output_dir", default="reports/dpo_pair_factory_v10b")
    args = parser.parse_args()
    if args.mode == "full":
        run_full(args)
    else:
        quality_mode(args, args.mode)


if __name__ == "__main__":
    main()
