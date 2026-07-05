from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any


WINNER_DETACHED_REPORT_ROOT = "reports/dpo_tiny_guarded_preference_v12c/winner_detached_preference"
WINNER_DETACHED_OUTPUT_ROOT = "local_assets/dpo_tiny_guarded_preference_v12c/winner_detached_preference"
WARM_START = "local_assets/dpo_objective_repair_v12b/winner_curriculum/checkpoints/winner_anchor_repeat_L0_camera_r4_step020_lora_state.pt"


def winner_detached_command(assigned_gpu: int) -> list[str]:
    return [
        "python3", "-m", "cam_physgeo.dpo.dpo_v12c_guarded_probe",
        "--train_manifest", "manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl",
        "--val_manifest", "manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl",
        "--scope", "L0_camera_r4",
        "--objective", "winner_detached_preference",
        "--steps", "10",
        "--beta", "0.1",
        "--lambda_winner_anchor", "1.0",
        "--lambda_pref", "0.02",
        "--lambda_loser", "0.0",
        "--init_lora_state", WARM_START,
        "--gpu", "0",
        "--prefix_len", "5",
        "--prediction_start_frame", "5",
        "--future_only", "true",
        "--output_root", WINNER_DETACHED_OUTPUT_ROOT,
        "--report_root", WINNER_DETACHED_REPORT_ROOT,
    ]


def default_jobs() -> list[dict[str, Any]]:
    return [
        {
            "job_id": "preflight_state_check",
            "type": "audit",
            "status": "PENDING",
            "required_gpus": 0,
            "assigned_gpus": [],
            "command": "internal:preflight_state_check",
            "depends_on": [],
            "gate": "preflight",
            "summary_path": "reports/dpo_gpu_scheduler_v12d/preflight_state_check.md",
        },
        {
            "job_id": "v12c_winner_detached_preference_s_pass4",
            "type": "train",
            "status": "PENDING",
            "required_gpus": 1,
            "preferred_gpus": [4, 5, 6, 7],
            "assigned_gpus": [],
            "command": "dynamic:winner_detached_command",
            "depends_on": ["preflight_state_check"],
            "gate": "training_signal",
            "report_root": WINNER_DETACHED_REPORT_ROOT,
            "summary_path": f"{WINNER_DETACHED_REPORT_ROOT}/training_summary.md",
        },
        {
            "job_id": "v12c_checkpoint_eval_winner_detached",
            "type": "eval",
            "status": "PENDING",
            "required_gpus": 1,
            "preferred_gpus": [4, 5, 6, 7],
            "assigned_gpus": [],
            "command": "blocked:checkpoint_eval_runner_required",
            "depends_on": ["v12c_winner_detached_preference_s_pass4"],
            "gate": "checkpoint_video_eval",
            "summary_path": "reports/dpo_tiny_guarded_preference_v12c/winner_detached_preference/checkpoint_eval/summary.md",
        },
        {
            "job_id": "v12c_tiny_loser_gradient_preference",
            "type": "train",
            "status": "PENDING",
            "required_gpus": 1,
            "preferred_gpus": [4, 5, 6, 7],
            "assigned_gpus": [],
            "command": "blocked:requires_checkpoint_eval_pass",
            "depends_on": ["v12c_checkpoint_eval_winner_detached"],
            "gate": "training_signal_and_no_loser_dominance",
            "summary_path": "reports/dpo_tiny_guarded_preference_v12c/tiny_loser_gradient_preference/training_summary.md",
        },
        {
            "job_id": "fallback_pair_and_metric_qa",
            "type": "fallback",
            "status": "PENDING",
            "required_gpus": 0,
            "assigned_gpus": [],
            "command": "internal:fallback_pair_and_metric_qa",
            "depends_on": [],
            "gate": "fallback_only_after_training_fail",
            "summary_path": "reports/dpo_gpu_scheduler_v12d/fallback_pair_and_metric_qa.md",
            "manual_trigger_only": True,
        },
    ]


def build_command(job: dict[str, Any], assigned_gpu: int | None = None) -> list[str]:
    if job.get("command") == "dynamic:winner_detached_command":
        if assigned_gpu is None:
            raise ValueError("assigned_gpu is required for winner detached command")
        return winner_detached_command(int(assigned_gpu))
    raise ValueError(f"No dynamic command for {job.get('job_id')}: {job.get('command')}")


def fresh_job_state() -> list[dict[str, Any]]:
    return deepcopy(default_jobs())
