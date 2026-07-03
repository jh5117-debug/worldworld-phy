from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]


def repo_path(p: str | None) -> Path:
    if not p:
        return Path("")
    path = Path(str(p))
    return path if path.is_absolute() else REPO / path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv_dict(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="") as f:
        return {r.get("pair_id", ""): r for r in csv.DictReader(f)}


def truth(v: Any) -> bool:
    return v is True or str(v).strip().lower() in {"true", "1", "yes", "y"}


def fnum(v: Any, default: float = 0.0) -> float:
    try:
        if v in (None, "", "nan", "NaN"):
            return default
        return float(v)
    except Exception:
        return default


def nested(d: dict[str, Any], *keys: str) -> Any:
    cur: Any = d
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def loser_video_path(pair: dict[str, Any]) -> str:
    return (
        nested(pair, "loser", "future_video_path")
        or nested(pair, "loser", "video_path")
        or nested(pair, "loser", "full_video_path")
        or pair.get("loser_video_path")
        or ""
    )


def winner_video_path(pair: dict[str, Any]) -> str:
    return (
        nested(pair, "winner", "future_video_path")
        or nested(pair, "winner", "video_path")
        or nested(pair, "winner", "full_video_path")
        or pair.get("winner_video_path")
        or ""
    )


def source_of(pair: dict[str, Any], score: dict[str, str], visual: dict[str, str]) -> str:
    explicit = pair.get("pair_source") or score.get("source") or visual.get("source")
    if explicit:
        return str(explicit)
    ptype = pair.get("pair_type")
    if ptype == "GT_C" or "rollout" in str(pair.get("_manifest_source", "")):
        return "rollout_derived"
    if ptype == "TypeA_plus":
        return "TypeA_plus"
    return "synthetic_controlled"


def failure_of(pair: dict[str, Any], score: dict[str, str], visual: dict[str, str]) -> str:
    return str(
        pair.get("failure_tag")
        or score.get("failure_type")
        or visual.get("failure_type")
        or nested(pair, "loser", "failure_type")
        or nested(pair, "loser", "corruption_type")
        or "unknown"
    )


def ffprobe_video(path: Path, timeout: int = 6) -> dict[str, Any]:
    out = {"exists": path.exists(), "decodable": False, "width": 0, "height": 0, "frames": 0, "duration": 0.0, "error": ""}
    if not path.exists():
        out["error"] = "missing"
        return out
    # H20 currently has no ffprobe in PATH, so use a lightweight OpenCV probe.
    # We intentionally read only the first frame; full-frame decode is too slow for 500-pair audit.
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            out["error"] = "cv2_open_failed"
            return out
        ok, frame = cap.read()
        if ok and frame is not None:
            h, w = frame.shape[:2]
            frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            out.update({
                "decodable": True,
                "width": int(w),
                "height": int(h),
                "frames": frames,
                "duration": float(frames / fps) if fps > 0 and frames > 0 else 0.0,
            })
        else:
            out["error"] = "cv2_first_frame_failed"
        cap.release()
    except Exception as exc:
        out["error"] = repr(exc)[:240]
    return out

def contact_sheet_stats(path: Path) -> dict[str, Any]:
    stats = {
        "contact_sheet_exists": path.exists(),
        "contact_sheet_readable": False,
        "sheet_width": 0,
        "sheet_height": 0,
        "loser_crop_brightness": 0.0,
        "loser_crop_contrast": 0.0,
        "loser_crop_sharpness": 0.0,
    }
    if not path.exists():
        return stats
    try:
        import cv2
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None:
            return stats
        h, w = img.shape[:2]
        # v11 sheets are four horizontal rows: prefix, WIN, LOSE, diff/zoom.
        y0, y1 = int(h * 0.50), int(h * 0.75)
        crop = img[y0:y1, :]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        stats.update({
            "contact_sheet_readable": True,
            "sheet_width": w,
            "sheet_height": h,
            "loser_crop_brightness": float(gray.mean()),
            "loser_crop_contrast": float(gray.std()),
            "loser_crop_sharpness": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        })
    except Exception:
        pass
    return stats


