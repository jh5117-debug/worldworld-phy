"""LoRA scope candidates for DPO training sanity v12."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

SCOPE_CANDIDATES: dict[str, dict[str, Any]] = {
    "L0_camera_r4": {
        "rank": 4,
        "alpha": 4,
        "target_groups": ["camera_conditioning"],
        "required_groups": ["camera_conditioning"],
        "block_start": 0,
        "block_end": None,
        "include_patterns": [],
        "exclude_patterns": [],
        "description": "camera conditioning only, rank 4",
        "memory_risk": "low",
    },
    "L1_camera_r8": {
        "rank": 8,
        "alpha": 8,
        "target_groups": ["camera_conditioning"],
        "required_groups": ["camera_conditioning"],
        "block_start": 0,
        "block_end": None,
        "include_patterns": [],
        "exclude_patterns": [],
        "description": "camera conditioning only, rank 8",
        "memory_risk": "low_medium",
    },
    "L2_camera_temporal_r4": {
        "rank": 4,
        "alpha": 4,
        "target_groups": ["camera_conditioning", "self_attention"],
        "required_groups": ["camera_conditioning", "self_attention"],
        "block_start": 0,
        "block_end": 3,
        "include_patterns": [],
        "exclude_patterns": ["ffn", "mlp", "feed_forward"],
        "description": "camera conditioning plus limited early self/temporal attention, rank 4, max 4 blocks",
        "memory_risk": "medium",
    },
    "L3_camera_cross_r4": {
        "rank": 4,
        "alpha": 4,
        "target_groups": ["camera_conditioning", "cross_attention"],
        "required_groups": ["camera_conditioning", "cross_attention"],
        "block_start": 0,
        "block_end": 3,
        "include_patterns": [],
        "exclude_patterns": ["ffn", "mlp", "feed_forward"],
        "description": "camera conditioning plus limited early cross attention, rank 4, max 4 blocks",
        "memory_risk": "medium_high",
    },
    "L4_adaln_camera_mod_r4": {
        "rank": 4,
        "alpha": 4,
        "target_groups": ["camera_conditioning"],
        "required_groups": [],
        "block_start": 0,
        "block_end": None,
        "include_patterns": ["ada", "mod", "scale", "shift", "cam"],
        "exclude_patterns": ["ffn", "mlp", "feed_forward"],
        "description": "camera / pose-conditioned AdaLN or scale-shift modulation if modules exist",
        "memory_risk": "low_unknown",
    },
}


def apply_scope_to_cfg(cfg: dict[str, Any], scope: str) -> dict[str, Any]:
    if scope not in SCOPE_CANDIDATES:
        raise KeyError(f"unknown v12 LoRA scope: {scope}")
    spec = SCOPE_CANDIDATES[scope]
    out = deepcopy(cfg)
    out["student_tuning_mode"] = "lora"
    out["student_lora_rank"] = int(spec["rank"])
    out["student_lora_alpha"] = int(spec["alpha"])
    out["student_lora_dropout"] = float(out.get("student_lora_dropout", 0.0))
    out["student_lora_target_groups"] = list(spec["target_groups"])
    out["student_lora_required_groups"] = list(spec["required_groups"])
    out["student_lora_block_start"] = int(spec["block_start"])
    out["student_lora_block_end"] = spec["block_end"]
    out["student_lora_include_patterns"] = list(spec["include_patterns"])
    out["student_lora_exclude_patterns"] = list(spec["exclude_patterns"])
    out["student_lora_merge_mode"] = str(out.get("student_lora_merge_mode", "out_of_place"))
    return out


def scope_summary_rows() -> list[dict[str, Any]]:
    rows = []
    for name, spec in SCOPE_CANDIDATES.items():
        rows.append({"scope": name, **spec})
    return rows
