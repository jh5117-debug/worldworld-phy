from pathlib import Path

from cam_physgeo.orchestration.physeditworld_gpu_policy_audit import (
    classify_visible_devices,
    decide,
    iter_target_files,
    scan_file,
)


def test_classify_visible_devices_allows_gpu4_7():
    status, detail = classify_visible_devices("4,5,6,7")
    assert status == "GPU_POLICY_PASS"
    assert "allowed=4,5,6,7" in detail


def test_classify_visible_devices_blocks_gpu0_3():
    status, detail = classify_visible_devices("0,4")
    assert status == "FORBIDDEN_GPU_ASSIGNMENT"
    assert "0" in detail


def test_classify_visible_devices_marks_dynamic_for_review():
    status, _ = classify_visible_devices("${CUDA_VISIBLE_DEVICES:-4}")
    assert status == "DYNAMIC_OR_EMPTY_ASSIGNMENT"


def test_scan_file_detects_assignments(tmp_path: Path):
    script = tmp_path / "run.sh"
    script.write_text("CUDA_VISIBLE_DEVICES=4 python ok.py\nCUDA_VISIBLE_DEVICES=3 python bad.py\n", encoding="utf-8")
    rows = scan_file(script)
    assert [row.status for row in rows] == ["GPU_POLICY_PASS", "FORBIDDEN_GPU_ASSIGNMENT"]


def test_decide_blocks_forbidden(tmp_path: Path):
    script = tmp_path / "run.sh"
    script.write_text("CUDA_VISIBLE_DEVICES=0 python bad.py\n", encoding="utf-8")
    rows = scan_file(script)
    assert decide(rows, scanned_files=1) == "PHYS_EDITWORLD_GPU_COMMAND_POLICY_BLOCKED_FORBIDDEN_ASSIGNMENT"


def test_decide_passes_no_assignments_when_files_scanned(tmp_path: Path):
    script = tmp_path / "run.sh"
    script.write_text("echo hello\n", encoding="utf-8")
    assert decide([], scanned_files=1) == "PHYS_EDITWORLD_GPU_COMMAND_POLICY_PASS"
