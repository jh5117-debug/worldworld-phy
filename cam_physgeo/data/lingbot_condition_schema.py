from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = ["target.mp4", "action.npy", "poses.npy", "intrinsics.npy", "prompt.txt", "gravity.json", "metadata.json"]
PREFIX_CHOICES = ["prefix.mp4", "image.jpg"]


def validate_condition_dir(path: str | Path) -> list[str]:
    root = Path(path)
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (root / name).exists():
            errors.append(f"missing:{name}")
    if not any((root / name).exists() for name in PREFIX_CHOICES):
        errors.append("missing:prefix_or_image")
    try:
        meta = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"metadata_read_error:{exc}")
        return errors
    for key in ["use_action", "use_camera", "use_intrinsics"]:
        if meta.get(key) is not True:
            errors.append(f"metadata_false:{key}")
    if meta.get("gravity_condition_type") != "prompt_only":
        errors.append("metadata_invalid:gravity_condition_type")
    if meta.get("gravity_value") is None:
        errors.append("metadata_missing:gravity_value")
    indices = meta.get("frame_indices")
    if not isinstance(indices, list) or not indices:
        errors.append("metadata_missing:frame_indices")
    alignment = meta.get("sampling_alignment")
    if not isinstance(alignment, dict):
        errors.append("metadata_missing:sampling_alignment")
    elif alignment.get("same_indices_for_action_camera_video") is not True:
        errors.append("metadata_invalid:sampling_alignment")
    for key in ["action_sampling", "camera_sampling"]:
        sampling = meta.get(key)
        if not isinstance(sampling, dict):
            errors.append(f"metadata_missing:{key}")
            continue
        if sampling.get("status") not in {"SAMPLED", "ALREADY_SAMPLED"}:
            errors.append(f"metadata_invalid:{key}_status")
        if isinstance(indices, list) and sampling.get("output_length") != len(indices):
            errors.append(f"metadata_invalid:{key}_length")
    scale = meta.get("intrinsics_scale")
    if not isinstance(scale, dict):
        errors.append("metadata_missing:intrinsics_scale")
    else:
        if scale.get("status") == "OK":
            if scale.get("scale_x") is None or scale.get("scale_y") is None:
                errors.append("metadata_invalid:intrinsics_scale")
        elif scale.get("status") not in {"SOURCE_SIZE_MISSING", "TARGET_SIZE_INVALID"}:
            errors.append("metadata_invalid:intrinsics_scale_status")
    return errors


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
