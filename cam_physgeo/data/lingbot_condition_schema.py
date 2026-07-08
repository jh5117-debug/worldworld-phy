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
    target_indices = meta.get("target_frame_indices")
    if not isinstance(target_indices, list) or not target_indices:
        errors.append("metadata_missing:target_frame_indices")
    prediction_start = meta.get("prediction_start_frame")
    if isinstance(indices, list) and isinstance(target_indices, list):
        if not isinstance(prediction_start, int):
            errors.append("metadata_missing:prediction_start_frame")
        elif target_indices != indices[prediction_start:]:
            errors.append("metadata_invalid:target_frame_indices")
    prefix_indices = meta.get("prefix_frame_indices")
    if not isinstance(prefix_indices, list) or not prefix_indices:
        errors.append("metadata_missing:prefix_frame_indices")
    prefix_sampling = meta.get("prefix_sampling")
    if not isinstance(prefix_sampling, dict):
        errors.append("metadata_missing:prefix_sampling")
    elif prefix_sampling.get("status") not in {"SAMPLED_PREFIX_VIDEO", "PROVIDED_PREFIX_VIDEO", "PROVIDED_IMAGE"}:
        errors.append("metadata_invalid:prefix_sampling_status")
    alignment = meta.get("sampling_alignment")
    if not isinstance(alignment, dict):
        errors.append("metadata_missing:sampling_alignment")
    else:
        if alignment.get("same_indices_for_action_camera") is not True:
            errors.append("metadata_invalid:sampling_alignment_action_camera")
        if alignment.get("target_video_indices_are_suffix_of_action_camera") is not True:
            errors.append("metadata_invalid:sampling_alignment_target_suffix")
    for key in ["video_sampling", "action_sampling", "camera_sampling"]:
        sampling = meta.get(key)
        if not isinstance(sampling, dict):
            errors.append(f"metadata_missing:{key}")
            continue
        allowed_status = {"SAMPLED"} if key == "video_sampling" else {"SAMPLED", "ALREADY_SAMPLED"}
        if sampling.get("status") not in allowed_status:
            errors.append(f"metadata_invalid:{key}_status")
        output_len = sampling.get("output_frame_count") if key == "video_sampling" else sampling.get("output_length")
        expected_len = len(target_indices) if key == "video_sampling" and isinstance(target_indices, list) else len(indices) if isinstance(indices, list) else None
        if expected_len is not None and output_len != expected_len:
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
