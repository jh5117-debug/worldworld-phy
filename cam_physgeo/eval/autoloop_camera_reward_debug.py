from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from cam_physgeo.utils.io import write_json


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _gpu_snapshot() -> str:
    try:
        return subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,memory.used,memory.total,utilization.gpu", "--format=csv"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=20,
        )
    except Exception as exc:  # pragma: no cover - host dependent
        return f"nvidia-smi unavailable: {exc!r}\n"


def _run_attempt(
    *,
    run_dir: Path,
    attempts_path: Path,
    commands_path: Path,
    attempt_id: int,
    phase: str,
    cmd: list[str],
    timeout: int,
    env: dict[str, str],
    dry_run: bool,
) -> dict[str, Any]:
    log_path = run_dir / "logs" / f"attempt_{attempt_id:04d}_{phase}.log"
    command_path = run_dir / "logs" / f"attempt_{attempt_id:04d}_{phase}.command.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = " ".join(shlex.quote(x) for x in cmd)
    command_path.write_text(command + "\n", encoding="utf-8")
    with commands_path.open("a", encoding="utf-8") as f:
        f.write(command + "\n")
    row: dict[str, Any] = {
        "attempt_id": attempt_id,
        "phase": phase,
        "command": command,
        "start_time": datetime.now().isoformat(timespec="seconds"),
        "stdout_log": str(log_path),
        "gpu_before": _gpu_snapshot(),
    }
    start = time.time()
    if dry_run:
        row.update({"status": "dry_run", "returncode": 0, "duration_sec": 0.0, "gpu_after": _gpu_snapshot(), "next_action": "not executed"})
    else:
        with log_path.open("w", encoding="utf-8", errors="replace") as log_f:
            proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT, text=True, env=env)
            try:
                proc.wait(timeout=timeout)
                row["returncode"] = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                log_f.write(f"\n[TIMEOUT] killed after {timeout}s\n")
                row.update({"returncode": proc.returncode, "error_type": "timeout"})
        row["duration_sec"] = round(time.time() - start, 3)
        row["gpu_after"] = _gpu_snapshot()
        row["status"] = "ok" if row.get("returncode") == 0 else "failed"
        if row["status"] == "failed" and "error_type" not in row:
            row["error_type"] = "unknown_exception"
        row["next_action"] = "continue" if row["status"] == "ok" else "inspect log and apply fallback"
    row["end_time"] = datetime.now().isoformat(timespec="seconds")
    with attempts_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-hours", "--max_hours", dest="max_hours", type=float, default=10.0)
    ap.add_argument("--gpu_ids", "--gpus", default="6,7")
    ap.add_argument("--sample_root", "--sample-root", default="local_assets/data/physion/processed/lingbot_cam_inputs/smoke")
    ap.add_argument("--rollout_root", "--rollout-root", default="local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke")
    ap.add_argument("--out_root", "--out-root", default="local_assets/reports/smoke")
    ap.add_argument("--timeout_per_attempt", "--timeout-per-attempt", dest="timeout_per_attempt", type=int, default=900)
    ap.add_argument("--stop_on_success", "--stop-on-success", dest="stop_on_success", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    run_dir = Path(args.out_root) / f"camera_reward_debug_autoloop_{_stamp()}"
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
    attempts_path = run_dir / "attempts.jsonl"
    commands_path = run_dir / "commands.sh"
    start_time = time.time()
    env = os.environ.copy()
    env.update(
        {
            "CUDA_VISIBLE_DEVICES": args.gpu_ids,
            "TRANSFORMERS_OFFLINE": "1",
            "HF_HUB_OFFLINE": "1",
            "PYTHONUNBUFFERED": "1",
            "TERM": "dumb",
            "TQDM_DISABLE": "1",
            "DISABLE_PROGRESS_BAR": "1",
        }
    )
    (run_dir / "environment.txt").write_text(
        json.dumps(
            {
                "cwd": os.getcwd(),
                "gpu_ids": args.gpu_ids,
                "sample_root": args.sample_root,
                "rollout_root": args.rollout_root,
                "start_time": datetime.now().isoformat(timespec="seconds"),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "gpu_snapshots.txt").write_text(_gpu_snapshot(), encoding="utf-8")

    ablation_out = "local_assets/data/physion/processed/rollouts/camera_ablation_strong_smoke"
    reward_out = "local_assets/reports/reward_calibration/fast_zero_shot_reward_debug"
    feature_out = "local_assets/reports/smoke/reward_feature_backend_check_camera_reward_debug.jsonl"
    commands = [
        (
            "compile",
            [sys.executable, "-m", "compileall", "-q", "cam_physgeo"],
            args.timeout_per_attempt + 120,
        ),
        (
            "camera_ablation_strong",
            [
                sys.executable,
                "-m",
                "cam_physgeo.eval.camera_condition_ablation",
                "--samples",
                args.sample_root,
                "--out",
                ablation_out,
                "--model_type",
                "fast",
                "--limit",
                "1",
                "--num_frames",
                "8",
                "--num_steps",
                "1",
                "--resolution",
                "480x832",
                "--variants",
                "repeat_correct_A",
                "repeat_correct_B",
                "correct",
                "frozen",
                "reversed",
                "exaggerated_yaw",
                "--same_seed",
                "true",
                "--save_contact_sheet",
                "--debug-camera-condition",
                "--save-condition-summary",
                "--timeout",
                str(args.timeout_per_attempt),
                "--local-files-only",
            ],
            max(args.timeout_per_attempt + 120, 6 * (args.timeout_per_attempt + 90)),
        ),
        (
            "reward_debug",
            [
                sys.executable,
                "-m",
                "cam_physgeo.eval.eval_fast_rollouts",
                "--samples",
                args.sample_root,
                "--rollouts",
                args.rollout_root,
                "--out",
                reward_out,
                "--limit",
                "3",
                "--save_debug",
                "--gpu_ids",
                args.gpu_ids,
                "--debug_reward_breakdown",
                "--confidence_weighted",
                "--report_all_variants",
            ],
            args.timeout_per_attempt + 120,
        ),
        (
            "feature_dinov2",
            [sys.executable, "-m", "cam_physgeo.trd.feature_extractors", "--check", "dinov2", "--weights_root", "local_assets/weights", "--device", "cuda", "--limit", "1"],
            180,
        ),
        (
            "feature_vjepa_or_videomae",
            [sys.executable, "-m", "cam_physgeo.trd.feature_extractors", "--check", "vjepa2_or_videomae2", "--weights_root", "local_assets/weights", "--device", "cuda", "--limit", "1"],
            180,
        ),
        (
            "feature_required_score",
            [
                sys.executable,
                "-m",
                "cam_physgeo.rewards.score_video",
                "--manifest",
                "local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl",
                "--source",
                "physion_movingcam",
                "--out",
                feature_out,
                "--limit",
                "3",
                "--save_debug_vis",
                "--require_feature_backend",
                "true",
                "--device",
                "cuda",
            ],
            args.timeout_per_attempt + 120,
        ),
    ]

    rows = []
    status = "success"
    for idx, (phase, cmd, timeout) in enumerate(commands, start=1):
        if (time.time() - start_time) / 3600.0 > args.max_hours:
            status = "timeout_budget_exhausted"
            break
        row = _run_attempt(
            run_dir=run_dir,
            attempts_path=attempts_path,
            commands_path=commands_path,
            attempt_id=idx,
            phase=phase,
            cmd=cmd,
            timeout=timeout,
            env=env,
            dry_run=args.dry_run,
        )
        rows.append(row)
        if row["status"] not in {"ok", "dry_run"}:
            status = "partial_success"
            # Do not enter VideoGPA/DPO fallback. Continue to independent diagnostics.

    final = {
        "status": status,
        "run_dir": str(run_dir),
        "start_time": datetime.fromtimestamp(start_time).isoformat(timespec="seconds"),
        "end_time": datetime.now().isoformat(timespec="seconds"),
        "total_hours": round((time.time() - start_time) / 3600.0, 4),
        "attempt_count": len(rows),
        "ablation_out": ablation_out,
        "reward_out": reward_out,
        "feature_out": feature_out,
        "no_training": True,
        "no_dpo": True,
        "no_videogpa_encode": True,
        "max_new_fast_videos_intended": 6,
    }
    write_json(final, run_dir / "final_status.json")
    (run_dir / "summary.md").write_text(
        "# Camera Reward Debug Autoloop\n\n"
        f"- Status: {status}\n"
        f"- Total hours: {final['total_hours']}\n"
        f"- Attempts: {len(rows)}\n"
        f"- Ablation output: `{ablation_out}`\n"
        f"- Reward debug output: `{reward_out}`\n"
        f"- Feature check output: `{feature_out}`\n"
        "- Safety: no training, no DPO, no VideoGPA encode.\n",
        encoding="utf-8",
    )
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0 if status in {"success", "partial_success"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
