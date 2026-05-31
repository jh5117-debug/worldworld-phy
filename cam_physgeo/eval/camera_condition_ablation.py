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


def _truthy(value: Any) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y", "on"}


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


def _repeat_first(arr: np.ndarray) -> np.ndarray:
    if arr.ndim < 1:
        raise ValueError(f"cannot repeat first camera pose for shape {arr.shape}")
    return np.repeat(arr[:1], len(arr), axis=0)


def _yaw_matrix(angle_rad: float) -> np.ndarray:
    c = float(np.cos(angle_rad))
    s = float(np.sin(angle_rad))
    return np.array([[c, 0.0, s, 0.0], [0.0, 1.0, 0.0, 0.0], [-s, 0.0, c, 0.0], [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)


def variant_poses(poses: np.ndarray, variant: str) -> np.ndarray:
    arr = np.asarray(poses)
    name = variant.replace("_camera", "")
    if name in {"correct", "repeat_correct_A", "repeat_correct_B"}:
        return arr.copy()
    if name in {"frozen", "zero_motion"}:
        return _repeat_first(arr)
    if name == "reversed":
        return arr[::-1].copy()
    if name == "shuffled":
        rng = np.random.default_rng(123)
        idx = np.arange(len(arr))
        rng.shuffle(idx)
        return arr[idx].copy()
    if name in {"exaggerated_yaw", "large_translation", "exaggerated_translation"}:
        out = arr.copy()
        if name == "exaggerated_translation" and out.ndim == 3 and out.shape[-2:] == (4, 4):
            denom = max(len(out) - 1, 1)
            direction = out[0, :3, 0].copy()
            norm = float(np.linalg.norm(direction)) + 1e-8
            direction = direction / norm
            for i in range(len(out)):
                out[i, :3, 3] = out[i, :3, 3] + direction * float(2.0 * i / denom)
            return out
        if out.ndim == 3 and out.shape[-2:] == (4, 4):
            # Apply a deliberately strong 60 degree yaw sweep over the short video.
            denom = max(len(out) - 1, 1)
            for i in range(len(out)):
                out[i] = _yaw_matrix(np.deg2rad(60.0 * i / denom)) @ out[i]
            return out
        if out.ndim == 2 and out.shape[-1] >= 3:
            out[:, 0] += np.linspace(0.0, 1.0, len(out), dtype=np.float32)
            return out
        raise ValueError(f"cannot exaggerate yaw for pose shape {out.shape}")
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
    meta: dict[str, Any] = {}
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
    generated = variant_out / sample_dir.name / "generated.mp4"
    if generated.exists():
        meta = {
            "sample_id": sample_dir.name,
            "variant": variant,
            "command": [],
            "returncode": 0,
            "elapsed_sec": 0.0,
            "generated": str(generated),
            "generated_exists": True,
            "skipped_existing": True,
            "log_path": str(variant_out / "stdout_stderr.log"),
        }
        write_json(meta, variant_out / "metadata.json")
        return meta
    seed = args.seed if _truthy(args.same_seed) else args.seed + abs(hash(variant)) % 1000
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
        "--save-condition-summary",
    ]
    # run_inference currently fixes the seed inside the LingBot runtime. The
    # command record keeps the intended seed explicit for future runtime wiring.
    if args.local_files_only:
        cmd.append("--local-files-only")
    if args.save_contact_sheet:
        cmd.append("--save_contact_sheet")
    if args.debug_camera_condition:
        cmd.append("--debug-camera-condition")
    if args.save_condition_summary:
        cmd.append("--save-condition-summary")
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("TERM", "dumb")
    env.setdefault("TQDM_DISABLE", "1")
    env.setdefault("DISABLE_PROGRESS_BAR", "1")
    env["CAM_PHYS_GEO_ABLATION_SEED"] = str(seed)
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
    condition_debug = variant_out / sample_dir.name / "condition_debug.json"
    meta = {
        "sample_id": sample_dir.name,
        "variant": variant,
        "command": cmd,
        "intended_seed": seed,
        "same_seed": _truthy(args.same_seed),
        "returncode": proc.returncode,
        "elapsed_sec": elapsed,
        "generated": str(generated),
        "generated_exists": generated.exists(),
        "condition_debug": str(condition_debug) if condition_debug.exists() else None,
        "log_path": str(log_path),
    }
    write_json(meta, variant_out / "metadata.json")
    return meta


def _read_metric_frames(path: str | Path, max_frames: int = 8, size: tuple[int, int] = (160, 96)) -> list[np.ndarray]:
    try:
        import cv2  # type: ignore

        cap = cv2.VideoCapture(str(path))
        frames: list[np.ndarray] = []
        while len(frames) < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.resize(frame, size)
            frames.append(frame.astype("float32") / 255.0)
        cap.release()
        return frames
    except Exception:
        return []


def video_diff_metrics(path_a: str | Path, path_b: str | Path) -> dict[str, Any]:
    frames_a = _read_metric_frames(path_a)
    frames_b = _read_metric_frames(path_b)
    n = min(len(frames_a), len(frames_b))
    if n == 0:
        return {"available": False, "reason": "missing_or_unreadable_video"}
    a = np.stack(frames_a[:n])
    b = np.stack(frames_b[:n])
    pixel_l1 = float(np.mean(np.abs(a - b)))
    motion_a = float(np.mean(np.abs(np.diff(a, axis=0)))) if n > 1 else 0.0
    motion_b = float(np.mean(np.abs(np.diff(b, axis=0)))) if n > 1 else 0.0
    return {
        "available": True,
        "frames_compared": int(n),
        "pixel_l1": pixel_l1,
        "video_feature_distance_proxy": pixel_l1,
        "motion_magnitude_a": motion_a,
        "motion_magnitude_b": motion_b,
        "motion_magnitude_delta": abs(motion_a - motion_b),
        "optical_flow_backend": "frame_diff_proxy",
        "background_flow_magnitude_proxy": float((motion_a + motion_b) / 2.0),
    }


def compute_ablation_metrics(sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_variant = {row["variant"]: row for row in sample_rows if row.get("generated_exists")}
    comparisons: dict[str, Any] = {}

    def add(name: str, a: str, b: str) -> None:
        if a in by_variant and b in by_variant:
            comparisons[name] = video_diff_metrics(by_variant[a]["generated"], by_variant[b]["generated"])

    add("repeat_correct_A_vs_repeat_correct_B", "repeat_correct_A", "repeat_correct_B")
    baseline = comparisons.get("repeat_correct_A_vs_repeat_correct_B", {}).get("pixel_l1")
    for variant in ["frozen", "reversed", "exaggerated_yaw", "exaggerated_translation", "zero_motion", "shuffled"]:
        add(f"repeat_correct_A_vs_{variant}", "repeat_correct_A", variant)
    for variant in ["frozen", "reversed", "exaggerated_yaw", "exaggerated_translation", "zero_motion", "shuffled"]:
        add(f"correct_vs_{variant}", "correct", variant)
    threshold = None
    conclusion = "not_proven"
    if baseline is not None:
        threshold = float(baseline) * 1.2 + 1e-6
        variant_scores = [
            comp.get("pixel_l1")
            for key, comp in comparisons.items()
            if (key.startswith("correct_vs_") or key.startswith("repeat_correct_A_vs_")) and comp.get("available")
        ]
        if variant_scores and max(float(v) for v in variant_scores if v is not None) > threshold:
            conclusion = "camera_likely_affects_generation"
        else:
            conclusion = "camera_variant_difference_not_above_noise"
    return {"comparisons": comparisons, "repeat_baseline_pixel_l1": baseline, "variant_threshold_pixel_l1": threshold, "metric_conclusion": conclusion}


def make_comparison_sheet(sample_id: str, variant_rows: list[dict[str, Any]], out_path: Path) -> bool:
    try:
        import cv2  # type: ignore

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
    ap.add_argument("--sample_id_from", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model_type", default="fast", choices=["fast", "base"])
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--num_frames", type=int, default=8)
    ap.add_argument("--num_steps", type=int, default=1)
    ap.add_argument("--resolution", default="480x832")
    ap.add_argument("--variants", nargs="+", default=["correct", "frozen", "reversed"])
    ap.add_argument("--same_seed", nargs="?", const="true", default="false")
    ap.add_argument("--seed", type=int, default=123)
    ap.add_argument("--save_contact_sheet", action="store_true")
    ap.add_argument("--debug-camera-condition", action="store_true")
    ap.add_argument("--save-condition-summary", action="store_true")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--local-files-only", action="store_true")
    args = ap.parse_args(argv)

    out = Path(args.out)
    rows: list[dict[str, Any]] = []
    all_samples = iter_samples(Path(args.samples), 0)
    if args.sample_id_from:
        selected = Path(args.sample_id_from).read_text(encoding="utf-8").strip()
        all_samples = [p for p in all_samples if p.name == selected]
    for sample_dir in all_samples[: args.limit]:
        sample_rows = []
        for variant in args.variants:
            row = run_variant(args, sample_dir, out, variant)
            rows.append(row)
            sample_rows.append(row)
        sheet = out / sample_dir.name / "comparison_contact_sheet.jpg"
        ok = make_comparison_sheet(sample_dir.name, sample_rows, sheet)
        metrics = compute_ablation_metrics(sample_rows)
        write_json(
            {
                "sample_id": sample_dir.name,
                "comparison_contact_sheet": str(sheet),
                "comparison_created": ok,
                "variants": sample_rows,
                "metrics": metrics,
            },
            out / sample_dir.name / "ablation_summary.json",
        )
    ok_count = sum(1 for row in rows if row.get("generated_exists"))
    payload = {"variants": len(rows), "ok_count": ok_count, "out": str(out), "rows": rows}
    write_json(payload, out / "camera_ablation_summary.json")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
