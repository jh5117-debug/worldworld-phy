
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

TRUE_VALUES = {"1", "true", "yes", "y", "pass", "passed"}
FALSE_VALUES = {"0", "false", "no", "n", "fail", "failed"}

DEFAULT_PAIR_MANIFESTS = [
    "reports/targeted_BC_loser_mining_v6b/dpo_ready_pairs_v6b.jsonl",
    "manifests/dpo_typeB_C_loser_pairs_v6b.jsonl",
    "manifests/dpo_typeB_C_loser_pairs_v6.jsonl",
    "reports/targeted_BC_loser_mining_v6/dpo_ready_pairs_v6.jsonl",
    "manifests/dpo_preference_protocol_v4_pairs.jsonl",
    "manifests/dpo_preference_protocol_v3_pairs.jsonl",
    "manifests/dpo_preference_protocol_v2_pairs.jsonl",
    "manifests/dpo_preference_protocol_v1_pairs.jsonl",
]


def boolish(value: Any, default: Optional[bool] = None) -> Optional[bool]:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text == "":
        return default
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    return default


def as_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


def nested_get(obj: Dict[str, Any], *paths: str) -> Any:
    for path in paths:
        cur: Any = obj
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return cur
    return None


def resolve_path(repo: Path, value: Any) -> Optional[Path]:
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.startswith("BLOCKED"):
        return None
    path = Path(text)
    if path.is_absolute():
        return path
    return repo / path


def file_exists(repo: Path, value: Any) -> bool:
    path = resolve_path(repo, value)
    return bool(path and path.exists() and path.stat().st_size > 0)


def video_decodable(repo: Path, value: Any) -> bool:
    path = resolve_path(repo, value)
    if not path or not path.exists() or path.stat().st_size == 0:
        return False
    if cv2 is None:
        return True
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return False
    ok, frame = cap.read()
    cap.release()
    return bool(ok and frame is not None)


def load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open() as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as exc:
                yield {"pair_id": f"JSON_ERROR_{path.name}_{line_no}", "_parse_error": str(exc)}
                continue
            obj["_manifest_source"] = str(path)
            yield obj


def read_csv_by_key(path: Path, key: str = "pair_id") -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    out: Dict[str, Dict[str, str]] = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            k = row.get(key, "")
            if k:
                out[k] = row
    return out


def load_reports(repo: Path) -> Dict[str, Dict[str, Dict[str, str]]]:
    return {
        "v5_visual": read_csv_by_key(repo / "reports/reward_visual_alignment_v5/pair_visual_alignment.csv"),
        "v6b_pairs": read_csv_by_key(repo / "reports/targeted_BC_loser_mining_v6b/pair_candidate_audit.csv"),
        "v6_pairs": read_csv_by_key(repo / "reports/targeted_BC_loser_mining_v6/pair_candidate_audit.csv"),
        "v4_pairs": read_csv_by_key(repo / "reports/dpo_pair_hardness_v4/protocol_v4_pair_audit.csv"),
        "v1_pairs": read_csv_by_key(repo / "reports/dpo_preference_protocol_v1/pair_audit.csv"),
        "v2_typea": read_csv_by_key(repo / "reports/dpo_preference_protocol_v2/typeA_localdpo_pair_audit.csv"),
    }


