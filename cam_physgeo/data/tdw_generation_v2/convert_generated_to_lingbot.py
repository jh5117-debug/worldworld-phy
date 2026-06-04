from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from cam_physgeo.data.convert_to_lingbot_cam_inputs import convert_sample


def _bool_arg(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _latest_validation_json(root: Path) -> Path | None:
    candidates = sorted((root / "reports").glob("validation_*.json"))
    if not candidates:
        return None
    preferred = [
        root / "reports" / "validation_50sample.json",
        root / "reports" / "validation_10sample.json",
        root / "reports" / "validation_1sample.json",
    ]
    for path in preferred:
        if path.exists():
            return path
    return candidates[-1]


def _camera_variant_from_dir(name: str) -> str | None:
    parts = name.split("_")
    if len(parts) < 4:
        return None
    if "seed" in parts:
        seed_idx = parts.index("seed")
        return "_".join(parts[2:seed_idx]) or None
    for idx, part in enumerate(parts):
        if part.startswith("seed"):
            return "_".join(parts[2:idx]) or None
    return "_".join(parts[2:-1]) or None


def _template_from_dir(name: str) -> str | None:
    parts = name.split("_")
    return parts[1] if len(parts) >= 2 else None


def _accepted_rows(root: Path, *, only_accepted: bool) -> tuple[list[dict[str, Any]], Path | None]:
    validation_path = _latest_validation_json(root)
    if validation_path is None:
        return [], None
    payload = json.loads(validation_path.read_text(encoding="utf-8"))
    rows = []
    for row in payload.get("rows", []):
        visible = row.get("target_visible_ratio")
        max_invisible = row.get("target_disappeared_consecutive_max")
        accepted = (
            row.get("status") == "ok"
            and row.get("has_rgb")
            and row.get("has_depth")
            and row.get("has_id")
            and row.get("has_camera_pose")
            and row.get("has_projection_or_camera_matrix")
            and row.get("has_object_state")
            and (visible is None or float(visible) >= 0.75)
            and (max_invisible is None or int(max_invisible) <= 20)
        )
        if only_accepted and not accepted:
            continue
        row = dict(row)
        row["accepted_for_warmup"] = bool(accepted)
        rows.append(row)
    return rows, validation_path


def _trial_dir_name(index: int, trial: dict[str, Any]) -> str:
    template = str(trial.get("template") or "unknown")
    variant = str(trial.get("camera_variant") or "unknown")
    seed = int(trial.get("seed", index))
    return f"{index:05d}_{template}_{variant}_seed{seed}"


def _manifest_output_subdir(profile: str, manifest: Path, num_trials: int) -> str:
    if "template_diverse" in manifest.stem:
        return f"{profile}_template_diverse_{num_trials}samples"
    return f"{profile}_plan_{num_trials}samples"


def _expected_paths_from_manifest(root: Path, manifest: Path) -> set[str]:
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    profile = str(rows[0].get("profile") or "warmup_mild") if rows else "warmup_mild"
    subdir = _manifest_output_subdir(profile, manifest, len(rows))
    out = set()
    for idx, row in enumerate(rows):
        trial_dir = root / "raw_hdf5" / subdir / _trial_dir_name(idx, row)
        out.add(str(trial_dir / "0000.hdf5"))
        out.add(str(trial_dir / "temp.hdf5"))
    return out


def _accepted_rows_for_manifest(root: Path, manifest: Path, *, only_accepted: bool) -> tuple[list[dict[str, Any]], Path | None]:
    expected = _expected_paths_from_manifest(root, manifest)
    validation_path = None
    suffix = manifest.stem
    for prefix in ("plan_warmup_mild_", "plan_"):
        if suffix.startswith(prefix):
            suffix = suffix[len(prefix):]
            break
    candidates = [root / "reports" / f"validation_{suffix}.json"]
    if "template_diverse" in manifest.stem:
        candidates.append(root / "reports" / "validation_template_diverse_10.json")
    for candidate in candidates:
        if candidate.exists():
            validation_path = candidate
            break
    if validation_path is None:
        rows, validation_path = _accepted_rows(root, only_accepted=only_accepted)
        return [row for row in rows if str(row.get("path")) in expected], validation_path
    payload = json.loads(validation_path.read_text(encoding="utf-8"))
    rows = []
    for row in payload.get("rows", []):
        visible = row.get("target_visible_ratio")
        max_invisible = row.get("target_disappeared_consecutive_max")
        accepted = (
            row.get("status") == "ok"
            and row.get("has_rgb")
            and row.get("has_depth")
            and row.get("has_id")
            and row.get("has_camera_pose")
            and row.get("has_projection_or_camera_matrix")
            and row.get("has_object_state")
            and (visible is None or float(visible) >= 0.75)
            and (max_invisible is None or int(max_invisible) <= 20)
        )
        if only_accepted and not accepted:
            continue
        row = dict(row)
        row["accepted_for_warmup"] = bool(accepted)
        rows.append(row)
    return [row for row in rows if str(row.get("path")) in expected], validation_path


def _sample_from_validation_row(row: dict[str, Any]) -> dict[str, Any]:
    hdf5_path = Path(str(row["path"]))
    trial_name = hdf5_path.parent.name
    sample_id = f"tdw_v2_{trial_name}_{hdf5_path.stem}"
    template = _template_from_dir(trial_name)
    camera_variant = _camera_variant_from_dir(trial_name)
    return {
        "sample_id": sample_id,
        "source": "tdw_generated_v2",
        "hdf5_path": str(hdf5_path),
        "template": template,
        "camera_variant": camera_variant,
        "camera_profile": "warmup_mild",
        "has_depth": bool(row.get("has_depth")),
        "has_id_mask": bool(row.get("has_id")),
        "has_camera_pose": bool(row.get("has_camera_pose")),
        "has_intrinsics": bool(row.get("has_projection_or_camera_matrix")),
        "has_object_state": bool(row.get("has_object_state")),
        "target_visible_ratio": row.get("target_visible_ratio"),
        "target_disappeared_consecutive_max": row.get("target_disappeared_consecutive_max"),
        "camera_path_length": row.get("camera_path_length"),
        "contact_sheet_path": row.get("contact_sheet_path"),
        "prompt_path": "generated://tdw_v2_warmup_mild",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Convert accepted generated TDW v2 samples to LingBot cam-only inputs.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only_accepted", type=_bool_arg, default=True)
    parser.add_argument("--num_frames", type=int, default=81)
    parser.add_argument("--fps", type=int, default=16)
    parser.add_argument("--size", default="480x832")
    parser.add_argument("--use_action", type=_bool_arg, default=False)
    parser.add_argument("--make_dummy_action", type=_bool_arg, default=True)
    parser.add_argument("--prompt-level", default="P1", choices=["P0", "P1", "P2"])
    parser.add_argument("--force_rewrite_video", type=_bool_arg, default=False)
    parser.add_argument("--probe_video", type=_bool_arg, default=False)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.use_action:
        raise SystemExit("TDW v2 cam-only conversion requires --use_action false; action.npy is dummy fallback only.")
    if args.manifest:
        rows, validation_path = _accepted_rows_for_manifest(args.root, args.manifest, only_accepted=bool(args.only_accepted))
    else:
        rows, validation_path = _accepted_rows(args.root, only_accepted=bool(args.only_accepted))
    args.out.mkdir(parents=True, exist_ok=True)
    convert_args = SimpleNamespace(
        dry_run=bool(args.dry_run),
        source="",
        num_frames=int(args.num_frames),
        fps=int(args.fps),
        size=str(args.size),
        use_action=False,
        make_dummy_action=bool(args.make_dummy_action),
        prefix_frames=0,
        prompt_level=args.prompt_level,
        link_mode="copy",
        force_rewrite_video=bool(args.force_rewrite_video),
        probe_video=bool(args.probe_video),
    )
    converted = []
    errors = []
    for row in rows:
        sample = _sample_from_validation_row(row)
        try:
            converted.append(convert_sample(sample, args.out, convert_args))
        except Exception as exc:
            errors.append({"sample_id": sample.get("sample_id"), "hdf5_path": sample.get("hdf5_path"), "error": repr(exc)})
    summary = {
        "root": str(args.root),
        "out": str(args.out),
        "validation_json": str(validation_path) if validation_path else None,
        "manifest": str(args.manifest) if args.manifest else None,
        "only_accepted": bool(args.only_accepted),
        "converted_count": len(converted),
        "error_count": len(errors),
        "converted": converted,
        "errors": errors,
        "use_action": False,
        "dummy_action": bool(args.make_dummy_action),
        "force_rewrite_video": bool(args.force_rewrite_video),
        "probe_video": bool(args.probe_video),
        "required_files": ["image.jpg", "target.mp4", "poses.npy", "intrinsics.npy", "prompt.txt", "metadata.json", "action.npy"],
    }
    (args.out / "conversion_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
