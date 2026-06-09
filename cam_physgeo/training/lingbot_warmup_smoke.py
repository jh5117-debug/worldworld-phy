from __future__ import annotations

import argparse
import gc
import json
import os
import random
import subprocess
import time
from pathlib import Path
from typing import Any


def _bool_arg(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in {"1", "true", "yes", "y", "on"}


def _gpu_snapshot() -> list[dict[str, Any]]:
    cmd = [
        "nvidia-smi",
        "--query-gpu=index,pci.bus_id,memory.used,memory.total,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        out = subprocess.check_output(cmd, text=True, timeout=30)
    except Exception as exc:
        return [{"error": repr(exc)}]
    rows = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 5:
            rows.append(
                {
                    "index": int(parts[0]),
                    "pci_bus_id": parts[1],
                    "memory_used_mib": int(parts[2]),
                    "memory_total_mib": int(parts[3]),
                    "utilization_gpu_pct": int(parts[4]),
                }
            )
    return rows


def _write_report(out_dir: Path, name: str, payload: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    lines = [
        f"# LingBot warmup {name.replace('_', ' ')}",
        "",
        f"Status: {payload.get('status')}",
        "",
        f"Reason: {payload.get('reason', '')}",
        "",
        "Safety:",
        f"- no_backward: {payload.get('safety', {}).get('no_backward')}",
        f"- no_optimizer: {payload.get('safety', {}).get('no_optimizer')}",
        f"- no_checkpoint: {payload.get('safety', {}).get('no_checkpoint')}",
    ]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _torch_dtype(name: str):
    from cam_physgeo.dpo.lingbot_fast_videogpa_adapter import _torch_dtype as adapter_dtype

    return adapter_dtype(name)


def _torch_device(name: str):
    from cam_physgeo.dpo.lingbot_fast_videogpa_adapter import _torch_device as adapter_device

    return adapter_device(name)


def _tensor_summary(tensor: Any) -> dict[str, Any]:
    from cam_physgeo.dpo.lingbot_fast_videogpa_adapter import _tensor_summary as adapter_tensor_summary

    return adapter_tensor_summary(tensor)


def _safe_item(value: Any) -> Any:
    try:
        if hasattr(value, "detach"):
            value = value.detach()
        if hasattr(value, "cpu"):
            value = value.cpu()
        if hasattr(value, "item"):
            return value.item()
    except Exception:
        pass
    return value


def _component_inspection(pipe: Any, adapter: Any) -> dict[str, Any]:
    from cam_physgeo.training.model_loading import inspect_checkpoint

    model = getattr(pipe, "model", None)
    scheduler = getattr(pipe, "scheduler", None)
    fast_info = inspect_checkpoint(adapter.paths["lingbot_fast"], label="lingbot_fast").to_dict()
    base_info = inspect_checkpoint(adapter.paths["lingbot_base"], label="lingbot_base").to_dict()
    attrs = {}
    for name in [
        "num_train_timesteps",
        "sample_steps",
        "control_type",
        "patch_size",
        "text_len",
        "sp_size",
        "pipe_dtype",
        "param_dtype",
        "device",
    ]:
        try:
            value = getattr(pipe, name, None)
            attrs[name] = str(value) if value is not None else None
        except Exception as exc:
            attrs[name] = f"error:{exc!r}"
    model_attrs = {}
    for name in [
        "high_noise_model",
        "low_noise_model",
        "expert",
        "experts",
        "router",
        "timestep_boundary",
        "time_embedding",
        "enable_physics_adapter",
    ]:
        try:
            value = getattr(model, name, None)
            model_attrs[name] = type(value).__name__ if value is not None else None
        except Exception as exc:
            model_attrs[name] = f"error:{exc!r}"
    explicit_fast_route = any(model_attrs.get(k) for k in ["high_noise_model", "low_noise_model", "expert", "experts", "router"])
    return {
        "pipe_attrs": attrs,
        "model_attrs": model_attrs,
        "scheduler_class": type(scheduler).__name__ if scheduler is not None else None,
        "fast_checkpoint": fast_info,
        "base_checkpoint": base_info,
        "expert_route": "exposed" if explicit_fast_route else "unavailable_in_fast_or_not_exposed",
        "moe_layout_in_base_checkpoint": bool(base_info.get("has_high_noise_model") and base_info.get("has_low_noise_model")),
        "fast_checkpoint_has_explicit_moe_branches": bool(fast_info.get("has_high_noise_model") and fast_info.get("has_low_noise_model")),
        "notes": [
            "LingBot Base checkpoint layout contains high_noise_model/low_noise_model when detected.",
            "LingBot-Fast runtime may be distilled/sharded and may not expose explicit expert routing on the pipe.model object.",
        ],
    }


def _load_tokenizer(runtime_paths: dict[str, str], *, local_files_only: bool) -> dict[str, Any]:
    tokenizer_root = Path(str(runtime_paths.get("tokenizer_root") or ""))
    result: dict[str, Any] = {
        "tokenizer_root": str(tokenizer_root),
        "exists": tokenizer_root.exists(),
        "loaded": False,
        "deferred": False,
    }
    if not tokenizer_root.exists():
        result["error"] = "tokenizer_root_missing"
        return result
    try:
        from transformers import AutoTokenizer  # type: ignore

        tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_root), local_files_only=local_files_only)
        result.update({"loaded": True, "class": type(tokenizer).__name__, "vocab_size": getattr(tokenizer, "vocab_size", None)})
    except Exception as exc:
        result.update({"loaded": False, "deferred": True, "error": repr(exc), "reason": "Wan runtime may still load tokenizer/T5 internally."})
    return result


def _sample_to_pair(row: dict[str, Any]) -> dict[str, Any]:
    prompt_path = Path(str(row.get("prompt_path") or Path(row.get("sample_dir", "")) / "prompt.txt"))
    prompt = prompt_path.read_text(encoding="utf-8", errors="replace").strip() if prompt_path.exists() else ""
    condition = {
        "image": row.get("image_path") or str(Path(row["sample_dir"]) / "image.jpg"),
        "prompt": str(prompt_path),
        "poses": row.get("poses_path") or str(Path(row["sample_dir"]) / "poses.npy"),
        "intrinsics": row.get("intrinsics_path") or str(Path(row["sample_dir"]) / "intrinsics.npy"),
        "action": row.get("action_path") or str(Path(row["sample_dir"]) / "action.npy"),
        "metadata": row.get("metadata_path") or str(Path(row["sample_dir"]) / "metadata.json"),
        "use_action": False,
    }
    return {
        "pair_id": row.get("sample_id") or Path(str(row.get("sample_dir"))).name,
        "pair_type": "single_sample_warmup_forward_smoke",
        "prompt": prompt or "A synthetic physical scene.",
        "condition": condition,
        "winner": {"video": row.get("target_video_path")},
        "loser": {"video": row.get("target_video_path")},
        "metadata": {
            "sample_id": row.get("sample_id"),
            "template": row.get("template"),
            "camera_variant": row.get("camera_variant"),
            "use_action": False,
            "human_approved": row.get("human_approved"),
        },
    }


def _load_video_latent(video_path: str | Path, *, vae: Any, num_frames: int, resolution: str, dtype: str, device: str) -> tuple[Any, dict[str, Any]]:
    from cam_physgeo.dpo.lingbot_fast_videogpa_adapter import _call_vae_encode, _video_tensor

    import torch  # type: ignore

    device_obj = _torch_device(device)
    dtype_obj = _torch_dtype(dtype)
    start = time.time()
    tensor = _video_tensor(video_path, num_frames=num_frames, resolution=resolution, dtype=dtype_obj, device=device_obj)
    with torch.no_grad():
        latent, pattern = _call_vae_encode(vae, tensor)
    if not hasattr(latent, "detach"):
        raise RuntimeError(f"VAE encode returned unsupported type: {type(latent)!r}")
    latent = latent.detach().to(device=device_obj, dtype=dtype_obj)
    if latent.ndim == 5 and int(latent.shape[0]) == 1:
        latent = latent[0]
    if latent.ndim != 4:
        raise RuntimeError(f"expected latent shape C,F,H,W after VAE encode, got {list(latent.shape)}")
    return latent, {
        "video_path": str(video_path),
        "input_tensor": _tensor_summary(tensor),
        "latent": _tensor_summary(latent),
        "vae_encode_pattern": pattern,
        "elapsed_sec": time.time() - start,
    }


def _choose_timestep(mode: str, *, num_train_timesteps: int, high_noise_timestep: int | None, low_noise_timestep: int | None) -> list[tuple[str, int, str]]:
    max_t = max(int(num_train_timesteps) - 1, 1)
    high = max(0, min(max_t, int(high_noise_timestep) if high_noise_timestep is not None else int(round(max_t * 0.80))))
    low = max(0, min(max_t, int(low_noise_timestep) if low_noise_timestep is not None else int(round(max_t * 0.20))))
    random_t = random.randint(0, max_t)
    if mode == "high_noise":
        return [("diagnostic_high_noise_quantile", high, "scheduler_0.80_quantile_or_user_value")]
    if mode == "low_noise":
        return [("diagnostic_low_noise_quantile", low, "scheduler_0.20_quantile_or_user_value")]
    if mode == "mixed":
        return [
            ("diagnostic_high_noise_quantile", high, "scheduler_0.80_quantile_or_user_value"),
            ("random", random_t, "random_uniform_timestep"),
        ]
    if mode == "both":
        return [
            ("diagnostic_high_noise_quantile", high, "scheduler_0.80_quantile_or_user_value"),
            ("diagnostic_low_noise_quantile", low, "scheduler_0.20_quantile_or_user_value"),
            ("random", random_t, "random_uniform_timestep"),
        ]
    return [("random", random_t, "random_uniform_timestep")]


def _cleanup_cuda() -> None:
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    gc.collect()


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _module_trainable_summary(model: Any) -> dict[str, Any]:
    total = 0
    trainable = 0
    base_trainable = 0
    lora_trainable = 0
    for name, param in model.named_parameters():
        n = int(param.numel())
        total += n
        if param.requires_grad:
            trainable += n
            if "lora_" in name:
                lora_trainable += n
            else:
                base_trainable += n
    return {
        "param_count": total,
        "trainable_param_count": trainable,
        "lora_trainable_param_count": lora_trainable,
        "base_trainable_param_count": base_trainable,
    }


def _grad_status(params: list[Any]) -> dict[str, Any]:
    import torch  # type: ignore

    with_grad = 0
    nonzero_grad = 0
    any_nan = False
    any_inf = False
    for param in params:
        if param.grad is None:
            continue
        with_grad += 1
        grad = param.grad.detach().float()
        if grad.numel() and bool((grad.abs() > 0).any().item()):
            nonzero_grad += 1
        if grad.numel():
            any_nan = any_nan or bool(torch.isnan(grad).any().item())
            any_inf = any_inf or bool(torch.isinf(grad).any().item())
    return {
        "params_with_grad": with_grad,
        "params_with_nonzero_grad": nonzero_grad,
        "any_nan_grad": any_nan,
        "any_inf_grad": any_inf,
    }


def _total_grad_norm(params: list[Any]) -> float:
    import torch  # type: ignore

    total = torch.zeros((), dtype=torch.float32)
    for param in params:
        if param.grad is None:
            continue
        total = total + param.grad.detach().float().pow(2).sum().cpu()
    return float(torch.sqrt(total).item())


def _base_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "mode": args.mode,
        "status": "blocked",
        "reason": "",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "gpu_snapshot_before": _gpu_snapshot(),
        "config": args.config,
        "model_type": args.model_type,
        "device": args.device,
        "dtype": args.dtype,
        "local_files_only": _bool_arg(args.local_files_only),
        "safety": {
            "no_training": True,
            "no_backward": _bool_arg(args.no_backward),
            "no_optimizer": _bool_arg(args.no_optimizer),
            "no_checkpoint": _bool_arg(args.no_checkpoint),
            "no_lora_save": True,
        },
    }


