from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

REQUIRED = ("video.mp4", "target.mp4", "image.jpg", "poses.npy", "intrinsics.npy", "prompt.txt", "metadata.json")
FIELDNAMES = ["sample_id", "clip_path", "prompt", "template", "camera_id", "trajectory_name", "seed", "source_width", "source_height", "prefix_len", "prediction_start_frame", "loss_frame_indices", "control_type", "use_action"]


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _stable_key(sample_id: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}:{sample_id}".encode("utf-8")).hexdigest()


def _row_for(sample_dir: Path) -> dict:
    meta = _read_json(sample_dir / "metadata.json")
    prompt = (sample_dir / "prompt.txt").read_text(encoding="utf-8", errors="replace").strip()
    sample_id = sample_dir.name
    parts = sample_id.split("_")
    template = str(meta.get("template") or (parts[1] if len(parts) > 1 else "unknown"))
    camera = str(meta.get("camera_variant") or meta.get("camera_motion") or meta.get("trajectory_name") or "_".join(parts[2:-1]) or "unknown")
    seed = meta.get("seed") or meta.get("trial_seed") or ""
    if not seed and "seed" in sample_id:
        seed = sample_id.rsplit("seed", 1)[-1]
    return {
        "sample_id": sample_id,
        "clip_path": str(sample_dir.resolve()),
        "prompt": prompt,
        "template": template,
        "camera_id": camera,
        "trajectory_name": camera,
        "seed": seed,
        "source_width": int(meta.get("width") or meta.get("source_width") or 832),
        "source_height": int(meta.get("height") or meta.get("source_height") or 480),
        "prefix_len": 5,
        "prediction_start_frame": 5,
        "loss_frame_indices": "5-80",
        "control_type": "cam",
        "use_action": "false",
    }


def scan_roots(roots: Iterable[Path]) -> tuple[list[dict], list[dict]]:
    seen: dict[str, Path] = {}
    rejected: list[dict] = []
    for root in roots:
        if not root.exists():
            rejected.append({"sample_id": "", "path": str(root), "status": "missing_root", "reason": "root_missing"})
            continue
        for sample_dir in sorted(root.iterdir()):
            if not sample_dir.is_dir() or sample_dir.name.startswith(".") or sample_dir.name.endswith(".tmp"):
                continue
            missing = [name for name in REQUIRED if not (sample_dir / name).exists()]
            if missing:
                rejected.append({"sample_id": sample_dir.name, "path": str(sample_dir), "status": "rejected", "reason": "missing:" + ",".join(missing)})
                continue
            seen.setdefault(sample_dir.name, sample_dir)
    return [_row_for(path) for _, path in sorted(seen.items())], rejected


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def main() -> int:
    parser = argparse.ArgumentParser(description="Build all-available V2V-5 warmup split: all clips train, mirrored eval subset for monitoring.")
    parser.add_argument("--converted_root", action="append", required=True)
    parser.add_argument("--dataset_dir", required=True)
    parser.add_argument("--report_dir", required=True)
    parser.add_argument("--eval_mirror_count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=3299)
    args = parser.parse_args()
    roots = [Path(v).resolve() for v in args.converted_root]
    rows, rejected = scan_roots(roots)
    rows.sort(key=lambda row: _stable_key(str(row["sample_id"]), args.seed))
    if not rows:
        raise RuntimeError("no usable Stage1-ready clips found")
    eval_count = min(args.eval_mirror_count, len(rows))
    eval_rows = rows[:eval_count]
    dataset_dir = Path(args.dataset_dir).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    write_csv(dataset_dir / "metadata_train.csv", rows)
    write_csv(dataset_dir / "metadata_val.csv", eval_rows)
    write_csv(dataset_dir / "metadata_test.csv", eval_rows)
    summary = {
        "status": "SPLIT_READY_ALL_AVAILABLE",
        "train_rows": len(rows),
        "val_rows": len(eval_rows),
        "test_rows": len(eval_rows),
        "eval_is_mirrored_from_train": True,
        "converted_roots": [str(r) for r in roots],
        "rejected_count": len(rejected),
        "dataset_dir": str(dataset_dir),
    }
    (report_dir / "all_available_split_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (report_dir / "stage1_ready_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_id", "clip_path", "template", "camera_id", "seed"])
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames or []})
    md = [
        "# V2V-5 All-Available Warmup Split",
        "",
        "Status: SPLIT_READY_ALL_AVAILABLE",
        f"Train rows: {len(rows)}",
        f"Val/test rows: {len(eval_rows)} mirrored from train for monitoring only",
        "Eval holdout caveat: user requested all usable data for warmup, so val/test are not held out.",
        "",
        "Converted roots:",
        *[f"- {r}" for r in roots],
    ]
    (report_dir / "all_available_split_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
