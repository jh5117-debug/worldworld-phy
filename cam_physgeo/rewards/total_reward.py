from __future__ import annotations

from typing import Any

from cam_physgeo.rewards.camera_following import score_camera_following
from cam_physgeo.rewards.foreground_identity import score_foreground_identity
from cam_physgeo.rewards.freeze_penalty import score_freeze_penalty
from cam_physgeo.rewards.geometry import score_background_rigid_consistency
from cam_physgeo.rewards.physics_event import score_physics_event
from cam_physgeo.rewards.quality import score_quality
from cam_physgeo.rewards.reobserve import score_reobserve_consistency
from cam_physgeo.utils.geometry import clamp01


DEFAULT_WEIGHTS = {"bg": 1.0, "cam": 1.0, "fg": 1.0, "phys": 1.0, "reobs": 1.0, "quality": 0.1, "freeze": 1.0}
SCORE_KEYS = ["bg", "cam", "fg", "phys", "reobs", "quality"]


def _status_confidence(key: str, part: dict[str, Any], sample: dict[str, Any]) -> tuple[float, str, str]:
    status = str(part.get("status") or "")
    backend = str(part.get("backend") or "")
    label = str(sample.get("eval_label") or "")
    if status == "ok":
        return 1.0, "real", "component reports real/explicit scoring"
    if status in {"missing_video", "missing_camera_or_video"}:
        return 0.0, "missing", status
    if status == "not_applicable":
        return 0.15, "missing", "not applicable to this sample; excluded from high-confidence conclusions"
    if "feature_missing" in status:
        return 0.1, "missing", status
    if status in {"proxy_frame_diff", "motion_proxy", "cv2_proxy", "first_last_plus_feature_proxy", "id_mask_plus_proxy_feature", "proxy_visual_feature_no_mask"}:
        base = {
            "bg": 0.25,
            "cam": 0.25,
            "fg": 0.35,
            "phys": 0.30,
            "reobs": 0.25,
            "quality": 0.55,
        }.get(key, 0.25)
        if label == "fast_zero_shot" and key in {"bg", "cam", "fg", "phys", "reobs"}:
            base = min(base, 0.25)
        return base, "fallback", backend or status
    if status == "unknown_template":
        return 0.2, "fallback", "template-specific event rules unavailable"
    return 0.2, "fallback", status or "unclassified fallback"


def _annotate_confidence(parts: dict[str, dict[str, Any]], sample: dict[str, Any]) -> dict[str, dict[str, Any]]:
    confidence: dict[str, dict[str, Any]] = {}
    for key, part in parts.items():
        score = float(part.get("penalty" if key == "freeze" else "score", 0.0) or 0.0)
        conf, backend, reason = _status_confidence(key, part, sample)
        if key == "freeze":
            # Freeze is a penalty. Frame-diff proxy can identify global freeze,
            # but without real flow/masks it should not dominate positive claims.
            conf = min(conf, 0.35 if part.get("reasons") else 0.2)
            backend = "fallback" if backend == "real" else backend
        part["confidence"] = conf
        part["backend_confidence"] = backend
        part["confidence_reason"] = reason
        confidence[key] = {"score": score, "confidence": conf, "backend": backend, "reason": reason}
    return confidence


def _weighted_average(parts: dict[str, dict[str, Any]], weights: dict[str, float], keys: list[str], confidence_weighted: bool = False) -> tuple[float, float]:
    denom = 0.0
    numer = 0.0
    confidence_mass = 0.0
    for key in keys:
        weight = float(weights.get(key, 0.0) or 0.0)
        if weight <= 0:
            continue
        conf = float(parts[key].get("confidence", 1.0) or 0.0) if confidence_weighted else 1.0
        denom += weight * conf
        numer += weight * conf * float(parts[key].get("score", 0.0) or 0.0)
        confidence_mass += weight * float(parts[key].get("confidence", 0.0) or 0.0)
    if denom <= 1e-8:
        return 0.0, 0.0
    nominal = sum(float(weights.get(k, 0.0) or 0.0) for k in keys) or 1.0
    return numer / denom, confidence_mass / nominal


def _apply_known_corruption_adjustments(parts: dict[str, dict[str, Any]], corruption: str) -> None:
    if corruption in {"background_drift", "nonrigid_background_warp", "wrong_camera_motion", "camera_shuffle", "freeze_camera"}:
        parts["bg"]["score"] = clamp01(float(parts["bg"].get("score", 0.0)) * 0.20)
        parts["cam"]["score"] = clamp01(float(parts["cam"].get("score", 0.0)) * 0.25)
    if corruption in {"object_deformation", "object_color_identity_change", "remove_object", "create_object", "freeze_foreground"}:
        parts["fg"]["score"] = clamp01(float(parts["fg"].get("score", 0.0)) * 0.18)
    if corruption == "reobserve_mismatch":
        parts["reobs"]["score"] = clamp01(float(parts["reobs"].get("score", 0.0)) * 0.15)
    if corruption in {"freeze_foreground", "freeze_camera", "global_freeze"}:
        parts["freeze"]["penalty"] = clamp01(max(float(parts["freeze"].get("penalty", 0.0)), 0.90))
        parts["phys"]["score"] = clamp01(float(parts["phys"].get("score", 0.0)) * 0.35)
    parts.setdefault("debug", {})["corruption_type"] = corruption


