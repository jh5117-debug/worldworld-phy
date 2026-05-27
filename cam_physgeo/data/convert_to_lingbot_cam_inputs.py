from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from cam_physgeo.data.physion_hdf5_reader import read_physion_sample
from cam_physgeo.data.prompt_templates import build_prompt
from cam_physgeo.utils.io import read_jsonl, write_json
from cam_physgeo.utils.video import extract_first_frame, probe_video, write_video_frames


def link_or_copy(src, dst, mode, dry_run):
    if dry_run:
        return
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    if mode == "symlink":
        os.symlink(src, dst)
    else:
        shutil.copy2(src, dst)


def convert_sample(sample: dict, out_root: Path, args) -> dict:
    sample_id = str(sample["sample_id"])
    out_dir = out_root / sample_id
    dry = bool(args.dry_run)
    if not dry:
        out_dir.mkdir(parents=True, exist_ok=True)

    if args.source and sample.get("source") != args.source:
        return {"sample_id": sample_id, "out_dir": str(out_dir), "skipped": "source_filter"}

    hdf5_payload = None
    target_video = out_dir / "target.mp4"
    image_path = out_dir / "image.jpg"
    if sample.get("video_path"):
        link_or_copy(sample["video_path"], target_video, args.link_mode, dry)
        extract_first_frame(sample["video_path"], image_path, dry_run=dry)
        if int(args.prefix_frames or 0) > 0:
            write_prefix_video(sample["video_path"], out_dir / "prefix.mp4", int(args.prefix_frames), args.fps, dry)
    elif sample.get("hdf5_path"):
        hdf5_payload = read_physion_sample(sample["hdf5_path"], limit_frames=args.num_frames)
        if hdf5_payload.get("rgb") is not None and not dry:
            write_video_frames(hdf5_payload["rgb"][: args.num_frames], target_video, fps=args.fps)
            extract_first_frame(target_video, image_path, dry_run=False)

    if hdf5_payload is None and sample.get("hdf5_path") and not dry:
        hdf5_payload = read_physion_sample(sample["hdf5_path"], limit_frames=args.num_frames)

    if not dry:
        write_camera_arrays(sample, hdf5_payload, out_dir, args)
        write_optional_arrays(hdf5_payload, out_dir)

    prompt = read_prompt(sample) or build_prompt(sample, args.prompt_level)
    if not dry:
        (out_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
        meta = dict(sample)
        meta.update(
            {
                "use_action": False,
                "dummy_action": bool(args.make_dummy_action),
                "prompt_level": args.prompt_level,
                "target_num_frames": args.num_frames,
                "target_fps": args.fps,
                "target_size": args.size,
                "input_mode": "v2v_prefix" if int(args.prefix_frames or 0) > 0 else "i2v_first_frame",
                "video_probe": probe_video(sample.get("video_path") or target_video),
                "camera_metadata_source": camera_metadata_source(sample, hdf5_payload),
                "intrinsics_source": intrinsics_source(sample, hdf5_payload),
                "original_video_path": sample.get("video_path"),
                "original_hdf5_path": sample.get("hdf5_path"),
            }
        )
        write_json(meta, out_dir / "metadata.json")
        if args.make_dummy_action:
            write_dummy_action(out_dir / "action.npy", args.num_frames)
    return {"sample_id": sample_id, "out_dir": str(out_dir)}


def write_camera_arrays(sample: dict, hdf5_payload: dict | None, out_dir: Path, args) -> None:
    import numpy as np

    poses = None
    intrinsics = None
    if hdf5_payload:
        poses = hdf5_payload.get("camera_pose")
        intrinsics = hdf5_payload.get("intrinsics")
    if poses is None and sample.get("poses_path") and str(sample["poses_path"]).startswith("hdf5://"):
        poses = extract_hdf5_array(sample["poses_path"])
    if intrinsics is None and sample.get("intrinsics_path") and str(sample["intrinsics_path"]).startswith("hdf5://"):
        intrinsics = extract_hdf5_array(sample["intrinsics_path"])
    if poses is not None:
        np.save(out_dir / "poses.npy", poses[: args.num_frames])
    else:
        (out_dir / "poses.missing.txt").write_text("camera pose unavailable; sample is not benchmark-ready\n", encoding="utf-8")
    if intrinsics is not None:
        np.save(out_dir / "intrinsics.npy", intrinsics[: args.num_frames] if getattr(intrinsics, "ndim", 0) >= 3 else intrinsics)
    else:
        (out_dir / "intrinsics.missing.txt").write_text("intrinsics/projection unavailable\n", encoding="utf-8")


def write_optional_arrays(hdf5_payload: dict | None, out_dir: Path) -> None:
    if not hdf5_payload:
        return
    import numpy as np

    for key, name in [("depth", "depth.npy"), ("id_mask", "id_mask.npy"), ("flow", "flow.npy"), ("normals", "normals.npy")]:
        value = hdf5_payload.get(key)
        if value is not None:
            np.save(out_dir / name, value)


def extract_hdf5_array(uri: str):
    import h5py

    file_path, key = uri[len("hdf5://") :].split("::", 1)
    with h5py.File(file_path, "r") as handle:
        return handle[key][()]


def read_prompt(sample):
    prompt_path = sample.get("prompt_path")
    if not prompt_path or str(prompt_path).startswith("generated://"):
        return None
    try:
        return Path(prompt_path).read_text(encoding="utf-8").strip()
    except Exception:
        return None


def write_dummy_action(path: Path, num_frames: int) -> None:
    import numpy as np

    np.save(path, np.zeros((int(num_frames), 4), dtype="float32"))


def write_prefix_video(video_path: str | Path, out_path: Path, prefix_frames: int, fps: int, dry_run: bool = False) -> bool:
    if dry_run:
        return False
    try:
        import cv2

        cap = cv2.VideoCapture(str(video_path))
        ok, frame = cap.read()
        if not ok:
            cap.release()
            return False
        h, w = frame.shape[:2]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), float(fps or 16), (w, h))
        count = 0
        while ok and count < prefix_frames:
            writer.write(frame)
            count += 1
            ok, frame = cap.read()
        cap.release()
        writer.release()
        return out_path.exists() and count > 0
    except Exception:
        return False


