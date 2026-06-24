from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from cam_physgeo.dpo.preference_schema import validate_pair
from cam_physgeo.utils.io import read_jsonl, write_jsonl

BAD_FAILURE_TAGS = {
    "black", "corrupt", "decode_failed", "scene_replace", "global_freeze", "object_disappear",
}


def _read_csv(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _num(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = row.get(key)
        if value in {None, "", "missing"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _score(row: dict[str, Any]) -> float:
    if row.get("reward_total") not in {None, "", "missing"}:
        return _num(row, "reward_total")
    quality = _num(row, "quality_proxy")
    ssim = _num(row, "ssim")
    csgc = _num(row, "csgc_score", default=quality)
    freeze = _num(row, "freeze_rate")
    pixel_l1 = _num(row, "pixel_l1_proxy")
    return max(0.0, min(1.0, 0.35 * quality + 0.30 * ssim + 0.20 * csgc + 0.15 * (1.0 - freeze) - 0.10 * pixel_l1))


def _failure_tags(row: dict[str, Any]) -> set[str]:
    text = str(row.get("failure_tags") or row.get("precheck_tags") or "")
    return {x.strip() for x in text.replace(",", ";").split(";") if x.strip()}


def _quality_ok(row: dict[str, Any], *, min_quality: float, max_freeze: float) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if str(row.get("decode_status") or "ok") != "ok":
        reasons.append("decode_not_ok")
    if _num(row, "quality_proxy") < min_quality:
        reasons.append("quality_below_floor")
    if _num(row, "freeze_rate") > max_freeze:
        reasons.append("freeze_above_floor")
    tags = _failure_tags(row)
    bad = sorted(tags & BAD_FAILURE_TAGS)
    if bad:
        reasons.extend(f"bad_tag:{x}" for x in bad)
    return not reasons, reasons


def _load_manifest(path: str | Path) -> dict[str, dict[str, Any]]:
    return {str(row.get("sample_id")): row for row in read_jsonl(path)}


def _video(row: dict[str, Any]) -> str:
    for key in ("candidate_video", "generated_video", "video_path", "target_video", "winner_video", "loser_video"):
        if row.get(key):
            return str(row[key])
    return ""


def build_pairs(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    conditions = _load_manifest(args.conditions)
    rows = _read_csv(args.metrics_csv)
    by_sample: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_sample.setdefault(str(row.get("sample_id")), []).append(row)
    pairs: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for sid, sample_rows in by_sample.items():
        condition = conditions.get(sid, {"sample_id": sid})
        gt_rows = [r for r in sample_rows if str(r.get("model", "")).lower() in {"gt", "clean_gt"}]
        if not gt_rows:
            rejected.append({"sample_id": sid, "reason": "missing_gt_row"})
            continue
        gt = gt_rows[0]
        winner_score = _score(gt)
        for row in sample_rows:
            model = str(row.get("model", ""))
            if row is gt or model.lower() in {"gt", "clean_gt"}:
                continue
            ok, reasons = _quality_ok(row, min_quality=args.min_quality, max_freeze=args.max_freeze_rate)
            loser_score = _score(row)
            margin = winner_score - loser_score
            if not ok:
                rejected.append({"sample_id": sid, "model": model, "reason": ";".join(reasons), "loser_score": loser_score, "winner_score": winner_score})
                continue
            if margin < args.min_margin:
                rejected.append({"sample_id": sid, "model": model, "reason": "margin_too_small", "margin": margin, "loser_score": loser_score, "winner_score": winner_score})
                continue
            if margin > args.max_margin:
                rejected.append({"sample_id": sid, "model": model, "reason": "margin_too_large_trivial_loser", "margin": margin, "loser_score": loser_score, "winner_score": winner_score})
                continue
            pid = "anchored_" + hashlib.sha1(f"{sid}:{model}:{_video(row)}".encode()).hexdigest()[:14]
            pair = {
                "pair_id": pid,
                "condition": {
                    "sample_id": sid,
                    "image": condition.get("image", ""),
                    "prompt": condition.get("prompt", ""),
                    "poses": condition.get("poses", ""),
                    "intrinsics": condition.get("intrinsics", ""),
                    "use_action": False,
                    "template": condition.get("template", ""),
                    "camera_variant": condition.get("camera_variant", ""),
                },
                "winner": {"video": _video(gt), "source": "clean_gt", "score": winner_score, "metrics": gt},
                "loser": {"video": _video(row), "source": model, "score": loser_score, "metrics": row},
                "pair_type": "gt_vs_quality_bounded_rollout",
                "margin": margin,
                "quality_flags": [],
                "hard_negative_tags": sorted(_failure_tags(row)),
            }
            errors = validate_pair(pair)
            if errors:
                rejected.append({"sample_id": sid, "model": model, "reason": "schema:" + ";".join(errors)})
                continue
            pairs.append(pair)
            if args.max_pairs and len(pairs) >= args.max_pairs:
                return pairs, rejected
    return pairs, rejected


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build quality-bounded anchored DPO probe pairs from benchmark metrics.")
    ap.add_argument("--conditions", required=True)
    ap.add_argument("--metrics_csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rejected_out", default="")
    ap.add_argument("--min_quality", type=float, default=0.25)
    ap.add_argument("--max_freeze_rate", type=float, default=0.80)
    ap.add_argument("--min_margin", type=float, default=0.03)
    ap.add_argument("--max_margin", type=float, default=0.25)
    ap.add_argument("--max_pairs", type=int, default=0)
    args = ap.parse_args(argv)
    pairs, rejected = build_pairs(args)
    write_jsonl(pairs, args.out)
    if args.rejected_out:
        write_jsonl(rejected, args.rejected_out)
    print({"pairs": len(pairs), "rejected": len(rejected), "out": args.out})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
