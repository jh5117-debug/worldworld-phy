from __future__ import annotations

import argparse
from collections import Counter

from cam_physgeo.data.sample_schema import validate_sample
from cam_physgeo.utils.io import read_jsonl, write_json


def validate_manifest(path: str, check_paths: bool = True) -> dict:
    total = bad = 0
    errors: Counter[str] = Counter()
    src: Counter[str] = Counter()
    tmpl: Counter[str] = Counter()
    cam: Counter[str] = Counter()
    available = Counter()
    for sample in read_jsonl(path):
        total += 1
        src[sample.get("source", "missing")] += 1
        tmpl[sample.get("template", "missing")] += 1
        cam[sample.get("camera_motion", "missing")] += 1
        for key in ["has_camera_pose", "has_intrinsics", "has_depth", "has_id_mask", "has_object_state", "has_reobserve"]:
            if sample.get(key):
                available[key] += 1
        sample_errors = validate_sample(sample, check_paths=check_paths)
        if sample_errors:
            bad += 1
            errors.update(sample_errors)
    return {
        "manifest": path,
        "total": total,
        "bad_samples": bad,
        "errors": dict(errors),
        "by_source": dict(src),
        "by_template": dict(tmpl),
        "by_camera_motion": dict(cam),
        "availability": dict(available),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--no-path-check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    report = validate_manifest(args.manifest, check_paths=not args.no_path_check)
    print(report)
    if args.report and not args.dry_run:
        write_json(report, args.report)
    return 1 if report["bad_samples"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
