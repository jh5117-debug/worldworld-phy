from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return rows


def _write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    h = hashlib.sha256()
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            line = json.dumps(row, ensure_ascii=False, sort_keys=True)
            handle.write(line + "\n")
            h.update(line.encode("utf-8"))
            h.update(b"\n")
            count += 1
    (path.with_suffix(path.suffix + ".sha256")).write_text(h.hexdigest() + "\n", encoding="utf-8")
    return count


def _validation_counts(path: Path) -> dict[str, int | str]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

    def _count(label: str) -> int:
        match = re.search(rf"{re.escape(label)}:\s*(\d+)", text)
        return int(match.group(1)) if match else 0

    return {
        "report_path": str(path),
        "generated_hdf5_count": _count("Generated HDF5 count"),
        "validation_ok_count": _count("Validation ok count"),
        "suitable_for_warmup_count": _count("Suitable for warmup count"),
        "suitable_for_visible_motion_count": _count("Suitable for visible motion count"),
        "blocked_count": text.count("| blocked |"),
    }


def _sample_id(row: dict) -> str:
    for key in ("sample_id", "output_name", "trial_name", "name"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    out = str(row.get("output_path") or row.get("path") or "").strip()
    if out:
        return Path(out).parts[-2] if out.endswith("0000.hdf5") else Path(out).name
    index = row.get("trial_index", row.get("index", row.get("sample_index", "")))
    template = row.get("template", "unknown")
    seed = row.get("seed", row.get("trial_seed", ""))
    camera = row.get("camera_variant", row.get("camera_motion", "camera"))
    return f"{int(index):05d}_{template}_{camera}_seed{seed}" if str(index).strip() else f"{template}_{camera}_seed{seed}"


def _hdf5_path(row: dict, *, root: Path, raw_subdir: str) -> Path:
    for key in ("hdf5_path", "output_path", "path"):
        value = str(row.get(key) or "").strip()
        if value:
            path = Path(value)
            return path if path.is_absolute() else root / path
    return root / "raw_hdf5" / raw_subdir / _sample_id(row) / "0000.hdf5"


def _split_rows(rows: list[dict], *, seed: int) -> tuple[list[dict], list[dict], list[dict]]:
    grouped: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        group = str(row.get("scene_hash") or row.get("scene_seed") or row.get("seed") or row["sample_id"])
        grouped[group].append(row)
    keys = sorted(grouped)
    rng = hashlib.sha256(str(seed).encode("ascii")).hexdigest()
    keys.sort(key=lambda key: hashlib.sha256((rng + key).encode("utf-8")).hexdigest())
    total = sum(len(grouped[key]) for key in keys)
    train_target = int(total * 0.85)
    val_target = int(total * 0.10)
    train: list[dict] = []
    val: list[dict] = []
    test: list[dict] = []
    for key in keys:
        target = train if len(train) < train_target else (val if len(val) < val_target else test)
        target.extend(grouped[key])
    for split, split_rows_out in (("train", train), ("val", val), ("test_holdout", test)):
        for row in split_rows_out:
            row["split"] = split
    return train, val, test


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build immutable StageA v5 snapshot from completed TDW chunk manifests.")
    parser.add_argument("--generated_root", required=True)
    parser.add_argument("--manifest_chunks_dir", required=True)
    parser.add_argument("--reports_dir", required=True)
    parser.add_argument("--raw_subdir", default="v5_aggressive_2x_scaleup_4000_to_5000")
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--require_validation_ok", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    generated_root = Path(args.generated_root).resolve()
    chunks_dir = Path(args.manifest_chunks_dir).resolve()
    reports_dir = Path(args.reports_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    timestamp = args.timestamp or datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")

    eligible_rows: list[dict] = []
    chunk_summaries: list[dict] = []
    for chunk_path in sorted(chunks_dir.glob("chunk_*.jsonl")):
        chunk_id = chunk_path.stem.replace("chunk_", "")
        report_path = reports_dir / f"validation_chunk_{chunk_id}.md"
        counts = _validation_counts(report_path)
        rows = _read_jsonl(chunk_path)
        hdf5_existing = 0
        hdf5_eligible = 0
        for row in rows:
            hdf5_path = _hdf5_path(row, root=generated_root, raw_subdir=args.raw_subdir)
            if not hdf5_path.exists():
                continue
            hdf5_existing += 1
            if args.require_validation_ok and int(counts["validation_ok_count"]) <= 0:
                continue
            stat = hdf5_path.stat()
            record = dict(row)
            record.update(
                {
                    "sample_id": _sample_id(row),
                    "absolute_hdf5_path": str(hdf5_path),
                    "prepared_video_path": "",
                    "validation_report": str(report_path),
                    "validation_status": "ok" if int(counts["validation_ok_count"]) > 0 else "blocked",
                    "chunk_id": chunk_id,
                    "source_file_size": stat.st_size,
                    "source_file_mtime": int(stat.st_mtime),
                    "quality_flags": [] if int(counts["validation_ok_count"]) > 0 else ["validation_blocked"],
                    "use_action": False,
                }
            )
            hdf5_eligible += 1
            eligible_rows.append(record)
        chunk_summaries.append(
            {
                "chunk_id": chunk_id,
                "manifest": str(chunk_path),
                **counts,
                "manifest_rows": len(rows),
                "hdf5_existing": hdf5_existing,
                "eligible_rows": hdf5_eligible,
            }
        )

    train, val, test = _split_rows(eligible_rows, seed=args.seed)
    all_path = out_dir / f"stageA_v5_snapshot_{timestamp}_all.jsonl"
    train_path = out_dir / f"stageA_v5_snapshot_{timestamp}_train.jsonl"
    val_path = out_dir / f"stageA_v5_snapshot_{timestamp}_val.jsonl"
    test_path = out_dir / f"stageA_v5_snapshot_{timestamp}_test_holdout.jsonl"
    _write_jsonl(all_path, eligible_rows)
    _write_jsonl(train_path, train)
    _write_jsonl(val_path, val)
    _write_jsonl(test_path, test)
    templates = collections.Counter(str(row.get("template") or "") for row in eligible_rows)
    cameras = collections.Counter(str(row.get("camera_variant") or row.get("camera_motion") or "") for row in eligible_rows)
    summary = {
        "timestamp": timestamp,
        "generated_root": str(generated_root),
        "eligible_count": len(eligible_rows),
        "train_count": len(train),
        "val_count": len(val),
        "test_holdout_count": len(test),
        "require_validation_ok": bool(args.require_validation_ok),
        "templates": dict(sorted(templates.items())),
        "camera_variants": dict(cameras.most_common()),
        "manifests": {
            "all": str(all_path),
            "train": str(train_path),
            "val": str(val_path),
            "test_holdout": str(test_path),
        },
        "chunks": chunk_summaries,
        "ready_for_generated_v5_training": bool(eligible_rows) and all(
            row.get("validation_status") == "ok" for row in eligible_rows
        ),
    }
    summary_path = out_dir / f"stageA_v5_snapshot_{timestamp}_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
