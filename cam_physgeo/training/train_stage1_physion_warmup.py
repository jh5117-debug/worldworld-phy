from __future__ import annotations

import argparse
import sys

from cam_physgeo.training.model_loading import check_legacy_lingbot_import, resolve_model_paths
from cam_physgeo.training.train_utils import load_training_config, print_dry_run_plan


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", "--limit_samples", dest="limit_samples", type=int, default=0)
    ap.add_argument("--max_steps", type=int, default=0)
    args = ap.parse_args(argv)
    cfg = load_training_config(args.config)
    paths = resolve_model_paths(load_training_config("configs/cam_physgeo/paths.yaml"))
    import_check = check_legacy_lingbot_import(paths["lingbot_code"])
    command = [
        sys.executable,
        "-m",
        "physical_consistency.stages.stage1_physinone_cam.runner",
        "--config",
        str(cfg.get("legacy_config", "configs/train_stage1_physinone_cam.yaml")),
        "--control_type",
        "cam",
        "--base_model_dir",
        paths["lingbot_fast"] or paths["lingbot_base"],
        "--lingbot_code_dir",
        paths["lingbot_code"],
    ]
    print_dry_run_plan(
        "stage1_physion_support_warmup",
        cfg,
        command=command,
        limit_samples=args.limit_samples,
        max_steps=args.max_steps,
        legacy_import=import_check,
        dataset="Physion cam-only converted samples",
        action_conditioning="disabled; action.npy is dummy zero compatibility only",
        note="Real launch remains guarded behind --run and should use LoRA/adapter, low LR, short schedule.",
    )
    if args.dry_run or not args.run:
        return 0
    raise RuntimeError(
        "Stage1 Physion real training is guarded until the converted Physion manifest is reviewed. "
        "Use the printed legacy LingBot/TRD command as the integration path."
    )


if __name__ == "__main__":
    raise SystemExit(main())
