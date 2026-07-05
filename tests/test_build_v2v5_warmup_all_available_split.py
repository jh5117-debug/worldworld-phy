from pathlib import Path
from cam_physgeo.data.build_v2v5_warmup_all_available_split import scan_roots


def test_scan_roots_deduplicates_and_rejects(tmp_path: Path):
    r1 = tmp_path / "r1"
    r2 = tmp_path / "r2"
    good1 = r1 / "00001_drop_orbit_left_72_seed1"
    dup = r2 / good1.name
    bad = r1 / "00002_drop_orbit_left_72_seed2"
    for d in (good1, dup, bad):
        d.mkdir(parents=True)
    for d in (good1, dup):
        for name in ("video.mp4", "target.mp4", "image.jpg", "poses.npy", "intrinsics.npy", "prompt.txt", "metadata.json"):
            (d / name).write_text("{}" if name == "metadata.json" else "x", encoding="utf-8")
    (bad / "video.mp4").write_text("x", encoding="utf-8")
    rows, rejected = scan_roots([r1, r2])
    assert len(rows) == 1
    assert rows[0]["sample_id"] == good1.name
    assert rejected[0]["sample_id"] == bad.name
