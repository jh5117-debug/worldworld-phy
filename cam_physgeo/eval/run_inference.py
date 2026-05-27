from __future__ import annotations

import argparse
import json
from pathlib import Path

from cam_physgeo.training.model_loading import check_legacy_lingbot_import, inspect_checkpoint, resolve_model_paths
from cam_physgeo.utils.io import load_yaml


def iter_sample_dirs(root: str | Path, limit: int = 0) -> list[Path]:
    root = Path(root)
    if not root.exists():
        return []
    dirs = [p for p in sorted(root.iterdir()) if p.is_dir()]
    return dirs[:limit] if limit else dirs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/cam_physgeo/eval.yaml")
    ap.add_argument("--model_type", default="fast", choices=["fast", "base"])
    ap.add_argument("--samples", default="")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--out", default="local_assets/outputs/smoke/lingbot_fast_inference")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--smoke-run", action="store_true")
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--num_frames", type=int, default=16)
    ap.add_argument("--num_steps", type=int, default=2)
    args = ap.parse_args(argv)
    cfg = load_yaml(args.config) if args.config else {}
    paths_cfg = load_yaml("configs/cam_physgeo/paths.yaml")
    paths = resolve_model_paths(paths_cfg)
    model_path = paths["lingbot_fast" if args.model_type == "fast" else "lingbot_base"]
    checkpoint = inspect_checkpoint(model_path, label=f"lingbot_{args.model_type}")
    import_check = check_legacy_lingbot_import(paths["lingbot_code"])
    samples_root = args.samples or cfg.get("samples") or cfg.get("input_root") or ""
    sample_dirs = iter_sample_dirs(samples_root, args.limit) if samples_root else []
    payload = {
        "out": args.out,
        "model_type": args.model_type,
        "model_path": model_path,
        "checkpoint": checkpoint.to_dict(),
        "lingbot_code": paths["lingbot_code"],
        "legacy_import": import_check,
        "samples_root": samples_root,
        "sample_count": len(sample_dirs),
        "sample_dirs": [str(p) for p in sample_dirs],
        "control_type": "camera_conditioned",
        "use_action": False,
        "dummy_action_policy": "only_if_legacy_loader_requires_action.npy",
        "num_frames": args.num_frames,
        "num_steps": args.num_steps,
        "dry_run": args.dry_run,
        "smoke_run": args.smoke_run,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.smoke_run:
        raise RuntimeError(
            "LingBot-Fast short inference is not launched by this adapter yet. "
            "Dry-run path/import checks passed as reported; wire the legacy eval_batch runtime before GPU inference."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
