import csv
import json
from pathlib import Path

from cam_physgeo.orchestration.gate_checks_v12d import check_training_signal, check_gpu_usage_only_allowed, check_no_loser_dominance


def test_training_signal_pass(tmp_path: Path):
    root = tmp_path / "run"
    root.mkdir()
    (root / "training_summary.json").write_text(json.dumps({
        "rows_written": 2,
        "steps_requested": 2,
        "mean_winner_improvement_post": 0.1,
        "final_winner_improvement_post": 0.2,
        "mean_winner_contribution_ratio_post": 1.0,
        "status": "WINNER_DETACHED_PREFERENCE_PASS",
    }))
    with (root / "winner_detached_preference_10step.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["status", "grad_norm", "update_norm", "dpo_loss", "winner_contribution_ratio_post", "winner_improvement_post"])
        w.writeheader()
        w.writerow({"status": "PASS", "grad_norm": "1", "update_norm": "1", "dpo_loss": "0.69", "winner_contribution_ratio_post": "1", "winner_improvement_post": "0.1"})
        w.writerow({"status": "PASS", "grad_norm": "1", "update_norm": "1", "dpo_loss": "0.68", "winner_contribution_ratio_post": "1", "winner_improvement_post": "0.2"})
    assert check_training_signal(root)["status"] == "PASS"


def test_training_signal_fails_negative_winner(tmp_path: Path):
    root = tmp_path / "run"
    root.mkdir()
    (root / "training_summary.json").write_text(json.dumps({"rows_written": 1, "steps_requested": 1, "mean_winner_improvement_post": -1, "final_winner_improvement_post": -1, "status": "FAIL"}))
    assert check_training_signal(root)["status"] == "FAIL"


def test_gpu_assignment_check(tmp_path: Path):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"jobs": [{"assigned_gpus": [4]}, {"assigned_gpus": []}]}))
    assert check_gpu_usage_only_allowed(state)["status"] == "PASS"
    state.write_text(json.dumps({"jobs": [{"assigned_gpus": [0]}]}))
    assert check_gpu_usage_only_allowed(state)["status"] == "FAIL"


def test_loser_dominance_check(tmp_path: Path):
    csv_path = tmp_path / "m.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["winner_contribution_ratio_post", "winner_improvement_post"])
        w.writeheader()
        w.writerow({"winner_contribution_ratio_post": "0.1", "winner_improvement_post": "0.0"})
        w.writerow({"winner_contribution_ratio_post": "0.2", "winner_improvement_post": "-0.1"})
    assert check_no_loser_dominance(csv_path)["status"] == "FAIL"
