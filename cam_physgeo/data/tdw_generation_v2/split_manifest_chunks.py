from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_no}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Expected JSON object at {path}:{line_no}")
            rows.append(row)
    return rows


def split_rows(rows: list[dict[str, Any]], chunk_size: int) -> list[list[dict[str, Any]]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    return [rows[idx : idx + chunk_size] for idx in range(0, len(rows), chunk_size)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Split a JSONL TDW generation manifest into fixed-size chunks.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    parser.add_argument("--chunk_size", type=int, required=True)
    parser.add_argument("--prefix", default="chunk")
    args = parser.parse_args()

    rows = _read_jsonl(args.manifest)
    chunks = split_rows(rows, int(args.chunk_size))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for idx, chunk in enumerate(chunks):
        out = args.out_dir / f"{args.prefix}_{idx:03d}.jsonl"
        with out.open("w", encoding="utf-8") as handle:
            for row in chunk:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        outputs.append({"path": str(out), "count": len(chunk)})
    summary = {
        "manifest": str(args.manifest),
        "out_dir": str(args.out_dir),
        "chunk_size": int(args.chunk_size),
        "input_count": len(rows),
        "chunk_count": len(outputs),
        "chunks": outputs,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
