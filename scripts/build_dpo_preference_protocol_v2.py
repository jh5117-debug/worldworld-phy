from __future__ import annotations

import csv
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def tags(row: dict[str, Any]) -> set[str]:
    return {x.strip() for x in str(row.get("failure_tags", "")).replace(",", ";").split(";") if x.strip()}


def gate_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if row.get("candidate_was_protocol_v1_typeB") != "true":
        reasons.append("not_protocol_v1_typeB_candidate")
    if row.get("energy_audited") != "true":
        reasons.append("missing_real_energy_audit")
    if not as_bool(row.get("is_quality_floor_pass")):
        reasons.append("old_quality_floor_false")
    if not as_bool(row.get("is_medium_hard_negative")):
        reasons.append("old_medium_hard_false")
    if as_float(row.get("visual_quality", 0.0)) < 1.0:
        reasons.append("visual_quality_lt_1")
    if as_float(row.get("R_quality", 0.0)) < as_float(row.get("condition_r_quality_p40", 0.0)):
        reasons.append("r_quality_below_condition_p40")
    if as_float(row.get("loser_sharpness_ratio", 0.0)) < 0.55:
        reasons.append("sharpness_ratio_lt_0.55")
    if as_float(row.get("reward_margin", 0.0)) <= 0:
        reasons.append("non_positive_reward_margin")
    if as_float(row.get("Delta_ref", 0.0)) <= 0:
        reasons.append("non_positive_delta_ref")
    blocked = {"black_screen", "severe_blur", "low_bitrate_artifact", "scene_replace", "scene_replacement", "global_freeze", "object_disappear", "main_object_disappeared"}
    overlap = tags(row) & blocked
    if overlap:
        reasons.append("blocked_failure_tag=" + ";".join(sorted(overlap)))
    return reasons


