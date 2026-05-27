from __future__ import annotations

import argparse
from pathlib import Path

from cam_physgeo.data.prompt_templates import build_prompt
from cam_physgeo.utils.io import read_jsonl


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--level", default="P2", choices=["P0", "P1", "P2"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    out_dir = Path(args.out_dir)
    count = 0
    for i, sample in enumerate(read_jsonl(args.manifest)):
        if args.limit and i >= args.limit:
            break
        prompt = build_prompt(sample, args.level)
        path = out_dir / f"{sample['sample_id']}.txt"
        if not args.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(prompt + "\n", encoding="utf-8")
        count += 1
    print({"prompts": count, "out_dir": str(out_dir), "level": args.level, "dry_run": args.dry_run})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
