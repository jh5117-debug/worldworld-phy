from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from cam_physgeo.utils.io import ensure_dir, load_yaml, write_json


DEFAULT_PY = "/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python"


@dataclass
class AttemptResult:
    attempt_id: int
    phase: str
    command: str
    start_time: str
    end_time: str
    duration_sec: float
    status: str
    returncode: int | None
    error_type: str
    last_marker: str
    next_action: str
    log_path: str
    out_dir: str


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run_text(cmd: list[str], *, cwd: Path, timeout: int = 60, env: dict[str, str] | None = None) -> str:
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return proc.stdout.strip()
    except Exception as exc:  # pragma: no cover - host dependent
        return f"ERROR: {exc!r}"


def gpu_snapshot() -> str:
    return run_text(
        ["nvidia-smi", "--query-gpu=index,memory.used,memory.total,utilization.gpu", "--format=csv"],
        cwd=Path.cwd(),
        timeout=30,
    )


def redact_log_tail(text: str, limit: int = 4000) -> str:
    tail = text[-limit:]
    # Keep technical tracebacks, but avoid preserving accidental terminal garbage.
    return tail.replace("\x00", "")


def last_marker(log_text: str) -> str:
    marker = ""
    for line in log_text.splitlines():
        if "[MARK]" in line:
            marker = line.strip()
            continue
        if '"event"' in line:
            try:
                event = json.loads(line).get("event")
                if event:
                    marker = str(event)
            except Exception:
                pass
    return marker


def classify_error(log_text: str, returncode: int | None, timed_out: bool) -> str:
    low = log_text.lower()
    if timed_out:
        if "t5" in low:
            return "t5_timeout"
        return "timeout"
    if returncode == 0:
        return ""
    patterns = [
        ("out of memory", "oom"),
        ("cuda out of memory", "oom"),
        ("cublas", "cuda_error"),
        ("cuda error", "cuda_error"),
        ("no module named", "import_error"),
        ("modulenotfounderror", "import_error"),
        ("importerror", "import_error"),
        ("filenotfounderror", "missing_weight"),
        ("no such file", "missing_weight"),
        ("vae", "vae_load_error"),
        ("checkpoint", "fast_model_load_error"),
        ("safetensors", "dit_shard_error"),
        ("unknown option", "unsupported_arg"),
        ("unrecognized arguments", "unsupported_arg"),
        ("action", "dummy_action_error"),
        ("pose", "pose_load_error"),
        ("intrinsics", "intrinsics_load_error"),
        ("save_video", "save_video_error"),
        ("ffmpeg", "ffmpeg_error"),
        ("wani2vfast", "pipeline_api_mismatch"),
        ("typeerror", "pipeline_api_mismatch"),
    ]
    for needle, error in patterns:
        if needle in low:
            return error
    if returncode not in (0, None):
        return "unknown_exception"
    return ""


def shell_join(parts: list[str]) -> str:
    import shlex

    return " ".join(shlex.quote(str(p)) for p in parts)


