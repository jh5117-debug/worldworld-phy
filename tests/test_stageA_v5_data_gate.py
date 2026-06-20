from __future__ import annotations

import json
from pathlib import Path

import pytest

from cam_physgeo.data import stageA_v5_data_gate as gate


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _ready(sample_id: str, root: Path, *, stage1_ready: bool = True, converted_valid: bool = True) -> dict:
    d = root / sample_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text(json.dumps({"prompt": "Synthetic indoor physical scene.", "prompt_variant": "structured_prompt_v2", "frame_indices": list(range(81))}), encoding="utf-8")
    return {
        "sample_id": sample_id,
        "hdf5_path": str(root / f"{sample_id}.hdf5"),
        "converted_dir": str(d),
        "target_video_path": str(d / "target.mp4"),
        "video_path": str(d / "video.mp4"),
        "poses_path": str(d / "poses.npy"),
        "intrinsics_path": str(d / "intrinsics.npy"),
        "prompt_path": str(d / "prompt.txt"),
        "template": "drop",
        "camera_variant": "orbit_left_72",
        "seed": sample_id,
        "scene_seed": sample_id,
        "source_file_size": 123,
        "source_file_mtime": 456,
        "raw_hdf5_valid": True,
        "converted_valid": converted_valid,
        "stage1_ready": stage1_ready,
        "blocked_reason": [] if stage1_ready else ["not_converted"],
    }


def test_snapshot_accepts_only_stage1_ready(tmp_path: Path) -> None:
    validation = tmp_path / "validation.jsonl"
    rows = [_ready("ok_a", tmp_path), _ready("raw_only", tmp_path, stage1_ready=False, converted_valid=False)]
    _write_jsonl(validation, rows)
    out = tmp_path / "snapshot"
    args = type("Args", (), {"validation_jsonl": str(validation), "out_dir": str(out), "timestamp": "t", "seed": 1})()
    assert gate.run_snapshot(args) == 0
    written = [json.loads(x) for x in (out / "stageA_v5_t_all.jsonl").read_text().splitlines()]
    assert [r["sample_id"] for r in written] == ["ok_a"]
    summary = json.loads((out / "stageA_v5_t_summary.json").read_text())
    assert summary["eligible_count"] == 1
    assert summary["stage1_ready_count"] == 1
    assert summary["blocked_count"] == 1


def test_snapshot_rejects_duplicate_sample_id(tmp_path: Path) -> None:
    validation = tmp_path / "validation.jsonl"
    _write_jsonl(validation, [_ready("dup", tmp_path), _ready("dup", tmp_path)])
    args = type("Args", (), {"validation_jsonl": str(validation), "out_dir": str(tmp_path / "out"), "timestamp": "t", "seed": 1})()
    with pytest.raises(ValueError, match="duplicate sample_id"):
        gate.run_snapshot(args)
