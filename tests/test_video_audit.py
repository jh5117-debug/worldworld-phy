from pathlib import Path

import cv2
import numpy as np

from cam_physgeo.eval.video_audit import main


def test_video_audit_smoke(tmp_path):
    video = tmp_path / "vids" / "sample.mp4"
    video.parent.mkdir(parents=True)
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 16, (48, 32))
    for i in range(6):
        frame = np.zeros((32, 48, 3), dtype=np.uint8)
        frame[:, :, 2] = 40 + i * 5
        writer.write(frame)
    writer.release()
    out = tmp_path / "audit"
    rc = main(["--video_dir", str(video.parent), "--model_label", "m", "--out_dir", str(out), "--max_frames", "6"])
    assert rc == 0
    assert (out / "all_video_audit.csv").exists()
    assert list((out / "contact_sheets").glob("*.jpg"))
