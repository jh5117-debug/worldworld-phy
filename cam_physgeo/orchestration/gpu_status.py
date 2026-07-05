from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class GpuInfo:
    index: int
    memory_used_mb: int | None = None
    memory_total_mb: int | None = None
    utilization_percent: int | None = None
    pmon_pids: list[int] | None = None
    pmon_commands: list[str] | None = None
    is_allowed: bool = False
    is_forbidden: bool = False
    is_idle: bool = False
    unavailable_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run_timeout(cmd: list[str], timeout: int = 10) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, check=False, text=True, capture_output=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", exc.stderr or "timeout"
    except FileNotFoundError as exc:
        return 127, "", repr(exc)


def _int_from_cell(value: str) -> int | None:
    match = re.search(r"-?\d+", str(value))
    return int(match.group(0)) if match else None


def parse_nvidia_smi_csv(text: str) -> dict[int, GpuInfo]:
    rows = list(csv.DictReader(line for line in text.splitlines() if line.strip()))
    out: dict[int, GpuInfo] = {}
    for row in rows:
        idx = _int_from_cell(row.get("index", ""))
        if idx is None:
            continue
        mem_used = None
        mem_total = None
        util = None
        for key, val in row.items():
            lk = key.lower()
            if "memory.used" in lk:
                mem_used = _int_from_cell(val)
            elif "memory.total" in lk:
                mem_total = _int_from_cell(val)
            elif "utilization.gpu" in lk:
                util = _int_from_cell(val)
        out[idx] = GpuInfo(index=idx, memory_used_mb=mem_used, memory_total_mb=mem_total, utilization_percent=util, pmon_pids=[], pmon_commands=[])
    return out


def parse_pmon(text: str) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            gpu = int(parts[0])
        except ValueError:
            continue
        pid_cell = parts[1]
        if pid_cell == "-":
            continue
        try:
            pid = int(pid_cell)
        except ValueError:
            continue
        command = parts[-1] if parts else ""
        out.setdefault(gpu, []).append({"pid": pid, "command": command})
    return out


def query_gpu_status(
    allowed_physical_gpus: list[int],
    forbidden_physical_gpus: list[int],
    idle_memory_threshold_mb: int = 1000,
    idle_util_threshold_percent: int = 10,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    smi_cmd = [
        "nvidia-smi",
        "--query-gpu=index,memory.used,memory.total,utilization.gpu",
        "--format=csv",
    ]
    rc, stdout, stderr = _run_timeout(smi_cmd, timeout_seconds)
    gpus = parse_nvidia_smi_csv(stdout) if rc == 0 else {}
    pmon_rc, pmon_out, pmon_err = _run_timeout(["nvidia-smi", "pmon", "-c", "1"], timeout_seconds)
    pmon = parse_pmon(pmon_out) if pmon_rc == 0 else {}
    allowed = set(int(x) for x in allowed_physical_gpus)
    forbidden = set(int(x) for x in forbidden_physical_gpus)
    for idx, info in gpus.items():
        entries = pmon.get(idx, [])
        info.pmon_pids = [int(e["pid"]) for e in entries]
        info.pmon_commands = [str(e.get("command", "")) for e in entries]
        info.is_allowed = idx in allowed
        info.is_forbidden = idx in forbidden
        reasons: list[str] = []
        if idx in forbidden:
            reasons.append("forbidden_gpu")
        if info.memory_used_mb is None or info.utilization_percent is None:
            reasons.append("missing_gpu_metrics")
        else:
            if info.memory_used_mb > idle_memory_threshold_mb:
                reasons.append(f"memory_used_gt_{idle_memory_threshold_mb}mb")
            if info.utilization_percent > idle_util_threshold_percent:
                reasons.append(f"util_gt_{idle_util_threshold_percent}pct")
        if entries:
            reasons.append("pmon_process_present")
        info.is_idle = idx in allowed and not reasons
        info.unavailable_reason = ";".join(reasons)
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "nvidia_smi_returncode": rc,
        "nvidia_smi_error": stderr.strip(),
        "pmon_returncode": pmon_rc,
        "pmon_error": pmon_err.strip(),
        "gpus": {str(idx): info.to_dict() for idx, info in sorted(gpus.items())},
    }


def choose_idle_gpu(status: dict[str, Any], preferred: list[int] | None = None) -> int | None:
    preferred = preferred or []
    gpu_map = {int(k): v for k, v in status.get("gpus", {}).items()}
    for idx in list(preferred) + [i for i in sorted(gpu_map) if i not in preferred]:
        if gpu_map.get(idx, {}).get("is_idle"):
            return idx
    return None


def disk_free_summary(paths: list[str] | None = None) -> dict[str, Any]:
    paths = paths or ["/home/nvme03", "/home/nvme04"]
    out: dict[str, Any] = {}
    for p in paths:
        try:
            usage = shutil.disk_usage(p)
            out[p] = {
                "total_gb": round(usage.total / 1024**3, 3),
                "used_gb": round(usage.used / 1024**3, 3),
                "free_gb": round(usage.free / 1024**3, 3),
            }
        except FileNotFoundError:
            out[p] = {"error": "missing"}
    return out


def write_gpu_usage_csv(path: str | Path, status: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "index", "memory_used_mb", "memory_total_mb", "utilization_percent", "is_allowed", "is_forbidden", "is_idle", "pmon_pids", "unavailable_reason"])
        if not exists:
            writer.writeheader()
        for idx, info in sorted(status.get("gpus", {}).items(), key=lambda kv: int(kv[0])):
            writer.writerow({
                "timestamp": status.get("timestamp"),
                "index": idx,
                "memory_used_mb": info.get("memory_used_mb"),
                "memory_total_mb": info.get("memory_total_mb"),
                "utilization_percent": info.get("utilization_percent"),
                "is_allowed": info.get("is_allowed"),
                "is_forbidden": info.get("is_forbidden"),
                "is_idle": info.get("is_idle"),
                "pmon_pids": json.dumps(info.get("pmon_pids") or []),
                "unavailable_reason": info.get("unavailable_reason"),
            })
