from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

REQUIRED = ("video.mp4", "target.mp4", "image.jpg", "poses.npy", "intrinsics.npy", "prompt.txt", "metadata.json")
FIELDNAMES = [
    "sample_id",
    "clip_path",
    "prompt",
    "template",
    "camera_id",
    "trajectory_name",
    "seed",
    "source_width",
    "source_height",
    "prefix_len",
    "prediction_start_frame",
    "loss_frame_indices",
    "control_type",
    "use_action",
]


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
    template = str(meta.get("template") or sample_id.split("_")[1] if "_" in sample_id else meta.get("template") or "unknown")
    camera = str(meta.get("camera_variant") or meta.get("camera_motion") or meta.get("trajectory_name") or "unknown")
    seed = meta.get("seed") or meta.get("trial_seed") or ""
    if not seed:
        parts = sample_id.split("seed")
        seed = parts[-1] if len(parts) > 1 else ""
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
    rows = [_row_for(path) for _, path in sorted(seen.items())]
    return rows, rejected


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def main() -> int:
    parser = argparse.ArgumentParser(description="Build strict 4900/100 V2V-5 warmup metadata split from converted Stage1 clips.")
    parser.add_argument("--converted_root", action="append", required=True)
    parser.add_argument("--dataset_dir", required=True)
    parser.add_argument("--report_dir", required=True)
    parser.add_argument("--train_count", type=int, default=4900)
    parser.add_argument("--test_count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=4900)
    args = parser.parse_args()

    roots = [Path(value).resolve() for value in args.converted_root]
    rows, rejected = scan_roots(roots)
    rows.sort(key=lambda row: _stable_key(str(row["sample_id"]), args.seed))
    required_total = args.train_count + args.test_count
    dataset_dir = Path(args.dataset_dir).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "status": "PASS" if len(rows) >= required_total else "BLOCKED_INSUFFICIENT_STAGE1_READY_DATA",
        "required_train": args.train_count,
        "required_test": args.test_count,
        "required_total": required_total,
        "usable_unique_stage1_ready": len(rows),
        "shortfall": max(required_total - len(rows), 0),
        "converted_roots": [str(root) for root in roots],
        "rejected_count": len(rejected),
    }

    (report_dir / "stage1_ready_inventory.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (report_dir / "stage1_ready_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_id", "clip_path", "template", "camera_id", "seed"])
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames or []})
    with (report_dir / "rejected_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_id", "path", "status", "reason"])
        writer.writeheader()
        for row in rejected:
            writer.writerow(row)

    md = [
        "# V2V-5 Warmup 4900x2 Data Gate",
        "",
        f"Status: {summary['status']}",
        f"Required: train={args.train_count}, test={args.test_count}, total={required_total}",
        f"Usable unique Stage1-ready clips: {len(rows)}",
        f"Shortfall: {summary['shortfall']}",
        "",
        "Converted roots:",
        *[f"- {root}" for root in roots],
        "",
        "Policy: this builder refuses to create a 4900/100 split unless at least 5000 unique Stage1-ready clips exist.",
    ]
    (report_dir / "data_gate.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    if len(rows) < required_total:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 2

    train = rows[: args.train_count]
    test = rows[args.train_count : args.train_count + args.test_count]
    write_csv(dataset_dir / "metadata_train.csv", train)
    write_csv(dataset_dir / "metadata_test.csv", test)
    write_csv(dataset_dir / "metadata_val.csv", test)
    summary.update(
        {
            "status": "SPLIT_READY",
            "dataset_dir": str(dataset_dir),
            "train_rows": len(train),
            "test_rows": len(test),
            "val_rows": len(test),
        }
    )
    (report_dir / "stage1_ready_inventory.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
