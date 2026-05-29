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


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def shell_join(cmd: list[str]) -> str:
    return " ".join(shlex.quote(str(x)) for x in cmd)


def gpu_snapshot() -> str:
    try:
        return subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,memory.used,memory.total,utilization.gpu", "--format=csv"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=20,
        )
    except Exception as exc:
        return f"nvidia-smi unavailable: {exc!r}\n"


def classify_failure(log_text: str, returncode: int | None) -> str:
    lower = log_text.lower()
    if returncode == 124 or "timeout" in lower:
        return "timeout"
    if "cuda out of memory" in lower or "outofmemoryerror" in lower:
        return "oom"
    if "intrinsics" in lower and ("shape" in lower or "unsupported" in lower):
        return "intrinsics_conversion_error"
    if "no module named" in lower or "importerror" in lower:
        return "import_error"
    if "t5" in lower and "timeout" in lower:
        return "t5_timeout"
    if "traceback" in lower:
        return "unknown_exception"
    if returncode not in (0, None):
        return "unknown_exception"
    return ""


class Loop:
    def __init__(self, args):
        self.args = args
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = Path(args.out_root) / f"fast_rollout_reward_autoloop_{stamp}"
        self.logs_dir = self.run_dir / "logs"
        self.outputs_dir = self.run_dir / "outputs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        for sub in ["rollout", "camera_ablation", "reward_on_rollout", "contact_sheets", "debug_vis"]:
            (self.outputs_dir / sub).mkdir(parents=True, exist_ok=True)
        self.attempts_path = self.run_dir / "attempts.jsonl"
        self.commands_path = self.run_dir / "commands.sh"
        self.gpu_path = self.run_dir / "gpu_snapshots.txt"
        self.start = time.time()
        self.attempt_id = 0
        self.final: dict[str, Any] = {
            "status": "running",
            "start_time": now(),
            "run_dir": str(self.run_dir),
            "rollout_ok_count": 0,
            "ablation_ok_count": 0,
            "reward_valid_pairs": 0,
            "feature_backend_checked": False,
        }
        self.write_environment()

    def remaining(self) -> float:
        return max(0.0, float(self.args.max_hours) * 3600.0 - (time.time() - self.start))

    def write_environment(self) -> None:
        lines = [
            f"start_time={now()}",
            f"cwd={Path.cwd()}",
            f"python={sys.executable}",
            f"gpu_ids={self.args.gpu_ids}",
            f"sample_root={self.args.sample_root}",
            f"max_rollouts={self.args.max_rollouts}",
            "",
            "git:",
        ]
        try:
            lines.append(subprocess.check_output(["git", "status", "-sb"], text=True, stderr=subprocess.STDOUT, timeout=20))
            lines.append(subprocess.check_output(["git", "log", "-1", "--oneline"], text=True, stderr=subprocess.STDOUT, timeout=20))
        except Exception as exc:
            lines.append(f"git unavailable: {exc!r}")
        lines.extend(["", "gpu:", gpu_snapshot()])
        (self.run_dir / "environment.txt").write_text("\n".join(lines), encoding="utf-8")

    def append_attempt(self, row: dict[str, Any]) -> None:
        with self.attempts_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def run(self, phase: str, cmd: list[str], *, timeout: int | None = None, env_extra: dict[str, str] | None = None) -> dict[str, Any]:
        self.attempt_id += 1
        attempt = f"attempt_{self.attempt_id:04d}_{phase}"
        log_path = self.logs_dir / f"{attempt}.log"
        command_path = self.logs_dir / f"{attempt}.command.txt"
        command_path.write_text(shell_join(cmd) + "\n", encoding="utf-8")
        with self.commands_path.open("a", encoding="utf-8") as f:
            f.write(f"# {attempt}\n{shell_join(cmd)}\n\n")
        gpu_before = gpu_snapshot()
        with self.gpu_path.open("a", encoding="utf-8") as f:
            f.write(f"\n## {attempt} before {now()}\n{gpu_before}\n")
        start = time.time()
        env = os.environ.copy()
        env.update(
            {
                "PYTHONUNBUFFERED": "1",
                "TERM": "dumb",
                "TQDM_DISABLE": "1",
                "DISABLE_PROGRESS_BAR": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "HF_HUB_OFFLINE": "1",
            }
        )
        if self.args.gpu_ids:
            env["CUDA_VISIBLE_DEVICES"] = self.args.gpu_ids
        if env_extra:
            env.update(env_extra)
        status = "failed"
        returncode = None
        timeout_used = int(timeout or self.args.timeout_per_attempt)
        with log_path.open("w", encoding="utf-8", errors="replace") as log_f:
            proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT, text=True, env=env)
            try:
                returncode = proc.wait(timeout=min(timeout_used, max(1, int(self.remaining()))))
            except subprocess.TimeoutExpired:
                proc.kill()
                returncode = proc.wait()
                log_f.write(f"\n[TIMEOUT] killed after {timeout_used}s\n")
        duration = time.time() - start
        gpu_after = gpu_snapshot()
        with self.gpu_path.open("a", encoding="utf-8") as f:
            f.write(f"\n## {attempt} after {now()}\n{gpu_after}\n")
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        if returncode == 0:
            status = "ok"
        row = {
            "attempt_id": self.attempt_id,
            "phase": phase,
            "command": cmd,
            "command_path": str(command_path),
            "start_time": datetime.fromtimestamp(start).isoformat(timespec="seconds"),
            "end_time": now(),
            "duration_sec": round(duration, 3),
            "status": status,
            "returncode": returncode,
            "error_type": "" if status == "ok" else classify_failure(log_text[-8000:], returncode),
            "last_marker": self.extract_last_marker(log_text),
            "stdout_log": str(log_path),
            "gpu_before": gpu_before,
            "gpu_after": gpu_after,
            "next_action": "",
        }
        self.append_attempt(row)
        return row

    @staticmethod
    def extract_last_marker(log_text: str) -> str:
        markers = [line.strip() for line in log_text.splitlines() if "[MARK]" in line or '"event"' in line]
        return markers[-1][-500:] if markers else ""

    def count_rollouts(self, rollout_root: Path) -> int:
        return sum(1 for p in rollout_root.glob("*/generated.mp4") if p.exists())

    def run_all(self) -> dict[str, Any]:
        if self.args.dry_run:
            self.final.update({"status": "dry_run", "end_time": now()})
            self.finish()
            return self.final

        self.run("compile", [sys.executable, "-m", "compileall", "-q", "cam_physgeo"], timeout=180)
        self.run("intrinsics_test", [sys.executable, "tests/test_intrinsics_conversion.py"], timeout=120)

        rollout_root = Path("local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke")
        rollout_limit = max(1, min(int(self.args.max_rollouts), 3))
        rollout_cmd = [
            sys.executable,
            "-m",
            "cam_physgeo.eval.run_inference",
            "--config",
            "configs/cam_physgeo/eval.yaml",
            "--model_type",
            "fast",
            "--samples",
            self.args.sample_root,
            "--out",
            str(rollout_root),
            "--smoke-run",
            "--limit",
            str(rollout_limit),
            "--num_frames",
            "8",
            "--num_steps",
            "1",
            "--resolution",
            "480x832",
            "--timeout",
            str(self.args.timeout_per_attempt),
            "--local-files-only",
            "--save_contact_sheet",
        ]
        row = self.run("rollout_f8_s1_480x832", rollout_cmd, timeout=self.args.timeout_per_attempt * max(1, rollout_limit) + 120)
        rollout_ok = self.count_rollouts(rollout_root)
        if rollout_ok < min(3, rollout_limit):
            fallback_cmd = rollout_cmd.copy()
            fallback_cmd[fallback_cmd.index("480x832")] = "256x448"
            row = self.run("rollout_f8_s1_256x448", fallback_cmd, timeout=self.args.timeout_per_attempt * max(1, rollout_limit) + 120)
            rollout_ok = self.count_rollouts(rollout_root)
        self.final["rollout_ok_count"] = rollout_ok

        ablation_root = Path("local_assets/data/physion/processed/rollouts/camera_ablation_smoke")
        if rollout_ok >= 1 and self.remaining() > 600:
            ablation_cmd = [
                sys.executable,
                "-m",
                "cam_physgeo.eval.camera_condition_ablation",
                "--samples",
                self.args.sample_root,
                "--out",
                str(ablation_root),
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
                "correct",
                "frozen",
                "reversed",
                "--save_contact_sheet",
                "--timeout",
                str(self.args.timeout_per_attempt),
                "--local-files-only",
            ]
            self.run("camera_ablation_correct_frozen_reversed", ablation_cmd, timeout=self.args.timeout_per_attempt * 3 + 240)
            summary = ablation_root / "camera_ablation_summary.json"
            if summary.exists():
                try:
                    self.final["ablation_ok_count"] = int(json.loads(summary.read_text(encoding="utf-8")).get("ok_count", 0))
                except Exception:
                    self.final["ablation_ok_count"] = 0

        reward_root = Path("local_assets/reports/reward_calibration/fast_zero_shot_smoke")
        if rollout_ok >= 1:
            reward_cmd = [
                sys.executable,
                "-m",
                "cam_physgeo.eval.eval_fast_rollouts",
                "--samples",
                self.args.sample_root,
                "--rollouts",
                str(rollout_root),
                "--out",
                str(reward_root),
                "--limit",
                str(min(rollout_ok, 10)),
                "--save_debug",
                "--gpu_ids",
                self.args.gpu_ids,
            ]
            self.run("reward_on_rollout", reward_cmd, timeout=900)
            table = reward_root / "per_metric_table.csv"
            if table.exists():
                self.final["reward_valid_pairs"] = max(0, len(table.read_text(encoding="utf-8").splitlines()) - 1)

        feature_cmds = [
            [sys.executable, "-m", "cam_physgeo.trd.feature_extractors", "--check", "dinov2", "--weights_root", "local_assets/weights", "--device", "cuda", "--limit", "1"],
            [sys.executable, "-m", "cam_physgeo.trd.feature_extractors", "--check", "vjepa2_or_videomae2", "--weights_root", "local_assets/weights", "--device", "cuda", "--limit", "1"],
            [
                sys.executable,
                "-m",
                "cam_physgeo.rewards.score_video",
                "--manifest",
                "local_assets/data/physion/manifests/physion_cam_physgeo_smoke.jsonl",
                "--source",
                "physion_movingcam",
                "--out",
                "local_assets/reports/smoke/reward_feature_backend_check_after_rollout.jsonl",
                "--limit",
                "3",
                "--save_debug_vis",
                "--require_feature_backend",
                "true",
            ],
        ]
        feature_results = []
        for i, cmd in enumerate(feature_cmds, 1):
            if self.remaining() < 120:
                break
            feature_results.append(self.run(f"feature_backend_{i}", cmd, timeout=600))
        self.final["feature_backend_checked"] = bool(feature_results)

        status = "success"
        if self.final["rollout_ok_count"] < 3 or self.final["ablation_ok_count"] < 1 or self.final["reward_valid_pairs"] < 1:
            status = "partial_success" if self.final["rollout_ok_count"] >= 1 else "failed"
        if self.remaining() <= 0:
            status = "timeout_budget_exhausted"
        self.final.update({"status": status, "end_time": now(), "total_hours": round((time.time() - self.start) / 3600.0, 4)})
        self.finish()
        return self.final

    def finish(self) -> None:
        write_json(self.final, self.run_dir / "final_status.json")
        lines = [
            "# Fast Rollout Reward Autoloop Summary",
            "",
            f"- Status: {self.final.get('status')}",
            f"- Run dir: `{self.run_dir}`",
            f"- Rollout ok count: {self.final.get('rollout_ok_count')}",
            f"- Ablation ok count: {self.final.get('ablation_ok_count')}",
            f"- Reward valid pairs: {self.final.get('reward_valid_pairs')}",
            f"- Feature backend checked: {self.final.get('feature_backend_checked')}",
            "",
            "This smoke loop did not run training, DPO, VideoGPA encode, or Stage1 warm-up.",
        ]
        (self.run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-hours", type=float, default=10.0)
    ap.add_argument("--gpu_ids", "--gpus", dest="gpu_ids", default="6,7")
    ap.add_argument("--timeout-per-attempt", type=int, default=900)
    ap.add_argument("--sample_root", "--sample-root", dest="sample_root", default="local_assets/data/physion/processed/lingbot_cam_inputs/smoke")
    ap.add_argument("--out_root", "--out-root", dest="out_root", default="local_assets/reports/smoke")
    ap.add_argument("--max_rollouts", "--max-rollouts", dest="max_rollouts", type=int, default=10)
    ap.add_argument("--stop_on_success", "--stop-on-success", dest="stop_on_success", action="store_true")
    args = ap.parse_args(argv)
    loop = Loop(args)
    final = loop.run_all()
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0 if final.get("status") in {"success", "partial_success", "dry_run"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
