
import csv
from pathlib import Path


def test_camera_condition_audit_declares_not_run_not_fabricated():
    path = Path("reports/fast_support_diagnosis/camera_condition_audit.csv")
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    assert {row["variant"] for row in rows} >= {"correct_camera", "frozen_camera", "reversed_camera"}
    assert all(row["status"] == "NOT_RUN_THIS_ROUND" for row in rows)
    assert all(row["does_camera_affect_output"] == "UNKNOWN" for row in rows)
