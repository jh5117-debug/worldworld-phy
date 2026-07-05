from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        val = float(value)
    except (TypeError, ValueError):
        return None
    return val if math.isfinite(val) else None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def check_training_signal(report_root: str | Path) -> dict[str, Any]:
    root = Path(report_root)
    summary_path = root / "training_summary.json"
    if not summary_path.exists():
        return {"status": "BLOCKED", "decision": "TRAINING_SUMMARY_MISSING", "reason": str(summary_path)}
    summary = _read_json(summary_path)
    rows_written = int(summary.get("rows_written") or 0)
    steps_requested = int(summary.get("steps_requested") or 0)
    mean_winner = _safe_float(summary.get("mean_winner_improvement_post"))
    final_winner = _safe_float(summary.get("final_winner_improvement_post"))
    mean_ratio = _safe_float(summary.get("mean_winner_contribution_ratio_post"))
    status_text = str(summary.get("status") or "")
    reasons: list[str] = []
    if rows_written < max(1, steps_requested):
        reasons.append(f"steps_incomplete:{rows_written}/{steps_requested}")
    if mean_winner is None or mean_winner <= 0:
        reasons.append("mean_winner_improvement_not_positive")
    if final_winner is None or final_winner <= 0:
        reasons.append("final_winner_improvement_not_positive")
    if "OOM" in status_text or "NaN" in status_text or "SIGFPE" in status_text or "FAIL" in status_text:
        reasons.append(f"runner_status:{status_text}")
    csv_path = next(root.glob("*_10step.csv"), None) or next(root.glob("*.csv"), None)
    rows = _read_csv(csv_path) if csv_path else []
    if rows:
        pass_rows = [r for r in rows if str(r.get("status")) == "PASS"]
        if len(pass_rows) < rows_written:
            reasons.append("non_pass_training_rows")
        grad_vals = [_safe_float(r.get("grad_norm")) for r in pass_rows]
        upd_vals = [_safe_float(r.get("update_norm")) for r in pass_rows]
        if not any(v is not None and v > 0 for v in grad_vals):
            reasons.append("grad_norm_zero_or_missing")
        if not any(v is not None and v > 0 for v in upd_vals):
            reasons.append("update_norm_zero_or_missing")
        dpo_vals = [_safe_float(r.get("dpo_loss")) for r in pass_rows]
        if dpo_vals and all(v is not None and abs(v - 0.693147) < 1e-5 for v in dpo_vals[-min(5, len(dpo_vals)):]):
            reasons.append("dpo_loss_pure_no_signal")
    else:
        reasons.append("training_csv_missing")
    if reasons:
        return {"status": "FAIL", "decision": "TRAINING_SIGNAL_FAIL", "reasons": reasons, "summary_path": str(summary_path), "summary": summary}
    return {"status": "PASS", "decision": "TRAINING_SIGNAL_PASS", "summary_path": str(summary_path), "summary": summary, "mean_winner_improvement_post": mean_winner, "final_winner_improvement_post": final_winner, "mean_winner_contribution_ratio_post": mean_ratio}


def check_checkpoint_video_eval(eval_root: str | Path) -> dict[str, Any]:
    root = Path(eval_root)
    if not root.exists():
        return {"status": "BLOCKED", "decision": "CHECKPOINT_EVAL_MISSING", "reason": str(root)}
    audit = root / "video_audit.csv"
    if not audit.exists():
        return {"status": "BLOCKED", "decision": "VIDEO_AUDIT_MISSING", "reason": str(audit)}
    rows = _read_csv(audit)
    if not rows:
        return {"status": "FAIL", "decision": "VIDEO_AUDIT_EMPTY"}
    bad = [r for r in rows if str(r.get("reviewed", "")).lower() != "true" or not str(r.get("written_reason", "")).strip() or str(r.get("worse_than_step0", "")).lower() == "true"]
    if bad:
        return {"status": "FAIL", "decision": "VIDEO_EVAL_FAIL", "bad_rows": len(bad), "audit": str(audit)}
    return {"status": "PASS", "decision": "VIDEO_EVAL_PASS", "rows": len(rows), "audit": str(audit)}


def check_metrics(metrics_root: str | Path) -> dict[str, Any]:
    root = Path(metrics_root)
    if not root.exists():
        return {"status": "BLOCKED", "decision": "METRICS_MISSING", "reason": str(root)}
    summary = root / "checkpoint_summary.csv"
    if not summary.exists():
        return {"status": "BLOCKED", "decision": "METRIC_SUMMARY_MISSING", "reason": str(summary)}
    rows = _read_csv(summary)
    if not rows:
        return {"status": "FAIL", "decision": "METRIC_SUMMARY_EMPTY"}
    collapsed = [r for r in rows if str(r.get("metric_status", "")).upper() in {"FAIL", "COLLAPSE", "DEGRADED"}]
    if collapsed:
        return {"status": "FAIL", "decision": "METRICS_DEGRADED", "bad_rows": len(collapsed)}
    return {"status": "PASS", "decision": "METRICS_PASS", "rows": len(rows)}


def check_no_loser_dominance(metrics_csv: str | Path) -> dict[str, Any]:
    path = Path(metrics_csv)
    rows = _read_csv(path)
    if not rows:
        return {"status": "BLOCKED", "decision": "TRAINING_METRICS_CSV_MISSING", "reason": str(path)}
    ratios = [_safe_float(r.get("winner_contribution_ratio_post")) for r in rows if r.get("winner_contribution_ratio_post") not in (None, "")]
    winner = [_safe_float(r.get("winner_improvement_post")) for r in rows if r.get("winner_improvement_post") not in (None, "")]
    if ratios and sum(v < 0.30 for v in ratios if v is not None) >= 2:
        return {"status": "FAIL", "decision": "LOSER_DOMINANT", "min_ratio": min(v for v in ratios if v is not None)}
    if winner and sum(v <= 0 for v in winner if v is not None) >= 2:
        return {"status": "FAIL", "decision": "WINNER_NOT_IMPROVING"}
    return {"status": "PASS", "decision": "NO_LOSER_DOMINANCE_DETECTED"}


def check_gpu_usage_only_allowed(state_or_logs: str | Path, allowed: list[int] | None = None) -> dict[str, Any]:
    allowed = allowed or [4, 5, 6, 7]
    path = Path(state_or_logs)
    if not path.exists():
        return {"status": "BLOCKED", "decision": "STATE_MISSING", "reason": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    bad: list[int] = []
    for job in data.get("jobs", []):
        for gpu in job.get("assigned_gpus") or []:
            if int(gpu) not in allowed:
                bad.append(int(gpu))
    if bad:
        return {"status": "FAIL", "decision": "FORBIDDEN_GPU_ASSIGNED", "bad_gpus": sorted(set(bad))}
    return {"status": "PASS", "decision": "GPU_ASSIGNMENTS_ALLOWED"}


def check_no_large_file_staged(repo_root: str | Path = ".") -> dict[str, Any]:
    import subprocess
    proc = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=repo_root, text=True, capture_output=True, check=False)
    names = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    forbidden_ext = {".mp4", ".jpg", ".jpeg", ".png", ".hdf5", ".h5", ".npy", ".npz", ".pt", ".pth", ".safetensors"}
    bad = [n for n in names if Path(n).suffix.lower() in forbidden_ext or n.startswith("local_assets/")]
    if bad:
        return {"status": "FAIL", "decision": "LARGE_OR_FORBIDDEN_FILES_STAGED", "files": bad}
    return {"status": "PASS", "decision": "NO_FORBIDDEN_FILES_STAGED", "files": names}
