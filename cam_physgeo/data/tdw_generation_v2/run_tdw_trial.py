from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from pathlib import Path

from .generation_config import (
    allowed_gpu_indices,
    existing_workspace,
    get_profile,
    load_config,
    output_root,
    tdw_display_gpu_index,
    upstream_camera_mapping,
    validate_profile_camera_set,
)


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_mild_batch_wrapper(wrapper_path: Path, batch_runner: Path, variants: list[dict]) -> None:
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    wrapper_path.write_text(
        "from __future__ import annotations\n"
        "import importlib.util\n"
        "import sys\n"
        f"BATCH_RUNNER = {str(batch_runner)!r}\n"
        f"MILD_CAMERA_VARIANTS = {json.dumps(variants, ensure_ascii=False, indent=2)}\n"
        "spec = importlib.util.spec_from_file_location('tdw_mild_batch_runner', BATCH_RUNNER)\n"
        "if spec is None or spec.loader is None:\n"
        "    raise RuntimeError(f'Cannot import upstream batch runner: {BATCH_RUNNER}')\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(module)\n"
        "module.CAMERA_VARIANTS = MILD_CAMERA_VARIANTS\n"
        "argv = [sys.argv[0]] + sys.argv[1:]\n"
        "for i, arg in enumerate(argv):\n"
        "    if arg == '--camera_set' and i + 1 < len(argv):\n"
        "        argv[i + 1] = 'all'\n"
        "if '--camera_set' not in argv:\n"
        "    argv += ['--camera_set', 'all']\n"
        "sys.argv = argv\n"
        "module.main()\n",
        encoding="utf-8",
    )


def _upstream_importable_main(runner: Path) -> bool:
    try:
        return runner.exists() and "def main(" in runner.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False


def build_existing_batch_command(config: dict, profile_name: str, num_trials: int, out_root: Path, dry_run: bool) -> tuple[list[str], dict]:
    profile = get_profile(config, profile_name)
    validate_profile_camera_set(config, profile)
    workspace = existing_workspace(config)
    runner = workspace / "scripts" / "batch_generate_physion_dpo_conditions.py"
    mild_variants = upstream_camera_mapping(config, profile)
    wrapper = out_root / "logs" / f"upstream_batch_{profile_name}_mild_wrapper.py"
    _write_mild_batch_wrapper(wrapper, runner, mild_variants)
    py = workspace / ".conda_envs" / "tdw-physion" / "bin" / "python3"
    if not py.exists():
        py = workspace / ".conda_envs" / "tdw-physion" / "bin" / "python"
    templates = ",".join(profile.templates)
    variants = [v.get("name") for v in profile.camera_variants]
    blocker = None
    upstream_main = _upstream_importable_main(runner)
    if not upstream_main:
        blocker = "upstream batch runner cannot be imported with a callable main(); wrapper execution is blocked."
    display_gpu = tdw_display_gpu_index(config)
    allowed = allowed_gpu_indices(config)
    if not dry_run and display_gpu is not None and display_gpu not in allowed:
        blocker = (
            f"TDW display is configured on GPU {display_gpu}, but this task only allows "
            f"GPU indices {allowed}. Actual Unity generation is blocked until a GPU 6/7 "
            "display or user approval is available."
        )
    cmd = [
        str(py), str(wrapper),
        "--workspace", str(workspace),
        "--output_root", str(out_root / "raw_hdf5" / f"{profile_name}_{num_trials}samples"),
        "--display", str(config.get("display", ":8")),
        "--templates", templates,
        "--width", str(config.get("resolution", {}).get("width", 832)),
        "--height", str(config.get("resolution", {}).get("height", 480)),
        "--max_frames", str(config.get("frames", {}).get("max_frames", 81)),
        "--min_frames", str(config.get("frames", {}).get("min_frames", 81)),
        "--aligned_frames", str(config.get("frames", {}).get("aligned_frames", 81)),
        "--num_seeds", str(max(1, num_trials)),
        "--limit", str(num_trials),
        "--camera_set", "all",
    ]
    if dry_run:
        cmd.append("--dry_run")
    meta = {
        "workspace": str(workspace),
        "runner": str(runner),
        "wrapper": str(wrapper),
        "python": str(py),
        "templates": profile.templates,
        "camera_variants": variants,
        "upstream_camera_variants": mild_variants,
        "upstream_runner_has_main": upstream_main,
        "tdw_display": str(config.get("display", ":8")),
        "tdw_display_gpu_index": display_gpu,
        "allowed_gpu_indices": allowed,
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
