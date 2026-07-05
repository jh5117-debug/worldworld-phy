from pathlib import Path

from cam_physgeo.data.build_v2v5_warmup_4900_split import scan_roots


def test_scan_roots_rejects_missing_required(tmp_path: Path):
    root = tmp_path / "converted"
    good = root / "00001_drop_orbit_left_72_seed1"
    bad = root / "00002_drop_orbit_left_72_seed2"
    good.mkdir(parents=True)
    bad.mkdir(parents=True)
    for name in ("video.mp4", "target.mp4", "image.jpg", "poses.npy", "intrinsics.npy", "prompt.txt", "metadata.json"):
        (good / name).write_text("{}" if name == "metadata.json" else "x", encoding="utf-8")
    (bad / "video.mp4").write_text("x", encoding="utf-8")
    rows, rejected = scan_roots([root])
    assert len(rows) == 1
    assert rows[0]["sample_id"] == good.name
    assert rejected and rejected[0]["sample_id"] == bad.name
