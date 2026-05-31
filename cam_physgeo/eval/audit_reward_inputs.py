from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from cam_physgeo.eval.eval_fast_rollouts import make_sample
from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.utils.io import write_json, write_jsonl


CAMERA_KEYWORDS = (
    "camera",
    "avatar",
    "pose",
    "position",
    "rotation",
    "aim",
    "look_at",
    "intrinsic",
    "extrinsic",
    "projection",
    "matrix",
)
OBJECT_KEYWORDS = ("object", "state", "objects", "collisions", "contact", "target", "trial_complete")


def _sample_dirs(root: Path, limit: int) -> list[Path]:
    dirs = [p for p in sorted(root.iterdir()) if p.is_dir()] if root.exists() else []
    return dirs[:limit] if limit else dirs


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _npy_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    try:
        arr = np.load(path, mmap_mode="r")
        return {"exists": True, "shape": list(arr.shape), "dtype": str(arr.dtype), "size_bytes": path.stat().st_size}
    except Exception as exc:
        return {"exists": True, "error": repr(exc), "size_bytes": path.stat().st_size}


def _video_info(path: Path) -> dict[str, Any]:
    info = {"exists": path.exists(), "path": str(path)}
    if not path.exists():
        return info
    info["size_bytes"] = path.stat().st_size
    try:
        import cv2  # type: ignore

        cap = cv2.VideoCapture(str(path))
        info.update(
            {
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0),
                "fps": float(cap.get(cv2.CAP_PROP_FPS) or 0.0),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0),
            }
        )
        cap.release()
    except Exception as exc:
        info["video_probe_error"] = repr(exc)
    return info


def _walk_hdf5_keys(path: Path, max_keys: int = 4000) -> list[str]:
    keys: list[str] = []
    try:
        import h5py  # type: ignore

        with h5py.File(path, "r") as handle:
            def visitor(name: str, obj: Any) -> None:
                if len(keys) < max_keys:
                    keys.append(name)

            handle.visititems(visitor)
    except Exception:
        return keys
    return keys


def _hdf5_info(meta: dict[str, Any]) -> dict[str, Any]:
    raw_path = str(meta.get("hdf5_path") or "")
    if raw_path.startswith("hdf5://"):
        raw_path = raw_path[len("hdf5://") :].split("::", 1)[0]
    path = Path(raw_path) if raw_path else Path("")
    info: dict[str, Any] = {"path": raw_path or None, "exists": bool(raw_path and path.exists())}
    if not info["exists"]:
        return info
    keys = _walk_hdf5_keys(path)
    lower = [(key, key.lower()) for key in keys]
    info.update(
        {
            "key_count_sampled": len(keys),
            "has_depth_key": any("_depth" in low or low.endswith("depth") or "/depth" in low for _, low in lower),
            "has_id_key": any("_id" in low or "segmentation" in low or low.endswith("/id") for _, low in lower),
            "has_camera_key": any(any(term in low for term in CAMERA_KEYWORDS) for _, low in lower),
            "has_object_state_key": any(any(term in low for term in OBJECT_KEYWORDS) for _, low in lower),
            "camera_like_keys": [key for key, low in lower if any(term in low for term in CAMERA_KEYWORDS)][:40],
            "object_like_keys": [key for key, low in lower if any(term in low for term in OBJECT_KEYWORDS)][:40],
        }
    )
    return info


def _component_table(score: dict[str, Any]) -> dict[str, Any]:
    rows = {}
    for name, comp in score.get("components", {}).items():
        rows[name] = {
            "score": comp.get("penalty" if name == "freeze" else "score"),
            "status": comp.get("status"),
            "backend": comp.get("backend"),
            "confidence": comp.get("confidence"),
            "backend_confidence": comp.get("backend_confidence"),
            "confidence_reason": comp.get("confidence_reason"),
        }
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", required=True)
    ap.add_argument("--rollouts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=3)
    args = ap.parse_args(argv)

    sample_root = Path(args.samples)
    rollout_root = Path(args.rollouts)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for sample_dir in _sample_dirs(sample_root, args.limit):
        meta = _read_json(sample_dir / "metadata.json")
        target = sample_dir / "target.mp4"
        generated = rollout_root / sample_dir.name / "generated.mp4"
        clean_sample = make_sample(sample_dir, target, "clean_gt")
        fast_sample = make_sample(sample_dir, generated, "fast_zero_shot")
        clean_score = score_sample(clean_sample)
        fast_score = score_sample(fast_sample)
        hdf5 = _hdf5_info(meta)
        clean_component_backends = _component_table(clean_score)
        fast_component_backends = _component_table(fast_score)
        rows.append(
            {
                "sample_id": sample_dir.name,
                "metadata": {
                    "template": meta.get("template"),
                    "camera_motion": meta.get("camera_motion"),
                    "use_action": meta.get("use_action"),
                    "hdf5_path": meta.get("hdf5_path"),
                    "camera_metadata_source": meta.get("camera_metadata_source"),
                    "intrinsics_source": meta.get("intrinsics_source"),
                },
                "target_video": _video_info(target),
                "generated_video": _video_info(generated),
                "depth_npy": _npy_info(sample_dir / "depth.npy"),
                "id_mask_npy": _npy_info(sample_dir / "id_mask.npy"),
                "poses_npy": _npy_info(sample_dir / "poses.npy"),
                "intrinsics_npy": _npy_info(sample_dir / "intrinsics.npy"),
                "hdf5": hdf5,
                "clean_reward": {
                    "R_total": clean_score.get("R_total"),
                    "R_total_confidence_weighted": clean_score.get("R_total_confidence_weighted"),
                    "R_total_real_backend_only": clean_score.get("R_total_real_backend_only"),
                    "reward_provisional": clean_score.get("reward_provisional"),
                    "metadata_use": clean_score.get("metadata_use"),
                    "components": clean_component_backends,
                },
                "fast_reward": {
                    "R_total": fast_score.get("R_total"),
                    "R_total_confidence_weighted": fast_score.get("R_total_confidence_weighted"),
                    "R_total_real_backend_only": fast_score.get("R_total_real_backend_only"),
                    "reward_provisional": fast_score.get("reward_provisional"),
                    "metadata_use": fast_score.get("metadata_use"),
                    "components": fast_component_backends,
                },
                "clean_has_real_gt_metadata": bool(
                    (sample_dir / "depth.npy").exists()
                    or (sample_dir / "id_mask.npy").exists()
                    or hdf5.get("has_depth_key")
                    or hdf5.get("has_id_key")
                    or hdf5.get("has_camera_key")
                ),
                "fast_missing_generated_depth_or_id": not (rollout_root / sample_dir.name / "depth.npy").exists()
                and not (rollout_root / sample_dir.name / "id_mask.npy").exists(),
            }
        )

    write_jsonl(rows, out / "reward_input_audit.jsonl")
    write_json({"rows": rows}, out / "summary.json")

    with (out / "backend_table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample_id", "label", "component", "status", "backend", "backend_confidence", "confidence", "reason"])
        for row in rows:
            for label in ["clean_reward", "fast_reward"]:
                for component, comp in row[label]["components"].items():
                    writer.writerow(
                        [
                            row["sample_id"],
                            label,
                            component,
                            comp.get("status"),
                            comp.get("backend"),
                            comp.get("backend_confidence"),
                            comp.get("confidence"),
                            comp.get("confidence_reason"),
                        ]
                    )

    print(json.dumps({"samples": len(rows), "out": str(out)}, indent=2))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
