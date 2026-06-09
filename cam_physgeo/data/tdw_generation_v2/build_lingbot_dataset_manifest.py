from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np


SAMPLE_RE = re.compile(
    r"^tdw_v\d+_(?P<index>\d{5})_(?P<template>drop|collision|roll|containment)_(?P<camera>.+)_seed(?P<seed>\d+)_0000$"
)


def _bool_arg(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in {"1", "true", "yes", "y", "on"}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_validation_rows(root: Path) -> dict[str, dict[str, Any]]:
    reports = root.parent / "reports"
    rows: dict[str, dict[str, Any]] = {}
    if not reports.exists():
        return rows
    for path in sorted(reports.glob("validation_*.json")):
        payload = _read_json(path)
        for row in payload.get("rows") or []:
            hdf5 = str(row.get("path") or "")
            stem = Path(hdf5).parent.name if hdf5 else ""
            if stem:
                rows[stem] = row
    return rows


def _sample_id_parts(sample_id: str) -> dict[str, Any]:
    match = SAMPLE_RE.match(sample_id)
    if not match:
        return {}
    return {
        "index": int(match.group("index")),
        "template": match.group("template"),
        "camera_variant": match.group("camera"),
        "seed": int(match.group("seed")),
    }


def _action_norm(path: Path) -> float | None:
    if not path.exists():
        return None
    try:
        arr = np.load(path)
        return float(np.linalg.norm(arr))
    except Exception:
        return None


def build_manifest(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root = Path(args.root)
    validation_rows = _load_validation_rows(root)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for sample_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        sample_id = sample_dir.name
        parts = _sample_id_parts(sample_id)
        stem = sample_id
        if stem.startswith("tdw_v3_"):
            stem = stem[len("tdw_v3_") :]
        if stem.endswith("_0000"):
            stem = stem[: -len("_0000")]
        validation = validation_rows.get(stem, {})
        metadata_path = sample_dir / "metadata.json"
        metadata = _read_json(metadata_path)
        row = {
            "sample_id": sample_id,
            "sample_dir": str(sample_dir),
            "image_path": str(sample_dir / "image.jpg"),
            "target_video_path": str(sample_dir / "target.mp4"),
            "poses_path": str(sample_dir / "poses.npy"),
            "intrinsics_path": str(sample_dir / "intrinsics.npy"),
            "action_path": str(sample_dir / "action.npy"),
            "prompt_path": str(sample_dir / "prompt.txt"),
            "metadata_path": str(metadata_path),
            "depth_path": str(sample_dir / "depth.npy") if (sample_dir / "depth.npy").exists() else None,
            "id_mask_path": str(sample_dir / "id_mask.npy") if (sample_dir / "id_mask.npy").exists() else None,
            "template": parts.get("template") or metadata.get("template") or validation.get("template"),
            "camera_variant": parts.get("camera_variant") or metadata.get("camera_variant") or validation.get("camera_variant"),
            "seed": parts.get("seed") or metadata.get("seed") or validation.get("seed"),
            "source_hdf5_path": validation.get("path"),
            "target_visible_ratio": validation.get("target_visible_ratio"),
            "camera_path_length": validation.get("camera_path_length"),
            "background_motion_proxy": validation.get("background_motion_proxy"),
            "scene_hash": validation.get("scene_hash"),
            "prompt_hash": validation.get("prompt_hash"),
            "use_action": metadata.get("use_action"),
            "human_approved": _bool_arg(args.human_approved),
            "source_tag": args.source_tag,
            "split": None,
            "action_norm": _action_norm(sample_dir / "action.npy"),
        }
        missing: list[str] = []
        checks = {
            "target.mp4": args.require_target_mp4 and not Path(row["target_video_path"]).exists(),
            "poses.npy": args.require_camera and not Path(row["poses_path"]).exists(),
            "intrinsics.npy": args.require_camera and not Path(row["intrinsics_path"]).exists(),
            "prompt.txt": args.require_prompt and not Path(row["prompt_path"]).exists(),
        }
        for name, failed in checks.items():
            if failed:
                missing.append(name)
        if args.require_use_action_false and row["use_action"] is not False:
            missing.append("metadata.use_action_false")
        row["missing_required"] = missing
        if missing:
            errors.append({"sample_id": sample_id, "missing_required": missing})
        rows.append(row)
    return rows, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--human_approved", default="false")
    parser.add_argument("--source_tag", default="")
    parser.add_argument("--require_target_mp4", action="store_true")
    parser.add_argument("--require_camera", action="store_true")
    parser.add_argument("--require_prompt", action="store_true")
    parser.add_argument("--require_use_action_false", action="store_true")
    args = parser.parse_args()

    rows, errors = build_manifest(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {
        "root": args.root,
        "out": args.out,
        "count": len(rows),
        "error_count": len(errors),
        "errors": errors[:20],
        "human_approved": _bool_arg(args.human_approved),
        "source_tag": args.source_tag,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
