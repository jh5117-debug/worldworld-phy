"""Hardness calibration helpers for reward-guided V2V-5 preference pairs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Mapping


@dataclass(frozen=True)
class HardnessThresholds:
    min_visual_quality: float = 1.0
    min_sharpness_ratio: float = 0.65
    min_reward_margin: float = 0.12
    max_reward_margin: float = 0.40
    min_alignment_margin: float = 0.05
    min_lpips_future: float = 0.04
    max_lpips_future: float = 0.25
    min_ssim_future: float = 0.35

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


DEFAULT_HARDNESS_THRESHOLDS = HardnessThresholds()


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def classify_hardness(
    *,
    reward_margin: float,
    sharpness_ratio: float,
    visual_quality: float,
    alignment_pass: bool,
    winner_bad: bool = False,
    loser_collapsed: bool = False,
    main_failure: str | None = None,
    lpips_future: float | None = None,
    ssim_future: float | None = None,
    thresholds: HardnessThresholds = DEFAULT_HARDNESS_THRESHOLDS,
) -> Dict[str, object]:
    """Classify a candidate as too subtle, medium-hard, or too degraded."""

    reasons: list[str] = []
    if winner_bad:
        reasons.append("winner_bad")
    if loser_collapsed:
        reasons.append("loser_collapsed")
    if visual_quality < thresholds.min_visual_quality:
        reasons.append("visual_quality_lt_min")
    if sharpness_ratio < thresholds.min_sharpness_ratio:
        reasons.append("sharpness_ratio_lt_min")
    if main_failure and main_failure.lower() == "blur":
        reasons.append("blur_is_main_failure")
    if ssim_future is not None and ssim_future < thresholds.min_ssim_future:
        reasons.append("ssim_future_too_low")

    degraded = bool(reasons)
    if degraded:
        return {
            "hardness": "TOO_DEGRADED",
            "medium_hard": False,
            "too_subtle": False,
            "too_degraded": True,
            "reasons": reasons,
        }

    subtle_reasons: list[str] = []
    if reward_margin < thresholds.min_reward_margin:
        subtle_reasons.append("reward_margin_lt_min")
    if not alignment_pass:
        subtle_reasons.append("subreward_alignment_fail")
    if lpips_future is not None and lpips_future < thresholds.min_lpips_future:
        subtle_reasons.append("lpips_future_too_low")
    if subtle_reasons:
        return {
            "hardness": "TOO_SUBTLE",
            "medium_hard": False,
            "too_subtle": True,
            "too_degraded": False,
            "reasons": subtle_reasons,
        }

    if reward_margin > thresholds.max_reward_margin:
        return {
            "hardness": "TOO_DEGRADED",
            "medium_hard": False,
            "too_subtle": False,
            "too_degraded": True,
            "reasons": ["reward_margin_gt_max"],
        }
    if lpips_future is not None and lpips_future > thresholds.max_lpips_future:
        return {
            "hardness": "TOO_DEGRADED",
            "medium_hard": False,
            "too_subtle": False,
            "too_degraded": True,
            "reasons": ["lpips_future_too_high"],
        }

    return {
        "hardness": "MEDIUM_HARD",
        "medium_hard": True,
        "too_subtle": False,
        "too_degraded": False,
        "reasons": ["passes_medium_hard_gate"],
    }


def summarize_hardness(rows: list[Mapping[str, object]]) -> Dict[str, int]:
    summary = {"MEDIUM_HARD": 0, "TOO_SUBTLE": 0, "TOO_DEGRADED": 0, "OTHER": 0}
    for row in rows:
        key = str(row.get("hardness", "OTHER"))
        summary[key if key in summary else "OTHER"] += 1
    return summary