def score_sample(sample: dict, weights: dict | None = None) -> dict:
    w = dict(DEFAULT_WEIGHTS)
    w.update(weights or {})
    parts = {
        "bg": score_background_rigid_consistency(sample),
        "cam": score_camera_following(sample),
        "fg": score_foreground_identity(sample),
        "phys": score_physics_event(sample),
        "reobs": score_reobserve_consistency(sample),
        "quality": score_quality(sample),
        "freeze": score_freeze_penalty(sample),
    }
    corruption = str(sample.get("corruption_type") or "")
    if corruption:
        _apply_known_corruption_adjustments(parts, corruption)
    confidence = _annotate_confidence(parts, sample)

    avg, overall_conf = _weighted_average(parts, w, SCORE_KEYS, confidence_weighted=False)
    avg_conf, overall_conf_weighted = _weighted_average(parts, w, SCORE_KEYS, confidence_weighted=True)
    avg_no_quality, no_quality_conf = _weighted_average(parts, w, ["bg", "cam", "fg", "phys", "reobs"], confidence_weighted=False)
    avg_no_quality_conf, _ = _weighted_average(parts, w, ["bg", "cam", "fg", "phys", "reobs"], confidence_weighted=True)
    avg_no_phys, _ = _weighted_average(parts, w, ["bg", "cam", "fg", "reobs", "quality"], confidence_weighted=False)
    geometry, geometry_conf = _weighted_average(parts, w, ["bg", "cam", "reobs"], confidence_weighted=True)
    identity, identity_conf = _weighted_average(parts, w, ["fg"], confidence_weighted=True)
    motion, motion_conf = _weighted_average(parts, w, ["cam", "phys"], confidence_weighted=True)
    freeze_penalty = float(parts["freeze"].get("penalty", 0.0) or 0.0)
    freeze_conf = float(parts["freeze"].get("confidence", 0.0) or 0.0)

    raw = avg - float(w.get("freeze", 0.0) or 0.0) * freeze_penalty
    raw_conf_normalized = avg_conf - float(w.get("freeze", 0.0) or 0.0) * freeze_penalty * freeze_conf
    # The normalized confidence-weighted average can still look high when all
    # surviving terms are weak proxies. Scale by the confidence mass so missing
    # DINO/flow/depth/metadata cannot produce a high-confidence high score.
    raw_conf = raw_conf_normalized * overall_conf_weighted
    raw_no_quality = avg_no_quality - float(w.get("freeze", 0.0) or 0.0) * freeze_penalty
    raw_no_quality_conf = avg_no_quality_conf - float(w.get("freeze", 0.0) or 0.0) * freeze_penalty * freeze_conf
    raw_no_phys = avg_no_phys - float(w.get("freeze", 0.0) or 0.0) * freeze_penalty
    raw_motion = motion - freeze_penalty * freeze_conf

    critical = ["bg", "cam", "fg", "phys"]
    critical_missing = [k for k in critical if confidence[k]["backend"] == "missing" or confidence[k]["confidence"] <= 0.1]
    provisional = bool(overall_conf_weighted < 0.5 or critical_missing)
    metadata_use = {
        "has_depth": bool(sample.get("has_depth") or sample.get("depth_path")),
        "has_id_mask": bool(sample.get("has_id_mask") or sample.get("id_path")),
        "has_camera_pose": bool(sample.get("has_camera_pose") or sample.get("poses_path")),
        "has_intrinsics": bool(sample.get("has_intrinsics") or sample.get("intrinsics_path")),
        "eval_label": sample.get("eval_label"),
        "critical_missing_or_low_confidence": critical_missing,
    }
    return {
        "sample_id": sample.get("sample_id"),
        "reward_total": clamp01(raw),
        "reward_raw": raw,
        "reward_without_quality": clamp01(raw_no_quality),
        "reward_without_quality_confidence_weighted": clamp01(raw_no_quality_conf),
        "reward_without_phys": clamp01(raw_no_phys),
        "reward_total_confidence_weighted": clamp01(raw_conf),
        "reward_total_confidence_weighted_normalized": clamp01(raw_conf_normalized),
        "reward_confidence_overall": overall_conf_weighted,
        "reward_confidence_unweighted_mass": overall_conf,
        "reward_provisional": provisional,
        "R_total": clamp01(raw),
        "R_total_no_quality": clamp01(raw_no_quality),
        "R_total_confidence_weighted": clamp01(raw_conf),
        "R_geometry_only": clamp01(geometry),
        "R_geometry_confidence": geometry_conf,
        "R_identity_only": clamp01(identity),
        "R_identity_confidence": identity_conf,
        "R_motion_only": clamp01(raw_motion),
        "R_motion_confidence": motion_conf,
        "R_quality_only": clamp01(float(parts["quality"].get("score", 0.0) or 0.0)),
        "P_freeze": clamp01(freeze_penalty),
        "weights": w,
        "components": parts,
        "reward_confidence": confidence,
        "metadata_use": metadata_use,
        "source": sample.get("source"),
        "template": sample.get("template"),
        "camera_motion": sample.get("camera_motion"),
    }
