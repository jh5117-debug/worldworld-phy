from __future__ import annotations

from pathlib import Path
from typing import Any


DEPTH_TERMS = ("_depth", "/depth", "depth")
ID_TERMS = ("_id", "segmentation", "/id")
CAMERA_TERMS = ("camera", "avatar", "pose", "position", "rotation", "aim", "look_at", "projection", "matrix", "intrinsic", "extrinsic")
OBJECT_TERMS = ("object", "objects", "state", "collisions", "contact", "target", "trial_complete")


def resolve_hdf5_path(value: str | None) -> Path | None:
    if not value:
        return None
    raw = str(value)
    if raw.startswith("hdf5://"):
        raw = raw[len("hdf5://") :].split("::", 1)[0]
    path = Path(raw)
    return path if path.exists() else None


def hdf5_key_summary(path: str | Path | None, max_keys: int = 5000) -> dict[str, Any]:
    resolved = resolve_hdf5_path(str(path) if path else None)
    info: dict[str, Any] = {"path": str(path) if path else None, "exists": bool(resolved)}
    if not resolved:
        return info
    keys: list[str] = []
    try:
        import h5py  # type: ignore

        with h5py.File(resolved, "r") as handle:
            def visitor(name: str, obj: Any) -> None:
                if len(keys) < max_keys:
                    keys.append(name)

            handle.visititems(visitor)
    except Exception as exc:
        info["error"] = repr(exc)
        return info
    lower = [(key, key.lower()) for key in keys]
    info.update(
        {
            "key_count_sampled": len(keys),
            "has_depth_key": any(any(term in low for term in DEPTH_TERMS) for _, low in lower),
            "has_id_key": any(any(term in low for term in ID_TERMS) for _, low in lower),
            "has_camera_key": any(any(term in low for term in CAMERA_TERMS) for _, low in lower),
            "has_object_state_key": any(any(term in low for term in OBJECT_TERMS) for _, low in lower),
            "depth_like_keys": [key for key, low in lower if any(term in low for term in DEPTH_TERMS)][:30],
            "id_like_keys": [key for key, low in lower if any(term in low for term in ID_TERMS)][:30],
            "camera_like_keys": [key for key, low in lower if any(term in low for term in CAMERA_TERMS)][:40],
            "object_like_keys": [key for key, low in lower if any(term in low for term in OBJECT_TERMS)][:40],
        }
    )
    return info


def clean_gt_backend_coverage(sample: dict[str, Any]) -> dict[str, bool]:
    if str(sample.get("eval_label") or "") != "clean_gt":
        return {}
    supplied = sample.get("clean_gt_backend_coverage")
    if isinstance(supplied, dict):
        return {str(k): bool(v) for k, v in supplied.items()}
    hdf5 = hdf5_key_summary(sample.get("hdf5_path"))
    return {
        "depth": bool(sample.get("has_depth") or sample.get("depth_path") or hdf5.get("has_depth_key")),
        "id_mask": bool(sample.get("has_id_mask") or sample.get("id_path") or hdf5.get("has_id_key")),
        "camera": bool(sample.get("has_camera_pose") or sample.get("poses_path") or hdf5.get("has_camera_key")),
        "intrinsics": bool(sample.get("has_intrinsics") or sample.get("intrinsics_path") or hdf5.get("has_camera_key")),
        "object_state": bool(sample.get("has_object_state") or hdf5.get("has_object_state_key")),
    }


def clean_has(sample: dict[str, Any], *keys: str) -> bool:
    coverage = clean_gt_backend_coverage(sample)
    return bool(coverage) and all(bool(coverage.get(key)) for key in keys)
