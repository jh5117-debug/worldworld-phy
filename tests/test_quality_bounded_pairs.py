import csv
import json
from pathlib import Path

from cam_physgeo.dpo.quality_bounded_pairs import main


def test_quality_bounded_pair_builder(tmp_path):
    cond = tmp_path / "conditions.jsonl"
    cond.write_text(json.dumps({"sample_id": "s0", "target_video": "gt.mp4", "template": "drop"}) + "\n", encoding="utf-8")
    metrics = tmp_path / "metrics.csv"
    with metrics.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", "model", "candidate_video", "decode_status", "quality_proxy", "ssim", "csgc_score", "freeze_rate", "pixel_l1_proxy", "failure_tags"])
        writer.writeheader()
        writer.writerow({"sample_id": "s0", "model": "GT", "candidate_video": "gt.mp4", "decode_status": "ok", "quality_proxy": 1.0, "ssim": 1.0, "csgc_score": 1.0, "freeze_rate": 0.0, "pixel_l1_proxy": 0.0, "failure_tags": ""})
        writer.writerow({"sample_id": "s0", "model": "candidate", "candidate_video": "bad.mp4", "decode_status": "ok", "quality_proxy": 0.82, "ssim": 0.80, "csgc_score": 0.75, "freeze_rate": 0.1, "pixel_l1_proxy": 0.1, "failure_tags": "wrong_camera"})
        writer.writerow({"sample_id": "s0", "model": "collapsed", "candidate_video": "collapse.mp4", "decode_status": "ok", "quality_proxy": 0.05, "ssim": 0.1, "csgc_score": 0.1, "freeze_rate": 1.0, "pixel_l1_proxy": 0.8, "failure_tags": "global_freeze"})
    out = tmp_path / "pairs.jsonl"
    rejected = tmp_path / "rejected.jsonl"
    rc = main(["--conditions", str(cond), "--metrics_csv", str(metrics), "--out", str(out), "--rejected_out", str(rejected), "--min_margin", "0.03", "--max_margin", "0.30"])
    assert rc == 0
    pairs = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert len(pairs) == 1
    assert pairs[0]["loser"]["source"] == "candidate"
    assert "wrong_camera" in pairs[0]["hard_negative_tags"]
    assert "collapsed" in rejected.read_text(encoding="utf-8")