def component_load_smoke(args: argparse.Namespace) -> int:
    from cam_physgeo.dpo.lingbot_fast_videogpa_adapter import LingBotFastVideoGPAAdapter

    payload = _base_payload(args)
    out_dir = Path(args.out)
    name = "component_load_smoke_report"
    if args.model_type != "fast":
        payload.update({"status": "failed", "reason": "only model_type=fast is supported for this smoke"})
        _write_report(out_dir, name, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2
    try:
        start = time.time()
        adapter = LingBotFastVideoGPAAdapter(args.config)
        payload["paths"] = {
            "lingbot_fast": adapter.paths.get("lingbot_fast"),
            "lingbot_base": adapter.paths.get("lingbot_base"),
            "lingbot_code": adapter.paths.get("lingbot_code"),
            "runtime_paths": adapter.runtime_paths,
        }
        payload["tokenizer"] = _load_tokenizer(adapter.runtime_paths, local_files_only=_bool_arg(args.local_files_only))
        policy = adapter.load_policy_model(device=args.device, dtype=args.dtype, dry_run=False)
        pipe = policy.pop("object")
        vae_result = adapter.load_vae(device=args.device, dtype=args.dtype, dry_run=False)
        vae = vae_result.pop("object", None)
        if not vae_result.get("success") or vae is None:
            raise RuntimeError(f"VAE load failed: {vae_result}")
        if getattr(pipe, "vae", None) is None:
            setattr(pipe, "vae", vae)
        inspection = _component_inspection(pipe, adapter)
        payload.update(
            {
                "status": "passed_true_component_load",
                "reason": "Loaded LingBot-Fast policy pipe and Wan/LingBot VAE without optimizer, backward, checkpoint, or LoRA save.",
                "policy": policy,
                "vae": vae_result,
                "component_inspection": inspection,
                "camera_condition_helper": {
                    "status": "deferred_to_forward_condition_build",
                    "reason": "component load smoke has no sample manifest; true forward-loss smoke builds Plucker/control from poses/intrinsics.",
                },
                "elapsed_sec": time.time() - start,
                "gpu_snapshot_after": _gpu_snapshot(),
            }
        )
        del pipe, vae
        _cleanup_cuda()
        payload["gpu_snapshot_after_cleanup"] = _gpu_snapshot()
        _write_report(out_dir, name, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        _cleanup_cuda()
        payload.update(
            {
                "status": "failed_true_component_load",
                "reason": repr(exc),
                "gpu_snapshot_after": _gpu_snapshot(),
            }
        )
        _write_report(out_dir, name, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2


def true_forward_loss_dryrun(args: argparse.Namespace) -> int:
    from cam_physgeo.dpo.lingbot_fast_videogpa_adapter import LingBotFastVideoGPAAdapter

    import torch  # type: ignore

    payload = _base_payload(args)
    out_dir = Path(args.out)
    name = "true_forward_loss_dryrun_report"
    if _bool_arg(args.require_real_model_load) is False:
        payload.update({"status": "failed_not_real_model_load", "reason": "--require_real_model_load must be true for this gate"})
        _write_report(out_dir, name, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2
    if not _bool_arg(args.no_backward) or not _bool_arg(args.no_optimizer) or not _bool_arg(args.no_checkpoint):
        payload.update({"status": "failed_safety_flags", "reason": "true forward smoke requires no_backward/no_optimizer/no_checkpoint"})
        _write_report(out_dir, name, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2
    try:
        start = time.time()
        rows = _load_jsonl(args.train_manifest)
        if not rows:
            raise RuntimeError(f"empty train manifest: {args.train_manifest}")
        row = rows[0]
        pair = _sample_to_pair(row)
        metadata = _read_json(pair["condition"]["metadata"])
        action_norm = None
        try:
            import numpy as np

            action = np.load(pair["condition"]["action"])
            action_norm = float(np.linalg.norm(action.astype("float32")))
        except Exception as exc:
            action_norm = f"error:{exc!r}"
        adapter = LingBotFastVideoGPAAdapter(args.config)
        policy = adapter.load_policy_model(device=args.device, dtype=args.dtype, dry_run=False)
        pipe = policy.pop("object")
        vae_result = adapter.load_vae(device=args.device, dtype=args.dtype, dry_run=False)
        vae = vae_result.pop("object", None)
        if not vae_result.get("success") or vae is None:
            raise RuntimeError(f"VAE load failed: {vae_result}")
        setattr(pipe, "vae", vae)
        component = _component_inspection(pipe, adapter)
        latent, latent_info = _load_video_latent(
            row["target_video_path"],
            vae=vae,
            num_frames=args.num_frames,
            resolution=args.resolution,
            dtype=args.dtype,
            device=args.device,
        )
        forward_condition = adapter._build_forward_condition(
            pair=pair,
            pipe=pipe,
            latent_shape=list(latent.shape),
            out_dir=out_dir / "condition",
            num_frames=args.num_frames,
            resolution=args.resolution,
            device=args.device,
            dtype=args.dtype,
        )
        device_obj = _torch_device(args.device)
        num_train_timesteps = int(getattr(pipe, "num_train_timesteps", 1000) or 1000)
        bands = _choose_timestep(
            args.timestep_mode,
            num_train_timesteps=num_train_timesteps,
            high_noise_timestep=args.high_noise_timestep,
            low_noise_timestep=args.low_noise_timestep,
        )
        band_results = []
        for band_name, timestep_value, band_source in bands:
            band_start = time.time()
            noise = torch.randn_like(latent)
            timestep = torch.full((1,), int(timestep_value), device=device_obj, dtype=torch.long)
            with torch.no_grad():
                pred, target, target_info = adapter._model_forward_once(
                    pipe=pipe,
                    x0=latent,
                    noise=noise,
                    timestep=timestep,
                    forward_condition=forward_condition,
                    enable_grad=False,
                )
                loss = torch.nn.functional.mse_loss(pred.float(), target.float())
            sigma = target_info.get("sigma")
            band_results.append(
                {
                    "band": band_name,
                    "band_source": band_source,
                    "timestep": int(timestep_value),
                    "num_train_timesteps": num_train_timesteps,
                    "sigma": sigma,
                    "target_type": target_info.get("target_type"),
                    "target_info": target_info,
                    "noise": _tensor_summary(noise),
                    "pred": _tensor_summary(pred),
                    "target": _tensor_summary(target),
                    "loss_value": float(loss.detach().cpu().item()),
                    "loss_finite": bool(torch.isfinite(loss.detach()).cpu().item()),
                    "elapsed_sec": time.time() - band_start,
                    "expert_route": component.get("expert_route", "unavailable_in_fast_or_not_exposed"),
                }
            )
            del noise, timestep, pred, target, loss
            _cleanup_cuda()
        passed = bool(band_results) and all(bool(r.get("loss_finite")) for r in band_results)
        payload.update(
            {
                "status": "passed_true_forward_loss" if passed else "failed_nonfinite_forward_loss",
                "reason": "Real LingBot-Fast policy/VAE/camera-condition forward MSE computed without backward/optimizer/checkpoint."
                if passed
                else "At least one real forward-loss band was non-finite.",
                "train_manifest": args.train_manifest,
                "sample": {
                    "sample_id": row.get("sample_id"),
                    "template": row.get("template"),
                    "camera_variant": row.get("camera_variant"),
                    "target_video_path": row.get("target_video_path"),
                    "image_path": row.get("image_path"),
                    "poses_path": row.get("poses_path"),
                    "intrinsics_path": row.get("intrinsics_path"),
                    "metadata_use_action": metadata.get("use_action"),
                    "dummy_action_norm": action_norm,
                },
                "policy": policy,
                "vae": vae_result,
                "component_inspection": component,
                "latent": latent_info,
                "forward_condition": forward_condition["summary"],
                "timestep_mode": args.timestep_mode,
                "band_results": band_results,
                "real_model_load_confirmed": True,
                "no_backward_confirmed": True,
                "no_optimizer_confirmed": True,
                "no_checkpoint_confirmed": True,
                "elapsed_sec": time.time() - start,
                "gpu_snapshot_after": _gpu_snapshot(),
            }
        )
        del pipe, vae, latent
        _cleanup_cuda()
        payload["gpu_snapshot_after_cleanup"] = _gpu_snapshot()
        _write_report(out_dir, name, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if passed else 2
    except Exception as exc:
        _cleanup_cuda()
        payload.update({"status": "failed_true_forward_loss", "reason": repr(exc), "gpu_snapshot_after": _gpu_snapshot()})
        _write_report(out_dir, name, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2


def staged_warmup_pilot(args: argparse.Namespace) -> int:
    from cam_physgeo.dpo.lingbot_fast_videogpa_adapter import LingBotFastVideoGPAAdapter
    from cam_physgeo.dpo.lora_utils import count_lora_parameters, freeze_non_lora_parameters, inject_lora_into_modules, list_lora_parameters

    import torch  # type: ignore

    payload = _base_payload(args)
    out_dir = Path(args.out)
    name = "stageA_warmup_pilot_summary"
    metrics_dir = out_dir / "metrics"
    train_metrics_path = metrics_dir / "train_metrics.jsonl"
    val_metrics_path = metrics_dir / "val_metrics.jsonl"
    summary_path = out_dir / "reports" / "stageA_summary.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    for path in [train_metrics_path, val_metrics_path]:
        if path.exists():
            path.unlink()
    if not _bool_arg(args.require_real_model_load):
        payload.update({"status": "failed_not_real_model_load", "reason": "--require_real_model_load must be true"})
        _write_report(out_dir, name, payload)
        return 2
    safety_flags = {
        "no_dpo": _bool_arg(args.no_dpo),
        "no_rollout": _bool_arg(args.no_rollout),
        "no_reward_calibration": _bool_arg(args.no_reward_calibration),
        "no_checkpoint": _bool_arg(args.no_checkpoint),
        "no_optimizer_state_save": _bool_arg(args.no_optimizer_state_save),
        "save_metrics_only": _bool_arg(args.save_metrics_only),
    }
    if not all(safety_flags.values()):
        payload.update({"status": "failed_safety_flags", "reason": f"Stage A requires all safety flags true: {safety_flags}"})
        _write_report(out_dir, name, payload)
        return 2
    if int(args.max_steps) > 100:
        payload.update({"status": "failed_max_steps", "reason": "Stage A pilot is capped at max_steps <= 100"})
        _write_report(out_dir, name, payload)
        return 2
    if int(args.batch_size) != 1:
        payload.update({"status": "failed_batch_size", "reason": "Stage A pilot requires batch_size=1"})
        _write_report(out_dir, name, payload)
        return 2
    if str(args.trainable_scope) != "camera_control_lora_tiny":
        payload.update({"status": "failed_trainable_scope", "reason": "Only camera_control_lora_tiny is enabled for this no-checkpoint pilot"})
        _write_report(out_dir, name, payload)
        return 2
    try:
        start = time.time()
        train_rows = _load_jsonl(args.train_manifest)
        val_rows = _load_jsonl(args.val_manifest) if args.val_manifest else []
        if not train_rows:
            raise RuntimeError("empty train manifest")
        if not val_rows:
            raise RuntimeError("empty val manifest")
        adapter = LingBotFastVideoGPAAdapter(args.config)
        policy = adapter.load_policy_model(device=args.device, dtype=args.dtype, dry_run=False)
        pipe = policy.pop("object")
        vae_result = adapter.load_vae(device=args.device, dtype=args.dtype, dry_run=False)
        vae = vae_result.pop("object", None)
        if not vae_result.get("success") or vae is None:
            raise RuntimeError(f"VAE load failed: {vae_result}")
        setattr(pipe, "vae", vae)
        model = getattr(pipe, "model", None)
        if model is None:
            raise RuntimeError("policy pipeline has no .model")
        model.eval()
        resolved = adapter._resolve_lora_targets(
            model,
            target_modules=args.target_modules,
            lora_scope=args.trainable_scope,
            rank=int(args.lora_rank),
            max_lora_params=int(args.max_trainable_params),
        )
        injections = inject_lora_into_modules(model, resolved["target_modules"], rank=int(args.lora_rank), alpha=float(args.lora_alpha))
        freeze_non_lora_parameters(model)
        trainable = adapter._select_trainable_params(model, scope=args.trainable_scope, max_trainable_params=int(args.max_trainable_params))
        if trainable["trainable_param_count"] <= 0:
            raise RuntimeError(f"no trainable LoRA parameters selected for scope={args.trainable_scope}")
        param_map = dict(model.named_parameters())
        optimizer_params = [param_map[name] for name in trainable["selected_names"] if name in param_map]
        if len(optimizer_params) != len(trainable["selected_names"]):
            raise RuntimeError("optimizer param name mismatch after LoRA injection")
        if not all("lora_" in name for name in trainable["selected_names"]):
            raise RuntimeError(f"non-LoRA parameters selected: {trainable['selected_names']}")
        base_names = adapter._sample_base_param_names(model, preferred_targets=resolved["target_modules"], limit=12)
        base_before = adapter._snapshot_param_samples(model, base_names)
        lora_before = adapter._snapshot_selected_params(model, trainable["selected_names"])
        optimizer = torch.optim.AdamW(optimizer_params, lr=float(args.learning_rate))
        num_train_timesteps = int(getattr(pipe, "num_train_timesteps", 1000) or 1000)
        component = _component_inspection(pipe, adapter)
        summary: dict[str, Any] = {
            "status": "running",
            "mode": "staged_warmup_pilot",
            "stage": "A_high_noise_global_camera",
            "train_manifest": args.train_manifest,
            "val_manifest": args.val_manifest,
            "max_steps": int(args.max_steps),
            "val_every": int(args.val_every),
            "batch_size": int(args.batch_size),
            "num_frames": int(args.num_frames),
            "resolution": args.resolution,
            "timestep_mode": args.timestep_mode,
            "trainable_scope_requested": args.trainable_scope,
            "learning_rate": float(args.learning_rate),
            "max_grad_norm": float(args.max_grad_norm),
            "policy": policy,
            "vae": vae_result,
            "component_inspection": component,
            "lora": {
                "target_modules": resolved["target_modules"],
                "target_selection": resolved.get("target_selection"),
                "rank": int(args.lora_rank),
                "alpha": float(args.lora_alpha),
                "injections": [inj.__dict__ for inj in injections],
                "lora_param_count": count_lora_parameters(model),
                "lora_params": list_lora_parameters(model)[:50],
            },
            "trainable_scope": trainable,
            "module_trainable_summary": _module_trainable_summary(model),
            "optimizer_param_groups": {
                "group_count": len(optimizer.param_groups),
                "param_count": len(optimizer_params),
                "optimizer_class": type(optimizer).__name__,
                "learning_rate": float(optimizer.param_groups[0]["lr"]),
                "contains_only_lora": True,
            },
            "safety_flags": safety_flags,
            "no_checkpoint_saved": True,
            "no_lora_saved": True,
            "no_optimizer_state_saved": True,
            "no_rollout": True,
            "no_dpo": True,
            "train_metrics_path": str(train_metrics_path),
            "val_metrics_path": str(val_metrics_path),
        }
        train_losses: list[float] = []
        grad_norms: list[float] = []
        sigmas: list[float] = []
        val_losses: list[float] = []
        steps_completed = 0
        stop_reason = None
        val_every = max(1, int(args.val_every))

        def compute_sample_loss(row: dict[str, Any], *, step: int, enable_grad: bool, split: str):
            pair = _sample_to_pair(row)
            latent, latent_info = _load_video_latent(
                row["target_video_path"],
                vae=vae,
                num_frames=int(args.num_frames),
                resolution=args.resolution,
                dtype=args.dtype,
                device=args.device,
            )
            cond_dir = out_dir / ("train_logs" if split == "train" else "val_logs") / f"{split}_step_{step:05d}"
            forward_condition = adapter._build_forward_condition(
                pair=pair,
                pipe=pipe,
                latent_shape=list(latent.shape),
                out_dir=cond_dir,
                num_frames=int(args.num_frames),
                resolution=args.resolution,
                device=args.device,
                dtype=args.dtype,
            )
            band = _choose_timestep(
                args.timestep_mode,
                num_train_timesteps=num_train_timesteps,
                high_noise_timestep=args.high_noise_timestep,
                low_noise_timestep=args.low_noise_timestep,
            )[0]
            band_name, timestep_value, band_source = band
            noise = torch.randn_like(latent)
            timestep = torch.full((1,), int(timestep_value), device=_torch_device(args.device), dtype=torch.long)
            pred, target, target_info = adapter._model_forward_once(
                pipe=pipe,
                x0=latent,
                noise=noise,
                timestep=timestep,
                forward_condition=forward_condition,
                enable_grad=enable_grad,
            )
            loss = torch.nn.functional.mse_loss(pred.float(), target.float())
            sigma = float((target_info.get("sigma") or [float(timestep_value) / float(num_train_timesteps)])[0])
            metric = {
                "step": int(step),
                "split": split,
                "sample_id": row.get("sample_id"),
                "template": row.get("template"),
                "camera_variant": row.get("camera_variant"),
                "band": band_name,
                "band_source": band_source,
                "timestep": int(timestep_value),
                "sigma": sigma,
                "loss": float(loss.detach().cpu().item()),
                "loss_finite": bool(torch.isfinite(loss.detach()).cpu().item()),
                "latent_shape": list(latent.shape),
                "control_shape": (forward_condition.get("summary") or {}).get("control_summary", {}).get("shape"),
                "dummy_action_norm": (forward_condition.get("summary") or {}).get("dummy_action_norm"),
                "use_action": False,
            }
            del latent, noise, timestep, pred, target, forward_condition
            return loss, metric

        for step in range(1, int(args.max_steps) + 1):
            step_start = time.time()
            row = train_rows[(step - 1) % len(train_rows)]
            optimizer.zero_grad(set_to_none=True)
            loss, metric = compute_sample_loss(row, step=step, enable_grad=True, split="train")
            if not torch.isfinite(loss.detach()):
                stop_reason = f"non_finite_train_loss_step_{step}"
                metric["stop_reason"] = stop_reason
                _append_jsonl(train_metrics_path, metric)
                break
            loss.backward()
            grad_before = _total_grad_norm(optimizer_params)
            clip_returned_norm = None
            if float(args.max_grad_norm) > 0:
                clip_returned_norm = float(torch.nn.utils.clip_grad_norm_(optimizer_params, float(args.max_grad_norm)).item())
            grad_after = _total_grad_norm(optimizer_params)
            grad_state = _grad_status(optimizer_params)
            if grad_state["any_nan_grad"] or grad_state["any_inf_grad"]:
                stop_reason = f"non_finite_grad_step_{step}"
                metric["stop_reason"] = stop_reason
                _append_jsonl(train_metrics_path, metric)
                break
            optimizer.step()
            steps_completed = step
            loss_value = float(metric["loss"])
            train_losses.append(loss_value)
            grad_norms.append(float(grad_after))
            sigmas.append(float(metric["sigma"]))
            metric.update(
                {
                    "grad_norm_before_clip": float(grad_before),
                    "clip_returned_norm": clip_returned_norm,
                    "grad_norm_after_clip": float(grad_after),
                    "params_with_grad": grad_state["params_with_grad"],
                    "params_with_nonzero_grad": grad_state["params_with_nonzero_grad"],
                    "elapsed_sec": time.time() - step_start,
                }
            )
            _append_jsonl(train_metrics_path, metric)
            del loss
            optimizer.zero_grad(set_to_none=True)
            _cleanup_cuda()
            if step % val_every == 0 or step == int(args.max_steps):
                with torch.no_grad():
                    val_row = val_rows[(step // val_every - 1) % len(val_rows)]
                    val_loss, val_metric = compute_sample_loss(val_row, step=step, enable_grad=False, split="val")
                    val_metric["elapsed_sec"] = time.time() - step_start
                    _append_jsonl(val_metrics_path, val_metric)
                    val_losses.append(float(val_metric["loss"]))
                    if not bool(val_metric["loss_finite"]):
                        stop_reason = f"non_finite_val_loss_step_{step}"
                        break
                    del val_loss
                _cleanup_cuda()
        lora_after = adapter._diff_full_snapshot(model, lora_before)
        base_after = adapter._diff_param_samples(model, base_before)
        success = bool(
            steps_completed >= 20
            and train_losses
            and all(torch.isfinite(torch.tensor(train_losses)).tolist())
            and (not val_losses or all(torch.isfinite(torch.tensor(val_losses)).tolist()))
            and max(grad_norms or [0.0]) > 0.0
            and lora_after.get("params_changed_count", 0) > 0
            and base_after.get("params_changed_count", 0) == 0
            and stop_reason is None
        )
        summary.update(
            {
                "status": "passed_stageA_warmup_pilot" if success else "failed_stageA_warmup_pilot",
                "success": success,
                "stop_reason": stop_reason,
                "steps_completed": int(steps_completed),
                "train_loss_first": train_losses[0] if train_losses else None,
                "train_loss_last": train_losses[-1] if train_losses else None,
                "train_loss_min": min(train_losses) if train_losses else None,
                "train_loss_max": max(train_losses) if train_losses else None,
                "val_losses": val_losses,
                "grad_norm_first": grad_norms[0] if grad_norms else None,
                "grad_norm_last": grad_norms[-1] if grad_norms else None,
                "grad_norm_max": max(grad_norms) if grad_norms else None,
                "sigma_min": min(sigmas) if sigmas else None,
                "sigma_max": max(sigmas) if sigmas else None,
                "sigma_mean": sum(sigmas) / len(sigmas) if sigmas else None,
                "lora_diff_after": lora_after,
                "base_diff_after": base_after,
                "frozen_params_unchanged": base_after.get("params_changed_count", 0) == 0,
                "trainable_params_received_gradients": max(grad_norms or [0.0]) > 0.0,
                "elapsed_sec": time.time() - start,
                "gpu_snapshot_after": _gpu_snapshot(),
            }
        )
        optimizer.zero_grad(set_to_none=True)
        del optimizer, pipe, vae, model
        _cleanup_cuda()
        summary["gpu_snapshot_after_cleanup"] = _gpu_snapshot()
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_report(out_dir, name, summary)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0 if success else 2
    except RuntimeError as exc:
        _cleanup_cuda()
        is_oom = "out of memory" in repr(exc).lower() or "cuda" in repr(exc).lower() and "memory" in repr(exc).lower()
        payload.update(
            {
                "status": "failed_oom" if is_oom else "failed_stageA_warmup_pilot",
                "reason": repr(exc),
                "oom": bool(is_oom),
                "gpu_snapshot_after": _gpu_snapshot(),
            }
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_report(out_dir, name, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2
    except Exception as exc:
        _cleanup_cuda()
        payload.update({"status": "failed_stageA_warmup_pilot", "reason": repr(exc), "gpu_snapshot_after": _gpu_snapshot()})
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_report(out_dir, name, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2


def placeholder_forward_loss_dryrun(args: argparse.Namespace) -> int:
    payload = _base_payload(args)
    payload.update(
        {
            "status": "failed_not_real_model_load" if _bool_arg(args.require_real_model_load) else "passed_placeholder_no_model_load",
            "reason": "Legacy placeholder tensor path. This is not valid for the true warmup forward-loss gate.",
        }
    )
    out_dir = Path(args.out)
    _write_report(out_dir, "forward_loss_dryrun_report", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 2 if _bool_arg(args.require_real_model_load) else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="forward_loss_dryrun", choices=["forward_loss_dryrun", "component_load_smoke", "true_forward_loss_dryrun", "staged_warmup_pilot"])
    parser.add_argument("--model_type", default="fast")
    parser.add_argument("--config", required=True)
    parser.add_argument("--train_manifest", default="")
    parser.add_argument("--val_manifest", default="")
    parser.add_argument("--out", required=True)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--num_batches", type=int, default=1)
    parser.add_argument("--max_steps", type=int, default=1)
    parser.add_argument("--val_every", type=int, default=25)
    parser.add_argument("--num_frames", type=int, default=8)
    parser.add_argument("--resolution", default="480x832")
    parser.add_argument("--dtype", default="bf16")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--use_action", default="false")
    parser.add_argument("--timestep_mode", default="random", choices=["random", "high_noise", "low_noise", "mixed", "both"])
    parser.add_argument("--num_timestep_bands", type=int, default=3)
    parser.add_argument("--high_noise_timestep", type=int, default=None)
    parser.add_argument("--low_noise_timestep", type=int, default=None)
    parser.add_argument("--log_expert_route", default="false")
    parser.add_argument("--require_real_model_load", default="false")
    parser.add_argument("--trainable_scope", default="camera_control_lora_tiny")
    parser.add_argument("--learning_rate", type=float, default=1e-5)
    parser.add_argument("--max_grad_norm", type=float, default=1.0)
    parser.add_argument("--lora_rank", type=int, default=2)
    parser.add_argument("--lora_alpha", type=float, default=4.0)
    parser.add_argument("--target_modules", default="auto")
    parser.add_argument("--max_trainable_params", type=int, default=1_000_000)
    parser.add_argument("--no_dpo", default="true")
    parser.add_argument("--no_rollout", default="true")
    parser.add_argument("--no_reward_calibration", default="true")
    parser.add_argument("--no_backward", default="true")
    parser.add_argument("--no_optimizer", default="true")
    parser.add_argument("--no_checkpoint", default="true")
    parser.add_argument("--no_optimizer_state_save", default="true")
    parser.add_argument("--save_metrics_only", default="true")
    parser.add_argument("--local_files_only", default="true")
    parser.add_argument("--timeout", type=int, default=0)
    args = parser.parse_args()

    if args.device == "cuda" and not os.environ.get("CUDA_VISIBLE_DEVICES"):
        payload = _base_payload(args)
        payload.update({"status": "blocked", "reason": "CUDA_VISIBLE_DEVICES is not set; refuse to run GPU smoke without explicit GPU restriction."})
        _write_report(Path(args.out), "warmup_smoke_blocked_report", payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2
    if args.mode == "component_load_smoke":
        return component_load_smoke(args)
    if args.mode == "true_forward_loss_dryrun":
        if not args.train_manifest:
            payload = _base_payload(args)
            payload.update({"status": "blocked", "reason": "--train_manifest is required for true_forward_loss_dryrun"})
            _write_report(Path(args.out), "true_forward_loss_dryrun_report", payload)
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 2
        return true_forward_loss_dryrun(args)
    if args.mode == "staged_warmup_pilot":
        if not args.train_manifest or not args.val_manifest:
            payload = _base_payload(args)
            payload.update({"status": "blocked", "reason": "--train_manifest and --val_manifest are required for staged_warmup_pilot"})
            _write_report(Path(args.out), "stageA_warmup_pilot_summary", payload)
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 2
        return staged_warmup_pilot(args)
    return placeholder_forward_loss_dryrun(args)


if __name__ == "__main__":
    raise SystemExit(main())
