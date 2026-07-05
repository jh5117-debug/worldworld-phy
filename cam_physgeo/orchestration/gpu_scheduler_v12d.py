from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from cam_physgeo.orchestration.gate_checks_v12d import check_training_signal
from cam_physgeo.orchestration.gpu_status import choose_idle_gpu, disk_free_summary, query_gpu_status, write_gpu_usage_csv
from cam_physgeo.orchestration.job_specs_v12d import build_command, fresh_job_state, WARM_START


REQUIRED_PREFLIGHT_FILES = [
    "manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl",
    "manifests/dpo_pair_factory_v11_train400_repaired.jsonl",
    "manifests/dpo_pair_factory_v11_val50_repaired.jsonl",
    "manifests/dpo_pair_factory_v11_test50_repaired.jsonl",
    "manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl",
    "manifests/dpo_v12b_subsets/val_video_4.jsonl",
    WARM_START,
    "reports/dpo_pair_factory_v11/metrics_backend_repair/metrics_backend_status.md",
]


def load_simple_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        data: dict[str, Any] = {}
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                data[key] = [int(x.strip()) for x in val[1:-1].split(",") if x.strip()]
            elif val.lower() in {"true", "false"}:
                data[key] = val.lower() == "true"
            else:
                try:
                    data[key] = int(val)
                except ValueError:
                    data[key] = val.strip('"')
        return data


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


