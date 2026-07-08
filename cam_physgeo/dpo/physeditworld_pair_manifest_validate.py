from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PASS_DECISION = "PHYS_EDITWORLD_PAIR_MANIFEST_PASS"


@dataclass
class PairValidationRow:
    pair_id: str
    status: str
    error_reason: str
    pair_type: str
    condition_id: str
    reward_margin: str
    gravity_metric_margin: str
    reviewed: str
    medium_hard: str
    written_reason: str


def _get_path(obj: dict[str, Any], dotted: str) -> Any:
    cur: Any = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def first_value(row: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = _get_path(row, key)
        if value is not None and value != "":
            return value
    return None


def bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "pass", "passed"}:
            return True
        if lowered in {"false", "0", "no", "n", "fail", "failed"}:
            return False
    return None


def float_value(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def read_jsonl(path: str | Path) -> tuple[list[dict[str, Any]], str | None]:
    p = Path(path)
    if not p.exists():
        return [], "missing"
    rows: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                rows.append({"pair_id": f"line_{line_no}", "_json_error": repr(exc)})
                continue
            if not isinstance(obj, dict):
                rows.append({"pair_id": f"line_{line_no}", "_json_error": "row is not a JSON object"})
                continue
            rows.append(obj)
    return rows, None


def _path_exists(value: Any, base_dir: Path) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    text = value.strip()
    if text.startswith(("s3://", "gs://", "http://", "https://")):
        return False
    p = Path(text)
    if not p.is_absolute():
        p = base_dir / p
    return p.exists()


def compute_reward_margin(row: dict[str, Any]) -> float | None:
    direct = float_value(first_value(row, ["reward_margin", "margin.reward", "metrics.reward_margin"]))
    if direct is not None:
        return direct
    winner = float_value(first_value(row, ["reward_winner", "winner_reward", "winner.reward", "metrics.reward_winner"]))
    loser = float_value(first_value(row, ["reward_loser", "loser_reward", "loser.reward", "metrics.reward_loser"]))
    if winner is None or loser is None:
        return None
    return winner - loser


def compute_gravity_metric_margin(row: dict[str, Any]) -> float | None:
    direct = float_value(
        first_value(
            row,
            [
                "gravity_metric_margin",
                "gravity_margin",
                "metrics.gravity_metric_margin",
                "metrics.gravity_margin",
                "metric_margin",
            ],
        )
    )
    if direct is not None:
        return direct
    winner = float_value(first_value(row, ["gravity_metric_winner", "winner.gravity_metric", "metrics.gravity_metric_winner"]))
    loser = float_value(first_value(row, ["gravity_metric_loser", "loser.gravity_metric", "metrics.gravity_metric_loser"]))
    if winner is None or loser is None:
        return None
    return winner - loser


def validate_row(row: dict[str, Any], base_dir: Path, check_paths: bool) -> PairValidationRow:
    pair_id = str(first_value(row, ["pair_id", "sample_id", "id"]) or "")
    pair_type = str(first_value(row, ["pair_type", "type"]) or "")
    condition_id = str(first_value(row, ["condition_id", "condition.condition_id", "condition.sample_id", "sample_id"]) or "")
    reasons: list[str] = []

    if row.get("_json_error"):
        reasons.append(str(row["_json_error"]))
    if not pair_id:
        reasons.append("missing pair_id")
    if not pair_type:
        reasons.append("missing pair_type")
    if not condition_id:
        reasons.append("missing condition_id")

    required_paths = {
        "prefix_video_path": ["prefix_video_path", "prefix_path", "condition.prefix_video_path", "condition.prefix_path"],
        "winner_video_path": ["winner_video_path", "winner.path", "winner.video_path", "winner.full_video_path", "winner.future_video_path"],
        "loser_video_path": ["loser_video_path", "loser.path", "loser.video_path", "loser.full_video_path", "loser.future_video_path"],
        "contact_sheet_path": ["contact_sheet_path", "audit.contact_sheet_path", "codex_visual_audit.contact_sheet_path"],
    }
    for label, keys in required_paths.items():
        value = first_value(row, keys)
        if value is None:
            reasons.append(f"missing {label}")
        elif check_paths and not _path_exists(value, base_dir):
            reasons.append(f"{label} does not exist")

    same_checks = {
        "same_condition": ["same_condition", "checks.same_condition"],
        "same_action": ["same_action", "checks.same_action"],
        "same_camera": ["same_camera", "same_poses", "checks.same_camera", "checks.same_poses"],
        "same_intrinsics": ["same_intrinsics", "checks.same_intrinsics"],
        "same_gravity": ["same_gravity", "checks.same_gravity"],
    }
    for label, keys in same_checks.items():
        value = bool_value(first_value(row, keys))
        if value is not True:
            reasons.append(f"{label} is not true")

    reward_margin = compute_reward_margin(row)
    gravity_margin = compute_gravity_metric_margin(row)
    if reward_margin is None:
        reasons.append("missing reward_margin")
    elif reward_margin <= 0:
        reasons.append("reward_margin <= 0")
    if gravity_margin is None:
        reasons.append("missing gravity_metric_margin")
    elif gravity_margin <= 0:
        reasons.append("gravity_metric_margin <= 0")

    reviewed = bool_value(first_value(row, ["codex_visual_audit.reviewed", "reviewed"]))
    written_reason = str(first_value(row, ["codex_visual_audit.written_reason", "written_reason"]) or "").strip()
    medium_hard = bool_value(first_value(row, ["medium_hard", "codex_visual_audit.medium_hard"]))
    if reviewed is not True:
        reasons.append("codex_visual_audit.reviewed is not true")
    if not written_reason:
        reasons.append("written_reason empty")
    if medium_hard is not True:
        reasons.append("medium_hard is not true")

    reject_flags = {
        "winner_bad": ["winner_bad", "codex_visual_audit.winner_bad"],
        "too_collapsed": ["too_collapsed", "loser_collapsed", "codex_visual_audit.too_collapsed"],
        "too_blurry": ["too_blurry", "loser_too_blurry", "codex_visual_audit.too_blurry"],
        "too_subtle": ["too_subtle", "loser_too_subtle", "codex_visual_audit.too_subtle"],
    }
    for label, keys in reject_flags.items():
        if bool_value(first_value(row, keys)) is True:
            reasons.append(f"{label} true")

    status = "ready_strict" if not reasons else "rejected"
    return PairValidationRow(
        pair_id=pair_id or "UNKNOWN",
        status=status,
        error_reason="; ".join(reasons),
        pair_type=pair_type,
        condition_id=condition_id,
        reward_margin="" if reward_margin is None else f"{reward_margin:.10g}",
        gravity_metric_margin="" if gravity_margin is None else f"{gravity_margin:.10g}",
        reviewed=str(reviewed),
        medium_hard=str(medium_hard),
        written_reason=written_reason,
    )


def decision_for(rows: list[PairValidationRow], missing_reason: str | None, min_pairs: int) -> str:
    if missing_reason == "missing":
        return "PHYS_EDITWORLD_PAIR_MANIFEST_BLOCKED_MISSING"
    if not rows:
        return "PHYS_EDITWORLD_PAIR_MANIFEST_BLOCKED_EMPTY"
    ready = sum(1 for row in rows if row.status == "ready_strict")
    if ready < min_pairs:
        return "PHYS_EDITWORLD_PAIR_MANIFEST_BLOCKED_INSUFFICIENT_READY"
    rejected = len(rows) - ready
    if rejected:
        return "PHYS_EDITWORLD_PAIR_MANIFEST_SCHEMA_FAIL"
    return PASS_DECISION


def write_csv(rows: list[PairValidationRow], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = list(PairValidationRow.__dataclass_fields__.keys())
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_json(rows: list[PairValidationRow], decision: str, path: str | Path, manifest: str, min_pairs: int) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ready = sum(1 for row in rows if row.status == "ready_strict")
    payload = {
        "decision": decision,
        "manifest": manifest,
        "min_pairs": min_pairs,
        "total_rows": len(rows),
        "ready_strict": ready,
        "rejected": len(rows) - ready,
        "rows": [row.__dict__ for row in rows],
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[PairValidationRow], decision: str, path: str | Path, manifest: str, min_pairs: int) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ready = sum(1 for row in rows if row.status == "ready_strict")
    rejected = len(rows) - ready
    lines = [
        "# PhysEditWorld Anchored Pair Manifest Validation",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Manifest: `{manifest}`",
        f"- Total rows: `{len(rows)}`",
        f"- Ready strict rows: `{ready}`",
        f"- Rejected rows: `{rejected}`",
        f"- Minimum ready pairs: `{min_pairs}`",
        "",
        "Validation requires same condition/action/camera/intrinsics/gravity, existing prefix/WIN/LOSE/contact-sheet paths, positive reward and gravity metric margins, Codex visual review, non-empty written reason, medium-hard loser, and no winner-bad/blur/collapse/subtle flags.",
    ]
    if rows and rejected:
        lines.extend(["", "## First Rejections", ""])
        for row in rows:
            if row.status != "ready_strict":
                lines.append(f"- `{row.pair_id}`: {row.error_reason}")
                if len([line for line in lines if line.startswith("- `")]) >= 10:
                    break
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Validate PhysEditWorld anchored DPO pair manifest before tiny DPO")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output_csv", required=True)
    ap.add_argument("--output_json", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--min_pairs", type=int, default=100)
    ap.add_argument("--base_dir", default=".")
    ap.add_argument("--no_check_path_exists", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw_rows, missing_reason = read_jsonl(args.manifest)
    base_dir = Path(args.base_dir)
    rows = [validate_row(row, base_dir, check_paths=not args.no_check_path_exists) for row in raw_rows]
    decision = decision_for(rows, missing_reason, args.min_pairs)
    write_csv(rows, args.output_csv)
    write_json(rows, decision, args.output_json, args.manifest, args.min_pairs)
    write_summary(rows, decision, args.summary, args.manifest, args.min_pairs)
    print(json.dumps({"decision": decision, "ready_strict": sum(1 for row in rows if row.status == "ready_strict"), "total_rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
