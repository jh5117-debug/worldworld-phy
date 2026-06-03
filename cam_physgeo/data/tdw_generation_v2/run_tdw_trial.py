from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from pathlib import Path

from .generation_config import existing_workspace, get_profile, load_config, output_root

MILD_VARIANTS = {"orbit_left_20", "strafe_right_045", "orbit_left_12", "strafe_right_025"}


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_existing_batch_command(config: dict, profile_name: str, num_trials: int, out_root: Path, dry_run: bool) -> tuple[list[str], dict]:
    profile = get_profile(config, profile_name)
    workspace = existing_workspace(config)
    runner = workspace / "scripts" / "batch_generate_physion_dpo_conditions.py"
    py = workspace / ".conda_envs" / "tdw-physion" / "bin" / "python3"
    if not py.exists():
        py = workspace / ".conda_envs" / "tdw-physion" / "bin" / "python"
    templates = ",".join(profile.templates)
    variants = [v.get("name") for v in profile.camera_variants]
    mild_only = all(v in MILD_VARIANTS for v in variants)
    blocker = None
    if profile_name == "warmup_mild" and not mild_only:
        blocker = "warmup_mild contains non-mild variants; refusing to generate."
    if profile_name == "warmup_mild":
        # Existing upstream batch has no explicit mild-only camera_set. Use dry-run by default;
        # actual execution requires wrapper-native mild support or an upstream mild-only option.
        blocker = blocker or "upstream batch runner has no explicit mild-only camera_set; actual generation blocked to avoid stress/reobserve leakage into warmup."
    cmd = [
        str(py), str(runner),
        "--workspace", str(workspace),
        "--output_root", str(out_root / "raw_hdf5" / f"{profile_name}_{num_trials}samples"),
        "--templates", templates,
        "--width", str(config.get("resolution", {}).get("width", 832)),
        "--height", str(config.get("resolution", {}).get("height", 480)),
        "--max_frames", str(config.get("frames", {}).get("max_frames", 81)),
        "--min_frames", str(config.get("frames", {}).get("min_frames", 81)),
        "--aligned_frames", str(config.get("frames", {}).get("aligned_frames", 81)),
        "--limit", str(num_trials),
    ]
    if dry_run:
        cmd.append("--dry_run")
    meta = {
        "workspace": str(workspace),
        "runner": str(runner),
        "python": str(py),
        "templates": profile.templates,
        "camera_variants": variants,
        "blocked_reason": blocker,
        "command": cmd,
    }
    return cmd, meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or dry-run staged TDW/Physion-style v2 generation.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--num_trials", type=int, required=True)
    parser.add_argument("--out_root", default=None)
    parser.add_argument("--no_overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute_existing_batch", action="store_true")
    parser.add_argument("--allow_warmup_mild_blocked_execution", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    root = output_root(config, args.out_root)
    root.mkdir(parents=True, exist_ok=True)
    for sub in ["raw_hdf5", "videos", "contact_sheets", "manifests", "lingbot_cam_inputs", "reports", "logs"]:
        (root / sub).mkdir(parents=True, exist_ok=True)
    cmd, meta = build_existing_batch_command(config, args.profile, args.num_trials, root, args.dry_run or not args.execute_existing_batch)
    report = {
        "profile": args.profile,
        "num_trials": args.num_trials,
        "out_root": str(root),
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dry_run": bool(args.dry_run or not args.execute_existing_batch),
        "execute_existing_batch": bool(args.execute_existing_batch),
        "no_overwrite": bool(args.no_overwrite),
        **meta,
    }
    cmd_txt = root / "logs" / f"run_{args.profile}_{args.num_trials}.cmd.txt"
    cmd_txt.write_text(shlex.join(cmd) + "\n", encoding="utf-8")
    _write_json(root / "reports" / f"run_{args.profile}_{args.num_trials}.json", report)

    if meta.get("blocked_reason") and not args.allow_warmup_mild_blocked_execution:
        report.update({"status": "blocked", "returncode": None})
        _write_json(root / "reports" / f"run_{args.profile}_{args.num_trials}.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if args.dry_run or not args.execute_existing_batch:
        report.update({"status": "dry_run_only", "returncode": None})
        _write_json(root / "reports" / f"run_{args.profile}_{args.num_trials}.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    env = os.environ.copy()
    env.setdefault("DISPLAY", str(config.get("display", ":8")))
    log_path = root / "logs" / f"run_{args.profile}_{args.num_trials}.stdout_stderr.log"
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=str(existing_workspace(config)), env=env)
    report.update({"status": "passed" if proc.returncode == 0 else "failed", "returncode": proc.returncode, "log_path": str(log_path)})
    _write_json(root / "reports" / f"run_{args.profile}_{args.num_trials}.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
