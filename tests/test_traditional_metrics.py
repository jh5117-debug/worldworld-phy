from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from cam_physgeo.eval.metrics_traditional import compute_video_pair_metrics, read_video_rgb


def _write_video(path: Path, frames: list[np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 8.0, (w, h))
    for frame in frames:
        writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    writer.release()


def _frames() -> list[np.ndarray]:
    frames = []
    for i in range(6):
        img = np.zeros((48, 64, 3), dtype=np.uint8)
        img[:, :, 0] = 40 + i * 10
        img[10:30, 15 + i : 35 + i, 1] = 220
        img[20:40, 5:25, 2] = 120
        frames.append(img)
    return frames


def test_read_video_and_psnr_ssim_identical(tmp_path: Path) -> None:
    frames = _frames()
    a = tmp_path / "a.mp4"
    b = tmp_path / "b.mp4"
    _write_video(a, frames)
    _write_video(b, frames)
    decoded, meta = read_video_rgb(a)
    assert decoded is not None
    assert meta["num_frames"] == 6
    metrics = compute_video_pair_metrics(a, b)
    assert metrics["status"] == "ok"
    assert metrics["psnr"] > 35
    assert metrics["ssim"] > 0.95
    assert metrics["mean_laplacian_sharpness"] >= 0


def test_blur_reduces_sharpness(tmp_path: Path) -> None:
    frames = _frames()
    sharp = tmp_path / "sharp.mp4"
    blur = tmp_path / "blur.mp4"
    blurred = [cv2.GaussianBlur(f, (11, 11), 0) for f in frames]
    _write_video(sharp, frames)
    _write_video(blur, blurred)
    sharp_metrics = compute_video_pair_metrics(sharp, sharp)
    blur_metrics = compute_video_pair_metrics(sharp, blur)
    assert blur_metrics["mean_laplacian_sharpness"] < sharp_metrics["mean_laplacian_sharpness"]
    assert blur_metrics["psnr"] < sharp_metrics["psnr"]
