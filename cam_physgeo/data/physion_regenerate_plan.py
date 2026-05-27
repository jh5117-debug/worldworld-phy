from __future__ import annotations

import argparse
from pathlib import Path


PATTERNS = [
    "batch_generate_physion",
    "moving_camera",
    "tdw_physion",
    "multi_template",
    "support_moving_camera",
    "teleport_avatar_to",
    "look_at_position",
    "camera_position",
    "camera_pose",
    "camera_aim",
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root)
    hits = []
    for path in root.rglob("*"):
        if path.suffix.lower() not in {".py", ".sh", ".txt", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        matched = [p for p in PATTERNS if p.lower() in text or p.lower() in path.name.lower()]
        if matched:
            hits.append({"path": str(path), "matched": matched[:5]})
        if args.limit and len(hits) >= args.limit:
            break
    print({"generation_code_hits": len(hits), "dry_run": args.dry_run})
    for hit in hits:
        print(hit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
