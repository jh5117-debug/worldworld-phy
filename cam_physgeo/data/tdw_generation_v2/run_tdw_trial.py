from __future__ import annotations

import argparse
import json
import os
import re
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
        "import json\n"
        "import sys\n"
        f"BATCH_RUNNER = {str(batch_runner)!r}\n"
        f"MILD_CAMERA_VARIANTS = json.loads({json.dumps(variants, ensure_ascii=False)!r})\n"
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


def _load_plan(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        raise ValueError(f"Plan is empty: {path}")
    return rows


def _trial_dir_name(index: int, trial: dict) -> str:
    template = str(trial.get("template") or "unknown")
    variant = str(trial.get("camera_variant") or "unknown")
    seed = int(trial.get("seed", index))
    return f"{index:05d}_{template}_{variant}_seed{seed}"


def _plan_output_subdir(profile_name: str, plan_path: Path, num_trials: int) -> str:
    stem = plan_path.stem
    if "template_diverse" in stem:
        return f"{profile_name}_template_diverse_{num_trials}samples"
    return f"{profile_name}_plan_{num_trials}samples"


def _template_specific_args(template: str) -> list[str]:
    if template == "drop":
        return [
            "--random", "0",
            "--num_distractors", "0",
            "--num_occluders", "0",
            "--room", "box",
            "--target", "cube,sphere",
            "--tscale", "[0.25,0.65]",
            "--drop", "cube,sphere",
            "--ymin", "1.1",
            "--ymax", "1.8",
            "--dscale", "[0.15,0.45]",
        ]
    if template == "collision":
        return [
            "--tcolor", "None",
            "--zcolor", "None",
            "--only_use_flex_objects",
            "--collision_axis_length", "2",
            "--frot", "[-8,8]",
            "--fscale", "[5.0,11.0]",
            "--fupforce", "[0.0,0.0]",
            "--target", "pyramid,cone,dumbbell,triangular_prism,torus",
            "--pmass", "4",
            "--monochrome", "1",
            "--random", "0",
            "--seed", "328",
            "--no_moving_distractors",
            "--room", "box",
        ]
    if template == "roll":
        return [
            "--tcolor", "None",
            "--zcolor", "None",
            "--only_use_flex_objects",
            "--collision_axis_length", "1.7",
            "--probe", "bowl,cone,cube,cylinder,dumbbell,pentagon,pipe,pyramid",
            "--target", "bowl,cone,cube,cylinder,dumbbell,pentagon,pipe,pyramid,sphere",
            "--prot", "[-180,180]",
            "--tlift", "0.25",
            "--fscale", "[2.,9.]",
            "--frot", "[-3,3]",
            "--camera_distance", "[2.3,2.5]",
            "--monochrome", "1",
            "--random", "0",
            "--seed", "914",
            "--no_moving_distractors",
            "--room", "box",
        ]
    if template == "containment":
        return [
            "--no_moving_distractors",
            "--fwait", "15",
            "--random", "0",
            "--seed", "1",
            "--only_use_flex_objects",
            "--tcolor=None",
            "--zcolor=None",
            "--middle=sphere",
            "--mscale=0.2,0.4",
            "--num_middle_range=1,4",
            "--spacing_jitter=0.3",
            "--attachment=None",
            "--ascale=0",
            "--base=bowl",
            "--bscale=0.5,1.1",
            "--bmass=2,3",
            "--bcolor=None",
            "--fscale=4,9",
            "--num_distractors", "1",
            "--distractor", "full",
            "--distractor_categories",
            "coffee_table,houseplant,vase,chair,dog,sofa,flowerpot,coffee_maker,stool,laptop,laptop_computer,globe,bookshelf,desktop_computer,garden_plant",
            "--occluder", "full",
            "--occluder_categories",
            "coffee_table,houseplant,vase,chair,dog,sofa,flowerpot,coffee_maker,stool,laptop,laptop_computer,globe,bookshelf,desktop_computer,garden_plant",
            "--num_occluders", "1",
        ]
    raise ValueError(f"Unsupported template: {template}")


def _single_trial_command(config: dict, root: Path, output_subdir: str, trial: dict, index: int) -> list[str]:
    workspace = existing_workspace(config)
    py = workspace / ".conda_envs" / "tdw-physion" / "bin" / "python3"
    if not py.exists():
        py = workspace / ".conda_envs" / "tdw-physion" / "bin" / "python"
    runner = workspace / "scripts" / "tdw_physion_multi_template_moving_camera.py"
    upstream = dict(trial.get("upstream_camera_variant") or {})
    motion = str(upstream.get("motion") or trial.get("camera_motion") or "orbit")
    template = str(trial.get("template"))
    seed = int(trial.get("seed", 10000))
    out_dir = (root / "raw_hdf5" / output_subdir / _trial_dir_name(index, trial)).resolve()
    cmd = [
        str(py), str(runner),
        "--template", template,
        "--port", str(1700 + index),
        "--gpu", "None",
        "--local_asset_dir", str(workspace / "assets" / "tdw_asset_bundles"),
        "--dir", str(out_dir),
        "--num", "1",
        "--width", str(config.get("resolution", {}).get("width", 832)),
        "--height", str(config.get("resolution", {}).get("height", 480)),
        "--framerate", str(config.get("framerate", 16)),
        "--seed", str(seed),
        "--max_frames", str(config.get("frames", {}).get("max_frames", 81)),
        "--camera_motion", motion,
        "--camera_motion_start", "24",
        "--camera_motion_end", "57",
        "--camera_orbit_degrees", str(float(upstream.get("orbit", 0.0))),
        "--camera_height_delta", str(float(upstream.get("height", 0.0))),
        "--camera_radius_delta", str(float(upstream.get("radius", 0.0))),
        "--camera_strafe_distance", str(float(upstream.get("strafe", 0.0))),
        "--camera_lookaway_yaw_degrees", "0.0",
        "--camera_lookaway_pitch_degrees", "0.0",
        "--camera_aim_offset_x", "0.0",
        "--camera_aim_offset_y", "0.0",
        "--camera_aim_offset_z", "0.0",
        "--write_passes", "_img,_id,_depth",
        "--run", "1",
        *_template_specific_args(template),
    ]
    return cmd


def _parse_gpu_ids(raw: str | None, fallback: list[int]) -> list[int]:
    if raw is None or raw == "":
        return fallback
    out = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part:
            out.append(int(part))
    return out


def _display_socket_exists(display: str) -> bool:
    match = re.match(r"^:?(\d+)", display.strip())
    if not match:
        return False
    return Path("/tmp/.X11-unix") .joinpath(f"X{match.group(1)}").exists()


def _detect_display_gpu_from_ps(display: str) -> dict:
    result = {
        "display": display,
        "x_socket_exists": _display_socket_exists(display),
        "xorg_process_found": False,
        "xorg_process": None,
        "xorg_config": None,
        "gpu_index": None,
        "source": "not_detected",
    }
    try:
        proc = subprocess.run(["ps", "-ef"], check=False, text=True, capture_output=True)
    except Exception as exc:
        result.update({"source": "ps_error", "error": repr(exc)})
        return result
    for line in proc.stdout.splitlines():
        if "Xorg" not in line and "Xvfb" not in line:
            continue
        if f" {display} " not in f" {line} ":
            continue
        result.update({"xorg_process_found": True, "xorg_process": line, "source": "process"})
        parts = shlex.split(line)
        if "-config" in parts:
            idx = parts.index("-config")
            if idx + 1 < len(parts):
                cfg = Path(parts[idx + 1])
                result["xorg_config"] = str(cfg)
                text = ""
                try:
                    text = cfg.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    text = ""
                hay = f"{cfg.name}\n{text}".lower()
                match = re.search(r"gpu\s*([0-9]+)", hay)
                if match:
                    result.update({"gpu_index": int(match.group(1)), "source": "xorg_config"})
        break
    return result


def detect_display_gpu(config: dict, display: str) -> dict:
    display = display or str(config.get("display", ":8"))
    display_map = config.get("display_gpu_map", {})
    detected = _detect_display_gpu_from_ps(display)
    if display in display_map:
        detected.update({
            "gpu_index": int(display_map[display]),
            "source": f"config_display_gpu_map+{detected.get('source')}",
        })
    elif display == str(config.get("tdw_display", {}).get("display", "")):
        gpu = tdw_display_gpu_index(config)
        if gpu is not None:
            detected.update({"gpu_index": gpu, "source": f"config_tdw_display+{detected.get('source')}"})
    return detected


def build_existing_batch_command(
    config: dict,
    profile_name: str,
    num_trials: int,
    out_root: Path,
    dry_run: bool,
    *,
    display: str | None = None,
    allowed_gpu_ids: list[int] | None = None,
    require_allowed_gpu_display: bool = True,
    no_run_if_display_gpu_mismatch: bool = True,
    allow_unapproved_gpu: bool = False,
    gpu_confirmation_token: str | None = None,
    validate_display: bool = False,
) -> tuple[list[str], dict]:
    profile = get_profile(config, profile_name)
    validate_profile_camera_set(config, profile)
    out_root = out_root.resolve()
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
    display = display or str(config.get("display", ":8"))
    upstream_main = _upstream_importable_main(runner)
    if not upstream_main:
        blocker = "upstream batch runner cannot be imported with a callable main(); wrapper execution is blocked."
    allowed = allowed_gpu_ids or allowed_gpu_indices(config)
    display_detection = detect_display_gpu(config, display)
    display_gpu = display_detection.get("gpu_index")
    display_unknown = display_gpu is None
    display_mismatch = display_gpu not in allowed if display_gpu is not None else True
    confirmation_ok = allow_unapproved_gpu and gpu_confirmation_token == "USER_CONFIRMED_UNAPPROVED_GPU"
    must_validate_display = validate_display or not dry_run
    if must_validate_display and require_allowed_gpu_display and display_unknown:
        blocker = (
            f"TDW display {display} GPU could not be detected. Actual Unity generation is blocked "
            f"until the display is proven to use allowed GPU indices {allowed}."
        )
    if (
        must_validate_display
        and no_run_if_display_gpu_mismatch
        and display_mismatch
        and not confirmation_ok
    ):
        blocker = (
            f"TDW display {display} is configured/detected on GPU {display_gpu}, but this task only "
            f"allows GPU indices {allowed}. Actual Unity generation is blocked until a GPU 6/7 "
            "display or explicit user confirmation is available."
        )
    cmd = [
        str(py), str(wrapper),
        "--workspace", str(workspace),
        "--output_root", str(out_root / "raw_hdf5" / f"{profile_name}_{num_trials}samples"),
        "--display", display,
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
        "tdw_display": display,
        "tdw_display_gpu_index": display_gpu,
        "display_detection": display_detection,
        "allowed_gpu_indices": allowed,
        "require_allowed_gpu_display": require_allowed_gpu_display,
        "no_run_if_display_gpu_mismatch": no_run_if_display_gpu_mismatch,
        "allow_unapproved_gpu": allow_unapproved_gpu,
        "gpu_confirmation_token_ok": confirmation_ok,
        "blocked_reason": blocker,
        "command": cmd,
    }
    return cmd, meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or dry-run staged TDW/Physion-style v2 generation.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--num_trials", type=int, required=True)
    parser.add_argument("--plan", type=Path, default=None)
    parser.add_argument("--out_root", default=None)
    parser.add_argument("--no_overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dry-run-display-check", action="store_true")
    parser.add_argument("--execute_existing_batch", action="store_true")
    parser.add_argument("--display", default=None)
    parser.add_argument("--allowed_gpu_ids", default=None)
    parser.add_argument("--require_allowed_gpu_display", action="store_true", default=True)
    parser.add_argument("--no_run_if_display_gpu_mismatch", action="store_true", default=True)
    parser.add_argument("--allow_unapproved_gpu", action="store_true")
    parser.add_argument("--gpu_confirmation_token", default=None)
    parser.add_argument("--allow_warmup_mild_blocked_execution", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    root = output_root(config, args.out_root)
    root.mkdir(parents=True, exist_ok=True)
    for sub in ["raw_hdf5", "videos", "contact_sheets", "manifests", "lingbot_cam_inputs", "reports", "logs"]:
        (root / sub).mkdir(parents=True, exist_ok=True)
    allowed = _parse_gpu_ids(args.allowed_gpu_ids, allowed_gpu_indices(config))
    display_check_only = bool(args.dry_run_display_check)
    plan_rows = _load_plan(args.plan) if args.plan else None
    effective_num_trials = len(plan_rows) if plan_rows is not None else args.num_trials
    cmd, meta = build_existing_batch_command(
        config,
        args.profile,
        effective_num_trials,
        root,
        args.dry_run or not args.execute_existing_batch or display_check_only,
        display=args.display,
        allowed_gpu_ids=allowed,
        require_allowed_gpu_display=args.require_allowed_gpu_display,
        no_run_if_display_gpu_mismatch=args.no_run_if_display_gpu_mismatch,
        allow_unapproved_gpu=args.allow_unapproved_gpu,
        gpu_confirmation_token=args.gpu_confirmation_token,
        validate_display=display_check_only,
    )
    report = {
        "profile": args.profile,
        "num_trials": effective_num_trials,
        "out_root": str(root),
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dry_run": bool(args.dry_run or not args.execute_existing_batch),
        "execute_existing_batch": bool(args.execute_existing_batch),
        "dry_run_display_check": display_check_only,
        "plan": str(args.plan) if args.plan else None,
        "no_overwrite": bool(args.no_overwrite),
        **meta,
    }
    report_name = f"run_{args.profile}_{'plan_' if args.plan else ''}{effective_num_trials}"
    cmd_txt = root / "logs" / f"{report_name}.cmd.txt"
    if plan_rows is not None:
        output_subdir = _plan_output_subdir(args.profile, args.plan, effective_num_trials)
        plan_commands = [_single_trial_command(config, root, output_subdir, row, idx) for idx, row in enumerate(plan_rows)]
        batch_blocker = meta.get("blocked_reason")
        if isinstance(batch_blocker, str) and "upstream batch runner" in batch_blocker:
            meta["batch_runner_blocked_reason_ignored_for_plan"] = batch_blocker
            meta["blocked_reason"] = None
            report["blocked_reason"] = None
            report["batch_runner_blocked_reason_ignored_for_plan"] = batch_blocker
        report.update({
            "execution_mode": "plan_per_trial",
            "plan_output_subdir": output_subdir,
            "plan_templates": [row.get("template") for row in plan_rows],
            "plan_camera_variants": [row.get("camera_variant") for row in plan_rows],
            "plan_commands": plan_commands,
        })
        cmd_txt.write_text("\n".join(shlex.join(c) for c in plan_commands) + "\n", encoding="utf-8")
    else:
        plan_commands = None
        output_subdir = None
        cmd_txt.write_text(shlex.join(cmd) + "\n", encoding="utf-8")
    _write_json(root / "reports" / f"{report_name}.json", report)

    if meta.get("blocked_reason") and not args.allow_warmup_mild_blocked_execution:
        report.update({"status": "blocked", "returncode": None})
        _write_json(root / "reports" / f"{report_name}.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if args.dry_run or not args.execute_existing_batch or display_check_only:
        status = "display_check_passed" if display_check_only and not meta.get("blocked_reason") else "dry_run_only"
        if display_check_only and meta.get("blocked_reason"):
            status = "display_check_blocked"
        report.update({"status": status, "returncode": None})
        _write_json(root / "reports" / f"{report_name}.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    env = os.environ.copy()
    env.setdefault("DISPLAY", meta.get("tdw_display", str(config.get("display", ":8"))))
    if plan_rows is not None and plan_commands is not None and output_subdir is not None:
        trial_results = []
        for idx, (trial, trial_cmd) in enumerate(zip(plan_rows, plan_commands)):
            out_dir = root / "raw_hdf5" / output_subdir / _trial_dir_name(idx, trial)
            final_hdf5 = out_dir / "0000.hdf5"
            temp_hdf5 = out_dir / "temp.hdf5"
            log_path = root / "logs" / f"{report_name}_trial_{idx:05d}.stdout_stderr.log"
            out_dir.mkdir(parents=True, exist_ok=True)
            if args.no_overwrite and final_hdf5.exists():
                trial_results.append({
                    "index": idx,
                    "template": trial.get("template"),
                    "camera_variant": trial.get("camera_variant"),
                    "seed": trial.get("seed"),
                    "status": "skipped_existing",
                    "returncode": 0,
                    "hdf5": str(final_hdf5),
                    "log_path": str(log_path),
                })
                continue
            if temp_hdf5.exists() and not final_hdf5.exists():
                temp_hdf5.unlink(missing_ok=True)
            with log_path.open("w", encoding="utf-8") as log:
                proc = subprocess.run(trial_cmd, stdout=log, stderr=subprocess.STDOUT, cwd=str(existing_workspace(config)), env=env)
            trial_results.append({
                "index": idx,
                "template": trial.get("template"),
                "camera_variant": trial.get("camera_variant"),
                "seed": trial.get("seed"),
                "status": "passed" if proc.returncode == 0 else "failed",
                "returncode": proc.returncode,
                "hdf5": str(final_hdf5) if final_hdf5.exists() else str(temp_hdf5) if temp_hdf5.exists() else None,
                "log_path": str(log_path),
                "command": trial_cmd,
            })
            if proc.returncode != 0:
                continue
        failed = [row for row in trial_results if row.get("returncode") not in (0, None)]
        report.update({
            "status": "passed" if not failed else "failed",
            "returncode": 0 if not failed else 1,
            "trial_results": trial_results,
            "failed_count": len(failed),
        })
    else:
        log_path = root / "logs" / f"{report_name}.stdout_stderr.log"
        with log_path.open("w", encoding="utf-8") as log:
            proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=str(existing_workspace(config)), env=env)
        report.update({"status": "passed" if proc.returncode == 0 else "failed", "returncode": proc.returncode, "log_path": str(log_path)})
    _write_json(root / "reports" / f"{report_name}.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
