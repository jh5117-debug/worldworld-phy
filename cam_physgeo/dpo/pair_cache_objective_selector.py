from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from cam_physgeo.dpo.winner_anchor_cache_builder import sha256_file


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _read_validation(path: str | Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            out[str(row.get("pair_id", ""))] = dict(row)
    return out


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed"}


def _floatish(value: Any, default: float = float("nan")) -> float:
    try:
        return float(value)
    except Exception:
        return default


def compute_pair_weight(delta_ref: float, positive_mean: float) -> float:
    if not math.isfinite(delta_ref) or delta_ref <= 0.0:
        return 0.1
    if not math.isfinite(positive_mean) or positive_mean <= 0.0:
        return 1.0
    return min(2.0, max(0.5, float(delta_ref) / float(positive_mean)))


def _validate_index_row(root: Path, row: dict[str, Any], validation: dict[str, Any] | None) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if row.get("status") != "PASS":
        errors.append("index_status_not_pass")
    tensor_path = root / str(row.get("cache_tensor_path", ""))
    if not tensor_path.exists():
        errors.append("cache_tensor_missing")
    else:
        try:
            if sha256_file(tensor_path) != row.get("sha256"):
                errors.append("sha256_mismatch")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"sha256_error:{exc!r}")
    for key, expected in (("prefix_len", 5), ("prediction_start_frame", 5), ("used_window_frames", 49)):
        try:
            if int(row.get(key, -1)) != expected:
                errors.append(f"{key}_mismatch")
        except Exception:
            errors.append(f"{key}_invalid")
    if not _boolish(row.get("codex_visual_audit_reviewed")):
        errors.append("not_reviewed")
    if not _boolish(row.get("codex_visual_audit_is_dpo_ready")):
        errors.append("not_dpo_ready")
    for key in ("E_ref_winner_cached", "E_ref_loser_cached", "Delta_ref", "actual_sigma"):
        if not math.isfinite(_floatish(row.get(key))):
            errors.append(f"{key}_nonfinite")
    if row.get("same_seed_noise_id", "") == "":
        errors.append("same_seed_noise_id_missing")
    if validation is None:
        errors.append("validation_row_missing")
    else:
        if validation.get("status") != "PASS":
            errors.append("validation_not_pass")
        for key in ("winner_present", "loser_present", "winner_finite", "loser_finite", "future_mask_nonempty", "reviewed"):
            if not _boolish(validation.get(key)):
                errors.append(f"validation_{key}_false")
    return (len(errors) == 0), errors


def select_pairs(cache_root: str | Path, validation_csv: str | Path, output_dir: str | Path) -> dict[str, Any]:
    root = Path(cache_root)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = _read_jsonl(root / "cache_index.jsonl")
    validation = _read_validation(validation_csv)
    seen: set[str] = set()
    selected: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        pair_id = str(row.get("pair_id", ""))
        valid, errors = _validate_index_row(root, row, validation.get(pair_id))
        if not pair_id or pair_id in seen:
            valid = False
            errors.append("missing_or_duplicate_pair_id")
        seen.add(pair_id)
        delta_ref = _floatish(row.get("Delta_ref"))
        selected.append({
            "rank_source": idx,
            "pair_id": pair_id,
            "status": "PASS" if valid else "FAIL",
            "error_reason": ";".join(errors),
            "Delta_ref": delta_ref,
            "E_ref_winner_cached": _floatish(row.get("E_ref_winner_cached")),
            "E_ref_loser_cached": _floatish(row.get("E_ref_loser_cached")),
            "actual_sigma": _floatish(row.get("actual_sigma")),
            "timestep": _floatish(row.get("timestep")),
            "same_seed_noise_id": row.get("same_seed_noise_id", ""),
            "cache_tensor_path": row.get("cache_tensor_path", ""),
            "sha256": row.get("sha256", ""),
            "used_window_frames": row.get("used_window_frames", ""),
            "prefix_len": row.get("prefix_len", ""),
            "prediction_start_frame": row.get("prediction_start_frame", ""),
            "reviewed": row.get("codex_visual_audit_reviewed", ""),
            "dpo_ready": row.get("codex_visual_audit_is_dpo_ready", ""),
            "main_failure": row.get("codex_visual_audit_main_failure", ""),
            "written_reason": row.get("codex_visual_audit_written_reason", ""),
        })
    positive_values = [float(r["Delta_ref"]) for r in selected if r["status"] == "PASS" and float(r["Delta_ref"]) > 0.0]
    positive_mean = sum(positive_values) / len(positive_values) if positive_values else 0.0
    for row in selected:
        row["pair_weight"] = compute_pair_weight(float(row["Delta_ref"]), positive_mean)
    positives = sorted([r for r in selected if r["status"] == "PASS" and float(r["Delta_ref"]) > 0.0], key=lambda x: float(x["Delta_ref"]), reverse=True)
    nonpositive = sorted([r for r in selected if r["status"] == "PASS" and float(r["Delta_ref"]) <= 0.0], key=lambda x: float(x["Delta_ref"]))
    fieldnames = [
        "rank_source", "pair_id", "status", "error_reason", "Delta_ref", "pair_weight",
        "E_ref_winner_cached", "E_ref_loser_cached", "actual_sigma", "timestep", "same_seed_noise_id",
        "cache_tensor_path", "sha256", "used_window_frames", "prefix_len", "prediction_start_frame",
        "reviewed", "dpo_ready", "main_failure", "written_reason",
    ]
    with (out / "pair_cache_selection.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(selected)
    def write_subset(path: Path, subset: list[dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as f:
            for r in subset:
                f.write(json.dumps(r, sort_keys=True) + "\n")
    write_subset(out / "delta_ref_positive_pairs.jsonl", positives)
    write_subset(out / "top5_delta_ref_positive_pairs.jsonl", positives[:5])
    write_subset(out / "delta_ref_nonpositive_pairs.jsonl", nonpositive)
    status = "PAIR_SELECTION_PASS" if len(positives) >= 5 else "PAIR_SELECTION_BLOCKED_INSUFFICIENT_POSITIVE_DELTA_REF"
    summary = {
        "status": status,
        "total_rows": len(rows),
        "valid_rows": len([r for r in selected if r["status"] == "PASS"]),
        "positive_delta_ref": len(positives),
        "nonpositive_delta_ref": len(nonpositive),
        "positive_delta_ref_mean": positive_mean,
        "output_dir": str(out),
    }
    (out / "selection_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "selection_summary.md").write_text(
        "Current Status:\n" + status + "\n\n"
        "# v8n Pair Cache Selection\n\n"
        f"- Total cache rows: {len(rows)}\n"
        f"- Valid rows: {summary['valid_rows']}\n"
        f"- Delta_ref positive: {len(positives)}\n"
        f"- Delta_ref nonpositive diagnostic-only: {len(nonpositive)}\n"
        f"- Positive Delta_ref mean: {positive_mean}\n"
        "- Nonpositive rows are excluded from training objectives and kept for diagnostics only.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Select validated positive-Delta_ref v8m pair-cache rows for v8n objectives.")
    parser.add_argument("--cache_root", required=True)
    parser.add_argument("--validation_csv", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--diagnose_nonpositive_delta_ref", default="false")
    args = parser.parse_args(argv)
    select_pairs(args.cache_root, args.validation_csv, args.output_dir)


if __name__ == "__main__":
    main()