def extract_pair_fields(pair: Dict[str, Any], reports: Dict[str, Dict[str, Dict[str, str]]]) -> Dict[str, Any]:
    pid = str(pair.get("pair_id") or pair.get("id") or "")
    audit = pair.get("codex_audit") if isinstance(pair.get("codex_audit"), dict) else {}
    winner = pair.get("winner") if isinstance(pair.get("winner"), dict) else {}
    loser = pair.get("loser") if isinstance(pair.get("loser"), dict) else {}
    condition = pair.get("condition") if isinstance(pair.get("condition"), dict) else {}

    v5 = reports["v5_visual"].get(pid, {})
    v6b = reports["v6b_pairs"].get(pid, {})
    v6 = reports["v6_pairs"].get(pid, {})
    v4 = reports["v4_pairs"].get(pid, {})
    v1 = reports["v1_pairs"].get(pid, {})
    v2 = reports["v2_typea"].get(pid, {})

    reward_margin = as_float(pair.get("reward_margin"), None)
    for row in (v6b, v6, v5, v4, v1, v2):
        if reward_margin is None:
            reward_margin = as_float(row.get("reward_margin"), None)

    pair_type = str(pair.get("pair_type") or v6b.get("pair_type") or v6.get("pair_type") or v5.get("pair_type") or v1.get("pair_type") or "")
    corruption_type = str(nested_get(pair, "loser.corruption_type") or v6b.get("main_failure") or v6.get("main_failure") or v5.get("corruption_type") or v4.get("corruption_type") or v1.get("corruption_type") or "")
    protocol = str(pair.get("protocol_version") or "")

    return {
        "pair_id": pid,
        "protocol_version": protocol,
        "pair_type": pair_type,
        "corruption_type": corruption_type,
        "manifest_source": pair.get("_manifest_source", ""),
        "prefix_video": nested_get(pair, "condition.prefix_video_path", "condition.prefix_video", "condition.prefix", "prefix_video") or v6b.get("prefix_video") or v6.get("prefix_video"),
        "winner_video": nested_get(pair, "winner.future_video_path", "winner.full_video_path", "winner.video", "winner_video") or v6b.get("winner_video") or v6.get("winner_video") or v5.get("winner_video"),
        "loser_video": nested_get(pair, "loser.future_video_path", "loser.full_video_path", "loser.video", "loser_video") or v6b.get("loser_video") or v6.get("loser_video") or v5.get("loser_video"),
        "contact_sheet": audit.get("contact_sheet") or v5.get("contact_sheet") or v1.get("contact_sheet") or v2.get("contact_sheet"),
        "reward_margin": reward_margin,
        "medium_hard_manifest": boolish(pair.get("medium_hard"), None),
        "quality_floor_pass": boolish(pair.get("quality_floor_pass"), None),
        "sharpness_gate_pass": boolish(pair.get("sharpness_gate_pass"), None),
        "same_prefix": boolish(pair.get("same_prefix"), True),
        "same_prompt": boolish(pair.get("same_prompt"), True),
        "same_poses": boolish(pair.get("same_poses"), True),
        "same_intrinsics": boolish(pair.get("same_intrinsics"), True),
        "audit_valid": boolish(audit.get("valid_preference"), None),
        "audit_too_subtle": boolish(audit.get("too_subtle"), False),
        "audit_too_degraded": boolish(audit.get("too_degraded"), False),
        "audit_loser_collapsed": boolish(audit.get("loser_collapsed"), False),
        "audit_winner_bad": boolish(audit.get("winner_bad"), False),
        "written_reason": str(audit.get("written_reason") or v6b.get("written_reason") or v6.get("written_reason") or v5.get("written_reason") or v1.get("written_reason") or ""),
        "v5_status": v5.get("status", ""),
        "v5_can_see": v5.get("codex_can_see_difference", ""),
        "v5_explainable": v5.get("codex_failure_explainable", ""),
        "v6b_status": v6b.get("status", ""),
        "v6b_dpo_ready": v6b.get("dpo_ready", ""),
        "v1_valid": v1.get("is_valid_preference", ""),
        "v1_medium_hard": v1.get("is_medium_hard", ""),
        "v1_too_easy": v1.get("is_too_easy", ""),
        "v1_loser_collapsed": v1.get("is_loser_collapsed", ""),
        "v1_winner_bad": v1.get("is_winner_bad", ""),
    }


def decide(repo: Path, fields: Dict[str, Any]) -> Tuple[str, str, bool]:
    reasons: List[str] = []
    pid = fields["pair_id"]
    if not pid:
        return "REJECT_PARSE_OR_MISSING_ID", "missing pair_id", False

    path_checks = {
        "prefix": fields.get("prefix_video"),
        "winner": fields.get("winner_video"),
        "loser": fields.get("loser_video"),
    }
    for name, value in path_checks.items():
        if not file_exists(repo, value):
            reasons.append(f"missing_{name}_video")
        elif not video_decodable(repo, value):
            reasons.append(f"undecodable_{name}_video")
    if fields.get("contact_sheet") and not file_exists(repo, fields.get("contact_sheet")):
        reasons.append("missing_contact_sheet")

    if fields.get("same_prefix") is False or fields.get("same_prompt") is False or fields.get("same_poses") is False or fields.get("same_intrinsics") is False:
        reasons.append("not_same_condition")
    if fields.get("reward_margin") is None or fields.get("reward_margin") <= 0:
        reasons.append("nonpositive_or_missing_reward_margin")
    if fields.get("audit_valid") is False:
        reasons.append("codex_audit_invalid")
    if fields.get("audit_winner_bad"):
        reasons.append("winner_bad")
    if fields.get("audit_loser_collapsed"):
        reasons.append("loser_collapsed")
    if fields.get("audit_too_degraded"):
        reasons.append("too_degraded")
    if fields.get("audit_too_subtle"):
        reasons.append("too_subtle")
    if len(fields.get("written_reason") or "") < 12:
        reasons.append("missing_written_reason")

    if reasons:
        return "REJECT_TECHNICAL_OR_LABEL_GATE", ";".join(reasons), False

    v6b_ready = boolish(fields.get("v6b_dpo_ready"), False) or fields.get("v6b_status") == "dpo_ready_gt_c"
    v5_ready = fields.get("v5_status") == "DPO_READY_VISUAL_V5" and fields.get("v5_can_see") == "yes" and fields.get("v5_explainable") == "yes"
    old_typea = fields.get("protocol_version") in {"v1", "v2", "v3"} or str(fields.get("pair_id", "")).startswith(("protocol_v1_", "protocol_v2_", "protocol_v3_"))

    if v6b_ready:
        return "DPO_READY_EXISTING_STRICT", "v6b reviewed GT>C ready pair", True
    if v5_ready:
        return "DPO_READY_EXISTING_STRICT", "v5 visual alignment ready pair", True
    if old_typea:
        return "REVIEW_REQUIRED_OLD_SUBTLE_RISK", "old protocol pair passed broad audit but lacks v5-style human-visible gate", False
    if fields.get("medium_hard_manifest") and fields.get("quality_floor_pass") is not False and fields.get("sharpness_gate_pass") is not False:
        return "REVIEW_REQUIRED_UNMAPPED_AUDIT", "has manifest gates but no strict v5/v6b visual alignment row", False
    return "REJECT_NO_STRICT_VISUAL_GATE", "no strict human-visible visual gate", False


