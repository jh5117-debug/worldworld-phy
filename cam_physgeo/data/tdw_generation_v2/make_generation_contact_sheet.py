from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create/collect contact sheet placeholders for TDW generation v2.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--validation_json", type=Path, default=None)
    args = parser.parse_args()
    images = sorted(args.root.rglob("*contact*.jpg")) + sorted(args.root.rglob("*contact*.png"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# TDW Generation v2 Contact Sheet Index", "", f"Root: `{args.root}`", ""]
    validation_rows = []
    if args.validation_json and args.validation_json.exists():
        data = json.loads(args.validation_json.read_text(encoding="utf-8"))
        validation_rows = data.get("rows", [])
        lines += [
            f"Validation JSON: `{args.validation_json}`",
            "",
            f"Visible-motion suitable: {sum(1 for r in validation_rows if r.get('suitable_for_visible_motion') is True)} / {len(validation_rows)}",
            f"Too static: {sum(1 for r in validation_rows if r.get('too_static') is True)}",
            f"Too extreme: {sum(1 for r in validation_rows if r.get('too_extreme') is True)}",
            f"Delayed camera motion: {sum(1 for r in validation_rows if r.get('delayed_camera_motion') is True)}",
            f"Duplicate scene hash: {sum(1 for r in validation_rows if r.get('duplicate_scene_hash') is True)}",
            f"Unique scene hash: {len({str(r.get('scene_hash')) for r in validation_rows if r.get('scene_hash')})}",
            "",
        ]
    if not images:
        lines.append("No contact sheets found yet. Run validation with generated video/HDF5 outputs first.")
    for p in images[:100]:
        lines.append(f"- `{p}`")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print({"out": str(args.out), "contact_sheets": len(images)})

if __name__ == "__main__":
    main()
