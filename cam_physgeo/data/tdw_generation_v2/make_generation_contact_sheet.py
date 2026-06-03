from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create/collect contact sheet placeholders for TDW generation v2.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    images = sorted(args.root.rglob("*contact*.jpg")) + sorted(args.root.rglob("*contact*.png"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# TDW Generation v2 Contact Sheet Index", "", f"Root: `{args.root}`", ""]
    if not images:
        lines.append("No contact sheets found yet. Run validation with generated video/HDF5 outputs first.")
    for p in images[:100]:
        lines.append(f"- `{p}`")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print({"out": str(args.out), "contact_sheets": len(images)})

if __name__ == "__main__":
    main()