def audit_pair(pair: dict[str, Any], score: dict[str, str], visual: dict[str, str]) -> dict[str, Any]:
    pid = str(pair.get("pair_id") or "")
    va = pair.get("codex_visual_audit") or {}
    ca = pair.get("codex_audit") or {}
    source = source_of(pair, score, visual)
    failure = failure_of(pair, score, visual)
    contact = pair.get("contact_sheet_path") or visual.get("contact_sheet_path") or ""
    loser_path_str = loser_video_path(pair)
    winner_path_str = winner_video_path(pair)
    loser_info = ffprobe_video(repo_path(loser_path_str))
    sheet = contact_sheet_stats(repo_path(contact))

    reviewed = truth(va.get("reviewed", visual.get("reviewed", True)))
    human_visible = truth(va.get("human_visible", visual.get("human_visible", True)))
    medium_hard = truth(pair.get("medium_hard", va.get("medium_hard", visual.get("medium_hard", True))))
    visual_ready = truth(va.get("is_dpo_ready", visual.get("is_dpo_ready", True)))
    written_reason = str(va.get("written_reason") or ca.get("written_reason") or visual.get("written_reason") or "")

    loser_visual_quality = int(fnum(visual.get("loser_visual_quality"), 1))
    winner_visual_quality = int(fnum(visual.get("winner_visual_quality"), 2))
    reward_margin = fnum(pair.get("reward_margin", score.get("reward_margin")))
    sharp_ratio = fnum(score.get("sharpness_ratio"), 1.0)
    mean_absdiff = fnum(score.get("mean_absdiff"))
    local_diff = max(fnum(score.get("local_absdiff_mean")), fnum(score.get("local_absdiff_p95")) / 2.5, mean_absdiff / 8.0)
    freeze_rate = fnum(score.get("freeze_rate"))
    brightness = fnum(score.get("brightness"), sheet["loser_crop_brightness"])
    contrast = fnum(score.get("contrast"), sheet["loser_crop_contrast"])

    reasons: list[str] = []
    if not loser_info["exists"]:
        reasons.append("missing_loser_video")
    elif not loser_info["decodable"]:
        reasons.append("undecodable_loser_video")
    if not sheet["contact_sheet_exists"]:
        reasons.append("missing_contact_sheet")
    elif not sheet["contact_sheet_readable"]:
        reasons.append("unreadable_contact_sheet")
    if not reviewed:
        reasons.append("not_reviewed")
    if not written_reason:
        reasons.append("missing_written_reason")
    if winner_visual_quality < 1 or truth(va.get("winner_bad", visual.get("winner_bad", False))):
        reasons.append("winner_bad")
    if not human_visible or truth(va.get("too_subtle", visual.get("too_subtle", False))):
        reasons.append("too_subtle_visual")
    if not medium_hard or truth(visual.get("too_easy", False)) or truth(visual.get("too_hard", False)):
        reasons.append("not_medium_hard")
    if truth(va.get("too_blurry", visual.get("too_blurry", False))) or (source != "rollout_derived" and sharp_ratio < 0.12):
        reasons.append("loser_too_blurry")
    if truth(va.get("too_collapsed", visual.get("too_collapsed", False))) or contrast < 2.0 or brightness < 5.0:
        reasons.append("loser_collapsed_or_black")
    if freeze_rate > 0.90:
        reasons.append("global_freeze")
    if source != "rollout_derived" and local_diff < 2.0:
        reasons.append("too_subtle_metric")
    # Controlled synthetic failures may be intentionally visible, but reject the extreme cases.
    if source == "synthetic_controlled" and (truth(visual.get("too_artificial", False)) or mean_absdiff > 150):
        reasons.append("too_artificial")
    if reward_margin <= 0 and source == "rollout_derived":
        reasons.append("non_positive_reward_margin")
    if not visual_ready:
        reasons.append("visual_audit_not_ready")
    if loser_visual_quality < 1:
        reasons.append("loser_visual_quality_low")

    trainable = len(reasons) == 0
    return {
        "pair_id": pid,
        "pair_type": pair.get("pair_type", ""),
        "source": source,
        "failure_type": failure,
        "condition_id": nested(pair, "condition", "condition_id") or score.get("condition_id") or visual.get("condition_id") or "",
        "template": nested(pair, "condition", "template") or score.get("template") or visual.get("template") or "",
        "camera_motion": nested(pair, "condition", "camera_motion") or score.get("camera_motion") or visual.get("camera_motion") or "",
        "winner_video_path": winner_path_str,
        "loser_video_path": loser_path_str,
        "contact_sheet_path": contact,
        "loser_video_exists": loser_info["exists"],
        "loser_video_decodable": loser_info["decodable"],
        "loser_frames": loser_info["frames"],
        "loser_width": loser_info["width"],
        "loser_height": loser_info["height"],
        "contact_sheet_exists": sheet["contact_sheet_exists"],
        "contact_sheet_readable": sheet["contact_sheet_readable"],
        "loser_crop_brightness": round(sheet["loser_crop_brightness"], 4),
        "loser_crop_contrast": round(sheet["loser_crop_contrast"], 4),
        "loser_crop_sharpness": round(sheet["loser_crop_sharpness"], 4),
        "winner_visual_quality": winner_visual_quality,
        "loser_visual_quality": loser_visual_quality,
        "reward_winner": pair.get("reward_winner", score.get("reward_winner", "")),
        "reward_loser": pair.get("reward_loser", score.get("reward_loser", "")),
        "reward_margin": reward_margin,
        "PSNR": score.get("PSNR", ""),
        "SSIM": score.get("SSIM", ""),
        "sharpness_ratio": sharp_ratio,
        "mean_absdiff": mean_absdiff,
        "local_visible_diff": round(local_diff, 4),
        "freeze_rate": freeze_rate,
        "brightness": brightness,
        "contrast": contrast,
        "reviewed": reviewed,
        "human_visible": human_visible,
        "medium_hard": medium_hard,
        "visual_audit_ready": visual_ready,
        "written_reason": written_reason,
        "reject_reasons": ";".join(reasons),
        "trainable_after_loser_audit": trainable,
        "status": "TRAINABLE" if trainable else "REJECT_OR_REVIEW",
    }


