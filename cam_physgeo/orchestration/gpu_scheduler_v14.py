from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

ALLOWED_PHYSICAL_GPUS = [4, 5]
FORBIDDEN_PHYSICAL_GPUS = [0, 1, 2, 3, 6, 7]
DEFAULT_DECISION_PATH = Path("reports/dpo_utility_calibration_v14/best_scheme_decision.json")
DEFAULT_REPORT_ROOT = Path("reports/dpo_utility_calibration_v14")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def load_simple_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        data: dict[str, Any] = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                data[key.strip()] = [int(x.strip()) for x in value[1:-1].split(",") if x.strip()]
            elif value.lower() in {"true", "false"}:
                data[key.strip()] = value.lower() == "true"
            else:
                try:
                    data[key.strip()] = int(value)
                except ValueError:
                    data[key.strip()] = value.strip('"')
        return data


def query_gpu_status() -> dict[str, Any]:
    cmd = [
        "timeout", "-k", "2s", "8s", "nvidia-smi",
        "--query-gpu=index,memory.used,memory.total,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
    except Exception as exc:
        return {"error": repr(exc), "gpus": {}}
    if proc.returncode != 0:
        return {"error": proc.stderr.strip() or proc.stdout.strip(), "gpus": {}}
    gpus: dict[str, dict[str, int]] = {}
    for line in proc.stdout.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        try:
            idx = int(parts[0])
            gpus[str(idx)] = {
                "index": idx,
                "memory_used_mb": int(parts[1]),
                "memory_total_mb": int(parts[2]),
                "utilization_percent": int(parts[3]),
            }
        except ValueError:
            continue
    return {"gpus": gpus}


def idle_allowed_gpus(status: dict[str, Any], allowed: list[int], mem_threshold: int, util_threshold: int) -> list[int]:
    out: list[int] = []
    for gpu in allowed:
        row = status.get("gpus", {}).get(str(gpu))
        if not row:
            continue
        if int(row.get("memory_used_mb", 999999)) <= mem_threshold and int(row.get("utilization_percent", 999)) <= util_threshold:
            out.append(gpu)
    return out


def read_decision(path: Path = DEFAULT_DECISION_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"decision": "MISSING_DECISION"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"decision": "BAD_DECISION_JSON", "error": repr(exc)}


def build_state(config: dict[str, Any], state_path: Path, heartbeat_path: Path, decision_path: Path = DEFAULT_DECISION_PATH) -> dict[str, Any]:
    allowed = [int(x) for x in config.get("allowed_physical_gpus", ALLOWED_PHYSICAL_GPUS)]
    forbidden = [int(x) for x in config.get("forbidden_physical_gpus", FORBIDDEN_PHYSICAL_GPUS)]
    mem_threshold = int(config.get("idle_memory_threshold_mb", 1000))
    util_threshold = int(config.get("idle_util_threshold_percent", 10))
    gpu_status = query_gpu_status()
    idle = idle_allowed_gpus(gpu_status, allowed, mem_threshold, util_threshold)
    decision = read_decision(decision_path)
    final_decision = decision.get("decision")
    next_action = "NO_TRAINING_RECIPE_NOT_FOUND"
    scheduler_decision = "NO_TRAINING_NO_SCALE"
    if final_decision not in {"DPO_RECIPE_NOT_FOUND_V14", "DPO_RECIPE_VIDEO_METRIC_FAIL_V14"}:
        next_action = "MANUAL_REVIEW_REQUIRED_BEFORE_ANY_TRAINING"
        scheduler_decision = "BLOCKED_PENDING_MANUAL_REVIEW"
    jobs = [{
        "job_id": "v14_decision_preflight",
        "type": "audit",
        "status": "PASS" if final_decision == "DPO_RECIPE_NOT_FOUND_V14" else "BLOCKED",
        "required_gpus": 0,
        "assigned_gpus": [],
        "command": "none",
        "decision": final_decision,
        "summary_path": "reports/dpo_utility_calibration_v14/requirement_audit.md",
    }]
    state = {
        "timestamp": now(),
        "allowed_gpus": allowed,
        "forbidden_gpus": forbidden,
        "gpu_status": gpu_status,
        "idle_allowed_gpus": idle,
        "decision_file": str(decision_path),
        "objective_decision": decision,
        "scheduler_decision": scheduler_decision,
        "next_action": next_action,
        "jobs": jobs,
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
    with heartbeat_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": now(), "scheduler_decision": scheduler_decision, "idle_allowed_gpus": idle, "objective_decision": final_decision}, sort_keys=True) + "\n")
    return state


def write_final_summary(report_root: Path, state: dict[str, Any]) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    decision = state.get("objective_decision", {}).get("decision")
    lines = [
        "# v14 GPU4/5 Scheduler Summary",
        "",
        f"- Timestamp: `{state.get('timestamp')}`",
        f"- Allowed physical GPUs: `{state.get('allowed_gpus')}`",
        f"- Forbidden physical GPUs: `{state.get('forbidden_gpus')}`",
        f"- Idle allowed GPUs: `{state.get('idle_allowed_gpus')}`",
        f"- Objective decision: `{decision}`",
        f"- Scheduler decision: `{state.get('scheduler_decision')}`",
        f"- Next action: `{state.get('next_action')}`",
        "",
        "This v14 scheduler is intentionally conservative after the objective search decision. If the current decision is `DPO_RECIPE_NOT_FOUND_V14`, it does not launch additional training and only records GPU/state evidence. This preserves the v14 `NO_SCALE` gate.",
    ]
    (report_root / "scheduler_state_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="GPU4/5-only conservative scheduler/status writer for v14 DPO utility calibration.")
    parser.add_argument("--config", default="configs/cam_physgeo/dpo_v14_scheduler.yaml")
    parser.add_argument("--state", default="reports/dpo_utility_calibration_v14/scheduler_state.json")
    parser.add_argument("--heartbeat", default="reports/dpo_utility_calibration_v14/heartbeat.jsonl")
    parser.add_argument("--report_root", default=str(DEFAULT_REPORT_ROOT))
    parser.add_argument("--decision", default=str(DEFAULT_DECISION_PATH))
    args = parser.parse_args(argv)
    config = load_simple_yaml(Path(args.config))
    state = build_state(config, Path(args.state), Path(args.heartbeat), Path(args.decision))
    write_final_summary(Path(args.report_root), state)
    print(json.dumps(state, indent=2, sort_keys=True))
    return state


if __name__ == "__main__":
    main()
