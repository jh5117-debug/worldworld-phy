from __future__ import annotations

import cv2
import numpy as np

from cam_physgeo.rewards.conditioned_sgc import evaluate_csgc_video


def test_csgc_constant_translation_video_runs(tmp_path) -> None:
    path = tmp_path / "shift.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 8, (96, 64))
    base = np.zeros((64, 96, 3), dtype=np.uint8)
    for y in range(0, 64, 8):
        cv2.line(base, (0, y), (95, y), (80, 80, 80), 1)
    for x in range(0, 96, 8):
        cv2.line(base, (x, 0), (x, 63), (80, 80, 80), 1)
    for i in range(41):
        M = np.float32([[1, 0, i * 0.3], [0, 1, 0]])
        frame = cv2.warpAffine(base, M, (96, 64))
        writer.write(frame)
    writer.release()
    poses = np.repeat(np.eye(4)[None], 41, axis=0)
    poses[:, 0, 3] = np.linspace(0, 0.1, 41)
    K = np.repeat(np.array([[[80.0, 0, 48.0], [0, 80.0, 32.0], [0, 0, 1.0]]]), 41, axis=0)
    result = evaluate_csgc_video(path, poses, K, frame_i=0, frame_j=40, grid_rows=2, grid_cols=3, min_points_per_region=8)
    assert result.valid_region_count >= 3
    assert result.status == "ok"
    assert result.confidence > 0
