from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any

import numpy as np
from cam_physgeo.training.model_loading import check_legacy_lingbot_import, inspect_checkpoint, resolve_model_paths
from cam_physgeo.utils.camera import convert_projection_to_lingbot_intrinsics
from cam_physgeo.utils.io import load_yaml, write_json
from cam_physgeo.eval.make_contact_sheet import make_sheet, read_selected_video_frames

DEFAULT_LINGBOT_ENV = ""


def python_cmd_for_env(env_path: str) -> list[str]:
    """Prefer the env's Python directly so smoke logs stream before timeout."""
    if env_path:
        direct = Path(env_path) / "bin" / "python"
        if direct.exists():
            return [str(direct), "-u"]
        return ["conda", "run", "-p", env_path, "python", "-u"]
    return [sys.executable, "-u"]


def iter_sample_dirs(root: str | Path, limit: int = 0) -> list[Path]:
    root = Path(root)
    if not root.exists():
        return []
    dirs = [p for p in sorted(root.iterdir()) if p.is_dir()]
    return dirs[:limit] if limit else dirs


def parse_resolution(value: str) -> tuple[int, int]:
    raw = str(value).lower().replace("*", "x")
    if "x" not in raw:
        raise ValueError(f"resolution must be HxW or H*W, got {value!r}")
    a, b = raw.split("x", 1)
    return int(a), int(b)