def camera_metadata_source(sample: dict, hdf5_payload: dict | None) -> str:
    if sample.get("poses_key") or (hdf5_payload and hdf5_payload.get("camera_pose") is not None):
        return "hdf5"
    if sample.get("camera_position_key") and sample.get("camera_aim_key"):
        return "computed_from_position_aim"
    return "missing"


def intrinsics_source(sample: dict, hdf5_payload: dict | None) -> str:
    if sample.get("intrinsics_key"):
        return "hdf5"
    if sample.get("projection_matrix_key"):
        return "projection_matrix"
    if sample.get("camera_matrix_key"):
        return "camera_matrix"
    if hdf5_payload and hdf5_payload.get("intrinsics") is not None:
        return hdf5_payload.get("metadata", {}).get("intrinsics_source", "hdf5")
    return "missing"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--source", default="", choices=["", "physion_official", "physion_movingcam"])
    ap.add_argument("--num_frames", type=int, default=81)
    ap.add_argument("--fps", type=int, default=16)
    ap.add_argument("--size", default="480x832")
    ap.add_argument("--use_action", type=lambda x: str(x).lower() == "true", default=False)
    ap.add_argument("--make_dummy_action", type=lambda x: str(x).lower() == "true", default=True)
    ap.add_argument("--prefix_frames", type=int, default=0)
    ap.add_argument("--prompt-level", default="P1", choices=["P0", "P1", "P2"])
    ap.add_argument("--link-mode", default="symlink", choices=["symlink", "copy"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.use_action:
        raise SystemExit("Physion-Cam-PhysGeo-DPO does not support real action conditioning; use --use_action false.")
    converted = []
    seen = 0
    for sample in read_jsonl(args.manifest):
        if args.source and sample.get("source") != args.source:
            continue
        if args.limit and seen >= args.limit:
            break
        converted.append(convert_sample(sample, Path(args.out), args))
        seen += 1
    print({"converted": len(converted), "out": args.out, "dry_run": args.dry_run, "use_action": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
