from __future__ import annotations

import argparse
from collections import Counter

from cam_physgeo.data.scan_physion_movingcam import iter_physion_movingcam_samples
from cam_physgeo.data.scan_physion_official import iter_physion_official_samples
from cam_physgeo.utils.io import write_jsonl


def build_manifest(
    *,
    physion_official_root: str | None = None,
    physion_movingcam_root: str | None = None,
    physion_movingcam_outputs: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    records: list[dict] = []
    if physion_official_root:
        records.extend(iter_physion_official_samples(physion_official_root, limit=limit))
    if physion_movingcam_root or physion_movingcam_outputs:
        records.extend(
            iter_physion_movingcam_samples(
                physion_movingcam_root,
                outputs_root=physion_movingcam_outputs,
                limit=limit,
            )
        )
    records.sort(
        key=lambda row: (
            row.get("source", ""),
            not bool(row.get("has_camera_pose")),
            not bool(row.get("has_intrinsics")),
            row.get("video_path") is None,
            row.get("sample_id", ""),
        )
    )
    return records[:limit] if limit else records


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--physion_official_root", default="")
    ap.add_argument("--physion_movingcam_root", default="")
    ap.add_argument("--physion_movingcam_outputs", default="")
    ap.add_argument("--out", default="manifests/physion_cam_physgeo_all.jsonl")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    # Deprecated aliases are accepted to avoid hard crashes in old shell history,
    # but they are never emitted as active manifest sources.
    ap.add_argument("--phyinone_root", default="", help=argparse.SUPPRESS)
    ap.add_argument("--movingcam_root", default="", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.phyinone_root:
        print("WARNING: --phyinone_root is deprecated and ignored in the Physion-only pipeline.")
    moving_root = args.physion_movingcam_root or args.movingcam_root
    records = build_manifest(
        physion_official_root=args.physion_official_root or None,
        physion_movingcam_root=moving_root or None,
        physion_movingcam_outputs=args.physion_movingcam_outputs or None,
        limit=args.limit or None,
    )
    by_source = Counter(row["source"] for row in records)
    print({"total": len(records), "by_source": dict(by_source), "out": args.out, "dry_run": args.dry_run})
    if not args.dry_run:
        print(f"wrote {write_jsonl(records, args.out)} samples to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
