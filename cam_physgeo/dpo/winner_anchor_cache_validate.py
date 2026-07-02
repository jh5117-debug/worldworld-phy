
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import torch


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def tensor_tree_finite(obj: Any) -> bool:
    if torch.is_tensor(obj):
        return bool(torch.isfinite(obj.float()).all().item())
    if isinstance(obj, dict):
        return all(tensor_tree_finite(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return all(tensor_tree_finite(v) for v in obj)
    return True


def append_csv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def validate_cache_root(cache_root: str | Path, output: str | Path) -> dict[str, Any]:
    root = Path(cache_root)
    out = Path(output)
    if out.exists():
        out.unlink()
    index = root / "cache_index.jsonl"
    rows = load_jsonl(index) if index.exists() else []
    fieldnames = [
        "pair_id", "status", "cache_tensor_path", "exists", "sha256_match", "finite", "used_window_frames",
        "prefix_len", "prediction_start_frame", "future_mask_nonempty", "mask_excludes_prefix",
        "no_loser_fields", "E_ref_winner_cached_finite", "actual_sigma_present", "duplicate_pair_id",
        "error_reason",
    ]
    seen: set[str] = set()
    pass_count = 0
    fail_count = 0
    for row in rows:
        pair_id = str(row.get("pair_id", ""))
        duplicate = pair_id in seen
        seen.add(pair_id)
        status = "PASS"
        errors: list[str] = []
        rel = str(row.get("cache_tensor_path", ""))
        tensor_path = root / rel
        payload: dict[str, Any] | None = None
        exists = tensor_path.exists()
        sha_match = False
        finite = False
        future_mask_nonempty = False
        mask_excludes_prefix = False
        no_loser_fields = "loser" not in json.dumps(row).lower()
        eref_finite = False
        actual_sigma_present = row.get("actual_sigma") not in {None, ""}
        try:
            if not exists:
                raise FileNotFoundError(str(tensor_path))
            sha_match = sha256_file(tensor_path) == str(row.get("sha256", ""))
            if not sha_match:
                errors.append("sha256_mismatch")
            payload = torch.load(tensor_path, map_location="cpu")
            required = {"target", "noisy_latent", "context", "y", "dit_cond", "seq_len", "latent_loss_indices", "timestep_tensor", "actual_sigma", "timestep_weight"}
            missing = sorted(required - set(payload))
            if missing:
                errors.append("missing:" + ",".join(missing))
            finite = tensor_tree_finite(payload)
            indices = list(payload.get("latent_loss_indices", []))
            future_mask_nonempty = len(indices) > 0
            mask_excludes_prefix = future_mask_nonempty and min(int(x) for x in indices) >= 2
            no_loser_fields = no_loser_fields and "loser" not in json.dumps(sorted(payload.keys())).lower()
            eref = float(row.get("E_ref_winner_cached"))
            eref_finite = math.isfinite(eref)
            if int(row.get("used_window_frames", -1)) != 49:
                errors.append("used_window_frames_not_49")
            if int(row.get("prefix_len", -1)) != 5:
                errors.append("prefix_len_not_5")
            if int(row.get("prediction_start_frame", -1)) != 5:
                errors.append("prediction_start_frame_not_5")
            if not future_mask_nonempty:
                errors.append("empty_future_mask")
            if not mask_excludes_prefix:
                errors.append("mask_includes_prefix_or_unknown")
            if not finite:
                errors.append("nonfinite_tensor")
            if not eref_finite:
                errors.append("nonfinite_E_ref")
            if not actual_sigma_present:
                errors.append("missing_actual_sigma")
            if duplicate:
                errors.append("duplicate_pair_id")
        except Exception as exc:  # noqa: BLE001
            errors.append(repr(exc))
        if errors:
            status = "FAIL"
            fail_count += 1
        else:
            pass_count += 1
        append_csv(
            out,
            {
                "pair_id": pair_id,
                "status": status,
                "cache_tensor_path": str(tensor_path),
                "exists": exists,
                "sha256_match": sha_match,
                "finite": finite,
                "used_window_frames": row.get("used_window_frames", ""),
                "prefix_len": row.get("prefix_len", ""),
                "prediction_start_frame": row.get("prediction_start_frame", ""),
                "future_mask_nonempty": future_mask_nonempty,
                "mask_excludes_prefix": mask_excludes_prefix,
                "no_loser_fields": no_loser_fields,
                "E_ref_winner_cached_finite": eref_finite,
                "actual_sigma_present": actual_sigma_present,
                "duplicate_pair_id": duplicate,
                "error_reason": ";".join(errors),
            },
            fieldnames,
        )
    status = "CACHE_VALIDATION_PASS" if rows and pass_count == len(rows) else "CACHE_VALIDATION_FAIL"
    summary = {"status": status, "rows": len(rows), "pass": pass_count, "fail": fail_count, "cache_root": str(root), "output": str(out)}
    Path(output).with_name("cache_validation_summary.md").write_text(
        "Current Status:\n" + status + "\n\n"
        "# v8d Cache Validation Summary\n\n"
        f"- Rows: {len(rows)}\n"
        f"- Pass: {pass_count}\n"
        f"- Fail: {fail_count}\n"
        f"- Cache root: `{root}`\n"
        f"- Output: `{out}`\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate reusable v8d winner-anchor cache.")
    parser.add_argument("--cache_root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    validate_cache_root(args.cache_root, args.output)


if __name__ == "__main__":
    main()