class Autoloop:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.cwd = Path.cwd()
        self.start_monotonic = time.monotonic()
        self.start_wall = now_iso()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = ensure_dir(Path(args.out_root) / f"fast_inference_autoloop_{stamp}")
        self.logs_dir = ensure_dir(self.run_dir / "logs")
        self.outputs_dir = ensure_dir(self.run_dir / "outputs")
        self.attempts_path = self.run_dir / "attempts.jsonl"
        self.commands_path = self.run_dir / "commands.sh"
        self.gpu_path = self.run_dir / "gpu_snapshots.txt"
        self.attempt_id = 0
        self.success: dict[str, Any] | None = None
        self.final_status: dict[str, Any] = {}
        self.py = args.python or DEFAULT_PY
        self.base_env = os.environ.copy()
        self.base_env.setdefault("PYTHONUNBUFFERED", "1")
        self.base_env.setdefault("TOKENIZERS_PARALLELISM", "false")
        self.base_env.setdefault("TRANSFORMERS_OFFLINE", "1")
        self.base_env.setdefault("HF_HUB_OFFLINE", "1")
        self.base_env.setdefault("HF_DATASETS_OFFLINE", "1")

    def append(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", errors="replace") as f:
            f.write(text)

    def write_environment(self) -> None:
        paths = load_yaml("configs/cam_physgeo/paths.yaml")
        env = {
            "hostname": socket.gethostname(),
            "pwd": str(self.cwd),
            "worktree": self.args.worktree,
            "branch": run_text(["git", "branch", "--show-current"], cwd=self.cwd),
            "commit": run_text(["git", "rev-parse", "HEAD"], cwd=self.cwd),
            "git_status": run_text(["git", "status", "--short"], cwd=self.cwd),
            "git_remote": run_text(["git", "remote", "-v"], cwd=self.cwd),
            "python": self.py,
            "local_assets": str((self.cwd / "local_assets").resolve()) if (self.cwd / "local_assets").exists() else "missing",
            "local_assets_is_symlink": (self.cwd / "local_assets").is_symlink(),
            "paths_yaml_head": {k: paths.get(k) for k in ["LOCAL_ASSETS_ROOT", "LINGBOT_FAST_ROOT", "LINGBOT_BASE_ROOT", "LINGBOT_CODE_ROOT", "LINGBOT_ENV"]},
            "sample_root": self.args.sample_root,
            "gpu_ids": self.args.gpu_ids,
            "max_hours": self.args.max_hours,
            "timeout_per_attempt": self.args.timeout_per_attempt,
            "initial_gpu": gpu_snapshot(),
            "running_processes": run_text(["bash", "-lc", 'pgrep -af "train|accelerate|run_inference|cam_physgeo|lingbot|python|VideoGPA" || echo none'], cwd=self.cwd),
        }
        write_json(env, self.run_dir / "environment.json")
        (self.run_dir / "environment.txt").write_text(json.dumps(env, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def budget_remaining(self) -> float:
        return self.args.max_hours * 3600 - (time.monotonic() - self.start_monotonic)

    def command_env(self, gpu_ids: str | None = None, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = self.base_env.copy()
        if gpu_ids is not None:
            env["CUDA_VISIBLE_DEVICES"] = gpu_ids
        if extra:
            env.update(extra)
        return env

    def run_attempt(
        self,
        phase: str,
        cmd: list[str],
        *,
        timeout: int | None = None,
        env: dict[str, str] | None = None,
        out_dir: Path | None = None,
        next_action_success: str = "",
        next_action_failure: str = "",
    ) -> AttemptResult:
        self.attempt_id += 1
        attempt_out = out_dir or ensure_dir(self.outputs_dir / f"attempt_{self.attempt_id:04d}_{phase}")
        attempt_out.mkdir(parents=True, exist_ok=True)
        log_path = self.logs_dir / f"attempt_{self.attempt_id:04d}_{phase}.log"
        command_text = shell_join(cmd)
        (attempt_out / "command.txt").write_text(command_text + "\n", encoding="utf-8")
        self.append(self.commands_path, f"# attempt {self.attempt_id:04d} {phase}\n{command_text}\n\n")
        start = now_iso()
        started = time.monotonic()
        self.append(self.gpu_path, f"\n## attempt {self.attempt_id:04d} {phase} before {start}\n{gpu_snapshot()}\n")
        timed_out = False
        rc: int | None = None
        with log_path.open("w", encoding="utf-8", errors="replace") as log:
            log.write(f"[AUTOLOOP] attempt={self.attempt_id} phase={phase} start={start}\n")
            log.write(f"[AUTOLOOP] command={command_text}\n")
            log.flush()
            if self.args.dry_run:
                rc = 0
                log.write("[AUTOLOOP] dry_run skipped command\n")
            else:
                proc = subprocess.Popen(cmd, cwd=self.cwd, env=env or self.base_env, text=True, stdout=log, stderr=subprocess.STDOUT)
                try:
                    rc = proc.wait(timeout=timeout or self.args.timeout_per_attempt)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    proc.kill()
                    rc = proc.wait()
                    log.write(f"\n[AUTOLOOP_TIMEOUT] killed after {timeout or self.args.timeout_per_attempt}s\n")
        ended = now_iso()
        duration = round(time.monotonic() - started, 3)
        self.append(self.gpu_path, f"\n## attempt {self.attempt_id:04d} {phase} after {ended}\n{gpu_snapshot()}\n")
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        marker = last_marker(log_text)
        error_type = classify_error(log_text, rc, timed_out)
        status = "ok" if rc == 0 and not timed_out else "failed"
        next_action = next_action_success if status == "ok" else (next_action_failure or self.next_action_for(error_type))
        result = AttemptResult(
            attempt_id=self.attempt_id,
            phase=phase,
            command=command_text,
            start_time=start,
            end_time=ended,
            duration_sec=duration,
            status=status,
            returncode=rc,
            error_type=error_type,
            last_marker=marker,
            next_action=next_action,
            log_path=str(log_path),
            out_dir=str(attempt_out),
        )
        record = result.__dict__ | {"log_tail": redact_log_tail(log_text)}
        self.append(self.attempts_path, json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        write_json(record, attempt_out / "metadata.json")
        return result

    def next_action_for(self, error_type: str) -> str:
        table = {
            "oom": "retry with fewer frames, lower resolution, or a single allowed GPU",
            "t5_timeout": "retry only with GPU bf16 and longer timeout; do not rerun CPU full T5",
            "vae_load_error": "audit LingBot-Base companion VAE path and resolver",
            "fast_model_load_error": "audit LingBot-Fast shard/config layout",
            "dit_shard_error": "audit safetensors shards under LingBot-Fast root",
            "import_error": "fix PYTHONPATH or LingBot env usage",
            "pipeline_api_mismatch": "inspect WanI2VFast/generate signatures and patch adapter minimally",
            "save_video_error": "try frame/contact-sheet fallback or video writer fallback",
            "timeout": "retry more conservative parameters if within budget",
        }
        return table.get(error_type, "inspect log and continue with conservative fallback if safe")

    def find_sample(self) -> Path | None:
        root = Path(self.args.sample_root)
        if not root.exists():
            return None
        for sample in sorted(root.iterdir()):
            if sample.is_dir() and (sample / "image.jpg").exists() and (sample / "prompt.txt").exists():
                return sample
        return None

    def preflight(self) -> bool:
        sample = self.find_sample()
        sample_payload = {"sample_root": self.args.sample_root, "sample": str(sample) if sample else "", "exists": bool(sample)}
        write_json(sample_payload, self.run_dir / "preflight_sample.json")
        if not sample:
            self.final_status["top_level_blocker"] = "missing_sample"
            return False
        t5_out = self.run_dir / "preflight_t5_gpu.json"
        cmd = [
            self.py, "-m", "cam_physgeo.eval.probe_lingbot_t5",
            "--fast_root", "local_assets/weights/lingbot_fast",
            "--stage", "full_t5",
            "--device", "cuda",
            "--dtype", "bf16",
            "--local-files-only",
            "--timeout", "900",
            "--out", str(t5_out),
        ]
        res = self.run_attempt(
            "preflight_t5_gpu",
            cmd,
            timeout=min(self.args.timeout_per_attempt, 1000),
            env=self.command_env(self.args.gpu_ids),
            next_action_success="proceed to official demo discovery",
            next_action_failure="stop inference loop because T5 GPU preflight failed",
        )
        if res.status != "ok" and t5_out.exists():
            try:
                payload = json.loads(t5_out.read_text(encoding="utf-8"))
            except Exception:
                payload = {}
            if payload.get("ok") is True:
                self.append(
                    self.attempts_path,
                    json.dumps(
                        {
                            "attempt_id": res.attempt_id,
                            "phase": "preflight_t5_gpu_override",
                            "status": "ok",
                            "returncode": res.returncode,
                            "error_type": "",
                            "last_marker": res.last_marker,
                            "next_action": "probe JSON reported ok=true; continue despite noisy interpreter exit",
                            "source_attempt": res.__dict__,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n",
                )
                return True
        return res.status == "ok"

    def official_demo_probe(self) -> None:
        candidates_file = self.run_dir / "official_demo_candidates.txt"
        find_cmd = (
            "find local_assets/third_party /home/nvme03/workspace/lingbot-world -type f "
            "2>/dev/null | grep -Ei 'infer|demo|sample|generate|i2v|fast|lingbot|wan' | head -300"
        )
        res = self.run_attempt(
            "official_demo_find",
            ["bash", "-lc", find_cmd],
            timeout=120,
            env=self.command_env(None),
            out_dir=ensure_dir(self.outputs_dir / "official_demo_find"),
            next_action_success="inspect candidate list; cam_physgeo inference remains primary path",
        )
        try:
            shutil.copy2(res.log_path, candidates_file)
        except OSError:
            pass
        help_target = Path("local_assets/third_party/lingbot_world/generate_fast.py")
        if help_target.exists():
            self.run_attempt(
                "official_demo_help",
                [self.py, str(help_target), "--help"],
                timeout=120,
                env=self.command_env(self.args.gpu_ids),
                out_dir=ensure_dir(self.outputs_dir / "official_demo_help"),
                next_action_success="official help is available; still proceed to cam_physgeo one-sample path",
                next_action_failure="official demo entry exists but help failed; do not force unknown args",
            )

    def cam_dry_run(self) -> bool:
        cmd = [
            self.py, "-m", "cam_physgeo.eval.run_inference",
            "--config", "configs/cam_physgeo/eval.yaml",
            "--model_type", "fast",
            "--samples", self.args.sample_root,
            "--out", "local_assets/outputs/smoke/lingbot_fast_inference",
            "--dry-run",
            "--limit", "1",
            "--timeout", str(self.args.timeout_per_attempt),
            "--local-files-only",
        ]
        res = self.run_attempt(
            "cam_physgeo_dry_run",
            cmd,
            timeout=300,
            env=self.command_env(None),
            next_action_success="proceed to one-sample actual inference",
            next_action_failure="fix cam_physgeo dry-run blocker before actual inference",
        )
        return res.status == "ok"

    def attempt_actual(self) -> bool:
        fallbacks = [
            {"gpus": self.args.gpu_ids, "frames": 8, "steps": 1, "resolution": "480x832", "extra_env": {}},
            {"gpus": self.args.gpu_ids, "frames": 4, "steps": 1, "resolution": "480x832", "extra_env": {}},
            {"gpus": self.args.gpu_ids, "frames": 8, "steps": 1, "resolution": "256x448", "extra_env": {}},
            {"gpus": self.args.gpu_ids, "frames": 4, "steps": 1, "resolution": "256x448", "extra_env": {}},
            {"gpus": "6", "frames": 4, "steps": 1, "resolution": "256x448", "extra_env": {}},
            {"gpus": "7", "frames": 4, "steps": 1, "resolution": "256x448", "extra_env": {}},
            {"gpus": "6", "frames": 4, "steps": 1, "resolution": "256x448", "extra_env": {"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}},
            {"gpus": "7", "frames": 4, "steps": 1, "resolution": "256x448", "extra_env": {"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}},
        ]
        for item in fallbacks:
            if self.budget_remaining() <= 60:
                self.final_status["top_level_blocker"] = "timeout_budget_exhausted"
                return False
            phase = f"actual_f{item['frames']}_s{item['steps']}_{item['resolution'].replace('x', 'x')}_gpu{item['gpus'].replace(',', '-')}"
            attempt_out = ensure_dir(self.outputs_dir / f"attempt_{self.attempt_id + 1:04d}_{phase}")
            cmd = [
                self.py, "-m", "cam_physgeo.eval.run_inference",
                "--config", "configs/cam_physgeo/eval.yaml",
                "--model_type", "fast",
                "--samples", self.args.sample_root,
                "--out", str(attempt_out),
                "--smoke-run",
                "--limit", "1",
                "--num_frames", str(item["frames"]),
                "--num_steps", str(item["steps"]),
                "--resolution", item["resolution"],
                "--timeout", str(self.args.timeout_per_attempt),
                "--local-files-only",
                "--save_contact_sheet",
            ]
            res = self.run_attempt(
                phase,
                cmd,
                timeout=self.args.timeout_per_attempt + 60,
                env=self.command_env(item["gpus"], item.get("extra_env")),
                out_dir=attempt_out,
                next_action_success="stop-on-success",
                next_action_failure="try next conservative fallback",
            )
            generated = list(attempt_out.rglob("generated.mp4"))
            if res.status == "ok" and generated:
                self.success = {
                    "attempt_id": res.attempt_id,
                    "phase": phase,
                    "generated": str(generated[0]),
                    "contact_sheets": [str(p) for p in attempt_out.rglob("contact_sheet.jpg")],
                    "out_dir": str(attempt_out),
                    "frames": item["frames"],
                    "steps": item["steps"],
                    "resolution": item["resolution"],
                    "gpus": item["gpus"],
                }
                return True
        return False

    def write_summary(self, status: str) -> None:
        end = now_iso()
        attempts = []
        if self.attempts_path.exists():
            for line in self.attempts_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.strip():
                    try:
                        attempts.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        final = {
            "status": status,
            "success": self.success,
            "start_time": self.start_wall,
            "end_time": end,
            "total_hours": round((time.monotonic() - self.start_monotonic) / 3600, 4),
            "run_dir": str(self.run_dir),
            "attempt_count": len(attempts),
            "final_gpu": gpu_snapshot(),
            **self.final_status,
        }
        write_json(final, self.run_dir / "final_status.json")
        rows = "\n".join(
            f"| {a.get('attempt_id')} | {a.get('phase')} | {a.get('duration_sec')} | {a.get('status')} | {a.get('error_type')} | `{a.get('last_marker','')[:80]}` |"
            for a in attempts
        )
        summary = f"""# LingBot-Fast 1-Sample Autoloop Summary

Status: `{status}`

Run directory: `{self.run_dir}`

Start: {self.start_wall}
End: {end}
Total hours: {final['total_hours']}

Success payload:

```json
{json.dumps(self.success, ensure_ascii=False, indent=2, sort_keys=True)}
```

Top-level blocker: `{final.get('top_level_blocker', '')}`

## Attempts

| id | phase | seconds | status | error_type | last_marker |
| --- | --- | ---: | --- | --- | --- |
{rows}

## Gates

Fast rollout: {'yes' if self.success else 'no'}
Reward-on-rollout: no
VideoGPA encode: no
DPO: no

The loop intentionally stops after one successful short video or after the attempt budget is exhausted. It does not run reward, VideoGPA, DPO, Stage1, or training.
"""
        (self.run_dir / "summary.md").write_text(summary, encoding="utf-8")

    def run(self) -> int:
        self.write_environment()
        if self.args.dry_run:
            self.write_summary("dry_run")
            return 0
        if not self.preflight():
            self.write_summary("failed")
            return 2
        self.official_demo_probe()
        if not self.cam_dry_run():
            self.write_summary("failed")
            return 2
        if self.attempt_actual():
            self.write_summary("success")
            return 0
        if not self.final_status.get("top_level_blocker"):
            self.final_status["top_level_blocker"] = "actual_inference_failed"
        self.write_summary("failed")
        return 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bounded autoloop for exactly one LingBot-Fast actual inference smoke.")
    ap.add_argument("--max-hours", type=float, default=10.0)
    ap.add_argument("--gpu_ids", "--gpus", dest="gpu_ids", default="6,7")
    ap.add_argument("--sample_root", "--sample-root", dest="sample_root", default="local_assets/data/physion/processed/lingbot_cam_inputs/smoke")
    ap.add_argument("--out_root", "--out-root", dest="out_root", default="local_assets/reports/smoke")
    ap.add_argument("--timeout_per_attempt", "--timeout-per-attempt", dest="timeout_per_attempt", type=int, default=900)
    ap.add_argument("--python", default=os.environ.get("LINGBOT_PY", DEFAULT_PY))
    ap.add_argument("--worktree", default="auto")
    ap.add_argument("--stop-on-success", action="store_true", default=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    return Autoloop(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
