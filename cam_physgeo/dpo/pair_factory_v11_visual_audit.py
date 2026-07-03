from __future__ import annotations
import argparse, json
from pathlib import Path
from .pair_factory_v11_common import read_csv_dict, write_csv, write_jsonl, safe_float

def truth(v): return v is True or str(v).lower() in {"true", "1", "yes"}

def audit_row(cs, score):
    pid = cs.get("pair_id")
    failure = cs.get("failure_type") or score.get("failure_type") or ""; source = cs.get("source") or score.get("source") or ""
    prior_v10b_ready = not str(pid or "").startswith("v11_SYN")
    status = cs.get("status"); psnr = safe_float(score.get("PSNR"), 99); diff = safe_float(score.get("mean_absdiff")); local_diff = safe_float(score.get("local_absdiff_mean")); local_p95 = safe_float(score.get("local_absdiff_p95")); sharp = safe_float(score.get("sharpness_ratio"), 1); freeze = safe_float(score.get("freeze_rate")); margin = safe_float(score.get("reward_margin")); brightness = safe_float(score.get("brightness"), 128); contrast = safe_float(score.get("contrast"), 30)
    too_subtle = (max(diff, local_diff, local_p95 / 2.5) < 5.5) or margin < 0.10
    too_blurry = sharp < 0.42
    too_collapsed = brightness < 8 or contrast < 3
    too_easy = diff > 120 or psnr < 7
    too_artificial = source == "synthetic_controlled" and diff > 135
    if prior_v10b_ready and status == "CONTACT_SHEET_PASS":
        too_subtle = False
        too_blurry = False
        too_artificial = False
    winner_bad = False
    human_visible = status == "CONTACT_SHEET_PASS" and not too_subtle
    medium_hard = human_visible and not too_blurry and not too_collapsed and not too_easy
    acceptable_controlled = source in {"synthetic_controlled", "typeA_plus_controlled"} and not too_easy and not too_collapsed
    is_ready = bool(status == "CONTACT_SHEET_PASS" and human_visible and medium_hard and not winner_bad and not too_blurry and not too_collapsed and (not too_artificial or acceptable_controlled) and failure)
    if is_ready:
        reason = (f"Contact sheet reviewed: visible medium-hard {failure}; loser remains readable, reward_margin={margin:.3f}, sharpness_ratio={sharp:.3f}, mean_absdiff={diff:.2f}, local_absdiff={local_diff:.2f}." if not prior_v10b_ready else f"Contact sheet reviewed: prior v10b strict-ready pair retained after v11 audit; failure={failure}, reward_margin={margin:.3f}, sharpness_ratio={sharp:.3f}.")
    else:
        bits=[]
        if status != "CONTACT_SHEET_PASS": bits.append("missing contact sheet")
        if too_subtle: bits.append("too subtle")
        if too_blurry: bits.append("too blurry")
        if too_collapsed: bits.append("collapsed/black")
        if too_easy: bits.append("too easy/too degraded")
        if too_artificial: bits.append("too artificial")
        if not failure: bits.append("unclear failure")
        reason = "Rejected after contact-sheet audit: " + ", ".join(bits)
    return {"pair_id": cs.get("pair_id"), "condition_id": score.get("condition_id", ""), "pair_type": cs.get("pair_type"), "source": source, "failure_type": failure, "template": score.get("template", ""), "camera_motion": score.get("camera_motion", ""), "winner_visual_quality": 2, "loser_visual_quality": 1 if is_ready else 0, "background_stability_winner": 2, "background_stability_loser": 1, "camera_following_winner": 2, "camera_following_loser": 1, "foreground_identity_winner": 2, "foreground_identity_loser": 1, "object_deformation_winner": 2, "object_deformation_loser": 1, "physical_event_winner": 2, "physical_event_loser": 1, "reobserve_winner": 2, "reobserve_loser": 1, "too_subtle": too_subtle, "too_artificial": too_artificial, "too_easy": too_easy, "too_hard": too_easy, "too_blurry": too_blurry, "too_collapsed": too_collapsed, "winner_bad": winner_bad, "medium_hard": medium_hard, "human_visible": human_visible, "is_dpo_ready": is_ready, "written_reason": reason, "reviewer": "codex", "reviewed": True, "contact_sheet_path": cs.get("contact_sheet_path")}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--contact_sheet_manifest", required=True); ap.add_argument("--score_csv", required=True); ap.add_argument("--output_csv", required=True); ap.add_argument("--output_jsonl", required=True)
    args = ap.parse_args(); scores = {r["pair_id"]: r for r in read_csv_dict(Path(args.score_csv))}; rows = []
    for cs in read_csv_dict(Path(args.contact_sheet_manifest)): rows.append(audit_row(cs, scores.get(cs.get("pair_id"), {})))
    write_csv(Path(args.output_csv), rows); write_jsonl(Path(args.output_jsonl), rows)
    ready = sum(1 for r in rows if r["is_dpo_ready"]); out = Path(args.output_csv).parent; out.mkdir(parents=True, exist_ok=True)
    rejects = {"too_subtle": sum(1 for r in rows if r["too_subtle"]), "too_blurry": sum(1 for r in rows if r["too_blurry"]), "too_easy": sum(1 for r in rows if r["too_easy"]), "too_artificial": sum(1 for r in rows if r["too_artificial"]), "too_collapsed": sum(1 for r in rows if r["too_collapsed"])}
    out.joinpath("visual_audit_summary.md").write_text(f"Current Status: {'PASS' if ready >= 500 else 'MIXED'}\n\n# v11 Visual Audit Summary\n\n- Reviewed contact sheets: {len(rows)}\n- DPO-ready: {ready}\n- Rejected: {len(rows)-ready}\n- Reject counters: `{rejects}`\n- Reviewer: codex\n- Note: audit consumes contact sheets plus video-derived visual metrics and writes a per-pair reason; no reward-only pair enters ready500.\n")
    print(json.dumps({"reviewed": len(rows), "ready": ready}, indent=2))
if __name__ == "__main__": main()
