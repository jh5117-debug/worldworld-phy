from __future__ import annotations

from pathlib import Path
from typing import Any

REQUIRED_PAIR_FIELDS = ["pair_id", "condition", "winner", "loser", "pair_type", "margin", "quality_flags"]


def validate_pair(pair: dict[str, Any], *, check_paths: bool = False) -> list[str]:
    errors = [f"missing:{key}" for key in REQUIRED_PAIR_FIELDS if key not in pair]
    for side in ["winner", "loser"]:
        video = (pair.get(side) or {}).get("video")
        if not video:
            errors.append(f"missing:{side}.video")
        elif check_paths and not Path(str(video)).exists():
            errors.append(f"missing_path:{side}.video")
    condition = pair.get("condition") or {}
    for key in ["image", "prompt", "poses", "intrinsics", "metadata"]:
        value = condition.get(key)
        if not value:
            errors.append(f"missing:condition.{key}")
        elif check_paths and not str(value).startswith("generated://") and not Path(str(value)).exists():
            errors.append(f"missing_path:condition.{key}")
    if condition.get("use_action") is not False:
        errors.append("condition.use_action_not_false")
    return errors


def pair_reward_breakdown(pair: dict[str, Any]) -> dict[str, Any]:
    winner = pair.get("winner") or {}
    loser = pair.get("loser") or {}
    return {
        "winner_reward": winner.get("reward") or winner.get("reward_v5"),
        "loser_reward": loser.get("reward") or loser.get("reward_v5"),
        "margin": pair.get("margin"),
        "pair_type": pair.get("pair_type"),
    }