def iter_pairs(repo: Path, manifests: List[str]) -> Iterable[Dict[str, Any]]:
    seen = set()
    for manifest in manifests:
        path = repo / manifest
        if not path.exists():
            continue
        for pair in load_jsonl(path):
            pid = str(pair.get("pair_id") or "")
            key = pid or json.dumps(pair, sort_keys=True)[:200]
            if key in seen:
                continue
            seen.add(key)
            yield pair


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--output_dir", default="reports/dpo_pair_factory_v10/existing_pair_audit")
    parser.add_argument("--ready_manifest", default="manifests/dpo_pair_factory_v10_existing_ready_pairs.jsonl")
    parser.add_argument("--manifests", nargs="*", default=DEFAULT_PAIR_MANIFESTS)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    out_dir = repo / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    reports = load_reports(repo)

    rows: List[Dict[str, Any]] = []
    ready_pairs: List[Dict[str, Any]] = []
    rejected_pairs: List[Dict[str, Any]] = []

    for pair in iter_pairs(repo, args.manifests):
        fields = extract_pair_fields(pair, reports)
        status, reason, ready = decide(repo, fields)
        fields.update({"status": status, "decision_reason": reason, "dpo_ready_existing_strict": ready})
        rows.append(fields)
        if ready:
            pair["pair_factory_v10_existing_audit"] = {"status": status, "decision_reason": reason, "reviewed": True}
            ready_pairs.append(pair)
        else:
            pair["pair_factory_v10_existing_audit"] = {"status": status, "decision_reason": reason, "reviewed": False}
            rejected_pairs.append(pair)

    fieldnames = [
        "pair_id", "protocol_version", "pair_type", "corruption_type", "manifest_source", "status", "decision_reason",
        "dpo_ready_existing_strict", "reward_margin", "v5_status", "v5_can_see", "v5_explainable", "v6b_status", "v6b_dpo_ready",
        "prefix_video", "winner_video", "loser_video", "contact_sheet", "written_reason",
    ]
    with (out_dir / "existing_pair_audit.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    ready_path = repo / args.ready_manifest
    ready_path.parent.mkdir(parents=True, exist_ok=True)
    with ready_path.open("w") as f:
        for pair in ready_pairs:
            f.write(json.dumps(pair, ensure_ascii=False, sort_keys=True) + "\n")
    with (out_dir / "rejected_or_review_required_pairs.jsonl").open("w") as f:
        for pair in rejected_pairs:
            f.write(json.dumps(pair, ensure_ascii=False, sort_keys=True) + "\n")

    counts = Counter(row["status"] for row in rows)
    type_counts = Counter(row["pair_type"] for row in rows if row["dpo_ready_existing_strict"])
    summary = {
        "status": "EXISTING_PAIR_AUDIT_READY" if ready_pairs else "EXISTING_PAIR_AUDIT_NO_READY_PAIRS",
        "total_pairs_checked": len(rows),
        "dpo_ready_existing_strict": len(ready_pairs),
        "status_counts": dict(counts),
        "ready_pair_types": dict(type_counts),
        "ready_manifest": args.ready_manifest,
        "rule": "Only v6b reviewed GT>C or v5 human-visible pairs are strict-ready; old v1/v2/v3 broad TypeA pairs are review-required, not counted.",
    }
    (out_dir / "existing_pair_audit_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    lines = [
        "Current Status:",
        summary["status"],
        "",
        "# DPO Pair Factory v10 Existing Pair Audit",
        "",
        "- Total pairs checked: {}".format(summary["total_pairs_checked"]),
        "- Strict DPO-ready existing pairs: {}".format(summary["dpo_ready_existing_strict"]),
        "- Ready manifest: `{}`".format(args.ready_manifest),
        "- Status counts: `{}`".format(json.dumps(summary["status_counts"], sort_keys=True)),
        "- Ready pair types: `{}`".format(json.dumps(summary["ready_pair_types"], sort_keys=True)),
        "- Gate: v6b reviewed GT>C or v5 human-visible only. Old protocol v1/v2/v3 pairs require re-visual audit and are not used to inflate count.",
    ]
    (out_dir / "existing_pair_audit_summary.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