def normalize_frame_count(frame_num: int) -> int:
    """Wan I2V expects 4n+1 frames; round requested counts upward."""
    if frame_num <= 1:
        return 1
    return ((frame_num - 1 + 3) // 4) * 4 + 1


def timestep_indices(num_steps: int) -> list[int]:
    base = [0, 179, 358, 679]
    return base[: max(1, min(int(num_steps), len(base)))]


def _symlink_or_keep(src: Path, dst: Path) -> dict[str, Any]:
    result = {"dst": str(dst), "src": str(src), "exists": dst.exists() or dst.is_symlink(), "created": False, "ok": False, "error": ""}
    try:
        if dst.exists() or dst.is_symlink():
            if dst.is_symlink() and Path(os.readlink(dst)) == src:
                result["ok"] = True
                return result
            result["ok"] = True
            result["note"] = "destination already exists; left unchanged"
            return result
        if not src.exists():
            result["error"] = "source missing"
            return result
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(src, dst)
        result["created"] = True
        result["ok"] = True
    except Exception as exc:  # pragma: no cover - host dependent
        result["error"] = repr(exc)
    return result


def prepare_fast_runtime_bundle(paths: dict[str, str], paths_cfg: dict[str, Any]) -> dict[str, Any]:
    """Create a symlink-only runtime root expected by WanI2VFast."""
    cache_root = Path(paths_cfg.get("CACHE_ROOT") or Path(paths["lingbot_fast"]).parents[2] / "cache")
    runtime = cache_root / "lingbot_fast_cam_runtime"
    base = Path(paths["lingbot_base"])
    fast = Path(paths["lingbot_fast"])
    links = []
    runtime.mkdir(parents=True, exist_ok=True)
    links.append(_symlink_or_keep(base / "Wan2.1_VAE.pth", runtime / "Wan2.1_VAE.pth"))
    links.append(_symlink_or_keep(base / "models_t5_umt5-xxl-enc-bf16.pth", runtime / "models_t5_umt5-xxl-enc-bf16.pth"))
    links.append(_symlink_or_keep(base / "google", runtime / "google"))
    links.append(_symlink_or_keep(fast, runtime / "lingbot_world_fast"))
    ok = runtime.exists() and all(item.get("ok") for item in links)
    return {"runtime_root": str(runtime), "ok": ok, "links": links}


def sample_payload(sample_dir: Path) -> dict[str, Any]:
    meta_path = sample_dir / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    prompt_path = sample_dir / "prompt.txt"
    prompt = prompt_path.read_text(encoding="utf-8", errors="replace").strip() if prompt_path.exists() else "A synthetic physical scene."
    return {
        "sample_id": sample_dir.name,
        "sample_dir": str(sample_dir),
        "image": str(sample_dir / "image.jpg"),
        "target": str(sample_dir / "target.mp4"),
        "poses": str(sample_dir / "poses.npy"),
        "intrinsics": str(sample_dir / "intrinsics.npy"),
        "action": str(sample_dir / "action.npy"),
        "prompt": prompt,
        "metadata": meta,
        "use_action": bool(meta.get("use_action", False)),
        "has_dummy_action": (sample_dir / "action.npy").exists(),
    }


def validate_sample(sample: dict[str, Any]) -> list[str]:
    missing = []
    for key in ["image", "poses", "intrinsics"]:
        if not Path(sample[key]).exists():
            missing.append(key)
    if sample.get("use_action"):
        missing.append("metadata_use_action_true")
    return missing


def _image_size(path: str | Path, fallback_meta: dict[str, Any]) -> tuple[int, int]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except Exception:
        width = int(fallback_meta.get("width") or 832)
        height = int(fallback_meta.get("height") or 480)
        return width, height


def prepare_condition_dir(sample: dict[str, Any], sample_dir: Path, sample_out: Path) -> dict[str, Any]:
    condition_dir = sample_out / "lingbot_condition"
    condition_dir.mkdir(parents=True, exist_ok=True)
    width, height = _image_size(sample["image"], sample.get("metadata", {}))

    poses_src = Path(sample["poses"])
    poses_dst = condition_dir / "poses.npy"
    if not poses_dst.exists():
        try:
            os.symlink(poses_src.resolve(), poses_dst)
        except OSError:
            shutil.copy2(poses_src, poses_dst)

    intrinsics_src = Path(sample["intrinsics"])
    raw_intrinsics = np.load(intrinsics_src)
    intrinsics_vec, intrinsics_meta = convert_projection_to_lingbot_intrinsics(raw_intrinsics, width=width, height=height)
    np.save(condition_dir / "intrinsics.npy", intrinsics_vec.astype(np.float32))

    action_src = Path(sample["action"])
    action_dst = condition_dir / "action.npy"
    dummy_action_created = False
    if action_src.exists() and not action_dst.exists():
        try:
            os.symlink(action_src.resolve(), action_dst)
        except OSError:
            shutil.copy2(action_src, action_dst)
    elif not action_dst.exists():
        poses = np.load(poses_src)
        np.save(action_dst, np.zeros((len(poses), 4), dtype=np.float32))
        dummy_action_created = True

    return {
        "condition_dir": str(condition_dir),
        "poses_runtime_path": str(poses_dst),
        "intrinsics_runtime_path": str(condition_dir / "intrinsics.npy"),
        "action_runtime_path": str(action_dst),
        "intrinsics_source": str(intrinsics_src),
        "intrinsics_source_shape": list(raw_intrinsics.shape),
        "intrinsics_runtime_shape": list(intrinsics_vec.shape),
        "intrinsics_adapter": intrinsics_meta.get("source_format"),
        "intrinsics_conversion": intrinsics_meta,
        "condition_image_size": [width, height],
        "uses_action_as_core_condition": False,
        "dummy_action_created": dummy_action_created,
    }


def _safe_array_summary(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"path": str(path), "exists": False}
    try:
        arr = np.load(path)
        summary: dict[str, Any] = {
            "path": str(path),
            "exists": True,
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
            "finite": bool(np.isfinite(arr).all()) if np.issubdtype(arr.dtype, np.number) else None,
        }
        if np.issubdtype(arr.dtype, np.number):
            summary.update(
                {
                    "norm": float(np.linalg.norm(arr.astype("float64"))),
                    "mean": float(np.mean(arr.astype("float64"))),
                    "std": float(np.std(arr.astype("float64"))),
                    "min": float(np.min(arr.astype("float64"))),
                    "max": float(np.max(arr.astype("float64"))),
                }
            )
        return summary
    except Exception as exc:  # pragma: no cover - host/local data dependent
        return {"path": str(path), "exists": True, "error": repr(exc)}


def build_condition_debug(
    *,
    sample: dict[str, Any],
    condition_info: dict[str, Any],
    pipeline_kwargs_keys: list[str],
    runtime_debug: dict[str, Any] | None = None,
) -> dict[str, Any]:
    poses = _safe_array_summary(condition_info["poses_runtime_path"])
    raw_intrinsics = _safe_array_summary(condition_info["intrinsics_source"])
    runtime_intrinsics = _safe_array_summary(condition_info["intrinsics_runtime_path"])
    action = _safe_array_summary(condition_info["action_runtime_path"])
    runtime_debug = runtime_debug or {}
    signature_keys = runtime_debug.get("generate_signature_keys") or []
    camera_passed = "action_path" in pipeline_kwargs_keys or "action_path" in signature_keys
    dummy_action_norm = action.get("norm") if isinstance(action, dict) else None
    return {
        "sample_id": sample["sample_id"],
        "poses_input_shape": poses.get("shape"),
        "intrinsics_raw_shape": raw_intrinsics.get("shape"),
        "intrinsics_converted_shape": runtime_intrinsics.get("shape"),
        "action_shape": action.get("shape"),
        "use_action": bool(sample.get("use_action", False)),
        "camera_condition_passed_to_pipeline": bool(camera_passed),
        "pipeline_kwargs_keys": pipeline_kwargs_keys,
        "pipeline_generate_signature_keys": signature_keys,
        "plucker_or_camera_embedding_shape": runtime_debug.get("plucker_or_camera_embedding_shape"),
        "plucker_or_camera_embedding_norm": runtime_debug.get("plucker_or_camera_embedding_norm"),
        "camera_embedding_changes_with_variant": runtime_debug.get("camera_embedding_changes_with_variant"),
        "dummy_action_norm": dummy_action_norm,
        "poses_summary": poses,
        "intrinsics_raw_summary": raw_intrinsics,
        "intrinsics_converted_summary": runtime_intrinsics,
        "action_summary": action,
        "condition_info": condition_info,
        "runtime_debug": runtime_debug,
        "notes": (
            "WanI2VFast receives camera files through legacy action_path. "
            "This proves poses/intrinsics are passed to the pipeline call, but a direct "
            "Plucker/camera embedding hook is not exposed here unless runtime_debug reports one."
        ),
    }


def write_runtime_script(path: Path) -> None:
    code = r'''
import argparse
import json
import os
import sys
import time
from pathlib import Path

from PIL import Image


T0 = time.time()


def mark(name, **kwargs):
    payload = {"event": name, "elapsed_sec": round(time.time() - T0, 3)}
    payload.update(kwargs)
    print(json.dumps(payload, sort_keys=True), flush=True)


def main():
    mark("runtime_start")
    ap = argparse.ArgumentParser()
    ap.add_argument("--lingbot_code", required=True)
    ap.add_argument("--ckpt_dir", required=True)
    ap.add_argument("--image", required=True)
    ap.add_argument("--condition_dir", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frame_num", type=int, required=True)
    ap.add_argument("--max_area", type=int, required=True)
    ap.add_argument("--timesteps", default="0")
    ap.add_argument("--seed", type=int, default=123)
    ap.add_argument("--offload_model", action="store_true")
    ap.add_argument("--max_attention_size", type=int, default=0)
    ap.add_argument("--probe_only", action="store_true")
    ap.add_argument("--local_files_only", action="store_true")
    ap.add_argument("--debug_camera_condition", action="store_true")
    ap.add_argument("--condition_debug_out", default="")
    args = ap.parse_args()
    if args.local_files_only:
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    sys.path.insert(0, args.lingbot_code)
    mark("import_torch_start")
    import torch
    import inspect
    import numpy as np
    mark("import_torch_done", cuda_available=bool(torch.cuda.is_available()))
    mark("import_wan_start")
    import wan
    from wan.configs import WAN_CONFIGS
    from wan.utils.utils import save_video
    mark("import_wan_done")

    cfg = WAN_CONFIGS["i2v-A14B"]
    img = Image.open(args.image).convert("RGB")
    mark("load_image_done", image=args.image, size=list(img.size))
    timesteps = [int(x) for x in args.timesteps.split(",") if x.strip()]
    if args.probe_only:
        mark("probe_only_done", note="stopped before WanI2VFast initialization")
        return
    mark("pipeline_init_start", ckpt_dir=args.ckpt_dir)
    pipe = wan.WanI2VFast(
        config=cfg,
        checkpoint_dir=args.ckpt_dir,
        device_id=0,
        rank=0,
        t5_fsdp=False,
        dit_fsdp=False,
        use_sp=False,
        t5_cpu=False,
        convert_model_dtype=False,
    )
    mark("pipeline_init_done")
    runtime_condition_debug = {}
    if args.debug_camera_condition:
        mark("camera_condition_debug_start")
        try:
            signature = inspect.signature(pipe.generate)
            runtime_condition_debug["generate_signature_keys"] = list(signature.parameters.keys())
        except Exception as exc:
            runtime_condition_debug["generate_signature_error"] = repr(exc)
        runtime_condition_debug["condition_dir"] = args.condition_dir
        runtime_condition_debug["condition_files"] = sorted(p.name for p in Path(args.condition_dir).glob("*"))
        runtime_condition_debug["pipeline_kwargs_keys"] = [
            "prompt",
            "img",
            "action_path",
            "chunk_size",
            "max_area",
            "frame_num",
            "timesteps_index",
            "shift",
            "seed",
            "offload_model",
            "max_attention_size",
        ]
        for name in ["poses.npy", "intrinsics.npy", "action.npy"]:
            p = Path(args.condition_dir) / name
            try:
                arr = np.load(p)
                runtime_condition_debug[name] = {
                    "shape": list(arr.shape),
                    "dtype": str(arr.dtype),
                    "norm": float(np.linalg.norm(arr.astype("float64"))) if np.issubdtype(arr.dtype, np.number) else None,
                }
            except Exception as exc:
                runtime_condition_debug[name] = {"error": repr(exc), "path": str(p)}
        if args.condition_debug_out:
            Path(args.condition_debug_out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.condition_debug_out).write_text(json.dumps(runtime_condition_debug, indent=2, sort_keys=True), encoding="utf-8")
        mark("camera_condition_debug_done")
    mark("ready_to_generate")
    mark("generate_start", frame_num=args.frame_num, timesteps=timesteps, max_area=args.max_area)
    video = pipe.generate(
        args.prompt,
        img,
        action_path=args.condition_dir,
        chunk_size=3,
        max_area=args.max_area,
        frame_num=args.frame_num,
        timesteps_index=timesteps,
        shift=cfg.sample_shift,
        seed=args.seed,
        offload_model=args.offload_model,
        max_attention_size=(None if args.max_attention_size <= 0 else args.max_attention_size),
    )
    mark("generate_done")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    save_video(tensor=video[None], save_file=args.out, fps=cfg.sample_fps, nrow=1, normalize=True, value_range=(-1, 1))
    mark("save_done", out=args.out)
    peak = torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0
    print(json.dumps({"ok": True, "out": args.out, "peak_cuda_bytes": int(peak), "frame_num": args.frame_num, "timesteps": timesteps}))


if __name__ == "__main__":
    main()
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")


def run_one_sample(
    *,
    sample_dir: Path,
    out_root: Path,
    paths: dict[str, str],
    runtime_bundle: dict[str, Any],
    num_frames: int,
    num_steps: int,
    resolution: str,
    save_contact_sheet: bool,
    env_path: str,
    timeout_sec: int = 300,
    probe_only: bool = False,
    local_files_only: bool = False,
    debug_camera_condition: bool = False,
    save_condition_tensors: bool = False,
    save_condition_summary: bool = False,
    assert_camera_used: bool = False,
    fail_if_camera_unused: bool = False,
) -> dict[str, Any]:
    run_one_sample.timeout_sec = timeout_sec
    sample = sample_payload(sample_dir)
    missing = validate_sample(sample)
    sample_out = out_root / sample_dir.name
    sample_out.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"sample_id": sample_dir.name, "sample": sample, "missing": missing, "ok": False, "out_dir": str(sample_out)}
    if missing:
        result["error"] = f"sample missing required fields: {missing}"
        write_json(result, sample_out / "inference_metadata.json")
        return result

    h, w = parse_resolution(resolution)
    frame_num = normalize_frame_count(num_frames)
    steps = timestep_indices(num_steps)
    generated = sample_out / "generated.mp4"
    script_path = Path(runtime_bundle["runtime_root"]) / "run_lingbot_fast_once.py"
    write_runtime_script(script_path)
    condition_info = prepare_condition_dir(sample, sample_dir, sample_out)
    pipeline_kwargs_keys = [
        "prompt",
        "img",
        "action_path",
        "chunk_size",
        "max_area",
        "frame_num",
        "timesteps_index",
        "shift",
        "seed",
        "offload_model",
        "max_attention_size",
    ]
    condition_debug_path = sample_out / "condition_debug.json"
    runtime_condition_debug_path = sample_out / "runtime_condition_debug.json"
    initial_condition_debug = build_condition_debug(
        sample=sample,
        condition_info=condition_info,
        pipeline_kwargs_keys=pipeline_kwargs_keys,
    )
    if debug_camera_condition or save_condition_summary:
        write_json(initial_condition_debug, condition_debug_path)
    if save_condition_tensors:
        try:
            np.savez_compressed(
                sample_out / "condition_tensors.npz",
                poses=np.load(condition_info["poses_runtime_path"]),
                intrinsics=np.load(condition_info["intrinsics_runtime_path"]),
                action=np.load(condition_info["action_runtime_path"]),
            )
        except Exception as exc:  # pragma: no cover - host dependent
            initial_condition_debug["condition_tensor_save_error"] = repr(exc)
            write_json(initial_condition_debug, condition_debug_path)
    for name, src in {
        "input_image.jpg": sample["image"],
        "prompt.txt": sample_dir / "prompt.txt",
        "poses.npy": sample["poses"],
        "intrinsics.npy": sample["intrinsics"],
        "metadata.json": sample_dir / "metadata.json",
    }.items():
        dst = sample_out / name
        if not dst.exists() and Path(src).exists():
            try:
                os.symlink(Path(src).resolve(), dst)
            except FileExistsError:
                pass
            except OSError:
                shutil.copy2(src, dst)
    launcher = python_cmd_for_env(env_path)
    cmd = [
        *launcher, str(script_path),
        "--lingbot_code", paths["lingbot_code"],
        "--ckpt_dir", runtime_bundle["runtime_root"],
        "--image", sample["image"],
        "--condition_dir", condition_info["condition_dir"],
        "--prompt", sample["prompt"],
        "--out", str(generated),
        "--frame_num", str(frame_num),
        "--max_area", str(h * w),
        "--timesteps", ",".join(str(x) for x in steps),
        "--seed", "123",
        "--offload_model",
    ]
    if probe_only:
        cmd.append("--probe_only")
    if local_files_only:
        cmd.append("--local_files_only")
    if debug_camera_condition or save_condition_summary:
        cmd.extend(["--debug_camera_condition", "--condition_debug_out", str(runtime_condition_debug_path)])
    log_path = sample_out / "inference_log.txt"
    start = time.time()
    proc_env = os.environ.copy()
    proc_env["PYTHONUNBUFFERED"] = "1"
    if local_files_only:
        proc_env.setdefault("TRANSFORMERS_OFFLINE", "1")
        proc_env.setdefault("HF_HUB_OFFLINE", "1")
        proc_env.setdefault("HF_DATASETS_OFFLINE", "1")
    proc_env.setdefault("TOKENIZERS_PARALLELISM", "false")
    with log_path.open("w", encoding="utf-8", errors="replace") as log_f:
        proc = subprocess.Popen(cmd, text=True, stdout=log_f, stderr=subprocess.STDOUT, env=proc_env)
        try:
            proc.wait(timeout=run_one_sample.timeout_sec)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            log_f.write(f"\n[TIMEOUT] killed after {run_one_sample.timeout_sec} seconds\n")
    elapsed = time.time() - start
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    runtime_condition_debug = {}
    if runtime_condition_debug_path.exists():
        try:
            runtime_condition_debug = json.loads(runtime_condition_debug_path.read_text(encoding="utf-8"))
        except Exception as exc:
            runtime_condition_debug = {"read_error": repr(exc), "path": str(runtime_condition_debug_path)}
    final_condition_debug = build_condition_debug(
        sample=sample,
        condition_info=condition_info,
        pipeline_kwargs_keys=pipeline_kwargs_keys,
        runtime_debug=runtime_condition_debug,
    )
    if debug_camera_condition or save_condition_summary:
        write_json(final_condition_debug, condition_debug_path)
    camera_used = bool(final_condition_debug.get("camera_condition_passed_to_pipeline"))
    if assert_camera_used and not camera_used:
        result["camera_condition_assertion_error"] = "poses/intrinsics were prepared but action_path was not visible in pipeline call/signature"
    if fail_if_camera_unused and not camera_used:
        proc_returncode = proc.returncode if proc is not None else 2
        result.update(
            {
                "returncode": proc_returncode,
                "ok": False,
                "error": result.get("camera_condition_assertion_error") or "camera condition was not passed to the pipeline",
                "condition_debug": final_condition_debug,
            }
        )
        write_json(result, sample_out / "inference_metadata.json")
        return result
    result.update({
        "cmd": cmd,
        "python_launcher": launcher,
        "returncode": proc.returncode,
        "elapsed_sec": elapsed,
        "timeout_sec": run_one_sample.timeout_sec,
        "log_tail": log_text[-4000:],
        "generated": str(generated),
        "condition_info": condition_info,
        "normalized_frame_num": frame_num,
        "requested_num_frames": num_frames,
        "num_steps": num_steps,
        "timesteps_index": steps,
        "resolution": resolution,
        "max_area": h * w,
        "uses_action_as_core_condition": False,
        "action_policy": "sample_dir passed only because WanI2VFast expects poses/intrinsics under action_path; cam mode ignores action.npy",
        "probe_only": probe_only,
        "local_files_only": local_files_only,
        "debug_camera_condition": debug_camera_condition,
        "condition_debug": final_condition_debug if (debug_camera_condition or save_condition_summary) else None,
        "camera_condition_passed_to_pipeline": camera_used,
    })
    if proc.returncode == 0 and generated.exists():
        result["ok"] = True
        if save_contact_sheet:
            contact = sample_out / "contact_sheet.jpg"
            try:
                frames = read_selected_video_frames(generated, [0, 1, 2, 3, 4, 5, 6, 7, 8])
                make_sheet({"sample_id": sample_dir.name, "template": sample.get("metadata", {}).get("template"), "camera_motion": sample.get("metadata", {}).get("camera_motion")}, frames, contact)
                result["contact_sheet"] = str(contact)
            except Exception as exc:  # pragma: no cover
                result["contact_sheet_error"] = repr(exc)
    else:
        result["error"] = log_text[-4000:]
    write_json(result, sample_out / "inference_metadata.json")
    return result


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
    ap.add_argument("--resolution", default="480x832")
    ap.add_argument("--save_contact_sheet", action="store_true")
    ap.add_argument("--lingbot_env", default=os.environ.get("LINGBOT_FAST_ENV", DEFAULT_LINGBOT_ENV))
    ap.add_argument("--timeout", "--timeout_sec", dest="timeout_sec", type=int, default=300)
    ap.add_argument("--probe-only", action="store_true")
    ap.add_argument("--skip-t5-if-cached", action="store_true")
    ap.add_argument("--text-embedding-cache", default="")
    ap.add_argument("--local-files-only", action="store_true")
    ap.add_argument("--debug-camera-condition", action="store_true")
    ap.add_argument("--save-condition-tensors", action="store_true")
    ap.add_argument("--save-condition-summary", action="store_true")
    ap.add_argument("--assert-camera-used", action="store_true")
    ap.add_argument("--fail-if-camera-unused", action="store_true")
    args = ap.parse_args(argv)
    cfg = load_yaml(args.config) if args.config else {}
    paths_cfg = load_yaml("configs/cam_physgeo/paths.yaml")
    paths = resolve_model_paths(paths_cfg)
    if not args.lingbot_env:
        args.lingbot_env = str(paths_cfg.get("LINGBOT_ENV") or "")
    model_path = paths["lingbot_fast" if args.model_type == "fast" else "lingbot_base"]
    checkpoint = inspect_checkpoint(model_path, label=f"lingbot_{args.model_type}")
    import_check = check_legacy_lingbot_import(paths["lingbot_code"])
    runtime_bundle = prepare_fast_runtime_bundle(paths, paths_cfg) if args.model_type == "fast" else {"runtime_root": model_path, "ok": checkpoint.recognized_by_legacy_loader, "links": []}
    samples_root = args.samples or cfg.get("samples") or cfg.get("input_root") or ""
    sample_dirs = iter_sample_dirs(samples_root, args.limit) if samples_root else []
    sample_checks = []
    for sample_dir in sample_dirs:
        s = sample_payload(sample_dir)
        sample_checks.append({
            "sample_id": s["sample_id"],
            "missing": validate_sample(s),
            "prompt": s["prompt"],
            "camera_motion": s.get("metadata", {}).get("camera_motion"),
            "use_action": s["use_action"],
            "has_dummy_action": s["has_dummy_action"],
        })
    payload = {
        "out": args.out,
        "model_type": args.model_type,
        "model_path": model_path,
        "checkpoint": checkpoint.to_dict(),
        "lingbot_code": paths["lingbot_code"],
        "legacy_import": import_check,
        "runtime_bundle": runtime_bundle,
        "samples_root": samples_root,
        "sample_count": len(sample_dirs),
        "sample_dirs": [str(p) for p in sample_dirs],
        "sample_checks": sample_checks,
        "control_type": "camera_conditioned",
        "image_condition": "image.jpg",
        "prompt_condition": "prompt.txt",
        "camera_condition": {"poses": "poses.npy", "intrinsics": "intrinsics.npy", "passed_via_legacy_action_path": True},
        "use_action": False,
        "dummy_action_policy": "action.npy is ignored in cam mode and kept only for legacy compatibility",
        "num_frames_requested": args.num_frames,
        "num_frames_normalized": normalize_frame_count(args.num_frames),
        "num_steps": args.num_steps,
        "timesteps_index": timestep_indices(args.num_steps),
        "resolution": args.resolution,
        "lingbot_env": args.lingbot_env,
        "python_launcher": python_cmd_for_env(args.lingbot_env),
        "probe_only": args.probe_only,
        "local_files_only": args.local_files_only,
        "debug_camera_condition": args.debug_camera_condition,
        "save_condition_tensors": args.save_condition_tensors,
        "save_condition_summary": args.save_condition_summary,
        "assert_camera_used": args.assert_camera_used,
        "fail_if_camera_unused": args.fail_if_camera_unused,
        "text_embedding_cache": args.text_embedding_cache,
        "skip_t5_if_cached": args.skip_t5_if_cached,
        "cached_text_embedding_supported": False,
        "cached_text_embedding_note": "WanI2VFast constructs its T5 encoder in __init__; skipping T5 requires a LingBot runtime patch and is intentionally not faked.",
        "dry_run": args.dry_run,
        "smoke_run": args.smoke_run,
    }
    if args.dry_run or not args.smoke_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.skip_t5_if_cached or args.text_embedding_cache:
        payload["error"] = "cached text embedding is not wired into WanI2VFast; refusing to fake T5 bypass"
        Path(args.out).mkdir(parents=True, exist_ok=True)
        write_json(payload, Path(args.out) / "run_summary.json")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2
    out_root = Path(args.out)
    results = []
    for sample_dir in sample_dirs:
        results.append(run_one_sample(
            sample_dir=sample_dir,
            out_root=out_root,
            paths=paths,
            runtime_bundle=runtime_bundle,
            num_frames=args.num_frames,
            num_steps=args.num_steps,
            resolution=args.resolution,
            save_contact_sheet=args.save_contact_sheet,
            env_path=args.lingbot_env,
            timeout_sec=args.timeout_sec,
            probe_only=args.probe_only,
            local_files_only=args.local_files_only,
            debug_camera_condition=args.debug_camera_condition,
            save_condition_tensors=args.save_condition_tensors,
            save_condition_summary=args.save_condition_summary,
            assert_camera_used=args.assert_camera_used,
            fail_if_camera_unused=args.fail_if_camera_unused,
        ))
    payload["results"] = results
    payload["ok_count"] = sum(1 for r in results if r.get("ok"))
    payload["fail_count"] = sum(1 for r in results if not r.get("ok"))
    Path(args.out).mkdir(parents=True, exist_ok=True)
    write_json(payload, Path(args.out) / "run_summary.json")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["fail_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
