from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan conversion of generated TDW v2 samples to LingBot cam-only inputs.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "# TDW Generation v2 LingBot Conversion Plan\n\n"
        f"Root: `{args.root}`\n\n"
        f"Dry run: {args.dry_run}\n\n"
        "Conversion is intentionally gated behind HDF5 validation and filtering. Expected output fields: target.mp4, first_frame.png, prompt.txt, poses.npy, intrinsics.npy, dummy action.npy with use_action=false.\n",
        encoding="utf-8",
    )
    print({"out": str(args.out), "dry_run": args.dry_run})

if __name__ == "__main__":
    main()
