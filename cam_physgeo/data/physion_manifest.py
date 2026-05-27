from __future__ import annotations

from collections import Counter
from typing import Iterable


def summarize_manifest(rows: Iterable[dict]) -> dict:
    rows = list(rows)
    return {
        "total": len(rows),
        "by_source": dict(Counter(r.get("source", "missing") for r in rows)),
        "by_template": dict(Counter(r.get("template", "missing") for r in rows)),
        "by_camera_motion": dict(Counter(r.get("camera_motion", "missing") for r in rows)),
        "has_camera_pose": sum(1 for r in rows if r.get("has_camera_pose")),
        "has_intrinsics": sum(1 for r in rows if r.get("has_intrinsics")),
        "has_depth": sum(1 for r in rows if r.get("has_depth")),
        "has_id_mask": sum(1 for r in rows if r.get("has_id_mask")),
        "has_flow": sum(1 for r in rows if r.get("has_flow")),
        "has_normals": sum(1 for r in rows if r.get("has_normals")),
        "has_object_state": sum(1 for r in rows if r.get("has_object_state")),
        "has_reobserve": sum(1 for r in rows if r.get("has_reobserve")),
    }