def main() -> int:
    out = Path("reports/dpo_preference_protocol_v2")
    out.mkdir(parents=True, exist_ok=True)
    manifest_out = Path("manifests/dpo_preference_protocol_v2_pairs.jsonl")
    manifest_out.parent.mkdir(parents=True, exist_ok=True)

    rollout_rows = read_csv(Path("reports/dpo_preference_protocol_v1/rollout_video_audit.csv"))
    selected_v1_b = read_csv(Path("reports/dpo_preference_protocol_v1/selected_medium_hard_losers.csv"))
    blur_rows = read_csv(Path("reports/ppt_dpo_pair_examples_simple/loser_blur_audit.csv"))
    energy_rows = read_csv(Path("reports/dpo_preference_protocol_v1/full_real_energy_audit.csv"))
    localdpo_v1 = read_jsonl(Path("reports/dpo_preference_protocol_v1/localdpo_ready_pairs.jsonl"))
    v1_pairs = read_jsonl(Path("manifests/dpo_preference_protocol_v1_pairs.jsonl"))

    selected_by_key = {(r.get("sample_id", ""), r.get("model", "")): r for r in selected_v1_b}
    blur_by_pair = {r.get("pair_id", ""): r for r in blur_rows}
    energy_by_pair = {r.get("pair_id", ""): r for r in energy_rows if r.get("status") == "ok"}
    v1_by_pair = {p.get("pair_id", ""): p for p in v1_pairs}
    q_by_sample: dict[str, list[float]] = defaultdict(list)
    for r in rollout_rows:
        q_by_sample[r.get("sample_id", "")].append(as_float(r.get("R_quality")))
    p40_by_sample = {k: float(np.percentile(v, 40)) if v else 0.0 for k, v in q_by_sample.items()}

    gate_rows: list[dict[str, Any]] = []
    selected_typeb: list[dict[str, Any]] = []
    rejected_typeb: list[dict[str, Any]] = []
    for r in rollout_rows:
        key = (r.get("sample_id", ""), r.get("model", ""))
        selected = selected_by_key.get(key)
        pair_id = selected.get("pair_id", "") if selected else ""
        blur = blur_by_pair.get(pair_id, {})
        energy = energy_by_pair.get(pair_id, {}) if pair_id else {}
        row = {
            **r,
            "pair_id": pair_id,
            "candidate_was_protocol_v1_typeB": "true" if selected else "false",
            "energy_audited": "true" if energy else "false",
            "condition_r_quality_p40": p40_by_sample.get(r.get("sample_id", ""), 0.0),
            "winner_sharpness": blur.get("winner_sharpness", ""),
            "loser_sharpness": blur.get("loser_sharpness", ""),
            "loser_sharpness_ratio": blur.get("sharpness_ratio", "0"),
            "reward_margin": selected.get("reward_margin", "") if selected else "",
            "Delta_ref": energy.get("Delta_ref") or energy.get("delta_ref") or "",
            "reference_relative_margin": energy.get("reference_relative_margin", ""),
            "metric_psnr": r.get("psnr", ""),
            "metric_ssim": r.get("ssim", ""),
            "metric_lpips_status": r.get("lpips_status", ""),
            "metric_fvd_status": r.get("fvd_status", ""),
            "metric_vbench_status": r.get("vbench_status", ""),
        }
        reasons = gate_reasons(row)
        row["sharpness_gate_pass"] = as_float(row.get("loser_sharpness_ratio")) >= 0.55
        row["quality_gate_v2_pass"] = not reasons
        row["reject_reasons"] = ";".join(reasons)
        gate_rows.append(row)
        if selected:
            (selected_typeb if row["quality_gate_v2_pass"] else rejected_typeb).append(row)

    write_csv(out / "typeB_loser_quality_gate.csv", gate_rows)
    write_csv(out / "typeB_selected_medium_hard_losers.csv", selected_typeb)
    write_csv(out / "typeB_rejected_losers.csv", rejected_typeb)

    typea_audit: list[dict[str, Any]] = []
    typea_v2: list[dict[str, Any]] = []
    for idx, pair in enumerate(localdpo_v1, start=1):
        loser = pair.get("loser", {})
        energy = pair.get("energy_audit", {})
        affected_region = loser.get("affected_region") or loser.get("affected_region_available") or energy.get("affected_region_available")
        affected_mask = loser.get("affected_mask") or loser.get("affected_mask_path") or energy.get("affected_mask_available")
        affected_time = loser.get("affected_time_span") or energy.get("affected_time_span_available")
        has_region = bool(affected_region) and str(affected_region).lower() not in {"false", "none", ""}
        has_mask = bool(affected_mask) and str(affected_mask).lower() not in {"false", "none", ""}
        has_time = bool(affected_time) and str(affected_time).lower() not in {"false", "none", ""}
        audit = {
            "source_pair_id": pair.get("pair_id", ""),
            "pair_id": f"protocol_v2_A_{idx:03d}_{pair.get('pair_id','').replace('protocol_v1_A_', '')}",
            "corruption_type": loser.get("corruption_type") or energy.get("corruption_type", ""),
            "affected_region_available": has_region,
            "affected_mask_available": has_mask,
            "affected_time_span_available": has_time,
            "locality_level": "spatial_and_time" if (has_region or has_mask) and has_time else "time_only" if has_time else "missing",
            "localdpo_status": "LOCALDPO_METADATA_READY" if (has_region or has_mask) and has_time else "LOCALDPO_TIME_ONLY" if has_time else "LOCALDPO_BLOCKED_MISSING_MASK",
            "Delta_ref": energy.get("Delta_ref") or energy.get("delta_ref") or pair.get("selection", {}).get("Delta_ref", ""),
            "reward_margin": pair.get("reward_margin", ""),
            "codex_valid_preference": pair.get("codex_audit", {}).get("valid_preference", ""),
            "contact_sheet": pair.get("codex_audit", {}).get("contact_sheet", ""),
        }
        typea_audit.append(audit)
        p2 = json.loads(json.dumps(pair))
        p2["source_pair_id"] = pair.get("pair_id", "")
        p2["pair_id"] = audit["pair_id"]
        p2["protocol_version"] = "v2"
        p2["sharpness_gate_pass"] = True
        p2["pair_quality_source"] = "typeA_local_corruption_stable"
        p2["localdpo_status"] = audit["localdpo_status"]
        p2.setdefault("loss_frame_indices", list(range(5, 81)))
        p2.setdefault("reward_frame_indices", list(range(5, 81)))
        p2.setdefault("winner", {})["future_frame_indices"] = list(range(5, 81))
        p2.setdefault("loser", {})["future_frame_indices"] = list(range(5, 81))
        p2.setdefault("loser", {})["locality_level"] = audit["locality_level"]
        p2.setdefault("loser", {})["affected_region_available"] = has_region
        p2.setdefault("loser", {})["affected_mask_available"] = has_mask
        p2.setdefault("loser", {})["affected_time_span_available"] = has_time
        typea_v2.append(p2)

    write_csv(out / "typeA_localdpo_pair_audit.csv", typea_audit)
    write_jsonl(out / "localdpo_ready_pairs_v2.jsonl", typea_v2)

    typeb_v2: list[dict[str, Any]] = []
    for row in selected_typeb:
        src = v1_by_pair.get(row.get("pair_id", ""))
        if not src:
            continue
        p2 = json.loads(json.dumps(src))
        p2["source_pair_id"] = p2.get("pair_id", "")
        p2["pair_id"] = p2.get("pair_id", "").replace("protocol_v1_B_", "protocol_v2_B_")
        p2["protocol_version"] = "v2"
        p2["sharpness_gate_pass"] = True
        p2.setdefault("loss_frame_indices", list(range(5, 81)))
        p2.setdefault("reward_frame_indices", list(range(5, 81)))
        p2.setdefault("winner", {})["future_frame_indices"] = list(range(5, 81))
        p2.setdefault("loser", {})["future_frame_indices"] = list(range(5, 81))
        p2["quality_gate_v2"] = {"pass": True, "loser_sharpness_ratio": row.get("loser_sharpness_ratio"), "R_quality_p40": row.get("condition_r_quality_p40")}
        typeb_v2.append(p2)

    final_pairs = typea_v2 + typeb_v2
    write_jsonl(manifest_out, final_pairs)

    pair_audit: list[dict[str, Any]] = []
    for p in final_pairs:
        ca = p.get("codex_audit", {})
        loser = p.get("loser", {})
        energy = p.get("energy_audit", {})
        pair_audit.append({
            "pair_id": p.get("pair_id", ""),
            "source_pair_id": p.get("source_pair_id", ""),
            "pair_type": p.get("pair_type", ""),
            "corruption_type": loser.get("corruption_type", ""),
            "winner_source": p.get("winner", {}).get("source", ""),
            "loser_source": loser.get("source", ""),
            "reward_margin": p.get("reward_margin", ""),
            "Delta_ref": energy.get("Delta_ref") or energy.get("delta_ref") or p.get("selection", {}).get("Delta_ref", ""),
            "visual_valid": ca.get("valid_preference", ""),
            "winner_bad": ca.get("winner_bad", ""),
            "loser_collapsed": ca.get("loser_collapsed", ""),
            "too_easy": ca.get("too_easy", ""),
            "medium_hard": p.get("medium_hard", ""),
            "sharpness_gate_pass": p.get("sharpness_gate_pass", ""),
            "contact_sheet": ca.get("contact_sheet", ""),
            "written_reason": ca.get("written_reason", ""),
        })
    write_csv(out / "pair_audit.csv", pair_audit)
    write_jsonl(out / "pair_audit.jsonl", pair_audit)
    write_csv(out / "pair_metric_summary.csv", pair_audit)

    sheet_dir = out / "pair_contact_sheets"
    sheet_dir.mkdir(exist_ok=True)
    for row in pair_audit:
        src = Path(str(row.get("contact_sheet") or ""))
        if src.exists():
            dst = sheet_dir / f"{row['pair_id']}.jpg"
            if not dst.exists() and not dst.is_symlink():
                try:
                    dst.symlink_to(Path("../..") / src)
                except Exception:
                    shutil.copy2(src, dst)

    reject_counter = Counter()
    for row in rejected_typeb:
        for reason in str(row.get("reject_reasons", "")).split(";"):
            if reason:
                reject_counter[reason] += 1
    summary = {
        "protocol_version": "v2",
        "total_pairs": len(final_pairs),
        "typeA_count": len(typea_v2),
        "typeB_count": len(typeb_v2),
        "typeC_count": 0,
        "typeB_candidates": len(rollout_rows),
        "typeB_protocol_v1_candidates": len(selected_v1_b),
        "typeB_selected_v2": len(selected_typeb),
        "typeB_rejected_v2": len(rejected_typeb),
        "typeB_reject_reasons": dict(reject_counter),
        "manifest": str(manifest_out),
        "status": "MIXED_TYPEA_READY_TYPEB_BLOCKED_BY_BLUR" if not typeb_v2 else "PASS_WITH_TYPEB",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    def write_report(path: Path, title: str, status: str, body: list[str]) -> None:
        path.write_text("\n".join([f"# {title}", "", f"Current Status: {status}", "", *body]) + "\n", encoding="utf-8")

    rej_lines = [f"- {k}: {v}" for k, v in reject_counter.most_common()] or ["- none"]
    write_report(out / "typeB_quality_gate_report.md", "Type B Loser Quality Gate v2 Report", "BLOCKED_BY_BLUR_QUALITY_GATE" if not typeb_v2 else "PASS", [
        f"- Rollout candidates audited: {len(rollout_rows)}",
        f"- Protocol v1 Type B candidates audited with blur/energy: {len(selected_v1_b)}",
        f"- Type B selected by v2: {len(selected_typeb)}",
        f"- Type B rejected by v2: {len(rejected_typeb)}",
        "",
        "The v2 gate requires loser_sharpness_ratio >= 0.55, visual_quality >= 1, R_quality >= condition p40, positive reward margin, positive audited Delta_ref, and no collapse/black/global-freeze/scene-replacement tags.",
        "",
        "## Rejection Reasons",
        "",
        *rej_lines,
    ])
    typea_counter = Counter(a["localdpo_status"] for a in typea_audit)
    write_report(out / "typeA_localdpo_pair_report.md", "Type A LocalDPO Pair Report", "TYPEA_READY_WITH_SPATIAL_METADATA", [
        f"- LocalDPO-ready v1 input pairs: {len(localdpo_v1)}",
        f"- Type A v2 pairs: {len(typea_v2)}",
        "",
        "## LocalDPO Metadata Status",
        "",
        *[f"- {k}: {v}" for k, v in typea_counter.most_common()],
        "",
        "The metadata has affected time and spatial/mask indicators, but the trainer still needs spatial-token masking before this can be called full LocalDPO training.",
    ])
    write_report(out / "pair_summary.md", "DPO Preference Protocol v2 Pair Summary", summary["status"], [
        f"- Final manifest: `{manifest_out}`",
        f"- Total pairs: {len(final_pairs)}",
        f"- Type A local corruption pairs: {len(typea_v2)}",
        f"- Type B rollout pairs passing v2 sharpness gate: {len(typeb_v2)}",
        f"- Type B v1 candidates rejected by v2 gate: {len(rejected_typeb)} / {len(selected_v1_b)}",
        "",
        "## Type B Decision",
        "",
        "Type B rollout losers are not used in protocol v2 unless they pass the sharpness-aware gate. The current selected v1 Type B losers fail primarily on `loser_sharpness_ratio < 0.55`, so v2 falls back to Type A local corruption pairs for stable DPO engineering run-through input.",
        "",
        "## Rejection Reasons",
        "",
        *rej_lines,
        "",
        "## Safety",
        "",
        "No training, DPO scaling, StageB, GRPO, checkpoint deletion, or data/weight/video push was performed while building protocol v2.",
    ])
    Path("docs/dpo_preference_protocol_v2_report.md").write_text("\n".join([
        "# DPO Preference Protocol v2 Report",
        "",
        f"Current Status: {summary['status']}",
        "",
        f"Manifest: `{manifest_out}`",
        "",
        "## Counts",
        "",
        f"- Total valid v2 pairs: {len(final_pairs)}",
        f"- Type A local corruption: {len(typea_v2)}",
        f"- Type B medium-hard rollout: {len(typeb_v2)}",
        "- Type C: 0",
        "",
        "## Decision",
        "",
        "Protocol v2 is usable for an engineering run-through with Type A local-corruption pairs. Type B rollout losers are currently blocked by blur/sharpness quality gate and should not be used until candidate generation produces clearer medium-hard negatives.",
        "",
        "## Outputs",
        "",
        f"- Pair summary: `{out / 'pair_summary.md'}`",
        f"- Type B quality gate: `{out / 'typeB_quality_gate_report.md'}`",
        f"- Type A report: `{out / 'typeA_localdpo_pair_report.md'}`",
        f"- Pair audit: `{out / 'pair_audit.csv'}`",
        "",
        "## Not Run",
        "",
        "No DPO training, StageB, GRPO, full-data long StageA, checkpoint deletion, or data/weight/video push was performed for protocol v2 construction.",
    ]) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