def write_header_if_needed(path: Path, fields: list[str]) -> None:
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", newline="") as f:
            csv.DictWriter(f, fieldnames=fields).writeheader()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ready_manifest", required=True)
    ap.add_argument("--score_csv", required=True)
    ap.add_argument("--visual_audit_csv", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--trainable_out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    audit_csv = out / "ready500_loser_quality_audit.csv"
    audit_jsonl = out / "ready500_loser_quality_audit.jsonl"
    rejected_jsonl = out / "ready500_loser_quality_rejected.jsonl"
    for p in (audit_csv, audit_jsonl, rejected_jsonl, Path(args.trainable_out)):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("")

    pairs = read_jsonl(Path(args.ready_manifest))
    if args.limit:
        pairs = pairs[: args.limit]
    scores = read_csv_dict(Path(args.score_csv))
    visuals = read_csv_dict(Path(args.visual_audit_csv))

    rows: list[dict[str, Any]] = []
    trainable_pairs: list[dict[str, Any]] = []
    rejected_pairs: list[dict[str, Any]] = []
    fields: list[str] | None = None

    for idx, pair in enumerate(pairs, 1):
        pid = str(pair.get("pair_id") or "")
        row = audit_pair(pair, scores.get(pid, {}), visuals.get(pid, {}))
        if fields is None:
            fields = list(row.keys())
            write_header_if_needed(audit_csv, fields)
        rows.append(row)
        with audit_csv.open("a", newline="") as f:
            csv.DictWriter(f, fieldnames=fields).writerow(row)
            f.flush()
        with audit_jsonl.open("a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
        if row["trainable_after_loser_audit"]:
            trainable_pairs.append(pair)
        else:
            rejected_pairs.append(pair)
            with rejected_jsonl.open("a") as f:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
        if idx % 25 == 0 or idx == len(pairs):
            print(json.dumps({"processed": idx, "trainable": len(trainable_pairs), "rejected": len(rejected_pairs)}, ensure_ascii=False), flush=True)

    with Path(args.trainable_out).open("w") as f:
        for pair in trainable_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    status_counts = Counter(r["status"] for r in rows)
    source_counts = Counter(r["source"] for r in rows)
    reason_counts: Counter[str] = Counter()
    failure_counts = Counter(r["failure_type"] for r in rows)
    for row in rows:
        for reason in filter(None, str(row.get("reject_reasons", "")).split(";")):
            reason_counts[reason] += 1
    status = "PASS" if len(trainable_pairs) == len(rows) == 500 else "MIXED"
    summary = (
        f"Current Status: {status}\n\n"
        "# Ready500 Loser Quality Audit\n\n"
        f"- Audited pairs: {len(rows)}\n"
        f"- Trainable after loser audit: {len(trainable_pairs)}\n"
        f"- Reject/review: {len(rejected_pairs)}\n"
        f"- Status counts: `{dict(status_counts)}`\n"
        f"- Source counts: `{dict(source_counts)}`\n"
        f"- Failure counts: `{dict(failure_counts)}`\n"
        f"- Reject reasons: `{dict(reason_counts)}`\n"
        f"- Trainable manifest: `{args.trainable_out}`\n\n"
        "Decision: only rows with `trainable_after_loser_audit=True` should be used for training. "
        "Rows marked `REJECT_OR_REVIEW` require manual correction or exclusion.\n"
    )
    (out / "ready500_loser_quality_summary.md").write_text(summary)
    print(json.dumps({
        "audited": len(rows),
        "trainable": len(trainable_pairs),
        "rejected": len(rejected_pairs),
        "reject_reasons": dict(reason_counts),
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
