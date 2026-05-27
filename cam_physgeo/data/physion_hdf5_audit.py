from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from cam_physgeo.data.physion_hdf5_reader import infer_key_mapping, list_hdf5_datasets


KEYWORDS = [
    "camera",
    "avatar",
    "pose",
    "position",
    "rotation",
    "aim",
    "look_at",
    "field_of_view",
    "fov",
    "projection",
    "projection_matrix",
    "camera_matrix",
    "intrinsic",
    "intrinsics",
    "extrinsic",
    "extrinsics",
    "view_matrix",
    "screen_width",
    "screen_height",
    "width",
    "height",
    "_depth",
    "_id",
    "_img",
    "flow",
    "normal",
    "objects",
    "object_states",
    "segmentation",
    "collisions",
    "contact",
    "target",
    "trial_complete",
]


def iter_hdf5_files(roots: list[str], limit: int = 0):
    seen: set[str] = set()
    for root in roots:
        r = Path(root).expanduser()
        if not r.exists():
            continue
        for path in r.rglob("*"):
            if path.suffix.lower() not in {".hdf5", ".h5"}:
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            yield path
            if limit and len(seen) >= limit:
                return


def audit_files(paths: list[Path]) -> dict:
    key_counter: Counter[str] = Counter()
    keyword_counter: Counter[str] = Counter()
    rows = []
    for path in paths:
        try:
            datasets = list_hdf5_datasets(path)
            mapping = infer_key_mapping(path)
            for key in datasets:
                key_counter[key] += 1
                low = key.lower()
                for kw in KEYWORDS:
                    if kw in low:
                        keyword_counter[kw] += 1
            rows.append({"path": str(path), "datasets": datasets, "mapping": mapping, "error": None})
        except Exception as exc:
            rows.append({"path": str(path), "datasets": {}, "mapping": {}, "error": repr(exc)})
    return {"files": rows, "key_counter": key_counter, "keyword_counter": keyword_counter}


def write_markdown(report: dict, out: str) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    files = report["files"]
    lines = [
        "# Physion HDF5 Key Audit",
        "",
        f"- files audited: {len(files)}",
        f"- files with explicit camera pose key: {sum(1 for r in files if r['mapping'].get('poses_key'))}",
        f"- files with projection/intrinsics key: {sum(1 for r in files if r['mapping'].get('intrinsics_key'))}",
        f"- files with camera_position + camera_aim: {sum(1 for r in files if r['mapping'].get('camera_position_key') and r['mapping'].get('camera_aim_key'))}",
        f"- files with depth: {sum(1 for r in files if r['mapping'].get('depth_key'))}",
        f"- files with id mask: {sum(1 for r in files if r['mapping'].get('id_key'))}",
        "",
        "## Conclusion",
        "",
        "The moving-camera Physion/TDW HDF5 layout is directly usable when `camera_pose`, `camera_position`, `camera_aim`, `camera_matrix` or `projection_matrix` keys are present. Explicit K-style intrinsics may be absent, but the projection matrix can be used as a camera calibration source; if neither projection nor FOV is present, the sample is marked unusable for camera-conditioned evaluation.",
        "",
        "## Files",
    ]
    for row in files:
        lines.extend(["", f"### `{row['path']}`"])
        if row["error"]:
            lines.append(f"- error: `{row['error']}`")
            continue
        mapping = row["mapping"]
        for key, value in mapping.items():
            lines.append(f"- {key}: `{value}`")
        lines.append("- matched datasets:")
        matched = [k for k in row["datasets"] if any(kw in k.lower() for kw in KEYWORDS)]
        for key in matched[:80]:
            meta = row["datasets"][key]
            lines.append(f"  - `{key}` shape={meta.get('shape')} dtype={meta.get('dtype')}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--out", default="docs/physion_hdf5_key_audit.md")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    paths = list(iter_hdf5_files(args.roots, limit=args.limit))
    report = audit_files(paths)
    print({"audited": len(paths), "out": args.out, "dry_run": args.dry_run})
    if not args.dry_run:
        write_markdown(report, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
