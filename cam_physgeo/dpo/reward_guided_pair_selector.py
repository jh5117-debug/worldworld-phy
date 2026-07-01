"""Reward-guided preference-pair selection helpers for V2V-5 DPO.

The module is deliberately lightweight: it contains deterministic scoring and
hardness/alignment checks, while video generation and expensive metrics live in
experiment scripts.  Backend provenance is carried through every reward vector so
reports can distinguish real metrics from proxy/diagnostic values.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, Mapping, MutableMapping, Sequence


RewardVector = Mapping[str, float | int | str | None]


@dataclass(frozen=True)
class RewardWeights:
    w_bg: float = 0.16
    w_cam: float = 0.16
    w_fg: float = 0.16
    w_phys: float = 0.18
    w_reobs: float = 0.14
    w_quality: float = 0.20
    w_freeze: float = 0.12
    w_blur: float = 0.18

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


DEFAULT_REWARD_WEIGHTS = RewardWeights()

SUBREWARD_KEYS = ("R_bg", "R_cam", "R_fg", "R_phys", "R_reobs", "R_quality")
PENALTY_KEYS = ("P_freeze", "P_blur")

FAILURE_ALIGNMENT_KEYS: Dict[str, tuple[str, ...]] = {
    "background_drift": ("margin_bg", "margin_cam"),
    "background_drift_local": ("margin_bg", "margin_cam"),
    "wrong_camera": ("margin_cam",),
    "wrong_camera_motion": ("margin_cam",),
    "wrong_camera_motion_local": ("margin_cam",),
    "object_deformation": ("margin_fg",),
    "object_deformation_local": ("margin_fg",),
    "object_identity_change": ("margin_fg",),
    "object_identity_change_local": ("margin_fg",),
    "identity_instability": ("margin_fg",),
    "reobserve_mismatch": ("margin_reobs",),
    "reobserve_mismatch_local": ("margin_reobs",),
    "physical_event_failure": ("margin_phys",),
    "physical_event_local_failure": ("margin_phys",),
    "weak_physical_event": ("margin_phys",),
    "partial_freeze": ("margin_freeze",),
    "extra_fragment": ("margin_fg", "margin_quality"),
    "hallucinated_fragment": ("margin_fg", "margin_quality"),
}


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def reward_backend(vector: RewardVector | None) -> str:
    if not vector:
        return "blocked"
    backend = vector.get("backend")
    return str(backend) if backend else "proxy"


def compute_total_reward(
    vector: RewardVector | None,
    weights: RewardWeights = DEFAULT_REWARD_WEIGHTS,
    *,
    prefer_existing_total: bool = False,
) -> float:
    """Compute the Cam-PhysGeo total reward from subrewards and penalties."""

    if not vector:
        return 0.0
    if prefer_existing_total and vector.get("R_total") is not None:
        return _as_float(vector.get("R_total"))
    return (
        weights.w_bg * _as_float(vector.get("R_bg"))
        + weights.w_cam * _as_float(vector.get("R_cam"))
        + weights.w_fg * _as_float(vector.get("R_fg"))
        + weights.w_phys * _as_float(vector.get("R_phys"))
        + weights.w_reobs * _as_float(vector.get("R_reobs"))
        + weights.w_quality * _as_float(vector.get("R_quality"))
        - weights.w_freeze * _as_float(vector.get("P_freeze"))
        - weights.w_blur * _as_float(vector.get("P_blur"))
    )


def normalized_reward_vector(
    vector: RewardVector | None,
    weights: RewardWeights = DEFAULT_REWARD_WEIGHTS,
    *,
    backend: str | None = None,
) -> Dict[str, float | str]:
    """Return a complete reward vector with an explicit computed R_total."""

    src: Mapping[str, object] = vector or {}
    out: Dict[str, float | str] = {k: _as_float(src.get(k), 1.0 if k.startswith("R_") else 0.0) for k in SUBREWARD_KEYS}
    for k in PENALTY_KEYS:
        out[k] = _as_float(src.get(k), 0.0)
    out["R_total"] = compute_total_reward(out, weights)
    out["backend"] = backend or reward_backend(src)
    confidence = src.get("confidence") if src else None
    out["confidence"] = _as_float(confidence, 0.5)
    return out


def subreward_margins(winner: RewardVector | None, loser: RewardVector | None) -> Dict[str, float]:
    """Compute winner-minus-loser reward and penalty margins."""

    winner = winner or {}
    loser = loser or {}
    margins = {
        "margin_bg": _as_float(winner.get("R_bg")) - _as_float(loser.get("R_bg")),
        "margin_cam": _as_float(winner.get("R_cam")) - _as_float(loser.get("R_cam")),
        "margin_fg": _as_float(winner.get("R_fg")) - _as_float(loser.get("R_fg")),
        "margin_phys": _as_float(winner.get("R_phys")) - _as_float(loser.get("R_phys")),
        "margin_reobs": _as_float(winner.get("R_reobs")) - _as_float(loser.get("R_reobs")),
        "margin_quality": _as_float(winner.get("R_quality")) - _as_float(loser.get("R_quality")),
        # Positive means the loser freezes/blurs more than the winner.
        "margin_freeze": _as_float(loser.get("P_freeze")) - _as_float(winner.get("P_freeze")),
        "margin_blur": _as_float(loser.get("P_blur")) - _as_float(winner.get("P_blur")),
    }
    return margins


def expected_alignment_keys(failure_type: str | None) -> tuple[str, ...]:
    if not failure_type:
        return ()
    ft = failure_type.lower()
    if ft in FAILURE_ALIGNMENT_KEYS:
        return FAILURE_ALIGNMENT_KEYS[ft]
    for key, expected in FAILURE_ALIGNMENT_KEYS.items():
        if key in ft:
            return expected
    return ()


def alignment_decision(
    failure_type: str | None,
    margins: Mapping[str, float],
    *,
    min_margin: float = 0.05,
) -> Dict[str, object]:
    expected = expected_alignment_keys(failure_type)
    if not expected:
        return {
            "aligned": False,
            "status": "UNKNOWN_FAILURE_TYPE",
            "expected_keys": [],
            "observed_max": 0.0,
        }
    observed = max((_as_float(margins.get(k)) for k in expected), default=0.0)
    aligned = observed > (min_margin + 1e-8)
    return {
        "aligned": aligned,
        "status": "PASS" if aligned else "REWARD_FAILURE_MISMATCH",
        "expected_keys": list(expected),
        "observed_max": observed,
    }


def reward_margin(
    winner: RewardVector | None,
    loser: RewardVector | None,
    weights: RewardWeights = DEFAULT_REWARD_WEIGHTS,
) -> float:
    return compute_total_reward(winner, weights) - compute_total_reward(loser, weights)


def selector_spec(weights: RewardWeights = DEFAULT_REWARD_WEIGHTS) -> Dict[str, object]:
    return {
        "name": "Cam-PhysGeo reward-guided selector v4",
        "reward_formula": "w_bg*R_bg + w_cam*R_cam + w_fg*R_fg + w_phys*R_phys + w_reobs*R_reobs + w_quality*R_quality - w_freeze*P_freeze - w_blur*P_blur",
        "weights": weights.to_dict(),
        "subreward_keys": list(SUBREWARD_KEYS),
        "penalty_keys": list(PENALTY_KEYS),
        "backend_policy": "Every reward vector must label backend as real, proxy, diagnostic, or blocked.",
        "typeb_policy": "TypeB rollout losers are not admitted unless they pass sharpness, quality, reward, and Codex visual gates.",
    }