class Scheduler:
    def __init__(self, config: dict[str, Any], state_path: Path, heartbeat_path: Path, log_path: Path):
        self.config = config
        self.state_path = state_path
        self.heartbeat_path = heartbeat_path
        self.log_path = log_path
        self.root = state_path.parent
        self.jobs_dir = self.root / "jobs"
        self.locks_dir = self.root / "locks"
        self.gpu_usage_csv = self.root / "gpu_usage.csv"
        self.events_path = self.root / "job_events.jsonl"
        self.final_summary = self.root / "final_summary.md"
        for p in [self.root, self.jobs_dir, self.locks_dir, self.heartbeat_path.parent, self.log_path.parent]:
            p.mkdir(parents=True, exist_ok=True)
        self.allowed = [int(x) for x in config.get("allowed_physical_gpus", [4, 5, 6, 7])]
        self.forbidden = [int(x) for x in config.get("forbidden_physical_gpus", [0, 1, 2, 3])]
        self.heartbeat_seconds = int(config.get("heartbeat_seconds", 60))
        self.poll_seconds = int(config.get("poll_seconds", 60))
        self.idle_memory_threshold_mb = int(config.get("idle_memory_threshold_mb", 1000))
        self.idle_util_threshold_percent = int(config.get("idle_util_threshold_percent", 10))
        self.max_retries = int(config.get("max_retries_per_job", 1))
        self.state = self._load_or_create_state()
        self.running: dict[str, subprocess.Popen] = {}

    def log(self, message: str) -> None:
        line = f"[{now()}] {message}\n"
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
        print(line, end="", flush=True)

    def event(self, job_id: str, event: str, **extra: Any) -> None:
        row = {"timestamp": now(), "job_id": job_id, "event": event, **extra}
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")
            f.flush()

    def _load_or_create_state(self) -> dict[str, Any]:
        if self.state_path.exists():
            try:
                state = json.loads(self.state_path.read_text(encoding="utf-8"))
                if state.get("allowed_gpus") == self.allowed and state.get("jobs"):
                    for job in state["jobs"]:
                        if job.get("status") == "RUNNING":
                            job["status"] = "BLOCKED"
                            job["decision"] = "STALE_RUNNING_JOB_ON_RESUME"
                    return state
            except Exception:
                pass
        return {"timestamp": now(), "allowed_gpus": self.allowed, "forbidden_gpus": self.forbidden, "gpu_status": {}, "jobs": fresh_job_state(), "last_error": "", "next_action": "preflight"}

    def save_state(self) -> None:
        self.state["timestamp"] = now()
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.state_path)

    def heartbeat(self, gpu_status: dict[str, Any]) -> None:
        jobs = self.state.get("jobs", [])
        row = {
            "timestamp": now(),
            "active_jobs": [j["job_id"] for j in jobs if j.get("status") == "RUNNING"],
            "pending_jobs": [j["job_id"] for j in jobs if j.get("status") == "PENDING" and not j.get("manual_trigger_only")],
            "completed_jobs": [j["job_id"] for j in jobs if j.get("status") == "PASS"],
            "blocked_jobs": [j["job_id"] for j in jobs if j.get("status") in {"FAIL", "BLOCKED"}],
            "allowed_gpu_status": {k: v for k, v in gpu_status.get("gpus", {}).items() if int(k) in self.allowed},
            "forbidden_gpu_status": {k: v for k, v in gpu_status.get("gpus", {}).items() if int(k) in self.forbidden},
            "disk_free": disk_free_summary(),
            "last_error": self.state.get("last_error", ""),
            "next_action": self.state.get("next_action", ""),
        }
        with self.heartbeat_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")
            f.flush()

    def write_job_files(self, job: dict[str, Any]) -> None:
        (self.jobs_dir / f"{job['job_id']}.json").write_text(json.dumps(job, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md = [f"# {job['job_id']}", "", f"- Status: `{job.get('status')}`", f"- Type: `{job.get('type')}`", f"- Assigned GPUs: `{job.get('assigned_gpus')}`", f"- Decision: `{job.get('decision', '')}`", f"- Summary: `{job.get('summary_path', '')}`"]
        if job.get("error"):
            md.append(f"- Error: `{job.get('error')}`")
        (self.jobs_dir / f"{job['job_id']}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    def job_by_id(self, job_id: str) -> dict[str, Any]:
        for job in self.state.get("jobs", []):
            if job.get("job_id") == job_id:
                return job
        raise KeyError(job_id)

    def deps_passed(self, job: dict[str, Any]) -> bool:
        return all(self.job_by_id(dep).get("status") == "PASS" for dep in job.get("depends_on", []))

    def run_preflight(self, job: dict[str, Any], gpu_status: dict[str, Any]) -> None:
        missing = [p for p in REQUIRED_PREFLIGHT_FILES if not Path(p).exists()]
        duplicate_tmux = subprocess.run(["tmux", "has-session", "-t", "dpo_gpu_scheduler_v12d"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        md = ["# v12d Preflight State Check", "", f"- Timestamp: `{now()}`", f"- Allowed GPUs: `{self.allowed}`", f"- Forbidden GPUs: `{self.forbidden}`", f"- Duplicate tmux session visible from inside scheduler: `{duplicate_tmux}`", "", "## Files"]
        for p in REQUIRED_PREFLIGHT_FILES:
            md.append(f"- {'PASS' if Path(p).exists() else 'MISSING'}: `{p}`")
        md.append("\n## GPU4-7")
        for idx in self.allowed:
            md.append(f"- GPU{idx}: `{gpu_status.get('gpus', {}).get(str(idx), {})}`")
        summary_path = Path(job["summary_path"])
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text("\n".join(md) + "\n", encoding="utf-8")
        if missing:
            job["status"] = "BLOCKED"
            job["decision"] = "PREFLIGHT_MISSING_REQUIRED_FILES"
            job["error"] = ";".join(missing)
        else:
            job["status"] = "PASS"
            job["decision"] = "PREFLIGHT_PASS"
        job["start_time"] = job.get("start_time") or now()
        job["end_time"] = now()
        self.event(job["job_id"], job["status"], decision=job.get("decision"), error=job.get("error", ""))
        self.write_job_files(job)

    def acquire_lock(self, gpu: int, job_id: str) -> Path | None:
        path = self.locks_dir / f"gpu{gpu}.lock"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                pid = int(data.get("pid") or -1)
                if pid > 0 and Path(f"/proc/{pid}").exists():
                    return None
            except Exception:
                return None
            path.unlink(missing_ok=True)
        path.write_text(json.dumps({"pid": os.getpid(), "job_id": job_id, "timestamp": now(), "owner": "dpo_gpu_scheduler_v12d"}) + "\n", encoding="utf-8")
        return path

    def release_lock(self, gpu: int) -> None:
        path = self.locks_dir / f"gpu{gpu}.lock"
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            if data.get("owner") == "dpo_gpu_scheduler_v12d":
                path.unlink(missing_ok=True)
        except Exception:
            pass

    def start_train_job(self, job: dict[str, Any], gpu_status: dict[str, Any]) -> bool:
        gpu = choose_idle_gpu(gpu_status, job.get("preferred_gpus") or self.allowed)
        if gpu is None:
            job["decision"] = "WAITING_FOR_ALLOWED_IDLE_GPU"
            self.state["next_action"] = "wait_for_gpu4_7"
            return False
        lock = self.acquire_lock(gpu, job["job_id"])
        if lock is None:
            job["decision"] = f"GPU{gpu}_LOCKED"
            return False
        cmd = build_command(job, gpu)
        job_log = self.jobs_dir / f"{job['job_id']}.stdout.log"
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = str(gpu)
        env["PYTORCH_CUDA_ALLOC_CONF"] = env.get("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        env["DPO_SCHEDULER_ASSIGNED_PHYSICAL_GPUS"] = str(gpu)
        f = job_log.open("a", encoding="utf-8")
        f.write(f"[{now()}] launch CUDA_VISIBLE_DEVICES={gpu} command={' '.join(cmd)}\n")
        f.flush()
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, text=True, env=env)
        job.update({"status": "RUNNING", "assigned_gpus": [gpu], "command": " ".join(cmd), "pid": proc.pid, "start_time": now(), "stdout_log": str(job_log), "decision": "RUNNING"})
        self.running[job["job_id"]] = proc
        self.event(job["job_id"], "START", assigned_gpus=[gpu], pid=proc.pid)
        self.write_job_files(job)
        self.state["next_action"] = f"monitor_{job['job_id']}"
        return True

    def finalize_processes(self) -> None:
        for job_id, proc in list(self.running.items()):
            rc = proc.poll()
            if rc is None:
                continue
            job = self.job_by_id(job_id)
            job["exit_code"] = rc
            job["end_time"] = now()
            for gpu in job.get("assigned_gpus") or []:
                self.release_lock(int(gpu))
            if rc != 0:
                job["status"] = "FAIL"
                job["decision"] = "PROCESS_EXIT_NONZERO"
            else:
                if job.get("gate") == "training_signal":
                    gate = check_training_signal(job.get("report_root", ""))
                    job["gate_result"] = gate
                    job["status"] = "PASS" if gate.get("status") == "PASS" else "FAIL"
                    job["decision"] = gate.get("decision")
                else:
                    job["status"] = "PASS"
                    job["decision"] = "PROCESS_PASS"
            self.event(job_id, job["status"], decision=job.get("decision"), exit_code=rc)
            self.write_job_files(job)
            del self.running[job_id]
            if job["status"] == "FAIL":
                self.activate_fallback(f"training_or_process_failed:{job_id}:{job.get('decision')}")

    def activate_fallback(self, reason: str) -> None:
        self.state["last_error"] = reason
        self.state["next_action"] = "fallback_non_training_only"
        for job in self.state.get("jobs", []):
            if job.get("manual_trigger_only") and job.get("type") == "fallback" and job.get("status") == "PENDING":
                job["manual_trigger_only"] = False
                job["decision"] = "ACTIVATED_AFTER_TRAINING_GATE_FAIL"

    def run_fallback(self, job: dict[str, Any]) -> None:
        path = Path(job["summary_path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Fallback Pair and Metric QA\n\nTraining gate failed or was blocked. Scheduler switched to non-training mode. No DPO scale is allowed from this state.\n", encoding="utf-8")
        job.update({"status": "PASS", "decision": "FALLBACK_SUMMARY_WRITTEN", "start_time": job.get("start_time") or now(), "end_time": now()})
        self.event(job["job_id"], "PASS", decision=job["decision"])
        self.write_job_files(job)

    def block_unimplemented_eval_if_ready(self) -> None:
        for job in self.state.get("jobs", []):
            if job.get("job_id") == "v12c_checkpoint_eval_winner_detached" and job.get("status") == "PENDING" and self.deps_passed(job):
                job["status"] = "BLOCKED"
                job["decision"] = "CHECKPOINT_EVAL_RUNNER_NOT_CONNECTED_NO_SCALE_ALLOWED"
                job["end_time"] = now()
                self.event(job["job_id"], "BLOCKED", decision=job["decision"])
                self.write_job_files(job)
                self.state["next_action"] = "checkpoint_eval_required_before_more_training"

    def write_final_summary(self) -> None:
        jobs = self.state.get("jobs", [])
        lines = ["# DPO GPU Scheduler v12d Summary", "", f"- Updated: `{now()}`", f"- Allowed GPUs: `{self.allowed}`", f"- Forbidden GPUs: `{self.forbidden}`", "", "## Jobs"]
        for job in jobs:
            lines.append(f"- `{job['job_id']}`: `{job.get('status')}` / `{job.get('decision', '')}` / GPUs `{job.get('assigned_gpus')}`")
        lines.append("\n## Scale Decision\n")
        lines.append("Train400 pilot is not allowed unless all prior tiny/small video, metric, and signal gates pass. Current scheduler summary does not grant large DPO permission.\n")
        self.final_summary.write_text("\n".join(lines), encoding="utf-8")

    def step(self) -> None:
        gpu_status = query_gpu_status(self.allowed, self.forbidden, self.idle_memory_threshold_mb, self.idle_util_threshold_percent)
        self.state["gpu_status"] = gpu_status
        write_gpu_usage_csv(self.gpu_usage_csv, gpu_status)
        self.finalize_processes()
        for job in self.state.get("jobs", []):
            if job.get("status") != "PENDING" or job.get("manual_trigger_only"):
                continue
            if not self.deps_passed(job):
                continue
            if job.get("command") == "internal:preflight_state_check":
                self.run_preflight(job, gpu_status)
                break
            if job.get("command") == "internal:fallback_pair_and_metric_qa":
                self.run_fallback(job)
                break
            if str(job.get("command", "")).startswith("blocked:"):
                # Do not silently skip an implemented gate. If it becomes ready, block with a clear reason.
                if self.deps_passed(job):
                    job["status"] = "BLOCKED"
                    job["decision"] = str(job.get("command"))
                    job["end_time"] = now()
                    self.event(job["job_id"], "BLOCKED", decision=job["decision"])
                    self.write_job_files(job)
                break
            if job.get("type") == "train":
                self.start_train_job(job, gpu_status)
                break
        self.save_state()
        self.heartbeat(gpu_status)
        self.write_final_summary()

    def run(self) -> None:
        self.log("scheduler_start")
        while True:
            try:
                self.step()
            except KeyboardInterrupt:
                self.log("scheduler_interrupted")
                raise
            except Exception as exc:
                self.state["last_error"] = repr(exc)
                self.event("scheduler", "ERROR", error=repr(exc))
                self.log(f"scheduler_error {exc!r}")
                self.save_state()
            time.sleep(self.poll_seconds)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="GPU4-7 gated DPO scheduler v12d")
    parser.add_argument("--config", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--heartbeat", required=True)
    parser.add_argument("--log", required=True)
    args = parser.parse_args(argv)
    config = load_simple_yaml(Path(args.config))
    scheduler = Scheduler(config, Path(args.state), Path(args.heartbeat), Path(args.log))
    scheduler.run()


if __name__ == "__main__":
    main()
