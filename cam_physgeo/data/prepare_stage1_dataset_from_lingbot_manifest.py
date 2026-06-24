from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from pathlib import Path
from typing import Iterable


CSV_FIELDS = [
    "clip_path",
    "prompt",
    "source_height",
    "source_width",
    "camera_id",
    "trajectory_name",
    "sample_id",
    "template",
    "camera_variant",
    "source_video_path",
    "source_poses_path",
    "source_intrinsics_path",
    "use_action",
    "prompt_variant",
]


def _read_jsonl(path: str | Path) -> list[dict]:
    rows: list[dict] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return rows


def _resolve_path(value: str | None, *, project_root: Path) -> Path:
    raw = str(value or "").strip()
    if not raw:
        return project_root / "__missing_stage1_manifest_path__"
    path = Path(raw)
    if path.is_absolute():
        return path
    return project_root / path


def _resolve_first_path(row: dict, keys: tuple[str, ...], *, project_root: Path) -> Path:
    for key in keys:
        value = row.get(key)
        if str(value or "").strip():
            return _resolve_path(str(value), project_root=project_root)
    return _resolve_path(None, project_root=project_root)


def _prompt_for_row(row: dict, *, project_root: Path) -> str:
    for key in ("prompt_path", "prompt_file"):
        prompt_path = _resolve_path(row.get(key), project_root=project_root)
        if prompt_path.is_file():
            return prompt_path.read_text(encoding="utf-8").strip()
    prompt = str(row.get("prompt") or "").strip()
    if prompt:
        prompt_as_path = _resolve_path(prompt, project_root=project_root)
        if prompt_as_path.is_file():
            return prompt_as_path.read_text(encoding="utf-8").strip()
        return prompt
    return ""


def _link_or_copy(src: Path, dst: Path, *, mode: str) -> None:
    if not src.is_file():
        raise FileNotFoundError(src)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(src, dst)
        return
    if mode == "symlink":
        os.symlink(src, dst)
        return
    try:
        os.link(src, dst)
    except OSError:
        os.symlink(src, dst)


def _write_split(
    *,
    split: str,
    manifest: Path,
    out_dir: Path,
    project_root: Path,
    link_mode: str,
) -> dict:
    rows = _read_jsonl(manifest)
    csv_rows: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    for row in rows:
        sample_id = str(row.get("sample_id") or row.get("id") or "").strip()
        if not sample_id:
            missing.append({"sample_id": "", "reason": "missing_sample_id"})
            continue
        target_video = _resolve_first_path(
            row,
            ("target_video_path", "target_video", "target_mp4", "video_path", "video"),
            project_root=project_root,
        )
        poses_path = _resolve_first_path(row, ("poses_path", "poses", "pose_path"), project_root=project_root)
        intrinsics_path = _resolve_first_path(
            row,
            ("intrinsics_path", "intrinsics", "camera_intrinsics_path"),
            project_root=project_root,
        )
        prompt = _prompt_for_row(row, project_root=project_root)
        bad_paths = [
            name
            for name, path in (
                ("target_video_path", target_video),
                ("poses_path", poses_path),
                ("intrinsics_path", intrinsics_path),
            )
            if not path.is_file()
        ]
        if bad_paths:
            missing.append({"sample_id": sample_id, "reason": "missing_" + ",".join(bad_paths)})
            continue
        if not prompt:
            missing.append({"sample_id": sample_id, "reason": "missing_prompt"})
            continue
        clip_rel = Path("clips") / split / sample_id
        clip_dir = out_dir / clip_rel
        _link_or_copy(target_video, clip_dir / "video.mp4", mode=link_mode)
        _link_or_copy(poses_path, clip_dir / "poses.npy", mode=link_mode)
        _link_or_copy(intrinsics_path, clip_dir / "intrinsics.npy", mode=link_mode)
        (clip_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
        csv_rows.append(
            {
                "clip_path": str(clip_rel),
                "prompt": prompt,
                "source_height": str(row.get("source_height") or row.get("height") or 480),
                "source_width": str(row.get("source_width") or row.get("width") or 832),
                "camera_id": str(row.get("camera_variant") or row.get("camera_id") or ""),
                "trajectory_name": str(row.get("camera_variant") or row.get("trajectory_name") or ""),
                "sample_id": sample_id,
                "template": str(row.get("template") or ""),
                "camera_variant": str(row.get("camera_variant") or ""),
                "source_video_path": str(target_video),
                "source_poses_path": str(poses_path),
                "source_intrinsics_path": str(intrinsics_path),
                "use_action": str(row.get("use_action", False)).lower(),
                "prompt_variant": str(row.get("prompt_variant") or ""),
            }
        )
    csv_path = out_dir / f"metadata_{split}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(csv_rows)
    return {
        "split": split,
        "manifest": str(manifest),
        "metadata_csv": str(csv_path),
        "input_rows": len(rows),
        "prepared_rows": len(csv_rows),
        "missing_rows": missing,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare Stage-1 metadata CSV from LingBot JSONL manifests.")
    parser.add_argument("--train_manifest", required=True)
    parser.add_argument("--val_manifest", required=True)
    parser.add_argument("--test_manifest", default="")
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--project_root", required=True)
    parser.add_argument("--link_mode", choices=["hardlink", "symlink", "copy"], default="hardlink")
    parser.add_argument("--summary_json", default="")
    args = parser.parse_args(list(argv) if argv is not None else None)

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    project_root = Path(args.project_root).resolve()
    summaries = [
        _write_split(
            split="train",
            manifest=Path(args.train_manifest),
            out_dir=out_dir,
            project_root=project_root,
            link_mode=args.link_mode,
        ),
        _write_split(
            split="val",
            manifest=Path(args.val_manifest),
            out_dir=out_dir,
            project_root=project_root,
            link_mode=args.link_mode,
        ),
    ]
    if args.test_manifest:
        summaries.append(
            _write_split(
                split="test",
                manifest=Path(args.test_manifest),
                out_dir=out_dir,
                project_root=project_root,
                link_mode=args.link_mode,
            )
        )
    summary = {
        "out_dir": str(out_dir),
        "project_root": str(project_root),
        "link_mode": args.link_mode,
        "splits": summaries,
        "ready": all(not item["missing_rows"] for item in summaries),
    }
    summary_path = Path(args.summary_json or out_dir / "stage1_dataset_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
