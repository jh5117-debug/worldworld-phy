import json
from pathlib import Path

import cv2
import numpy as np

from cam_physgeo.eval.reward_calibration_v2 import main


def _video(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 16, (48, 32))
    for i in range(6):
        frame = np.zeros((32, 48, 3), dtype=np.uint8)
        frame[:, :, 1] = 20 + i * 12
        writer.write(frame)
    writer.release()


def test_reward_calibration_v2_smoke(tmp_path):
    v = tmp_path / "sample" / "video.mp4"
    _video(v)
    manifest = tmp_path / "m.jsonl"
    manifest.write_text(json.dumps({"sample_id": "s0", "target_video": str(v), "template": "drop"}) + "\n", encoding="utf-8")
    out = tmp_path / "out"
    rc = main(["--manifest", str(manifest), "--out_dir", str(out), "--limit", "1", "--frame_count", "6", "--corruptions", "freeze_camera", "--skip_geometry"])
    assert rc == 0
    assert (out / "summary.json").exists()
    assert (out / "metrics" / "per_sample_metrics.csv").exists()
