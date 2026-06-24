#!/usr/bin/env python3
"""Resumable overnight supervisor for small-LoRA -> rollout -> DPO-probe gates.

This script is intentionally conservative: it never interrupts active training,
never deletes outputs, and only starts dependent jobs when their inputs exist and
sufficient GPU memory is free. It records every decision in pipeline_state.json
and supervisor.log so Codex/SSH can disconnect without losing progress.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

STATUSES = {"PENDING", "RUNNING", "PASS", "FAILED", "BLOCKED", "SKIPPED"}
REPO = Path(__file__).resolve().parents[1]
PY = "/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python"
FAST_ROOT = "/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam"
RUN_TS = "20260624_141215"
SWEEP_ROOT = REPO / "local_assets/experiments/small_lora_scope_sweep_20260624"
TRAIN_ROOT = SWEEP_ROOT / "train"
LOG_ROOT = SWEEP_ROOT / "logs"
SCREEN16 = REPO / "manifests/small_lora_screen16.jsonl"
SCREEN16_SUMMARY = REPO / "manifests/small_lora_screen16_summary.json"
CORE_BENCH = REPO / "manifests/quant_benchmark_v1_core.jsonl"
ALL_BENCH = REPO / "manifests/quant_benchmark_v1_all.jsonl"

SWEEPS: dict[str, dict[str, Any]] = {
    "A": {"name": f"small_lora_A_camera_r4_train200_{RUN_TS}", "scope": "camera-only", "rank": 4, "gpus": "0,1"},
    "B": {"name": f"small_lora_B_camera_r8_train200_{RUN_TS}", "scope": "camera-only", "rank": 8, "gpus": "2,3"},
    "C": {"name": f"small_lora_C_camera_self_r4_train200_{RUN_TS}", "scope": "camera+limited-self", "rank": 4, "gpus": "4,5"},
    "D": {"name": f"small_lora_D_camera_cross_r4_train200_{RUN_TS}", "scope": "camera+limited-cross", "rank": 4, "gpus": "6,7"},
}
for key, item in SWEEPS.items():
    item["out_root"] = TRAIN_ROOT / item["name"]
    item["log"] = LOG_ROOT / f"{item['name']}.log"
    item["ckpt_root"] = item["out_root"] / "checkpoints" / item["name"] / "high_only_phase"
    item["metrics"] = item["ckpt_root"] / "metrics.jsonl"

STATE_KEYS = [
    "sweep_A", "sweep_B", "sweep_C", "sweep_D", "rollout_screen", "video_audit_screen",
    "quant_screen", "reward_calibration", "candidate_selection", "full_benchmark", "pair_build",
    "dpo_bf16_single", "dpo_bf16_ddp2", "dpo_bf16_ddp8", "dpo_probe", "post_dpo_eval", "git_status",
]

MODEL_ORDER = ["original_fast", "old_tiny_camera"]


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run(cmd: list[str] | str, *, cwd: Path = REPO, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), shell=isinstance(cmd, str), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)


def log(root: Path, msg: str) -> None:
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    (root / "supervisor.log").parent.mkdir(parents=True, exist_ok=True)
    with (root / "supervisor.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def tmux_alive(name: str) -> bool:
    return run(["tmux", "has-session", "-t", name], timeout=10).returncode == 0


def start_tmux(name: str, command: str, root: Path) -> bool:
    if tmux_alive(name):
        return False
    wrapped = f"cd {REPO} && {command}"
    res = run(["tmux", "new-session", "-d", "-s", name, wrapped], timeout=20)
    log(root, f"start_tmux {name} rc={res.returncode} cmd={command}")
    return res.returncode == 0


def disk_free_gb(path: str = "/home/nvme04") -> float:
    usage = shutil.disk_usage(path)
    return usage.free / (1024 ** 3)


def gpu_snapshot() -> list[dict[str, Any]]:
    res = run(["nvidia-smi", "--query-gpu=index,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"], timeout=20)
    gpus: list[dict[str, Any]] = []
    if res.returncode != 0:
        return gpus
    for line in res.stdout.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 4:
            try:
                gpus.append({"index": int(parts[0]), "memory_used_mib": int(parts[1]), "memory_total_mib": int(parts[2]), "utilization_gpu": int(parts[3])})
            except ValueError:
                pass
    return gpus


def free_gpus(threshold_mib: int = 20000) -> list[int]:
    return [g["index"] for g in gpu_snapshot() if int(g.get("memory_used_mib", 10**9)) < threshold_mib]


def latest_log_step(log_path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"latest_step": None, "target_step": None, "latest_loss": None, "ema20": None, "ema100": None, "gate": "", "fixed_val": None, "errors": []}
    if not log_path.exists():
        info["errors"].append("missing_log")
        return info
    text = log_path.read_text(errors="replace")[-300000:]
    error_patterns = {
        "OOM": r"(?i)(?:out of memory|\bOOM\b)",
        "SIGFPE": r"\bSIGFPE\b",
        "NaN": r"(?i)\bNaN\b",
        "Inf": r"(?<![A-Za-z])(?:Inf|Infinity)(?![A-Za-z])",
        "Traceback": r"Traceback \(most recent call last\)",
        "RuntimeError": r"\bRuntimeError\b",
    }
    for token, pattern in error_patterns.items():
        if re.search(pattern, text):
            info["errors"].append(token)
    step_re = re.compile(r"step=(\d+)/(\d+).*?loss=([0-9.eE+-]+).*?ema20=([0-9.eE+-]+).*?ema100=([0-9.eE+-]+).*?gate=([^\s]+)")
    for m in step_re.finditer(text):
        info.update({"latest_step": int(m.group(1)), "target_step": int(m.group(2)), "latest_loss": float(m.group(3)), "ema20": float(m.group(4)), "ema100": float(m.group(5)), "gate": m.group(6)})
    val_re = re.compile(r"fixed-val step=(\d+).*?loss=([0-9.eE+-]+).*?unweighted=([0-9.eE+-]+).*?best=([0-9.eE+-]+).*?finite=(\w+)")
    vals = list(val_re.finditer(text))
    if vals:
        m = vals[-1]
        info["fixed_val"] = {"step": int(m.group(1)), "loss": float(m.group(2)), "unweighted": float(m.group(3)), "best": float(m.group(4)), "finite": m.group(5)}
    return info


def adapter_dir_for(sweep: str, step: int) -> Path:
    item = SWEEPS[sweep]
    return item["ckpt_root"] / "branches" / f"step_{step:06d}" / "fast_stageA_high_noise_adapter"


def existing_adapters() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for sweep in SWEEPS:
        for step in (50, 100, 200):
            d = adapter_dir_for(sweep, step)
            if (d / "adapter_state.pt").exists() and (d / "adapter_metadata.json").exists():
                out[f"{sweep}_step{step:03d}"] = d
    return out


def adapter_fingerprint(path: Path) -> dict[str, Any]:
    state = path / "adapter_state.pt"
    meta = path / "adapter_metadata.json"
    obj = {"path": str(path), "exists": state.exists() and meta.exists()}
    if state.exists():
        obj["adapter_state_sha256"] = sha256_file(state)
        obj["size_bytes"] = state.stat().st_size
    if meta.exists():
        try:
            m = json.loads(meta.read_text(encoding="utf-8"))
            obj["global_step"] = m.get("global_step")
            obj["adapter_tensor_count"] = m.get("adapter_tensor_count")
            obj["lora_config"] = m.get("lora_config")
        except Exception as exc:
            obj["metadata_error"] = str(exc)
    return obj


def update_sweep_state(state: dict[str, Any], root: Path) -> None:
    inventory_rows: list[dict[str, Any]] = []
    for key, item in SWEEPS.items():
        info = latest_log_step(item["log"])
        alive = tmux_alive(item["name"])
        adapters = {f"step{step:03d}": adapter_fingerprint(adapter_dir_for(key, step)) for step in (50, 100, 200)}
        status = "RUNNING" if alive else ("PASS" if adapters["step200"].get("exists") else ("FAILED" if info.get("errors") else "BLOCKED"))
        state[f"sweep_{key}"] = status
        state.setdefault("details", {})[f"sweep_{key}"] = {"tmux": item["name"], "alive": alive, "gpus": item["gpus"], "scope": item["scope"], "rank": item["rank"], **info, "adapters": adapters}
        inventory_rows.append({"sweep": key, "status": status, "tmux": item["name"], "gpus": item["gpus"], "scope": item["scope"], "rank": item["rank"], **{k: info.get(k) for k in ("latest_step", "target_step", "latest_loss", "ema20", "ema100", "gate")}})
    reports = root / "reports/small_lora_scope_sweep"
    reports.mkdir(parents=True, exist_ok=True)
    with (reports / "run_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(inventory_rows[0].keys()))
        writer.writeheader(); writer.writerows(inventory_rows)
    write_json(root / "reports/small_lora_scope_sweep/checkpoint_inventory.json", {k: str(v) for k, v in existing_adapters().items()})


def ensure_screen16(state: dict[str, Any], root: Path) -> None:
    if SCREEN16.exists() and SCREEN16_SUMMARY.exists():
        return
    rows = load_jsonl(CORE_BENCH)
    by_template: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        t = str(row.get("template") or row.get("benchmark_template") or "unknown")
        by_template.setdefault(t, []).append(row)
    selected: list[dict[str, Any]] = []
    for template in sorted(by_template):
        selected.extend(by_template[template][:4])
    if len(selected) < 16:
        selected = rows[:16]
    write_jsonl(SCREEN16, selected[:16])
    summary = {
        "count": len(selected[:16]),
        "source": str(CORE_BENCH),
        "sha256": sha256_file(SCREEN16),
        "templates": {t: sum(1 for r in selected[:16] if str(r.get("template") or r.get("benchmark_template") or "unknown") == t) for t in sorted(by_template)},
        "status": "READY",
    }
    write_json(SCREEN16_SUMMARY, summary)
    state.setdefault("artifacts", {})["screen16_manifest"] = str(SCREEN16)
    state["details"]["screen16"] = summary
    log(root, f"created screen16 manifest {SCREEN16} count={summary['count']}")


def old_tiny_adapter_dir() -> Path | None:
    # The old tiny checkpoint is a legacy adapter_state.pt-only artifact; the new
    # Fast wrapper requires adapter_metadata.json. Keep this explicit so we do not
    # silently run Original Fast while claiming tiny adapter was loaded.
    legacy = Path("/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work/local_assets/experiments/exp_stageA_1000_combined_prompt_v2_warmup/checkpoint/stageA_1000_promptv2_high_noise_camera_lora_final")
    if (legacy / "adapter_state.pt").exists() and (legacy / "adapter_metadata.json").exists():
        return legacy
    return None


def rollout_jobs(state: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    jobs = [{"label": "original_fast", "adapter": ""}]
    tiny = old_tiny_adapter_dir()
    if tiny:
        jobs.append({"label": "old_tiny_camera", "adapter": str(tiny)})
    else:
        state.setdefault("blockers", {})["old_tiny_camera"] = "legacy checkpoint lacks adapter_metadata.json required by strict Fast adapter loader"
    for label, path in sorted(existing_adapters().items()):
        jobs.append({"label": label, "adapter": str(path)})
    return jobs


def rollout_done(path: Path, expected: int = 16) -> bool:
    manifest = path / "generated_manifest.csv"
    if not manifest.exists():
        return False
    try:
        with manifest.open("r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        videos = [Path(r.get("generated_video", "")) for r in rows]
        return len(rows) >= expected and all(v.exists() for v in videos)
    except Exception:
        return False


def maybe_start_rollouts(state: dict[str, Any], root: Path) -> None:
    ensure_screen16(state, root)
    if disk_free_gb() < 200:
        state["rollout_screen"] = "BLOCKED"
        state.setdefault("blockers", {})["rollout_screen"] = "BLOCKED_LOW_DISK"
        return
    jobs = rollout_jobs(state, root)
    rollout_root = root / "screen16_rollouts"
    rollout_root.mkdir(parents=True, exist_ok=True)
    details = state.setdefault("details", {}).setdefault("rollout_jobs", {})
    all_done = True
    for job in jobs:
        out = rollout_root / job["label"]
        sess = f"ov_rollout_{job['label']}_{root.name[-15:]}".replace("/", "_")
        done = rollout_done(out)
        alive = tmux_alive(sess)
        details[job["label"]] = {"session": sess, "out": str(out), "adapter": job["adapter"], "done": done, "alive": alive}
        all_done = all_done and done
    if all_done and jobs:
        state["rollout_screen"] = "PASS"
        return
    state["rollout_screen"] = "RUNNING" if any(v.get("alive") for v in details.values()) else "PENDING"
    free = free_gpus()
    used_sessions = {v["session"] for v in details.values() if v.get("alive")}
    available = [g for g in free if g not in []]
    if not available:
        state.setdefault("next_action", "wait_for_free_gpu")
        return
    for job in jobs:
        out = rollout_root / job["label"]
        sess = details[job["label"]]["session"]
        if rollout_done(out) or tmux_alive(sess):
            continue
        if not available:
            break
        gpu = available.pop(0)
        cmd = (
            f"CUDA_VISIBLE_DEVICES={gpu} TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 "
            f"PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True {PY} -m cam_physgeo.eval.run_fast_adapter_inference "
            f"--manifest {SCREEN16} --out {out} --model_label {job['label']} --ckpt_dir {FAST_ROOT} "
            f"--max_samples 16 --per_template 4 --frame_num 81 --size 832*480 --height 480 --width 832 "
            f"--seed 123 --skip_existing --allow_gpu0"
        )
        if job["adapter"]:
            cmd += f" --adapter_dir {job['adapter']}"
        cmd += f" > {root}/logs/{sess}.log 2>&1"
        (root / "logs").mkdir(parents=True, exist_ok=True)
        if start_tmux(sess, cmd, root):
            details[job["label"]].update({"alive": True, "gpu": gpu})
            state["rollout_screen"] = "RUNNING"


def maybe_start_video_audit(state: dict[str, Any], root: Path) -> None:
    if state.get("rollout_screen") != "PASS":
        state["video_audit_screen"] = "PENDING"
        return
    audit_root = root / "video_audit_screen"
    rollout_root = root / "screen16_rollouts"
    jobs = [p for p in rollout_root.iterdir() if (p / "generated_manifest.csv").exists()]
    if not jobs:
        state["video_audit_screen"] = "BLOCKED"
        state.setdefault("blockers", {})["video_audit_screen"] = "no rollout manifests"
        return
    all_done = True
    for p in jobs:
        out = audit_root / p.name
        sess = f"ov_audit_{p.name}_{root.name[-15:]}"
        done = (out / "all_video_audit.csv").exists()
        alive = tmux_alive(sess)
        all_done = all_done and done
        if not done and not alive:
            cmd = f"{PY} -m cam_physgeo.eval.video_audit --candidate_manifest {p/'generated_manifest.csv'} --model_label {p.name} --out_dir {out} --sheet_frames 16 > {root}/logs/{sess}.log 2>&1"
            start_tmux(sess, cmd, root)
    state["video_audit_screen"] = "PASS" if all_done else "RUNNING"


def maybe_start_quant_screen(state: dict[str, Any], root: Path) -> None:
    if state.get("video_audit_screen") != "PASS":
        state["quant_screen"] = "PENDING"
        return
    out = root / "quant_screen"
    if (out / "per_sample_metrics.csv").exists():
        state["quant_screen"] = "PASS"
        return
    sess = f"ov_quant_screen_{root.name[-15:]}"
    if tmux_alive(sess):
        state["quant_screen"] = "RUNNING"
        return
    rollout_root = root / "screen16_rollouts"
    specs = ["--candidate GT=gt"]
    for p in sorted(rollout_root.iterdir()):
        m = p / "generated_manifest.csv"
        if m.exists():
            specs.append(f"--candidate {p.name}={m}")
    if len(specs) <= 1:
        state["quant_screen"] = "BLOCKED"
        state.setdefault("blockers", {})["quant_screen"] = "no generated manifests"
        return
    cmd = f"{PY} -m cam_physgeo.eval.quant_benchmark_v1 --conditions {SCREEN16} {' '.join(specs)} --out_dir {out} --frame_count 81 > {root}/logs/{sess}.log 2>&1"
    start_tmux(sess, cmd, root)
    state["quant_screen"] = "RUNNING"


def maybe_start_reward_calibration(state: dict[str, Any], root: Path) -> None:
    out = root / "reward_calibration_v2"
    if (out / "summary.json").exists():
        state["reward_calibration"] = "PASS"
        return
    if disk_free_gb() < 200:
        state["reward_calibration"] = "BLOCKED"
        state.setdefault("blockers", {})["reward_calibration"] = "BLOCKED_LOW_DISK"
        return
    sess = f"ov_reward_cal_{root.name[-15:]}"
    if tmux_alive(sess):
        state["reward_calibration"] = "RUNNING"
        return
    # CPU/light GPU-independent corruption and evaluation; geometry left enabled unless backend fails in tool.
    cmd = f"{PY} -m cam_physgeo.eval.reward_calibration_v2 --manifest {CORE_BENCH} --out_dir {out} --limit 40 --frame_count 81 > {root}/logs/{sess}.log 2>&1"
    start_tmux(sess, cmd, root)
    state["reward_calibration"] = "RUNNING"


def maybe_select_candidate(state: dict[str, Any], root: Path) -> None:
    if state.get("quant_screen") != "PASS":
        state["candidate_selection"] = "PENDING"
        return
    out = root / "candidate_decision.json"
    if out.exists():
        state["candidate_selection"] = "PASS"
        state.setdefault("artifacts", {})["candidate_decision"] = str(out)
        return
    metrics = root / "quant_screen/model_summary.csv"
    if not metrics.exists():
        state["candidate_selection"] = "BLOCKED"
        state.setdefault("blockers", {})["candidate_selection"] = "missing model_summary.csv"
        return
    rows = list(csv.DictReader(metrics.open("r", newline="", encoding="utf-8")))
    def num(row: dict[str, str], key: str, default: float = -1.0) -> float:
        try:
            return float(row.get(key, default))
        except Exception:
            return default
    candidates = [r for r in rows if r.get("model") not in {"GT", "original_fast"}]
    candidates.sort(key=lambda r: (num(r, "quality_proxy_mean"), num(r, "ssim_mean"), -num(r, "freeze_rate_mean", 99)), reverse=True)
    if candidates:
        best = candidates[0]
        decision = {"decision": "NEW_SMALL_LORA_SELECTED", "model": best.get("model"), "reason": "screen16 proxy/diagnostic selection; final full80 and visual audit still required", "row": best}
    else:
        decision = {"decision": "ORIGINAL_FAST_SELECTED", "model": "original_fast", "reason": "no valid candidate metrics"}
    write_json(out, decision)
    state["candidate_selection"] = "PASS"
    state.setdefault("artifacts", {})["candidate_decision"] = str(out)



def adapter_for_label(label: str) -> str:
    if label in {"", "original_fast", "GT"}:
        return ""
    adapters = existing_adapters()
    return str(adapters.get(label, ""))


def maybe_start_full_benchmark(state: dict[str, Any], root: Path) -> None:
    if state.get("candidate_selection") != "PASS":
        state["full_benchmark"] = "PENDING"
        return
    decision = read_json(root / "candidate_decision.json", {})
    selected = str(decision.get("model") or "original_fast")
    models = ["original_fast"]
    if selected and selected != "original_fast":
        models.append(selected)
    bench_root = root / "quant80_rollouts"
    bench_root.mkdir(parents=True, exist_ok=True)
    details = state.setdefault("details", {}).setdefault("full80_jobs", {})
    all_done = True
    for label in models:
        out = bench_root / label
        sess = f"ov_full80_{label}_{root.name[-15:]}"
        done = rollout_done(out, expected=80)
        alive = tmux_alive(sess)
        details[label] = {"session": sess, "out": str(out), "done": done, "alive": alive}
        all_done = all_done and done
    quant_out = root / "quant_benchmark_v1_full80"
    if all_done and (quant_out / "per_sample_metrics.csv").exists():
        state["full_benchmark"] = "PASS"
        return
    if all_done:
        sess = f"ov_quant_full80_{root.name[-15:]}"
        if tmux_alive(sess):
            state["full_benchmark"] = "RUNNING"
            return
        specs = ["--candidate GT=gt"]
        for label in models:
            manifest = bench_root / label / "generated_manifest.csv"
            if manifest.exists():
                specs.append(f"--candidate {label}={manifest}")
        cmd = f"{PY} -m cam_physgeo.eval.quant_benchmark_v1 --conditions {ALL_BENCH} {' '.join(specs)} --out_dir {quant_out} --frame_count 81 > {root}/logs/{sess}.log 2>&1"
        start_tmux(sess, cmd, root)
        state["full_benchmark"] = "RUNNING"
        return
    if disk_free_gb() < 200:
        state["full_benchmark"] = "BLOCKED"
        state.setdefault("blockers", {})["full_benchmark"] = "BLOCKED_LOW_DISK"
        return
    free = free_gpus()
    if not free:
        state["full_benchmark"] = "PENDING"
        return
    for label in models:
        out = bench_root / label
        sess = details[label]["session"]
        if rollout_done(out, expected=80) or tmux_alive(sess):
            continue
        if not free:
            break
        gpu = free.pop(0)
        adapter = adapter_for_label(label)
        if label != "original_fast" and not adapter:
            details[label]["blocked"] = "missing adapter for selected label"
            continue
        cmd = (
            f"CUDA_VISIBLE_DEVICES={gpu} TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 "
            f"PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True {PY} -m cam_physgeo.eval.run_fast_adapter_inference "
            f"--manifest {ALL_BENCH} --out {out} --model_label {label} --ckpt_dir {FAST_ROOT} "
            f"--max_samples 80 --per_template 0 --frame_num 81 --size 832*480 --height 480 --width 832 "
            f"--seed 123 --skip_existing --allow_gpu0"
        )
        if adapter:
            cmd += f" --adapter_dir {adapter}"
        cmd += f" > {root}/logs/{sess}.log 2>&1"
        start_tmux(sess, cmd, root)
        state["full_benchmark"] = "RUNNING"
    if state.get("full_benchmark") != "RUNNING":
        state["full_benchmark"] = "PENDING"

def maybe_start_pair_build(state: dict[str, Any], root: Path) -> None:
    if state.get("quant_screen") != "PASS":
        state["pair_build"] = "PENDING"
        return
    out = root / "anchored_pairs/anchored_dpo_probe_pairs.jsonl"
    rej = root / "anchored_pairs/rejected_pairs.jsonl"
    if out.exists():
        pairs = load_jsonl(out)
        state["pair_build"] = "PASS" if len(pairs) >= 20 else "BLOCKED"
        if len(pairs) < 20:
            state.setdefault("blockers", {})["pair_build"] = f"only {len(pairs)} quality-bounded pairs"
        return
    sess = f"ov_pair_build_{root.name[-15:]}"
    if tmux_alive(sess):
        state["pair_build"] = "RUNNING"
        return
    metrics = root / "quant_screen/per_sample_metrics.csv"
    if not metrics.exists():
        state["pair_build"] = "PENDING"
        return
    cmd = f"{PY} -m cam_physgeo.dpo.quality_bounded_pairs --conditions {SCREEN16} --metrics_csv {metrics} --out {out} --rejected_out {rej} --max_pairs 50 > {root}/logs/{sess}.log 2>&1"
    start_tmux(sess, cmd, root)
    state["pair_build"] = "RUNNING"


def dpo_trainer_ready() -> tuple[bool, str]:
    path = REPO / "cam_physgeo/training/train_stage2_anchored_dpo.py"
    if not path.exists():
        return False, "missing train_stage2_anchored_dpo.py"
    text = path.read_text(errors="replace")
    guarded_tokens = ["NotImplemented", "dry-run", "skeleton", "raise RuntimeError"]
    if any(tok.lower() in text.lower() for tok in guarded_tokens):
        return False, "anchored DPO trainer is still skeleton/guarded; real LingBot-Fast DPO path not callable"
    return True, "ready"


def update_dpo_states(state: dict[str, Any], root: Path) -> None:
    ready, reason = dpo_trainer_ready()
    if not ready:
        for key in ("dpo_bf16_single", "dpo_bf16_ddp2", "dpo_bf16_ddp8", "dpo_probe", "post_dpo_eval"):
            state[key] = "BLOCKED"
        state.setdefault("blockers", {})["dpo"] = reason
        return
    if state.get("pair_build") != "PASS":
        for key in ("dpo_bf16_single", "dpo_bf16_ddp2", "dpo_bf16_ddp8", "dpo_probe", "post_dpo_eval"):
            state[key] = "PENDING"
        return
    # Real DPO implementation should add launch commands here once trainer is complete.
    for key in ("dpo_bf16_single", "dpo_bf16_ddp2", "dpo_bf16_ddp8", "dpo_probe", "post_dpo_eval"):
        state[key] = "BLOCKED"
    state.setdefault("blockers", {})["dpo"] = "DPO trainer readiness hook exists, but launch command intentionally not defined until real preflight CLI is audited"


def update_git_status(state: dict[str, Any]) -> None:
    res = run(["git", "status", "--short"], timeout=30)
    head = run(["git", "rev-parse", "--short", "HEAD"], timeout=30).stdout.strip()
    branch = run(["git", "branch", "--show-current"], timeout=30).stdout.strip()
    state["git_status"] = "PASS" if res.returncode == 0 else "BLOCKED"
    state.setdefault("details", {})["git"] = {"branch": branch, "head": head, "status_short": res.stdout.splitlines()[:80]}


def heartbeat(state: dict[str, Any], root: Path) -> None:
    gpus = gpu_snapshot()
    state["last_heartbeat"] = now()
    state["gpu_snapshot"] = gpus
    state["disk_free_gb_home_nvme04"] = round(disk_free_gb(), 2)
    state["free_gpus_under_20g"] = free_gpus()
    state["current_queue"] = [k for k in STATE_KEYS if state.get(k) in {"PENDING", "RUNNING"}]
    state["next_action"] = infer_next_action(state)
    step_text = ", ".join(
        f"{k}:{state.get('details', {}).get('sweep_' + k, {}).get('latest_step')}"
        for k in SWEEPS
    )
    status_text = ",".join(f"{k}={state.get(k)}" for k in STATE_KEYS)
    log(root, f"heartbeat steps={{{step_text}}} statuses={status_text} free_gpus={state['free_gpus_under_20g']} disk={state['disk_free_gb_home_nvme04']}GB next={state['next_action']}")


def infer_next_action(state: dict[str, Any]) -> str:
    if state.get("disk_free_gb_home_nvme04", 999) < 200:
        return "BLOCKED_LOW_DISK: only light parsing/docs"
    if any(state.get(f"sweep_{k}") == "RUNNING" for k in SWEEPS):
        return "wait for sweep GPUs; continue CPU parsing and inventory"
    if state.get("rollout_screen") in {"PENDING", "RUNNING"}:
        return "run/finish screen16 rollout"
    if state.get("video_audit_screen") in {"PENDING", "RUNNING"}:
        return "run/finish screen16 video audit"
    if state.get("quant_screen") in {"PENDING", "RUNNING"}:
        return "run/finish screen16 quantitative benchmark"
    if state.get("pair_build") in {"PENDING", "RUNNING"}:
        return "build quality-bounded anchored pairs"
    if state.get("dpo_probe") == "BLOCKED":
        return "DPO blocked until real trainer/preflight is implemented"
    return "monitor"


def load_state(root: Path) -> dict[str, Any]:
    state = read_json(root / "pipeline_state.json", {})
    for key in STATE_KEYS:
        state.setdefault(key, "PENDING")
    state.setdefault("details", {})
    state.setdefault("blockers", {})
    state.setdefault("artifacts", {})
    return state


def write_status_doc(state: dict[str, Any], root: Path) -> None:
    lines = [
        "# Overnight Pipeline Status",
        "",
        f"Updated: {now()} CST",
        f"Supervisor root: `{root}`",
        f"State file: `{root / 'pipeline_state.json'}`",
        f"Heartbeat log: `{root / 'supervisor.log'}`",
        "",
        "## Status",
        "",
    ]
    for key in STATE_KEYS:
        lines.append(f"- {key}: {state.get(key)}")
    lines += ["", "## GPU / Disk", "", f"- free GPUs under 20GiB used: `{state.get('free_gpus_under_20g')}`", f"- /home/nvme04 free GB: `{state.get('disk_free_gb_home_nvme04')}`", "", "## Sweep Progress", ""]
    for key in SWEEPS:
        detail = state.get("details", {}).get(f"sweep_{key}", {})
        lines.append(f"- {key}: status={state.get('sweep_'+key)} step={detail.get('latest_step')}/{detail.get('target_step')} gate={detail.get('gate')} fixed_val={detail.get('fixed_val')} gpus={detail.get('gpus')}")
    if state.get("blockers"):
        lines += ["", "## Blockers", ""]
        for k, v in sorted(state["blockers"].items()):
            lines.append(f"- {k}: {v}")
    lines += ["", "## Safety", "", "- No full-data long StageA launched by this supervisor.", "- No StageB / GRPO / large-scale DPO launched.", "- No data, videos, HDF5, NPY, checkpoints, adapters, or weights are committed by this supervisor."]
    (REPO / "docs/overnight_pipeline_status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def tick(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    state = load_state(root)
    update_git_status(state)
    update_sweep_state(state, root)
    ensure_screen16(state, root)
    maybe_start_reward_calibration(state, root)
    # Do not compete with live sweep jobs; rollout scheduler itself waits for free GPUs.
    maybe_start_rollouts(state, root)
    maybe_start_video_audit(state, root)
    maybe_start_quant_screen(state, root)
    maybe_select_candidate(state, root)
    maybe_start_full_benchmark(state, root)
    maybe_start_pair_build(state, root)
    update_dpo_states(state, root)
    heartbeat(state, root)
    write_json(root / "pipeline_state.json", state)
    write_status_doc(state, root)
    return state


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Overnight small-LoRA to DPO probe supervisor")
    ap.add_argument("--root", default="")
    ap.add_argument("--timestamp", default="")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args(argv)
    ts = args.timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    root = Path(args.root) if args.root else REPO / f"local_assets/overnight_quant_lora_dpo_{ts}"
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / "pipeline.lock"
    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"Another supervisor holds {lock_path}", file=sys.stderr)
            return 2
        log(root, f"supervisor_start root={root} loop={args.loop} interval={args.interval}")
        while True:
            try:
                tick(root)
            except Exception as exc:
                log(root, f"ERROR {type(exc).__name__}: {exc}")
                state = load_state(root)
                state.setdefault("blockers", {})["supervisor_exception"] = f"{type(exc).__name__}: {exc}"
                write_json(root / "pipeline_state.json", state)
            if args.once or not args.loop:
                break
            time.sleep(max(30, args.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
