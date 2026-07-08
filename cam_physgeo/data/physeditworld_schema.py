from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = [
    "sample_id",
    "replay_group_id",
    "scene_id",
    "initial_state_id",
    "action_trace_id",
    "camera_policy_id",
    "gravity_value",
    "gravity_label",
    "video_path",
    "action_trace_path",
    "camera_trajectory_path",
    "intrinsics_path",
    "prompt",
    "num_frames",
    "fps",
    "height",
    "width",
    "duration_sec",
    "source_root",
    "status",
    "error_reason",
]

OPTIONAL_FIELDS = [
    "prefix_video_path",
    "image_path",
    "engine_state_path",
    "semantic_annotation_path",
    "depth_path",
    "normal_path",
]

GRAVITY_ALIASES = {
    "0.25": "0.25g",
    "0.5": "0.5g",
    "1": "1.0g",
    "1.0": "1.0g",
    "2": "2.0g",
    "4": "4.0g",
}


def stable_id(*parts: object, prefix: str = "pew") -> str:
    text = "|".join(str(p) for p in parts if p is not None)
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def normalize_gravity_label(value: object | None, label: object | None = None) -> tuple[float | None, str | None]:
    if value is None and label is None:
        return None, None
    raw = str(value if value is not None else label).strip().lower().replace("gravity", "").replace(":", "")
    raw = raw.replace("g", "").strip(" _=-")
    try:
        val = float(raw)
    except ValueError:
        val = None
    if val is None:
        lab = str(label or value).strip()
    else:
        lab = GRAVITY_ALIASES.get(f"{val:g}", f"{val:g}g")
    return val, lab


def build_replay_group_id(sample: dict[str, Any]) -> str:
    explicit = sample.get("replay_group_id")
    if explicit:
        return str(explicit)
    return stable_id(
        sample.get("scene_id", "unknown_scene"),
        sample.get("initial_state_id", "unknown_state"),
        sample.get("action_trace_id", "unknown_action"),
        sample.get("camera_policy_id", "unknown_camera"),
        prefix="replay",
    )


def default_prompt(gravity_label: str | None) -> str:
    gravity = gravity_label or "unknown gravity"
    return (
        "A first-person interactive world rollout.\n"
        "The character follows the given action sequence and camera trajectory.\n"
        f"The scene is rendered under gravity: {gravity}."
    )


def normalize_sample(sample: dict[str, Any]) -> dict[str, Any]:
    out = dict(sample)
    g_value, g_label = normalize_gravity_label(out.get("gravity_value"), out.get("gravity_label"))
    out["gravity_value"] = g_value
    out["gravity_label"] = g_label
    out["replay_group_id"] = build_replay_group_id(out)
    if not out.get("sample_id"):
        out["sample_id"] = stable_id(out.get("video_path"), out.get("gravity_label"), prefix="physedit")
    if not out.get("prompt"):
        out["prompt"] = default_prompt(g_label)
    for key in OPTIONAL_FIELDS:
        out.setdefault(key, None)
    out.setdefault("status", "UNKNOWN")
    out.setdefault("error_reason", "")
    return out


def _path_missing(value: object | None) -> bool:
    if not value:
        return True
    text = str(value)
    if text.startswith(("generated://", "missing://", "unknown://")):
        return False
    return not Path(text).exists()


def validate_sample(sample: dict[str, Any], check_paths: bool = True) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_FIELDS:
        if key not in sample:
            errors.append(f"missing:{key}")
    if sample.get("gravity_value") is None or sample.get("gravity_label") is None:
        errors.append("missing:gravity")
    if not sample.get("prompt"):
        errors.append("missing:prompt")
    if check_paths:
        for key in ["video_path", "action_trace_path", "camera_trajectory_path", "intrinsics_path"]:
            if _path_missing(sample.get(key)):
                errors.append(f"missing_path:{key}")
    if sample.get("num_frames") is not None:
        try:
            if int(sample["num_frames"]) <= 0:
                errors.append("invalid:num_frames")
        except Exception:
            errors.append("invalid:num_frames")
    return errors


def status_from_errors(errors: list[str]) -> tuple[str, str]:
    if not errors:
        return "OK", ""
    if any(e.startswith("missing_path:video_path") for e in errors):
        return "MISSING_VIDEO", ";".join(errors)
    if any("gravity" in e for e in errors):
        return "MISSING_GRAVITY", ";".join(errors)
    if any("action_trace" in e for e in errors):
        return "MISSING_ACTION", ";".join(errors)
    if any("camera_trajectory" in e or "intrinsics" in e for e in errors):
        return "MISSING_CAMERA", ";".join(errors)
    return "SCHEMA_INCOMPLETE", ";".join(errors)
