from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _stable_hash(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:12], 16)


def _stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(rows),
        "template": dict(Counter(r.get("template") for r in rows)),
        "camera_variant": dict(Counter(r.get("camera_variant") for r in rows)),
        "scene_hash_unique": len(set(r.get("scene_hash") or r.get("sample_id") for r in rows)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--train_count", type=int, required=True)
    parser.add_argument("--val_count", type=int, required=True)
    parser.add_argument("--test_count", type=int, required=True)
    parser.add_argument("--balance_keys", default="template,camera_variant")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rows = _load_jsonl(Path(args.manifest))
    expected = args.train_count + args.val_count + args.test_count
    if len(rows) != expected:
        raise SystemExit(f"expected {expected} rows, got {len(rows)}")

    rng = random.Random(args.seed)
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    balance_keys = [k.strip() for k in args.balance_keys.split(",") if k.strip()]
    for row in rows:
        groups[tuple(row.get(k) for k in balance_keys)].append(row)

    train: list[dict[str, Any]] = []
    val: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    split_targets = {"train": args.train_count, "val": args.val_count, "test": args.test_count}
    split_rows = {"train": train, "val": val, "test": test}

    for _, bucket in sorted(groups.items(), key=lambda item: str(item[0])):
        bucket = sorted(bucket, key=lambda r: _stable_hash(str(r.get("scene_hash") or r.get("sample_id"))))
        rng.shuffle(bucket)
        for row in bucket:
            split = min(split_rows, key=lambda name: len(split_rows[name]) / max(1, split_targets[name]))
            split_rows[split].append({**row, "split": split})

    # Fix exact sizes by moving overflow rows from largest splits to smallest splits.
    for _ in range(10000):
        overs = [name for name, target in split_targets.items() if len(split_rows[name]) > target]
        unders = [name for name, target in split_targets.items() if len(split_rows[name]) < target]
        if not overs and not unders:
            break
        if not overs or not unders:
            break
        src = max(overs, key=lambda name: len(split_rows[name]) - split_targets[name])
        dst = max(unders, key=lambda name: split_targets[name] - len(split_rows[name]))
        row = split_rows[src].pop()
        row["split"] = dst
        split_rows[dst].append(row)

    out_dir = Path(args.out_dir)
    _write_jsonl(out_dir / "train.jsonl", train)
    _write_jsonl(out_dir / "val.jsonl", val)
    _write_jsonl(out_dir / "test.jsonl", test)
    stats = {
        "manifest": args.manifest,
        "out_dir": args.out_dir,
        "seed": args.seed,
        "balance_keys": balance_keys,
        "train": _stats(train),
        "val": _stats(val),
        "test": _stats(test),
        "scene_overlap": {
            "train_val": len(set(r.get("scene_hash") for r in train) & set(r.get("scene_hash") for r in val)),
            "train_test": len(set(r.get("scene_hash") for r in train) & set(r.get("scene_hash") for r in test)),
            "val_test": len(set(r.get("scene_hash") for r in val) & set(r.get("scene_hash") for r in test)),
        },
    }
    (out_dir / "split_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
