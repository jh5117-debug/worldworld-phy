from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from cam_physgeo.eval.make_contact_sheet import read_selected_video_frames
from cam_physgeo.utils.io import write_json


def iter_samples(root: Path, limit: int) -> list[Path]:
    dirs = [p for p in sorted(root.iterdir()) if p.is_dir()] if root.exists() else []
    return dirs[:limit] if limit else dirs


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        return
    try:
        os.symlink(src.resolve(), dst)
    except OSError:
        shutil.copy2(src, dst)


def variant_poses(poses: np.ndarray, variant: str) -> np.ndarray:
    arr = np.asarray(poses)
    if variant == "correct":
        return arr.copy()
    if variant == "frozen":
        if arr.ndim < 1:
            raise ValueError(f"cannot freeze pose array with shape {arr.shape}")
        return np.repeat(arr[:1], len(arr), axis=0)
    if variant == "reversed":
        return arr[::-1].copy()
    if variant == "shuffled":
        rng = np.random.default_rng(123)
        idx = np.arange(len(arr))
        rng.shuffle(idx)
        return arr[idx].copy()
    raise ValueError(f"unknown camera variant {variant!r}")


def prepare_variant_input(sample_dir: Path, temp_root: Path, variant: str) -> Path:
    variant_sample = temp_root / sample_dir.name
    variant_sample.mkdir(parents=True, exist_ok=True)
    for name in ["image.jpg", "target.mp4", "prompt.txt", "intrinsics.npy", "id_mask.npy", "depth.npy"]:
        src = sample_dir / name
        if src.exists():
            link_or_copy(src, variant_sample / name)
    poses = np.load(sample_dir / "poses.npy")
    np.save(variant_sample / "poses.npy", variant_poses(poses, variant))
    action_src = sample_dir / "action.npy"
    if action_src.exists():
        link_or_copy(action_src, variant_sample / "action.npy")
    else:
        np.save(variant_sample / "action.npy", np.zeros((len(poses), 4), dtype=np.float32))
    meta = {}
    if (sample_dir / "metadata.json").exists():
        meta = json.loads((sample_dir / "metadata.json").read_text(encoding="utf-8"))
    meta.update(
        {
            "camera_ablation_variant": variant,
            "camera_ablation_source_sample": sample_dir.name,
            "use_action": False,
            "action_policy": "dummy action only; camera ablation changes poses.npy",
        }
    )
    write_json(meta, variant_sample / "metadata.json")
    return temp_root


def run_variant(args, sample_dir: Path, out_root: Path, variant: str) -> dict[str, Any]:
    temp_root = out_root / sample_dir.name / "_inputs" / variant
    variant_out = out_root / sample_dir.name / variant
    prepare_variant_input(sample_dir, temp_root, variant)
    cmd = [
        sys.executable,
        "-m",
        "cam_physgeo.eval.run_inference",
        "--config",
        args.config,
        "--model_type",
        args.model_type,
        "--samples",
        str(temp_root),
        "--out",
        str(variant_out),
        "--smoke-run",
        "--limit",
        "1",
        "--num_frames",
        str(args.num_frames),
        "--num_steps",
        str(args.num_steps),
        "--resolution",
        args.resolution,
        "--timeout",
        str(args.timeout),
    ]
    if args.local_files_only:
        cmd.append("--local-files-only")
    if args.save_contact_sheet:
        cmd.append("--save_contact_sheet")
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("TERM", "dumb")
    env.setdefault("TQDM_DISABLE", "1")
    env.setdefault("DISABLE_PROGRESS_BAR", "1")
    if args.local_files_only:
        env.setdefault("TRANSFORMERS_OFFLINE", "1")
        env.setdefault("HF_HUB_OFFLINE", "1")
    log_path = variant_out / "stdout_stderr.log"
    variant_out.mkdir(parents=True, exist_ok=True)
    (variant_out / "command.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")
    start = time.time()
    with log_path.open("w", encoding="utf-8", errors="replace") as log_f:
        proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT, text=True, env=env)
        try:
            proc.wait(timeout=args.timeout + 60)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            log_f.write(f"\n[TIMEOUT] camera ablation variant killed after {args.timeout + 60}s\n")
    elapsed = time.time() - start
    generated = variant_out / sample_dir.name / "generated.mp4"
    meta = {
        "sample_id": sample_dir.name,
        "variant": variant,
        "command": cmd,
        "returncode": proc.returncode,
        "elapsed_sec": elapsed,
        "generated": str(generated),
        "generated_exists": generated.exists(),
        "log_path": str(log_path),
    }
    write_json(meta, variant_out / "metadata.json")
    return meta


def make_comparison_sheet(sample_id: str, variant_rows: list[dict[str, Any]], out_path: Path) -> bool:
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        frames_by_variant = []
        for row in variant_rows:
            frames = read_selected_video_frames(row.get("generated"), [0, 1, 2, 3, 4, 5, 6, 7, 8], thumb_size=(160, 96))
            if frames:
                frames_by_variant.append((row["variant"], frames))
        if not frames_by_variant:
            return False
        w = 160
        h = 96
        label_h = 32
        cols = max(len(frames) for _, frames in frames_by_variant)
        canvas = np.zeros(((h + label_h) * len(frames_by_variant), w * cols, 3), dtype=np.uint8)
        for r, (variant, frames) in enumerate(frames_by_variant):
            y0 = r * (h + label_h)
            cv2.putText(canvas, f"{sample_id} | {variant}", (8, y0 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (230, 230, 230), 1, cv2.LINE_AA)
            for c, frame in enumerate(frames):
                canvas[y0 + label_h : y0 + label_h + h, c * w : (c + 1) * w] = frame
        out_path.parent.mkdir(parents=True, exist_ok=True)
        return bool(cv2.imwrite(str(out_path), canvas))
    except Exception:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/cam_physgeo/eval.yaml")
    ap.add_argument("--samples", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model_type", default="fast", choices=["fast", "base"])
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--num_frames", type=int, default=8)
    ap.add_argument("--num_steps", type=int, default=1)
    ap.add_argument("--resolution", default="480x832")
    ap.add_argument("--variants", nargs="+", default=["correct", "frozen", "reversed"])
    ap.add_argument("--save_contact_sheet", action="store_true")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--local-files-only", action="store_true")
    args = ap.parse_args(argv)

    out = Path(args.out)
    rows: list[dict[str, Any]] = []
    for sample_dir in iter_samples(Path(args.samples), args.limit):
        sample_rows = []
        for variant in args.variants:
            row = run_variant(args, sample_dir, out, variant)
            rows.append(row)
            sample_rows.append(row)
        sheet = out / sample_dir.name / "comparison_contact_sheet.jpg"
        ok = make_comparison_sheet(sample_dir.name, sample_rows, sheet)
        write_json({"sample_id": sample_dir.name, "comparison_contact_sheet": str(sheet), "comparison_created": ok, "variants": sample_rows}, out / sample_dir.name / "ablation_summary.json")
    ok_count = sum(1 for row in rows if row.get("generated_exists"))
    payload = {"variants": len(rows), "ok_count": ok_count, "out": str(out), "rows": rows}
    write_json(payload, out / "camera_ablation_summary.json")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
