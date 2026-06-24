import json
from pathlib import Path

import cv2
import numpy as np

from cam_physgeo.eval.quant_benchmark_v1 import main


def _write_video(path: Path, frames: list[np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 16, (w, h))
    for frame in frames:
        writer.write(frame)
    writer.release()


def test_quant_benchmark_gt_identity(tmp_path):
    frames = []
    for i in range(6):
        img = np.zeros((32, 48, 3), dtype=np.uint8)
        img[:, :, 0] = 30 + i
        img[8:18, 10 + i:20 + i, 1] = 200
        frames.append(img)
    video = tmp_path / "sample" / "video.mp4"
    _write_video(video, frames)
    poses = tmp_path / "sample" / "poses.npy"
    intr = tmp_path / "sample" / "intrinsics.npy"
    np.save(poses, np.repeat(np.eye(4)[None], 6, axis=0))
    np.save(intr, np.repeat(np.array([[40.0, 40.0, 24.0, 16.0]])[None], 6, axis=0))
    manifest = tmp_path / "conditions.jsonl"
    row = {"sample_id": "s0", "template": "drop", "camera_variant": "unit", "target_video": str(video), "poses": str(poses), "intrinsics": str(intr)}
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
    out = tmp_path / "out"
    rc = main(["--conditions", str(manifest), "--candidate", "GT=gt", "--out_dir", str(out), "--frame_count", "6", "--skip_geometry"])
    assert rc == 0
    text = (out / "model_summary.csv").read_text(encoding="utf-8")
    assert "GT" in text
    assert "psnr_mean" in text
