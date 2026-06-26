from __future__ import annotations

import argparse
from pathlib import Path

from cam_physgeo.training.prefix_conditioning import enrich_rows
from cam_physgeo.utils.io import read_jsonl, write_json, write_jsonl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build prefix-aware benchmark or DPO manifests.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--prefix_len", type=int, required=True)
    parser.add_argument("--num_frames", type=int, default=81)
    parser.add_argument("--temporal_compression", type=int, default=4)
    parser.add_argument("--summary", default="")
    args = parser.parse_args(argv)

    rows = list(read_jsonl(args.input))
    enriched = enrich_rows(
        rows,
        prefix_len=args.prefix_len,
        num_frames=args.num_frames,
        temporal_compression=args.temporal_compression,
    )
    count = write_jsonl(enriched, args.out)
    summary_path = Path(args.summary) if args.summary else Path(args.out).with_suffix(".summary.json")
    write_json(
        {
            "input": args.input,
            "out": args.out,
            "count": count,
            "prefix_len": args.prefix_len,
            "num_frames": args.num_frames,
            "temporal_compression": args.temporal_compression,
            "eval_future_only": True,
            "status": "ready",
        },
        summary_path,
    )
    print({"out": args.out, "count": count, "summary": str(summary_path)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

