from __future__ import annotations

import argparse
import contextlib
import importlib
import inspect
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from cam_physgeo.eval.probe_camera_embedding import _build_embedding, _load_cam_utils
from cam_physgeo.dpo.lora_utils import (
    LoRALinear,
    count_lora_parameters,
    freeze_non_lora_parameters,
    inject_lora_into_modules,
    list_lora_parameters,
)
from cam_physgeo.training.model_loading import inspect_checkpoint, resolve_model_paths, resolve_t5_runtime_paths
from cam_physgeo.utils.camera import convert_projection_to_lingbot_intrinsics
from cam_physgeo.utils.io import load_yaml, write_json
from cam_physgeo.utils.video import read_video_frames


@dataclass
class AdapterStatus:
    name: str
    implemented: bool
    dependency: str
    input_shape: str
    output_shape: str
    supports_camera_poses: bool
    supports_intrinsics: bool
    uses_dummy_action: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _bool_arg(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in {"1", "true", "yes", "y", "on"}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_energy_summary(path: str | Path, default_name: str) -> dict[str, Any]:
    p = Path(path)
    if p.is_dir():
        p = p / default_name
    payload = _read_json(p)
    if not payload:
        raise FileNotFoundError(str(p))
    return payload


def _torch_dtype(name: str):
    import torch  # type: ignore

    table = {"bf16": torch.bfloat16, "bfloat16": torch.bfloat16, "fp16": torch.float16, "float16": torch.float16, "fp32": torch.float32, "float32": torch.float32}
    return table.get(str(name).lower(), torch.float32)


def _torch_device(name: str):
    import torch  # type: ignore

    if str(name).startswith("cuda") and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _gpu_memory() -> dict[str, Any]:
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            return {
                "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                "allocated_bytes": int(torch.cuda.memory_allocated()),
                "reserved_bytes": int(torch.cuda.memory_reserved()),
                "max_allocated_bytes": int(torch.cuda.max_memory_allocated()),
            }
    except Exception as exc:
        return {"error": repr(exc)}
    return {"cuda_available": False}


def _tensor_summary(tensor) -> dict[str, Any]:
    import torch  # type: ignore

    t = tensor.detach()
    f = t.float()
    return {
        "shape": list(t.shape),
        "dtype": str(t.dtype).replace("torch.", ""),
        "device": str(t.device),
        "numel": int(t.numel()),
        "min": float(f.min().item()) if f.numel() else None,
        "max": float(f.max().item()) if f.numel() else None,
        "mean": float(f.mean().item()) if f.numel() else None,
        "std": float(f.std(unbiased=False).item()) if f.numel() else None,
        "has_nan": bool(torch.isnan(f).any().item()) if f.numel() else False,
        "has_inf": bool(torch.isinf(f).any().item()) if f.numel() else False,
    }


def _add_lingbot_path(paths: dict[str, str]) -> str:
    root = str(paths.get("lingbot_code") or "local_assets/third_party/lingbot_world")
    if root and root not in sys.path:
        sys.path.insert(0, root)
    return root


def _load_first_pair(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if p.suffix == ".jsonl":
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                return json.loads(line)
        raise ValueError(f"no rows in {p}")
    payload = json.loads(p.read_text(encoding="utf-8"))
    groups = payload.get("groups")
    if groups:
        return groups[0]
    return payload


def _load_pair_from_args_or_batch(args) -> dict[str, Any]:
    if getattr(args, "pairs", ""):
        return _normalize_pair(_load_first_pair(args.pairs))
    batch_dir = Path(getattr(args, "batch", "") or "")
    sidecar = _read_json(batch_dir / "condition_sidecar.json")
    summary = _read_json(batch_dir / "batch_summary.json")
    if sidecar:
        return _normalize_pair(
            {
                "pair_id": sidecar.get("pair_id") or summary.get("pair_id"),
                "pair_type": summary.get("pair_type"),
                "prompt": sidecar.get("prompt"),
                "condition": sidecar.get("condition") or {},
                "winner": {},
                "loser": {},
                "metadata": sidecar.get("metadata") or {},
                "margin": summary.get("reward_margin"),
            }
        )
    raise ValueError("pair input missing; pass --pairs or rerun dpo_batch_shape_dryrun to write condition_sidecar.json")


def _normalize_pair(pair: dict[str, Any]) -> dict[str, Any]:
    """Return a common pair shape with condition/winner/loser keys."""

    if "winner" in pair and "loser" in pair:
        return pair
    videos = pair.get("videos") or []
    if len(videos) < 2:
        raise ValueError("VideoGPA pair must have at least two videos")
    videos = sorted(videos, key=lambda v: float(v.get("consistency_score", 0.0)))
    return {
        "pair_id": pair.get("group_id"),
        "pair_type": (pair.get("metadata") or {}).get("pair_type"),
        "condition": pair.get("extra_condition") or {},
        "winner": {"video": videos[0].get("video_path"), "source": videos[0].get("source"), "reward": videos[0].get("reward") or {"reward_total": videos[0].get("physgeo_reward")}},
        "loser": {"video": videos[1].get("video_path"), "source": videos[1].get("source"), "reward": videos[1].get("reward") or {"reward_total": videos[1].get("physgeo_reward")}},
        "prompt": pair.get("prompt") or pair.get("text_prompt"),
        "margin": (pair.get("metadata") or {}).get("margin"),
        "metadata": pair.get("metadata") or {},
    }


def _sample_dir_from_condition(condition: dict[str, Any]) -> Path | None:
    meta = condition.get("metadata")
    if meta:
        path = Path(str(meta))
        if path.exists():
            return path.parent
    image = condition.get("image")
    if image:
        path = Path(str(image))
        if path.exists():
            return path.parent
    return None


def _video_tensor(video_path: str | Path, *, num_frames: int, resolution: str, dtype, device):
    import torch  # type: ignore

    height, width = [int(x) for x in str(resolution).lower().split("x", 1)]
    frames = read_video_frames(video_path, max_frames=num_frames, size=(width, height))
    if not frames:
        raise RuntimeError(f"failed to read video frames: {video_path}")
    while len(frames) < num_frames:
        frames.append(frames[-1])
    arr = np.stack(frames[:num_frames]).astype("float32")
    arr = arr / 127.5 - 1.0
    tensor = torch.from_numpy(arr).permute(3, 0, 1, 2).contiguous().to(device=device, dtype=dtype)
    return tensor


def _call_vae_encode(vae: Any, video_tensor: Any):
    attempts = [
        ("encode_list_cthw", lambda: vae.encode([video_tensor])),
        ("encode_bcthw", lambda: vae.encode(video_tensor.unsqueeze(0))),
        ("encode_cthw", lambda: vae.encode(video_tensor)),
    ]
    errors = []
    for name, fn in attempts:
        try:
            out = fn()
            if isinstance(out, (list, tuple)):
                out = out[0]
            return out, name
        except Exception as exc:
            errors.append({"attempt": name, "error": repr(exc)})
    raise RuntimeError(f"VAE encode failed for all call patterns: {errors}")


def _module_param_summary(module: Any) -> dict[str, Any]:
    import torch  # type: ignore

    total = 0
    trainable = 0
    devices: set[str] = set()
    dtypes: set[str] = set()
    try:
        for param in module.parameters():
            total += int(param.numel())
            if param.requires_grad:
                trainable += int(param.numel())
            devices.add(str(param.device))
            dtypes.add(str(param.dtype).replace("torch.", ""))
    except Exception as exc:
        return {"error": repr(exc)}
    return {
        "param_count": total,
        "requires_grad_count": trainable,
        "devices": sorted(devices),
        "dtypes": sorted(dtypes),
    }


_CAMERA_TRAINABLE_TOKENS = (
    "patch_embedding_wancamctrl",
    "c2ws_hidden_states_layer1",
    "c2ws_hidden_states_layer2",
    "cam_injector_layer",
    "cam_scale_layer",
    "cam_shift_layer",
)


_TRAINABLE_SCOPES = (
    "lora",
    "camera_adapter",
    "tiny_subset",
    "head_only",
    "plucker_projection_only",
    "action_scale_shift_tiny",
    "camera_lora_tiny",
    "camera_control_lora_tiny",
    "qkv_lora_tiny",
    "none",
)


_PLUCKER_PROJECTION_TOKENS = (
    "patch_embedding_wancamctrl",
    "c2ws_hidden_states_layer1",
    "c2ws_hidden_states_layer2",
)


_ACTION_SCALE_SHIFT_TOKENS = (
    "cam_scale_layer",
    "cam_shift_layer",
    "cam_injector_layer",
)


_QKV_TOKENS = (
    ".q.",
    ".k.",
    ".v.",
    ".q_proj",
    ".k_proj",
    ".v_proj",
    ".to_q",
    ".to_k",
    ".to_v",
)


def _scope_match(name: str, scope: str) -> bool:
    lname = name.lower()
    if "physics_" in lname or "physicsadapter" in lname:
        return False
    if scope == "camera_adapter":
        return any(token in lname for token in _CAMERA_TRAINABLE_TOKENS)
    if scope == "lora":
        return "lora_" in lname or ".lora" in lname
    if scope == "head_only":
        return lname.startswith("head.") or ".head." in lname or lname.startswith("head_")
    if scope == "plucker_projection_only":
        return any(token in lname for token in _PLUCKER_PROJECTION_TOKENS)
    if scope == "action_scale_shift_tiny":
        return any(token in lname for token in _ACTION_SCALE_SHIFT_TOKENS)
    if scope == "camera_lora_tiny":
        return ("lora_" in lname or ".lora" in lname) and any(token in lname for token in _CAMERA_TRAINABLE_TOKENS)
    if scope == "camera_control_lora_tiny":
        return ("lora_" in lname or ".lora" in lname) and any(token in lname for token in ("cam_", "camera", "c2ws", "wancamctrl", "control", "plucker"))
    if scope == "qkv_lora_tiny":
        return ("lora_" in lname or ".lora" in lname) and any(token in lname for token in _QKV_TOKENS)
    return False


def _camera_selection_key(name: str) -> tuple[int, int, int, str]:
    import re

    match = re.search(r"blocks\.(\d+)\.", name)
    block = int(match.group(1)) if match else -1
    lname = name.lower()
    # Prefer late, small camera parameters. A late-block bias exercises the
    # camera-conditioned path while keeping autograd activation retention small.
    size_rank = 0 if lname.endswith(".bias") else 1
    if "cam_shift_layer" in lname:
        module_rank = 0
    elif "cam_scale_layer" in lname:
        module_rank = 1
    elif "cam_injector_layer2" in lname:
        module_rank = 2
    elif "cam_injector_layer1" in lname:
        module_rank = 3
    elif "c2ws_hidden_states" in lname:
        module_rank = 4
    elif "patch_embedding_wancamctrl" in lname:
        module_rank = 5
    else:
        module_rank = 6
    return (-block, size_rank, module_rank, name)


def _scope_selection_key(name: str, scope: str) -> tuple[int, int, int, str]:
    lname = name.lower()
    if scope == "head_only":
        # Keep the old successful plumbing subset as a named baseline.
        preferred = 0 if lname.startswith("head.head.") else 1
        size_rank = 0 if lname.endswith(".bias") else 1
        return (preferred, size_rank, 0, name)
    if scope == "plucker_projection_only":
        # Prefer biases first. Full patch/c2ws weights are semantically relevant
        # but too risky for a first backward-only scope.
        size_rank = 0 if lname.endswith(".bias") else 1
        if "c2ws_hidden_states_layer2" in lname:
            module_rank = 0
        elif "c2ws_hidden_states_layer1" in lname:
            module_rank = 1
        elif "patch_embedding_wancamctrl" in lname:
            module_rank = 2
        else:
            module_rank = 3
        return (size_rank, module_rank, 0, name)
    if scope == "action_scale_shift_tiny":
        return _camera_selection_key(name)
    return _camera_selection_key(name)


def _scope_is_camera_related(scope: str) -> bool:
    return scope in {
        "camera_adapter",
        "plucker_projection_only",
        "action_scale_shift_tiny",
        "camera_lora_tiny",
        "camera_control_lora_tiny",
    }


def _scope_memory_risk(scope: str, count: int) -> str:
    if scope == "camera_adapter":
        return "high: full camera/control graph previously OOMed at this resolution"
    if scope in {"plucker_projection_only", "action_scale_shift_tiny", "camera_lora_tiny", "camera_control_lora_tiny"}:
        return "low-to-medium: camera-related but intentionally bounded to a small tensor set"
    if scope in {"tiny_subset", "head_only"}:
        return "low: late head-only plumbing scope, not semantically ideal"
    if scope == "qkv_lora_tiny":
        return "medium: only safe if existing LoRA params are already injected"
    if count <= 5_000_000:
        return "low"
    return "medium"


def _candidate_summary(model: Any, max_trainable_params: int = 50_000_000) -> dict[str, Any]:
    scopes = {scope: [] for scope in _TRAINABLE_SCOPES if scope != "none"}
    total_params = 0
    for name, param in model.named_parameters():
        numel = int(param.numel())
        total_params += numel
        for scope in scopes:
            if _scope_match(name, scope):
                scopes[scope].append((name, numel, str(param.dtype).replace("torch.", ""), str(param.device)))
        lname = name.lower()
        if "physics_" not in lname and numel <= max_trainable_params and len(scopes["tiny_subset"]) < 16:
            scopes["tiny_subset"].append((name, numel, str(param.dtype).replace("torch.", ""), str(param.device)))
    result: dict[str, Any] = {"total_param_count": total_params, "scopes": {}}
    for scope, rows in scopes.items():
        result["scopes"][scope] = {
            "candidate_param_count": int(sum(r[1] for r in rows)),
            "candidate_tensor_count": len(rows),
            "sample_names": [r[0] for r in rows[:25]],
            "sample_rows": [{"name": r[0], "numel": r[1], "dtype": r[2], "device": r[3]} for r in rows[:25]],
            "camera_related": _scope_is_camera_related(scope),
            "memory_risk": _scope_memory_risk(scope, int(sum(r[1] for r in rows))),
        }
    if result["scopes"]["action_scale_shift_tiny"]["candidate_param_count"] > 0:
        result["recommended_scope"] = "action_scale_shift_tiny"
        result["recommendation_reason"] = "Late camera scale/shift parameters are directly camera-related and much smaller than full camera_adapter."
    elif result["scopes"]["plucker_projection_only"]["candidate_param_count"] > 0:
        result["recommended_scope"] = "plucker_projection_only"
        result["recommendation_reason"] = "Plucker projection parameters are camera-specific, but may have higher activation-memory risk than late scale/shift."
    elif result["scopes"]["lora"]["candidate_param_count"] > 0:
        result["recommended_scope"] = "lora"
        result["recommendation_reason"] = "Existing LoRA parameters are present and are safer than full-model gradients."
    elif result["scopes"]["tiny_subset"]["candidate_param_count"] > 0:
        result["recommended_scope"] = "tiny_subset"
        result["recommendation_reason"] = "No LoRA/camera adapter candidates found; use a tiny existing parameter subset only as a blocker-localization fallback."
    else:
        result["recommended_scope"] = "none"
        result["recommendation_reason"] = "No safe trainable candidate was found."
    return result


def _module_linear_shape(module: Any) -> dict[str, Any]:
    try:
        return {"in_features": int(module.in_features), "out_features": int(module.out_features)}
    except Exception:
        return {"in_features": None, "out_features": None}


def _lora_name_flags(name: str) -> dict[str, bool]:
    lname = name.lower()
    return {
        "plucker": any(token in lname for token in ("plucker", "c2ws", "wancamctrl")),
        "camera": any(token in lname for token in ("cam_", "camera", "wancamctrl", "c2ws")),
        "action": "action" in lname,
        "control": "control" in lname or "wancamctrl" in lname,
        "scale_shift": any(token in lname for token in ("scale", "shift", "injector")),
        "adapter": "adapter" in lname,
        "projection": "proj" in lname or "embedding" in lname,
        "mlp": "mlp" in lname,
        "condition": "condition" in lname or "cond" in lname,
    }


def _block_index(name: str) -> int:
    import re

    match = re.search(r"blocks\.(\d+)\.", name)
    return int(match.group(1)) if match else -1


def _lora_target_priority(name: str) -> tuple[int, int, str]:
    lname = name.lower()
    if "cam_shift_layer" in lname:
        rank = 0
    elif "cam_scale_layer" in lname:
        rank = 1
    elif "cam_injector_layer2" in lname:
        rank = 2
    elif "cam_injector_layer1" in lname:
        rank = 3
    elif "c2ws_hidden_states_layer2" in lname:
        rank = 4
    elif "c2ws_hidden_states_layer1" in lname:
        rank = 5
    elif "patch_embedding_wancamctrl" in lname:
        rank = 6
    else:
        rank = 7
    return (rank, -_block_index(name), name)


def _estimate_lora_params(module: Any, rank: int) -> int:
    shape = _module_linear_shape(module)
    if shape["in_features"] is None or shape["out_features"] is None:
        return 0
    return int(rank) * int(shape["in_features"] + shape["out_features"])


def _shape_list(value: Any) -> list[int] | None:
    return list(value.shape) if hasattr(value, "shape") else None


def _cfg_get(cfg: Any, key: str, default: Any = None) -> Any:
    if hasattr(cfg, "get"):
        try:
            return cfg.get(key, default)
        except Exception:
            pass
    return getattr(cfg, key, default)


class LingBotFastVideoGPAAdapter:
    """Minimal non-training adapter contract between LingBot-Fast and VideoGPA."""

    def __init__(self, config_path: str = "configs/cam_physgeo/videogpa_adapter.yaml"):
        self.config_path = config_path
        cfg = load_yaml(config_path)
        paths_cfg = load_yaml("configs/cam_physgeo/paths.yaml")
        merged = {**paths_cfg, **cfg}
        self.paths_cfg = merged
        self.paths = resolve_model_paths(merged)
        self.runtime_paths = resolve_t5_runtime_paths(merged)
        self.adapter_cfg = (cfg.get("lingbot_fast_adapter") or {}) if isinstance(cfg, dict) else {}

    def _runtime_checkpoint_dir(self) -> Path:
        candidates = [
            Path(str(self.runtime_paths.get("runtime_root") or "")),
            Path(str(self.paths.get("lingbot_fast") or "")),
        ]
        for path in candidates:
            if path and path.exists():
                return path
        return candidates[0]

    def _wan_task_name(self) -> str:
        return str(self.adapter_cfg.get("wan_task") or self.adapter_cfg.get("task") or "i2v-A14B")

    def _import_fast_pipeline(self):
        root = _add_lingbot_path(self.paths)
        try:
            configs = importlib.import_module("wan.configs")
            image2video_fast = importlib.import_module("wan.image2video_fast")
        except Exception as exc:
            raise RuntimeError(f"failed to import LingBot Fast runtime from {root}: {exc!r}") from exc
        config_table = getattr(configs, "WAN_CONFIGS", None)
        task_name = self._wan_task_name()
        if not config_table or task_name not in config_table:
            available = sorted(config_table.keys()) if isinstance(config_table, dict) else []
            raise RuntimeError(f"Wan task config {task_name!r} not found; available={available}")
        cls = getattr(image2video_fast, "WanI2VFast")
        return cls, config_table[task_name], root

    def _load_fast_pipeline(self, *, device: str = "cuda", dtype: str = "bf16") -> tuple[Any, dict[str, Any]]:
        import copy
        import torch  # type: ignore

        start = time.time()
        device_obj = _torch_device(device)
        dtype_obj = _torch_dtype(dtype)
        if device_obj.type != "cuda":
            device_id = 0
        else:
            device_id = int(str(device_obj).split(":")[-1]) if ":" in str(device_obj) else 0
        cls, wan_cfg, code_root = self._import_fast_pipeline()
        # Disable the optional physics adapter in this DPO plumbing dry-run.
        # The Fast checkpoint does not contain those extra weights in the local
        # bundle, and allowing random initialization would contaminate energy.
        wan_cfg = copy.copy(wan_cfg)
        setattr(wan_cfg, "enable_physics_adapter", False)
        checkpoint_dir = self._runtime_checkpoint_dir()
        info: dict[str, Any] = {
            "checkpoint_dir": str(checkpoint_dir),
            "checkpoint_dir_exists": checkpoint_dir.exists(),
            "lingbot_code_root": str(code_root),
            "wan_task": self._wan_task_name(),
            "class": cls.__name__,
            "device": str(device_obj),
            "device_id": device_id,
            "dtype": str(dtype_obj).replace("torch.", ""),
            "memory_before": _gpu_memory(),
        }
        if not checkpoint_dir.exists():
            raise FileNotFoundError(str(checkpoint_dir))
        with torch.no_grad():
            pipe = cls(
                config=wan_cfg,
                checkpoint_dir=str(checkpoint_dir),
                device_id=device_id,
                rank=0,
                t5_fsdp=False,
                dit_fsdp=False,
                use_sp=False,
                t5_cpu=device_obj.type != "cuda",
                init_on_cpu=True,
                convert_model_dtype=False,
                pipe_dtype=dtype_obj,
            )
        model = getattr(pipe, "model", None)
        if model is not None and hasattr(model, "enable_physics_adapter"):
            # Some checkpoint configs carry optional physics-adapter modules
            # whose weights are absent in the Fast bundle. Keep those modules
            # disabled for this LingBot energy dry-run.
            model.enable_physics_adapter = False
        info.update(
            {
                "success": True,
                "elapsed_sec": time.time() - start,
                "memory_after": _gpu_memory(),
                "control_type": getattr(pipe, "control_type", None),
                "physics_adapter_enabled": bool(getattr(model, "enable_physics_adapter", False)) if model is not None else None,
                "num_train_timesteps": getattr(pipe, "num_train_timesteps", None),
                "scheduler_class": type(getattr(pipe, "scheduler", None)).__name__ if getattr(pipe, "scheduler", None) is not None else None,
                "model_class": type(model).__name__ if model is not None else None,
                "model_param_summary": _module_param_summary(model),
            }
        )
        return pipe, info

    def _vae_path(self) -> Path:
        candidates = [
            Path(str(self.runtime_paths.get("vae_checkpoint") or "")),
            Path(self.paths["lingbot_base"]) / "Wan2.1_VAE.pth",
            Path(self.paths["lingbot_base"]) / "wan_vae.pth",
        ]
        base = Path(self.paths["lingbot_base"])
        if base.exists():
            candidates.extend(sorted(base.glob("*VAE*.pth")))
            candidates.extend(sorted(base.glob("*vae*.pth")))
        for path in candidates:
            if path and path.exists():
                return path
        return candidates[0]

    def _import_vae_class(self):
        root = _add_lingbot_path(self.paths)
        errors = []
        for module_name in ["wan.modules.vae", "wan.modules.vae2_1", "wan.modules.vae2_2"]:
            try:
                module = importlib.import_module(module_name)
            except Exception as exc:
                errors.append({"module": module_name, "error": repr(exc)})
                continue
            for name in ["WanVAE", "VAE", "AutoencoderKLWan"]:
                cls = getattr(module, name, None)
                if cls is not None and inspect.isclass(cls):
                    return cls, module, root
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if "vae" in name.lower() or "autoencoder" in name.lower():
                    return obj, module, root
        raise RuntimeError(f"No VAE class found in known Wan VAE modules: {errors}")

    def load_policy_model(self, *, device: str = "cuda", dtype: str = "bf16", dry_run: bool = False) -> dict[str, Any]:
        """Load the real LingBot-Fast runtime model without optimizer/training state."""

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "checkpoint_dir": str(self._runtime_checkpoint_dir()),
                "wan_task": self._wan_task_name(),
                "training_allowed": False,
            }
        pipe, info = self._load_fast_pipeline(device=device, dtype=dtype)
        model = getattr(pipe, "model", None)
        if model is not None:
            model.eval()
            for param in model.parameters():
                param.requires_grad_(False)
        info.update(
            {
                "object": pipe,
                "training_allowed": False,
                "model_mode": "eval",
                "model_param_summary_after_freeze": _module_param_summary(model),
                "forward_signature": str(inspect.signature(model.forward)) if model is not None and hasattr(model, "forward") else None,
            }
        )
        return info

    def load_reference_model(self, *, device: str = "cuda", dtype: str = "bf16", defer: bool = True) -> dict[str, Any]:
        """Return a frozen reference status.

        The reference is the same frozen LingBot-Fast checkpoint, not LingBot-Base
        and not a reward surrogate. Callers can defer it for policy-only probes
        or load it sequentially for a real reference-energy dry-run.
        """

        if defer:
            return {
                "success": True,
                "deferred": True,
                "reason": "reference model is a frozen same-weight LingBot-Fast copy; deferred for policy-only probe",
                "training_allowed": False,
            }
        result = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
        pipe = result.get("object")
        model = getattr(pipe, "model", None)
        if model is not None:
            model.eval()
            for param in model.parameters():
                param.requires_grad_(False)
        result["reference"] = True
        result["reference_checkpoint"] = "same_frozen_lingbot_fast_checkpoint"
        result["no_grad_required"] = True
        return result

    def load_vae(self, *, device: str = "cuda", dtype: str = "bf16", dry_run: bool = False) -> dict[str, Any]:
        import torch  # type: ignore

        start = time.time()
        device_obj = _torch_device(device)
        dtype_obj = _torch_dtype(dtype)
        vae_path = self._vae_path()
        cls, module, code_root = self._import_vae_class()
        result: dict[str, Any] = {
            "success": False,
            "class": cls.__name__,
            "module": getattr(module, "__file__", None),
            "lingbot_code_root": code_root,
            "vae_path": str(vae_path),
            "vae_exists": vae_path.exists(),
            "device": str(device_obj),
            "dtype": str(dtype_obj).replace("torch.", ""),
            "dry_run": dry_run,
            "memory_before": _gpu_memory(),
        }
        if not vae_path.exists():
            result["error"] = "vae_checkpoint_missing"
            return result
        if dry_run:
            result["success"] = True
            result["elapsed_sec"] = time.time() - start
            return result
        attempts = [
            ("vae_pth_device", lambda: cls(vae_pth=str(vae_path), device=str(device_obj))),
            ("positional_device", lambda: cls(str(vae_path), device=str(device_obj))),
            ("checkpoint_device_dtype", lambda: cls(checkpoint_path=str(vae_path), device=str(device_obj), dtype=dtype_obj)),
            ("positional_only", lambda: cls(str(vae_path))),
        ]
        errors = []
        vae = None
        used = ""
        with torch.no_grad():
            for name, fn in attempts:
                try:
                    vae = fn()
                    used = name
                    break
                except Exception as exc:
                    errors.append({"attempt": name, "error": repr(exc)})
        if vae is None:
            result.update({"error": "vae_init_failed", "attempt_errors": errors, "elapsed_sec": time.time() - start})
            return result
        for attr in ["model", "net", "vae"]:
            obj = getattr(vae, attr, None)
            if hasattr(obj, "to"):
                try:
                    obj.to(device=device_obj, dtype=dtype_obj)
                except Exception:
                    try:
                        obj.to(device_obj)
                    except Exception:
                        pass
        result.update(
            {
                "success": True,
                "init_pattern": used,
                "elapsed_sec": time.time() - start,
                "memory_after": _gpu_memory(),
                "object": vae,
            }
        )
        return result

    def encode_video_to_latent(
        self,
        video_path: str | Path,
        *,
        vae: Any,
        out_path: str | Path | None = None,
        num_frames: int = 8,
        resolution: str = "480x832",
        dtype: str = "bf16",
        device: str = "cuda",
    ) -> dict[str, Any]:
        import torch  # type: ignore

        start = time.time()
        device_obj = _torch_device(device)
        dtype_obj = _torch_dtype(dtype)
        tensor = _video_tensor(video_path, num_frames=num_frames, resolution=resolution, dtype=dtype_obj, device=device_obj)
        with torch.no_grad():
            latent, pattern = _call_vae_encode(vae, tensor)
        if not hasattr(latent, "detach"):
            raise RuntimeError(f"VAE encode returned unsupported type: {type(latent)!r}")
        latent = latent.detach()
        summary = _tensor_summary(latent)
        summary.update(
            {
                "video_path": str(video_path),
                "input_tensor_shape": list(tensor.shape),
                "input_resolution": resolution,
                "num_frames": num_frames,
                "encode_pattern": pattern,
                "elapsed_sec": time.time() - start,
                "compression": _compression_summary(tensor, latent),
                "memory": _gpu_memory(),
            }
        )
        if out_path:
            out_path = Path(out_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(latent.detach().cpu(), out_path)
            summary["latent_path"] = str(out_path)
        return summary

    def encode_condition(self, pair_or_sample: dict[str, Any] | str | Path, *, device: str = "cuda", dtype: str = "bf16", out_dir: str | Path | None = None) -> dict[str, Any]:
        if isinstance(pair_or_sample, (str, Path)):
            sample_dir = Path(pair_or_sample)
            condition = {
                "image": str(sample_dir / "image.jpg"),
                "prompt": str(sample_dir / "prompt.txt"),
                "poses": str(sample_dir / "poses.npy"),
                "intrinsics": str(sample_dir / "intrinsics.npy"),
                "metadata": str(sample_dir / "metadata.json"),
                "action": str(sample_dir / "action.npy") if (sample_dir / "action.npy").exists() else None,
                "use_action": False,
            }
            prompt_text = (sample_dir / "prompt.txt").read_text(encoding="utf-8", errors="replace").strip() if (sample_dir / "prompt.txt").exists() else ""
        else:
            pair = _normalize_pair(pair_or_sample)
            condition = pair.get("condition") or {}
            prompt_text = pair.get("prompt") or ""
        image_path = Path(str(condition.get("image") or ""))
        prompt_path = Path(str(condition.get("prompt") or ""))
        if not prompt_text and prompt_path.exists():
            prompt_text = prompt_path.read_text(encoding="utf-8", errors="replace").strip()
        poses_path = Path(str(condition.get("poses") or ""))
        intr_path = Path(str(condition.get("intrinsics") or ""))
        action_path = Path(str(condition.get("action") or condition.get("dummy_action") or ""))
        metadata_path = Path(str(condition.get("metadata") or ""))
        poses = np.load(poses_path) if poses_path.exists() else None
        intr = np.load(intr_path) if intr_path.exists() else None
        action = np.load(action_path) if action_path.exists() else None
        dummy_action_norm = float(np.linalg.norm(action.astype("float32"))) if action is not None else None
        metadata_payload = _read_json(metadata_path)
        source_width = int(metadata_payload.get("width") or 832)
        source_height = int(metadata_payload.get("height") or 480)
        intr_raw_shape = list(intr.shape) if intr is not None else None
        intrinsics_conversion = None
        intr_for_plucker = intr
        if intr is not None:
            try:
                intr_for_plucker, intrinsics_conversion = convert_projection_to_lingbot_intrinsics(
                    intr,
                    width=source_width,
                    height=source_height,
                    convention="auto",
                )
            except Exception as exc:
                intrinsics_conversion = {"error": repr(exc), "input_shape": intr_raw_shape}
        plucker_summary = None
        plucker_error = None
        plucker_device = "cpu"
        if poses is not None and intr_for_plucker is not None and not (intrinsics_conversion or {}).get("error"):
            try:
                cam_utils = _load_cam_utils(self.config_path, self.paths.get("lingbot_code"))
                control = _build_embedding(
                    poses_np=poses[:8],
                    intrinsics_np=intr_for_plucker[:8],
                    actions_np=action[:8] if action is not None else None,
                    cam_utils=cam_utils,
                    source_width=source_width,
                    source_height=source_height,
                    height=source_height,
                    width=source_width,
                    lat_f=2,
                    lat_h=max(source_height // 8, 1),
                    lat_w=max(source_width // 8, 1),
                    control_type="act",
                    # The reusable probe helper concatenates one CPU tensor with
                    # one device tensor when control_type=act. Keep this dry-run
                    # condition probe on CPU; the actual LingBot pipeline still
                    # builds its camera tensors inside the runtime forward.
                    device=plucker_device,
                )
                plucker_summary = _tensor_summary(control["control"])
            except Exception as exc:
                plucker_error = repr(exc)
        summary = {
            "image": {"path": str(image_path), "exists": image_path.exists()},
            "prompt": prompt_text,
            "prompt_path": str(prompt_path) if prompt_path else None,
            "text_embedding": {"generated": False, "deferred_text_encode": True, "reason": "T5 text encode is deferred to LingBot runtime forward for this dry-run."},
            "poses": {"path": str(poses_path), "exists": poses_path.exists(), "shape": list(poses.shape) if poses is not None else None},
            "intrinsics": {
                "path": str(intr_path),
                "exists": intr_path.exists(),
                "raw_shape": intr_raw_shape,
                "converted_shape": list(intr_for_plucker.shape) if intr_for_plucker is not None and hasattr(intr_for_plucker, "shape") else None,
                "conversion": intrinsics_conversion,
            },
            "metadata": {"path": str(metadata_path), "exists": metadata_path.exists(), "payload": metadata_payload},
            "action": {"path": str(action_path) if str(action_path) else None, "exists": action_path.exists(), "shape": list(action.shape) if action is not None else None, "dummy_action_norm": dummy_action_norm},
            "use_action": False,
            "pipeline_kwargs_keys": ["image", "prompt", "action_path", "poses", "intrinsics"],
            "camera_condition": {
                "action_path_compatibility": str(action_path) if action_path.exists() else None,
                "plucker_probe_device": plucker_device,
                "plucker_or_control_summary": plucker_summary,
                "plucker_error": plucker_error,
            },
            "can_use_for_training_forward": plucker_summary is not None and image_path.exists() and poses_path.exists() and intr_path.exists(),
        }
        if out_dir:
            out = Path(out_dir)
            out.mkdir(parents=True, exist_ok=True)
            write_json(summary, out / "condition_summary.json")
        return summary

    def collate_winner_loser_batch(
        self,
        pair: dict[str, Any],
        *,
        latent_root: str | Path,
        out_dir: str | Path | None = None,
        device: str = "cuda",
        dtype: str = "bf16",
        same_noise: bool = True,
        same_timestep: bool = True,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        pair = _normalize_pair(pair)
        latent_root = Path(latent_root)
        winner_path = latent_root / str(pair.get("pair_id")) / "winner_latent.pt"
        loser_path = latent_root / str(pair.get("pair_id")) / "loser_latent.pt"
        if not winner_path.exists() or not loser_path.exists():
            raise FileNotFoundError(f"missing latent files: {winner_path}, {loser_path}")
        winner = torch.load(winner_path, map_location="cpu")
        loser = torch.load(loser_path, map_location="cpu")
        winner, loser, crop = _match_latent_shapes(winner, loser)
        device_obj = _torch_device(device)
        dtype_obj = _torch_dtype(dtype)
        winner = winner.to(device=device_obj, dtype=dtype_obj)
        loser = loser.to(device=device_obj, dtype=dtype_obj)
        noise = torch.randn_like(winner)
        if not same_noise:
            loser_noise = torch.randn_like(loser)
        else:
            loser_noise = noise
        t = torch.randint(0, 1000, (1,), device=device_obj)
        if not same_timestep:
            loser_t = torch.randint(0, 1000, (1,), device=device_obj)
        else:
            loser_t = t
        cond = self.encode_condition(pair, device=device, dtype=dtype)
        same_noise_confirmed = bool(torch.equal(noise.detach().cpu(), loser_noise.detach().cpu()))
        same_timestep_confirmed = bool(torch.equal(t.detach().cpu(), loser_t.detach().cpu()))
        summary = {
            "pair_id": pair.get("pair_id"),
            "pair_type": pair.get("pair_type"),
            "latent_root": str(latent_root),
            "winner_latent_path": str(winner_path),
            "loser_latent_path": str(loser_path),
            "winner_latent": _tensor_summary(winner),
            "loser_latent": _tensor_summary(loser),
            "shape_crop": crop,
            "noise": _tensor_summary(noise),
            "timestep": {"winner": t.detach().cpu().tolist(), "loser": loser_t.detach().cpu().tolist()},
            "same_noise_confirmed": same_noise_confirmed,
            "same_timestep_confirmed": same_timestep_confirmed,
            "condition_keys": sorted((pair.get("condition") or {}).keys()),
            "condition_summary": cond,
            "reward_margin": pair.get("margin") or (pair.get("metadata") or {}).get("margin"),
            "batch_ready_for_energy": same_noise_confirmed and same_timestep_confirmed and cond.get("can_use_for_training_forward"),
        }
        if out_dir:
            out = Path(out_dir)
            out.mkdir(parents=True, exist_ok=True)
            tensors_path = out / "batch_tensors.pt"
            torch.save(
                {
                    "winner_latent": winner.detach().cpu(),
                    "loser_latent": loser.detach().cpu(),
                    "winner_noise": noise.detach().cpu(),
                    "loser_noise": loser_noise.detach().cpu(),
                    "winner_timestep": t.detach().cpu(),
                    "loser_timestep": loser_t.detach().cpu(),
                },
                tensors_path,
            )
            summary["batch_tensors_path"] = str(tensors_path)
            write_json({"pair_id": pair.get("pair_id"), "condition": pair.get("condition"), "prompt": pair.get("prompt"), "metadata": pair.get("metadata")}, out / "condition_sidecar.json")
            write_json(summary, out / "batch_summary.json")
        return summary

    def prepare_winner_loser_batch(self, pair: dict[str, Any]) -> dict[str, Any]:
        pair = _normalize_pair(pair)
        cond = pair.get("condition") or {}
        videos = [pair.get("winner") or {}, pair.get("loser") or {}]
        return {
            "prompt": pair.get("prompt"),
            "condition_keys": sorted(cond.keys()),
            "camera_pose_path": cond.get("poses"),
            "intrinsics_path": cond.get("intrinsics"),
            "winner_loser_video_count": 2,
            "video_paths": [v.get("video") for v in videos],
            "batch_contract": {
                "winner_latent": "B,C,F,H,W or C,F,H,W after LingBot VAE encode",
                "loser_latent": "B,C,F,H,W or C,F,H,W after LingBot VAE encode",
                "condition": "image + prompt/text embedding + camera Plucker/control",
                "same_noise_same_timestep": True,
            },
        }

    def _prepare_condition_dir(self, pair: dict[str, Any], out_dir: str | Path, *, num_frames: int, resolution: str) -> tuple[Path, dict[str, Any]]:
        pair = _normalize_pair(pair)
        condition = pair.get("condition") or {}
        out = Path(out_dir) / "lingbot_condition"
        out.mkdir(parents=True, exist_ok=True)
        height, width = [int(x) for x in str(resolution).lower().split("x", 1)]
        poses_path = Path(str(condition.get("poses") or ""))
        intr_path = Path(str(condition.get("intrinsics") or ""))
        action_path = Path(str(condition.get("action") or condition.get("dummy_action") or ""))
        metadata_path = Path(str(condition.get("metadata") or ""))
        if not poses_path.exists():
            raise FileNotFoundError(f"poses missing: {poses_path}")
        if not intr_path.exists():
            raise FileNotFoundError(f"intrinsics missing: {intr_path}")
        poses = np.load(poses_path)
        intr_raw = np.load(intr_path)
        metadata = _read_json(metadata_path)
        source_width = int(metadata.get("width") or width)
        source_height = int(metadata.get("height") or height)
        intr, conversion = convert_projection_to_lingbot_intrinsics(intr_raw, width=source_width, height=source_height, convention="auto")
        np.save(out / "poses.npy", poses)
        np.save(out / "intrinsics.npy", intr)
        if action_path.exists():
            action = np.load(action_path)
        else:
            action = np.zeros((max(int(poses.shape[0]), num_frames), 4), dtype=np.float32)
        np.save(out / "action.npy", action.astype(np.float32))
        sidecar = {
            "condition_dir": str(out),
            "poses_source": str(poses_path),
            "intrinsics_source": str(intr_path),
            "intrinsics_raw_shape": list(intr_raw.shape),
            "intrinsics_converted_shape": list(intr.shape),
            "intrinsics_conversion": conversion,
            "action_source": str(action_path) if action_path.exists() else "dummy_zero_generated",
            "action_shape": list(action.shape),
            "dummy_action_norm": float(np.linalg.norm(action.astype("float32"))),
            "use_action": False,
            "source_width": source_width,
            "source_height": source_height,
            "resolution": resolution,
        }
        write_json(sidecar, out / "condition_summary.json")
        return out, sidecar

    def _image_condition_latent(
        self,
        *,
        pipe: Any,
        image_path: str | Path,
        latent_shape: list[int],
        num_frames: int,
        resolution: str,
        dtype: str,
        device: str,
    ):
        import torch  # type: ignore
        from PIL import Image  # type: ignore

        device_obj = _torch_device(device)
        dtype_obj = _torch_dtype(dtype)
        height, width = [int(x) for x in str(resolution).lower().split("x", 1)]
        image = Image.open(image_path).convert("RGB").resize((width, height))
        image_arr = np.asarray(image).astype("float32") / 127.5 - 1.0
        zeros = np.zeros_like(image_arr)
        frames = [image_arr] + [zeros for _ in range(max(num_frames - 1, 0))]
        video = torch.from_numpy(np.stack(frames[:num_frames])).permute(3, 0, 1, 2).contiguous().to(device=device_obj, dtype=dtype_obj)
        with torch.no_grad():
            y_latent, pattern = _call_vae_encode(pipe.vae, video)
        y_latent = y_latent.detach().to(device=device_obj, dtype=dtype_obj)
        if len(latent_shape) != 4:
            raise ValueError(f"expected C,F,H,W latent shape, got {latent_shape}")
        _, lat_f, lat_h, lat_w = [int(v) for v in latent_shape]
        if y_latent.ndim == 5:
            y_latent = y_latent[0]
        if list(y_latent.shape[-3:]) != [lat_f, lat_h, lat_w]:
            f = min(lat_f, int(y_latent.shape[-3]))
            h = min(lat_h, int(y_latent.shape[-2]))
            w = min(lat_w, int(y_latent.shape[-1]))
            tmp = torch.zeros((int(y_latent.shape[0]), lat_f, lat_h, lat_w), device=device_obj, dtype=dtype_obj)
            tmp[:, :f, :h, :w] = y_latent[:, :f, :h, :w]
            y_latent = tmp
        mask = torch.zeros((4, lat_f, lat_h, lat_w), device=device_obj, dtype=dtype_obj)
        mask[:, 0] = 1.0
        y = torch.cat([mask, y_latent], dim=0)
        return y, {"image_path": str(image_path), "image_condition_encode_pattern": pattern, "y_summary": _tensor_summary(y)}

    def _build_forward_condition(
        self,
        *,
        pair: dict[str, Any],
        pipe: Any,
        latent_shape: list[int],
        out_dir: str | Path,
        num_frames: int,
        resolution: str,
        device: str,
        dtype: str,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        pair = _normalize_pair(pair)
        condition = pair.get("condition") or {}
        device_obj = _torch_device(device)
        dtype_obj = _torch_dtype(dtype)
        height, width = [int(x) for x in str(resolution).lower().split("x", 1)]
        _, lat_f, lat_h, lat_w = [int(v) for v in latent_shape]
        condition_dir, condition_sidecar = self._prepare_condition_dir(pair, out_dir, num_frames=num_frames, resolution=resolution)
        poses = np.load(condition_dir / "poses.npy")
        intr = np.load(condition_dir / "intrinsics.npy")
        action = np.load(condition_dir / "action.npy")
        control_type = str(getattr(pipe, "control_type", None) or self.adapter_cfg.get("control_type") or "cam").lower()
        cam_utils = _load_cam_utils(self.config_path, self.paths.get("lingbot_code"))
        control = _build_embedding(
            poses_np=poses[:num_frames],
            intrinsics_np=intr[:num_frames],
            actions_np=action[:num_frames] if control_type == "act" else None,
            cam_utils=cam_utils,
            source_width=int(condition_sidecar["source_width"]),
            source_height=int(condition_sidecar["source_height"]),
            height=height,
            width=width,
            lat_f=lat_f,
            lat_h=lat_h,
            lat_w=lat_w,
            control_type=control_type,
            device="cpu",
        )["control"].to(device=device_obj, dtype=dtype_obj)
        prompt = pair.get("prompt") or ""
        prompt_path = Path(str(condition.get("prompt") or ""))
        if not prompt and prompt_path.exists():
            prompt = prompt_path.read_text(encoding="utf-8", errors="replace").strip()
        if not prompt:
            prompt = "A synthetic physical scene."
        # WanI2VFast constructs T5 on CPU and only moves it inside
        # generate() when t5_cpu=False. This adapter keeps prompt encoding on
        # CPU, then moves the resulting context to the model device. That avoids
        # a CPU-token / CUDA-embedding mismatch and avoids holding T5 on GPU
        # during the subsequent DiT forward.
        with torch.no_grad():
            context = pipe.text_encoder([prompt], torch.device("cpu"))
        if isinstance(context, (tuple, list)):
            context0 = context[0]
        else:
            context0 = context
        image_path = Path(str(condition.get("image") or ""))
        if not image_path.exists():
            raise FileNotFoundError(f"condition image missing: {image_path}")
        y, y_info = self._image_condition_latent(
            pipe=pipe,
            image_path=image_path,
            latent_shape=latent_shape,
            num_frames=num_frames,
            resolution=resolution,
            dtype=dtype,
            device=device,
        )
        model_args = pipe.model.config
        patch_t, patch_h, patch_w = [int(v) for v in (_cfg_get(model_args, "patch_size") or pipe.patch_size)]
        seq_len = int(math.ceil((lat_f * lat_h * lat_w) / (patch_t * patch_h * patch_w)) * (patch_t * patch_h * patch_w))
        frame_seqlen = int(lat_h * lat_w // (patch_h * patch_w))
        kv_size = int(frame_seqlen * lat_f)
        model_dim = int(_cfg_get(model_args, "dim"))
        num_heads = int(_cfg_get(model_args, "num_heads"))
        num_layers = int(_cfg_get(model_args, "num_layers"))
        head_dim = int(model_dim // num_heads)
        local_heads = int(num_heads // getattr(pipe, "sp_size", 1))
        kv_cache = pipe._initialize_self_kv_cache(
            num_layers,
            [1, kv_size, local_heads, head_dim],
            getattr(pipe, "pipe_dtype", dtype_obj),
            pipe.device,
        )
        crossattn_cache = pipe._initialize_crossattn_cache(
            num_layers,
            [1, int(getattr(pipe, "text_len", 512)), num_heads, head_dim],
            getattr(pipe, "pipe_dtype", dtype_obj),
            pipe.device,
        )
        forward_kwargs = {
            "context": [context0.to(device_obj)],
            "seq_len": seq_len,
            "y": [y],
            "dit_cond_dict": {"c2ws_plucker_emb": (control,)},
            "kv_cache": kv_cache,
            "crossattn_cache": crossattn_cache,
            "current_start": 0,
            "max_attention_size": kv_size,
        }
        summary = {
            "prompt": prompt,
            "text_context_summary": _tensor_summary(context0),
            "condition_dir": str(condition_dir),
            "condition_sidecar": condition_sidecar,
            "control_type": control_type,
            "control_summary": _tensor_summary(control),
            "y_info": y_info,
            "seq_len": seq_len,
            "kv_size": kv_size,
            "forward_kwargs_keys": sorted(forward_kwargs.keys()),
            "use_action": False,
            "dummy_action_norm": condition_sidecar["dummy_action_norm"],
        }
        write_json(summary, Path(out_dir) / "forward_condition_summary.json")
        return {"kwargs": forward_kwargs, "summary": summary}

    def _load_batch_tensors(self, batch_dir: str | Path, *, device: str, dtype: str) -> dict[str, Any]:
        import torch  # type: ignore

        batch_dir = Path(batch_dir)
        summary = _read_json(batch_dir / "batch_summary.json")
        tensor_path = Path(summary.get("batch_tensors_path") or batch_dir / "batch_tensors.pt")
        if not tensor_path.exists():
            raise FileNotFoundError(f"batch tensors missing: {tensor_path}; rerun dpo_batch_shape_dryrun with the current adapter")
        payload = torch.load(tensor_path, map_location="cpu")
        device_obj = _torch_device(device)
        dtype_obj = _torch_dtype(dtype)
        for key in ["winner_latent", "loser_latent", "winner_noise", "loser_noise"]:
            payload[key] = payload[key].to(device=device_obj, dtype=dtype_obj)
        for key in ["winner_timestep", "loser_timestep"]:
            payload[key] = payload[key].to(device=device_obj)
        return {"summary": summary, "tensors": payload, "tensor_path": str(tensor_path)}

    def _flow_noisy_and_target(self, x0: Any, noise: Any, timestep: Any, *, num_train_timesteps: int) -> tuple[Any, Any, dict[str, Any]]:
        sigma = (timestep.float() / float(num_train_timesteps)).view(1, 1, 1, 1)
        x0_f = x0.float()
        noise_f = noise.float()
        z_t = (1.0 - sigma) * x0_f + sigma * noise_f
        target = noise_f - x0_f
        return z_t.to(dtype=x0.dtype, device=x0.device), target, {
            "target_type": "flow_velocity_noise_minus_x0",
            "sigma_formula": "sigma = timestep / num_train_timesteps",
            "sigma": sigma.detach().cpu().reshape(-1).tolist(),
            "evidence": "LingBot scripts/train_lingbot_physics_predictor.py::sample_flow_batch",
        }

    def _model_forward_once(
        self,
        *,
        pipe: Any,
        x0: Any,
        noise: Any,
        timestep: Any,
        forward_condition: dict[str, Any],
        enable_grad: bool = False,
    ) -> tuple[Any, Any, dict[str, Any]]:
        import torch  # type: ignore

        num_train_timesteps = int(getattr(pipe, "num_train_timesteps", 1000) or 1000)
        z_t, target, target_info = self._flow_noisy_and_target(x0, noise, timestep, num_train_timesteps=num_train_timesteps)
        autocast_enabled = z_t.device.type == "cuda"
        grad_ctx = contextlib.nullcontext() if enable_grad else torch.no_grad()
        with grad_ctx, torch.amp.autocast("cuda", dtype=getattr(pipe, "param_dtype", z_t.dtype), enabled=autocast_enabled):
            pred = pipe.model(x=[z_t], t=timestep, **forward_condition["kwargs"])[0]
        return pred, target, target_info

    def _compute_energy_with_pipe(
        self,
        *,
        pipe: Any,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        device: str,
        dtype: str,
        num_frames: int,
        resolution: str,
        batch_override: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        batch = batch_override or self._load_batch_tensors(batch_dir, device=device, dtype=dtype)
        tensors = batch["tensors"]
        condition = self._build_forward_condition(
            pair=pair,
            pipe=pipe,
            latent_shape=list(tensors["winner_latent"].shape),
            out_dir=out_dir,
            num_frames=num_frames,
            resolution=resolution,
            device=device,
            dtype=dtype,
        )
        winner_pred, winner_target, target_info = self._model_forward_once(
            pipe=pipe,
            x0=tensors["winner_latent"],
            noise=tensors["winner_noise"],
            timestep=tensors["winner_timestep"],
            forward_condition=condition,
        )
        loser_pred, loser_target, _ = self._model_forward_once(
            pipe=pipe,
            x0=tensors["loser_latent"],
            noise=tensors["loser_noise"],
            timestep=tensors["loser_timestep"],
            forward_condition=condition,
        )
        e_winner = torch.mean((winner_pred.float() - winner_target.float()) ** 2)
        e_loser = torch.mean((loser_pred.float() - loser_target.float()) ** 2)
        return {
            "batch_summary": batch["summary"],
            "condition_summary": condition["summary"],
            "target_info": target_info,
            "E_winner": float(e_winner.detach().cpu().item()),
            "E_loser": float(e_loser.detach().cpu().item()),
            "Delta_loser_minus_winner": float((e_loser - e_winner).detach().cpu().item()),
            "winner_pred": _tensor_summary(winner_pred),
            "loser_pred": _tensor_summary(loser_pred),
            "winner_target": _tensor_summary(winner_target),
            "loser_target": _tensor_summary(loser_target),
            "finite_check": {
                "winner": bool(torch.isfinite(e_winner).item()),
                "loser": bool(torch.isfinite(e_loser).item()),
            },
        }

    def _compute_energy_tensors_with_pipe(
        self,
        *,
        pipe: Any,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        device: str,
        dtype: str,
        num_frames: int,
        resolution: str,
        enable_grad: bool,
        batch_override: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        batch = batch_override or self._load_batch_tensors(batch_dir, device=device, dtype=dtype)
        tensors = batch["tensors"]
        condition = self._build_forward_condition(
            pair=pair,
            pipe=pipe,
            latent_shape=list(tensors["winner_latent"].shape),
            out_dir=out_dir,
            num_frames=num_frames,
            resolution=resolution,
            device=device,
            dtype=dtype,
        )
        winner_pred, winner_target, target_info = self._model_forward_once(
            pipe=pipe,
            x0=tensors["winner_latent"],
            noise=tensors["winner_noise"],
            timestep=tensors["winner_timestep"],
            forward_condition=condition,
            enable_grad=enable_grad,
        )
        loser_pred, loser_target, _ = self._model_forward_once(
            pipe=pipe,
            x0=tensors["loser_latent"],
            noise=tensors["loser_noise"],
            timestep=tensors["loser_timestep"],
            forward_condition=condition,
            enable_grad=enable_grad,
        )
        e_winner = torch.mean((winner_pred.float() - winner_target.float()) ** 2)
        e_loser = torch.mean((loser_pred.float() - loser_target.float()) ** 2)
        return {
            "batch_summary": batch["summary"],
            "condition_summary": condition["summary"],
            "target_info": target_info,
            "E_winner_tensor": e_winner,
            "E_loser_tensor": e_loser,
            "E_winner": float(e_winner.detach().cpu().item()),
            "E_loser": float(e_loser.detach().cpu().item()),
            "Delta_loser_minus_winner": float((e_loser - e_winner).detach().cpu().item()),
            "winner_pred": _tensor_summary(winner_pred),
            "loser_pred": _tensor_summary(loser_pred),
            "winner_target": _tensor_summary(winner_target),
            "loser_target": _tensor_summary(loser_target),
            "finite_check": {
                "winner": bool(torch.isfinite(e_winner.detach()).item()),
                "loser": bool(torch.isfinite(e_loser.detach()).item()),
            },
        }

    def _make_step_batch_override(
        self,
        batch: dict[str, Any],
        *,
        step_index: int,
        resample_noise: bool,
        resample_timestep: bool,
        num_train_timesteps: int,
        seed: int = 12345,
        fixed_noise_seed: int | None = None,
        fixed_timestep: int | None = None,
    ) -> dict[str, Any]:
        import copy
        import torch  # type: ignore

        tensors_in = batch["tensors"]
        tensors = dict(tensors_in)
        device = tensors_in["winner_latent"].device
        dtype = tensors_in["winner_latent"].dtype
        step_seed = int(seed) + int(step_index)
        generator = torch.Generator(device=device)
        generator.manual_seed(step_seed)
        if resample_noise:
            noise = torch.randn(
                tuple(tensors_in["winner_latent"].shape),
                generator=generator,
                device=device,
                dtype=dtype,
            )
            tensors["winner_noise"] = noise
            tensors["loser_noise"] = noise.clone()
        elif fixed_noise_seed is not None:
            fixed_generator = torch.Generator(device=device)
            fixed_generator.manual_seed(int(fixed_noise_seed))
            noise = torch.randn(
                tuple(tensors_in["winner_latent"].shape),
                generator=fixed_generator,
                device=device,
                dtype=dtype,
            )
            tensors["winner_noise"] = noise
            tensors["loser_noise"] = noise.clone()
        if resample_timestep:
            timestep = torch.randint(
                low=0,
                high=int(num_train_timesteps),
                size=(1,),
                generator=generator,
                device=device,
                dtype=tensors_in["winner_timestep"].dtype,
            )
            tensors["winner_timestep"] = timestep
            tensors["loser_timestep"] = timestep.clone()
        elif fixed_timestep is not None:
            timestep_value = max(0, min(int(fixed_timestep), int(num_train_timesteps) - 1))
            timestep = torch.full(
                tuple(tensors_in["winner_timestep"].shape),
                timestep_value,
                device=device,
                dtype=tensors_in["winner_timestep"].dtype,
            )
            tensors["winner_timestep"] = timestep
            tensors["loser_timestep"] = timestep.clone()
        summary = copy.deepcopy(batch.get("summary") or {})
        summary["miniloop_step"] = int(step_index)
        summary["resample_noise"] = bool(resample_noise)
        summary["resample_timestep"] = bool(resample_timestep)
        summary["step_seed"] = step_seed
        summary["fixed_noise_seed"] = int(fixed_noise_seed) if fixed_noise_seed is not None else None
        summary["fixed_timestep"] = int(fixed_timestep) if fixed_timestep is not None else None
        summary["winner_timestep"] = [int(x) for x in tensors["winner_timestep"].detach().cpu().reshape(-1).tolist()]
        summary["loser_timestep"] = [int(x) for x in tensors["loser_timestep"].detach().cpu().reshape(-1).tolist()]
        return {
            "summary": summary,
            "tensors": tensors,
            "tensor_path": batch.get("tensor_path"),
            "step_seed": step_seed,
            "noise_resampled": bool(resample_noise),
            "timestep_resampled": bool(resample_timestep),
            "noise_fixed": not bool(resample_noise),
            "timestep_fixed": not bool(resample_timestep),
        }

    def model_forward_probe(
        self,
        *,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        device: str = "cuda",
        dtype: str = "bf16",
        num_frames: int = 8,
        resolution: str = "480x832",
    ) -> dict[str, Any]:
        import torch  # type: ignore

        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        load_result = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
        pipe = load_result.pop("object", None)
        batch = self._load_batch_tensors(batch_dir, device=device, dtype=dtype)
        tensors = batch["tensors"]
        latent_shape = list(tensors["winner_latent"].shape)
        condition = self._build_forward_condition(
            pair=pair,
            pipe=pipe,
            latent_shape=latent_shape,
            out_dir=out,
            num_frames=num_frames,
            resolution=resolution,
            device=device,
            dtype=dtype,
        )
        result: dict[str, Any] = {
            "success": False,
            "policy_load": load_result,
            "batch_summary": batch["summary"],
            "condition_summary": condition["summary"],
            "no_backward": True,
            "no_optimizer": True,
        }
        try:
            winner_pred, winner_target, target_info = self._model_forward_once(
                pipe=pipe,
                x0=tensors["winner_latent"],
                noise=tensors["winner_noise"],
                timestep=tensors["winner_timestep"],
                forward_condition=condition,
            )
            loser_pred, loser_target, _ = self._model_forward_once(
                pipe=pipe,
                x0=tensors["loser_latent"],
                noise=tensors["loser_noise"],
                timestep=tensors["loser_timestep"],
                forward_condition=condition,
            )
            result.update(
                {
                    "success": True,
                    "target_info": target_info,
                    "winner_pred": _tensor_summary(winner_pred),
                    "loser_pred": _tensor_summary(loser_pred),
                    "winner_target": _tensor_summary(winner_target),
                    "loser_target": _tensor_summary(loser_target),
                    "pred_shape_matches_latent": list(winner_pred.shape) == list(tensors["winner_latent"].shape) and list(loser_pred.shape) == list(tensors["loser_latent"].shape),
                    "memory": _gpu_memory(),
                }
            )
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "model_forward_failed", "memory": _gpu_memory()})
        write_json(_jsonable(result), out / "model_forward_probe_summary.json")
        return result

    def compute_dpo_energy_or_logprob(
        self,
        *,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        device: str = "cuda",
        dtype: str = "bf16",
        num_frames: int = 8,
        resolution: str = "480x832",
        require_real_target: bool = True,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        if not require_real_target:
            raise NotImplementedError("Energy dry-run requires a real target. Refusing to run without --require_real_target true.")
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        load_result = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
        pipe = load_result.pop("object", None)
        reference = self.load_reference_model(device=device, dtype=dtype, defer=True)
        result: dict[str, Any] = {
            "success": False,
            "policy_load": load_result,
            "reference_status": reference,
            "target_type": "flow_velocity_noise_minus_x0",
            "target_evidence": [
                "local_assets/third_party/lingbot_world/scripts/train_lingbot_physics_predictor.py::sample_flow_batch",
                "local_assets/third_party/VideoGPA/official_repo/train/Wan2.2-TI2V-5B/03_train.py::flow_matching_get_velocity",
                "local_assets/third_party/lingbot_world/wan/image2video_fast.py::_convert_flow_pred_to_x0 docstring",
            ],
            "no_backward": True,
            "no_optimizer": True,
            "dpo_loss_computed": False,
        }
        try:
            energy = self._compute_energy_with_pipe(
                pipe=pipe,
                pair=pair,
                batch_dir=batch_dir,
                out_dir=out,
                device=device,
                dtype=dtype,
                num_frames=num_frames,
                resolution=resolution,
            )
            result.update(
                {
                    "success": bool(energy["finite_check"]["winner"] and energy["finite_check"]["loser"]),
                    "batch_summary": energy["batch_summary"],
                    "condition_summary": energy["condition_summary"],
                    "target_info": energy["target_info"],
                    "E_policy_winner": energy["E_winner"],
                    "E_policy_loser": energy["E_loser"],
                    "Delta_policy_loser_minus_winner": energy["Delta_loser_minus_winner"],
                    "E_ref_winner": None,
                    "E_ref_loser": None,
                    "reference_delta": None,
                    "winner_pred": energy["winner_pred"],
                    "loser_pred": energy["loser_pred"],
                    "winner_target": energy["winner_target"],
                    "loser_target": energy["loser_target"],
                    "finite_check": energy["finite_check"],
                    "memory": _gpu_memory(),
                }
            )
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "energy_forward_failed", "memory": _gpu_memory()})
        write_json(_jsonable(result), out / "energy_logprob_summary.json")
        return result

    def compute_reference_energy(
        self,
        *,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        device: str = "cuda",
        dtype: str = "bf16",
        num_frames: int = 8,
        resolution: str = "480x832",
        sequential_reference_if_needed: bool = True,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result: dict[str, Any] = {
            "success": False,
            "reference_role": "frozen_same_lingbot_fast_checkpoint",
            "sequential_reference_if_needed": sequential_reference_if_needed,
            "no_backward": True,
            "no_optimizer": True,
            "training_allowed": False,
            "target_type": "flow_velocity_noise_minus_x0",
        }
        try:
            with torch.no_grad():
                ref_load = self.load_reference_model(device=device, dtype=dtype, defer=False)
                pipe = ref_load.pop("object", None)
                energy = self._compute_energy_with_pipe(
                    pipe=pipe,
                    pair=pair,
                    batch_dir=batch_dir,
                    out_dir=out,
                    device=device,
                    dtype=dtype,
                    num_frames=num_frames,
                    resolution=resolution,
                )
            result.update(
                {
                    "success": bool(energy["finite_check"]["winner"] and energy["finite_check"]["loser"]),
                    "reference_load": ref_load,
                    "reference_frozen_confirmed": (ref_load.get("model_param_summary_after_freeze") or {}).get("requires_grad_count") == 0,
                    "reference_no_grad_confirmed": True,
                    "policy_reference_same_weights": True,
                    "batch_summary": energy["batch_summary"],
                    "condition_summary": energy["condition_summary"],
                    "target_info": energy["target_info"],
                    "E_ref_winner": energy["E_winner"],
                    "E_ref_loser": energy["E_loser"],
                    "Delta_ref_loser_minus_winner": energy["Delta_loser_minus_winner"],
                    "winner_pred": energy["winner_pred"],
                    "loser_pred": energy["loser_pred"],
                    "winner_target": energy["winner_target"],
                    "loser_target": energy["loser_target"],
                    "finite_check": energy["finite_check"],
                    "memory": _gpu_memory(),
                }
            )
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "reference_energy_failed", "memory": _gpu_memory()})
        write_json(_jsonable(result), out / "reference_energy_summary.json")
        return result

    def compute_dpo_scalar_loss_dryrun(
        self,
        *,
        policy_energy_dir: str | Path,
        reference_energy_dir: str | Path,
        out_dir: str | Path,
        beta: float = 0.1,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        policy = _read_energy_summary(policy_energy_dir, "energy_logprob_summary.json")
        reference = _read_energy_summary(reference_energy_dir, "reference_energy_summary.json")
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        if not policy.get("success"):
            raise RuntimeError(f"policy energy did not pass: {policy.get('error')}")
        if not reference.get("success"):
            raise RuntimeError(f"reference energy did not pass: {reference.get('error')}")
        e_policy_w = float(policy["E_policy_winner"])
        e_policy_l = float(policy["E_policy_loser"])
        e_ref_w = float(reference["E_ref_winner"])
        e_ref_l = float(reference["E_ref_loser"])
        delta_policy = e_policy_l - e_policy_w
        delta_ref = e_ref_l - e_ref_w
        argument = float(beta) * (delta_policy - delta_ref)
        loss_tensor = -torch.nn.functional.logsigmoid(torch.tensor(argument, dtype=torch.float32))
        loss = float(loss_tensor.item())
        result = {
            "success": bool(math.isfinite(loss)),
            "beta": float(beta),
            "E_policy_winner": e_policy_w,
            "E_policy_loser": e_policy_l,
            "E_ref_winner": e_ref_w,
            "E_ref_loser": e_ref_l,
            "Delta_policy": delta_policy,
            "Delta_ref": delta_ref,
            "dpo_argument": argument,
            "L_DPO": loss,
            "loss_finite": bool(math.isfinite(loss)),
            "sign_convention": {
                "energy": "lower energy means higher model likelihood / preference under the denoising-error proxy",
                "delta": "Delta = E_loser - E_winner; positive means the model assigns lower energy to winner than loser",
                "formula": "L_DPO = -log sigmoid(beta * (Delta_policy - Delta_ref))",
            },
            "policy_reference_same_weights": bool(reference.get("policy_reference_same_weights")),
            "meaningful_if_policy_equals_reference": "Only plumbing-sign smoke. If policy and reference are identical, Delta_policy should match Delta_ref and loss should be close to log(2).",
            "no_backward": True,
            "no_optimizer": True,
            "training_allowed": False,
        }
        write_json(_jsonable(result), out / "dpo_scalar_loss_summary.json")
        return result

    def list_trainable_candidates(self, *, out_dir: str | Path, device: str = "cuda", dtype: str = "bf16", max_trainable_params: int = 50_000_000) -> dict[str, Any]:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result: dict[str, Any] = {"success": False, "no_backward": True, "no_optimizer": True, "training_allowed": False}
        try:
            load_result = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
            pipe = load_result.pop("object", None)
            model = getattr(pipe, "model", None)
            if model is None:
                raise RuntimeError("policy pipeline has no .model")
            candidates = _candidate_summary(model, max_trainable_params=max_trainable_params)
            result.update(
                {
                    "success": True,
                    "policy_load": load_result,
                    "candidate_summary": candidates,
                    "has_lora": candidates["scopes"]["lora"]["candidate_param_count"] > 0,
                    "has_camera_adapter": candidates["scopes"]["camera_adapter"]["candidate_param_count"] > 0,
                    "recommended_scope": candidates["recommended_scope"],
                    "why_safe_for_backward_only": "All params are frozen first; only the selected small scope is opened, no optimizer is constructed, and no step/save is allowed.",
                    "memory": _gpu_memory(),
                }
            )
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "list_trainable_candidates_failed", "memory": _gpu_memory()})
        write_json(_jsonable(result), out / "trainable_candidates_summary.json")
        return result

    def list_camera_trainable_scopes(self, *, out_dir: str | Path, device: str = "cuda", dtype: str = "bf16", max_trainable_params: int = 5_000_000) -> dict[str, Any]:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result: dict[str, Any] = {"success": False, "no_backward": True, "no_optimizer": True, "training_allowed": False}
        try:
            load_result = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
            pipe = load_result.pop("object", None)
            model = getattr(pipe, "model", None)
            if model is None:
                raise RuntimeError("policy pipeline has no .model")
            module_rows: list[dict[str, Any]] = []
            for module_name, module in model.named_modules():
                direct_params = list(module.named_parameters(recurse=False))
                if not direct_params:
                    continue
                lname = module_name.lower()
                contains = {
                    "plucker": any(token in lname for token in ("plucker", "c2ws", "wancamctrl")),
                    "camera": any(token in lname for token in ("cam_", "camera", "wancamctrl", "c2ws")),
                    "action": "action" in lname,
                    "control": "control" in lname or "wancamctrl" in lname,
                    "scale_shift": any(token in lname for token in ("scale", "shift", "injector")),
                    "lora": "lora" in lname,
                }
                if not any(contains.values()):
                    continue
                param_count = int(sum(int(param.numel()) for _, param in direct_params))
                candidate_scopes = [scope for scope in _TRAINABLE_SCOPES if scope != "none" and any(_scope_match(f"{module_name}.{pname}", scope) for pname, _ in direct_params)]
                safe_candidate = bool(candidate_scopes) and (
                    param_count <= max_trainable_params
                    or any(int(param.numel()) <= max_trainable_params and pname.endswith("bias") for pname, param in direct_params)
                )
                module_rows.append(
                    {
                        "module_name": module_name,
                        "module_class": type(module).__name__,
                        "parameter_count": param_count,
                        "direct_parameter_count": len(direct_params),
                        "requires_grad_default": any(bool(param.requires_grad) for _, param in direct_params),
                        "contains": contains,
                        "candidate_scopes": candidate_scopes,
                        "used_in_forward_path": bool(contains["camera"] or contains["plucker"] or contains["scale_shift"] or contains["control"]),
                        "safe_candidate": safe_candidate,
                        "reason": (
                            "direct camera/control module with small bias-level fallback"
                            if safe_candidate
                            else "camera-related but too large unless a smaller sub-scope or LoRA is used"
                        ),
                        "parameters": [
                            {
                                "name": f"{module_name}.{pname}" if module_name else pname,
                                "numel": int(param.numel()),
                                "shape": list(param.shape),
                                "dtype": str(param.dtype).replace("torch.", ""),
                                "device": str(param.device),
                            }
                            for pname, param in direct_params
                        ],
                    }
                )
            module_rows.sort(key=lambda row: (0 if row["safe_candidate"] else 1, row["parameter_count"], row["module_name"]))
            candidates = _candidate_summary(model, max_trainable_params=max_trainable_params)
            preview: dict[str, Any] = {}
            for scope in ["tiny_subset", "head_only", "plucker_projection_only", "action_scale_shift_tiny", "camera_lora_tiny", "qkv_lora_tiny"]:
                selected = self._select_trainable_params(model, scope=scope, max_trainable_params=max_trainable_params)
                preview[scope] = {
                    "selected_tensor_count": selected["selected_tensor_count"],
                    "trainable_param_count": selected["trainable_param_count"],
                    "selected_name_sample": selected["selected_name_sample"][:20],
                    "camera_related": _scope_is_camera_related(scope),
                    "memory_risk": selected.get("memory_risk"),
                    "status": "available" if selected["trainable_param_count"] > 0 else "skipped",
                }
            for param in model.parameters():
                param.requires_grad_(False)
            result.update(
                {
                    "success": True,
                    "policy_load": load_result,
                    "module_inventory": module_rows,
                    "module_inventory_count": len(module_rows),
                    "candidate_summary": candidates,
                    "scope_preview": preview,
                    "recommended_first_scope": "action_scale_shift_tiny"
                    if preview.get("action_scale_shift_tiny", {}).get("trainable_param_count", 0) > 0
                    else "plucker_projection_only",
                    "recommendation_reason": "Prefer direct camera scale/shift biases before full camera_adapter because the prior full camera_adapter backward OOMed near 95GB.",
                    "memory": _gpu_memory(),
                }
            )
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "list_camera_trainable_scopes_failed", "memory": _gpu_memory()})
        write_json(_jsonable(result), out / "camera_trainable_scope_inventory.json")
        return result

    def inspect_lora_targets(
        self,
        *,
        out_dir: str | Path,
        device: str = "cuda",
        dtype: str = "bf16",
        rank_candidates: list[int] | None = None,
    ) -> dict[str, Any]:
        import torch.nn as nn  # type: ignore

        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        ranks = [int(r) for r in (rank_candidates or [2, 4])]
        result: dict[str, Any] = {"success": False, "no_backward": True, "no_optimizer": True, "training_allowed": False}
        try:
            load_result = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
            pipe = load_result.pop("object", None)
            model = getattr(pipe, "model", None)
            if model is None:
                raise RuntimeError("policy pipeline has no .model")
            rows: list[dict[str, Any]] = []
            for module_name, module in model.named_modules():
                if not isinstance(module, nn.Linear):
                    continue
                flags = _lora_name_flags(module_name)
                if not any(flags.values()):
                    continue
                shape = _module_linear_shape(module)
                param_count = int(sum(int(param.numel()) for param in module.parameters()))
                estimates = {f"rank_{rank}": _estimate_lora_params(module, rank) for rank in ranks}
                camera_related = bool(flags["plucker"] or flags["camera"] or flags["control"] or flags["scale_shift"])
                safe = camera_related and bool(estimates) and min(estimates.values()) <= 1_000_000
                rows.append(
                    {
                        "module_name": module_name,
                        "module_class": type(module).__name__,
                        **shape,
                        "parameter_count": param_count,
                        "contains": flags,
                        "camera_related": camera_related,
                        "used_in_forward_path": camera_related,
                        "safe_for_lora": safe,
                        "estimated_lora_params": estimates,
                        "reason": (
                            "late camera/control linear target; LoRA trains low-rank delta while base remains frozen"
                            if safe
                            else "not first-choice for tiny camera LoRA"
                        ),
                    }
                )
            rows.sort(key=lambda row: (0 if row["safe_for_lora"] else 1, _lora_target_priority(row["module_name"])))
            recommended = self._resolve_lora_targets(
                model,
                target_modules="auto",
                lora_scope="camera_control_lora_tiny",
                rank=min(ranks or [2]),
                max_lora_params=1_000_000,
            )
            result.update(
                {
                    "success": True,
                    "policy_load": load_result,
                    "rank_candidates": ranks,
                    "candidate_target_count": len(rows),
                    "candidate_targets": rows,
                    "recommended_target_modules": recommended["target_modules"],
                    "recommended_lora_param_count_rank2": recommended.get("lora_param_count"),
                    "recommended_scope": "camera_control_lora_tiny",
                    "recommendation_reason": "Start with rank-2 LoRA on the latest-block camera shift/scale Linear layers. This is camera-conditioned, far smaller than full camera_adapter, and avoids modifying third_party code or weights.",
                    "memory": _gpu_memory(),
                }
            )
            for param in model.parameters():
                param.requires_grad_(False)
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "inspect_lora_targets_failed", "memory": _gpu_memory()})
        write_json(_jsonable(result), out / "lora_target_inspection.json")
        return result

    def _resolve_lora_targets(
        self,
        model: Any,
        *,
        target_modules: str,
        lora_scope: str,
        rank: int,
        max_lora_params: int,
    ) -> dict[str, Any]:
        import torch.nn as nn  # type: ignore

        module_map = dict(model.named_modules())
        if target_modules and target_modules != "auto":
            requested = [name.strip() for name in str(target_modules).split(",") if name.strip()]
            missing = [name for name in requested if name not in module_map]
            non_linear = [name for name in requested if name in module_map and not isinstance(module_map[name], nn.Linear)]
            if missing or non_linear:
                raise ValueError(f"invalid LoRA targets; missing={missing}, non_linear={non_linear}")
            total = int(sum(_estimate_lora_params(module_map[name], rank) for name in requested))
            if total > max_lora_params:
                raise RuntimeError(f"requested LoRA target params {total} exceed max_lora_params={max_lora_params}")
            return {"target_modules": requested, "lora_param_count": total, "target_selection": "explicit"}

        candidates = []
        for name, module in module_map.items():
            if not isinstance(module, nn.Linear):
                continue
            flags = _lora_name_flags(name)
            if lora_scope == "camera_control_lora_tiny":
                keep = bool(flags["camera"] or flags["plucker"] or flags["control"] or flags["scale_shift"])
            else:
                keep = bool(flags["camera"] or flags["plucker"] or flags["control"])
            if not keep:
                continue
            lora_params = _estimate_lora_params(module, rank)
            if lora_params <= 0:
                continue
            candidates.append((name, module, lora_params))
        candidates.sort(key=lambda item: _lora_target_priority(item[0]))
        selected: list[str] = []
        total = 0
        if lora_scope == "camera_control_lora_tiny":
            late_blocks = sorted({_block_index(name) for name, _, _ in candidates if _block_index(name) >= 0}, reverse=True)
            if late_blocks:
                top_block = late_blocks[0]
                for wanted in ("cam_shift_layer", "cam_scale_layer"):
                    for name, _, lora_params in candidates:
                        lname = name.lower()
                        if _block_index(name) != top_block or wanted not in lname:
                            continue
                        if total + lora_params <= max_lora_params:
                            selected.append(name)
                            total += lora_params
                        break
                if selected:
                    return {"target_modules": selected, "lora_param_count": int(total), "target_selection": "auto_latest_block_shift_scale"}
        for name, _, lora_params in candidates:
            lname = name.lower()
            if lora_scope == "camera_control_lora_tiny" and not ("cam_shift_layer" in lname or "cam_scale_layer" in lname):
                continue
            if total + lora_params > max_lora_params:
                continue
            selected.append(name)
            total += lora_params
            if len(selected) >= 2:
                break
        if not selected:
            for name, _, lora_params in candidates:
                if total + lora_params > max_lora_params:
                    continue
                selected.append(name)
                total += lora_params
                if len(selected) >= 1:
                    break
        if not selected:
            raise RuntimeError("no safe LoRA target modules resolved")
        return {"target_modules": selected, "lora_param_count": int(total), "target_selection": "auto"}

    def inject_lora_dryrun(
        self,
        *,
        out_dir: str | Path,
        device: str = "cuda",
        dtype: str = "bf16",
        lora_scope: str = "camera_control_lora_tiny",
        lora_rank: int = 2,
        lora_alpha: float = 4.0,
        target_modules: str = "auto",
        max_lora_params: int = 1_000_000,
    ) -> dict[str, Any]:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result: dict[str, Any] = {"success": False, "no_backward": True, "no_optimizer": True, "no_step": True, "no_lora_save": True, "training_allowed": False}
        try:
            load_result = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
            pipe = load_result.pop("object", None)
            model = getattr(pipe, "model", None)
            if model is None:
                raise RuntimeError("policy pipeline has no .model")
            resolved = self._resolve_lora_targets(
                model,
                target_modules=target_modules,
                lora_scope=lora_scope,
                rank=int(lora_rank),
                max_lora_params=int(max_lora_params),
            )
            injections = inject_lora_into_modules(
                model,
                resolved["target_modules"],
                rank=int(lora_rank),
                alpha=float(lora_alpha),
            )
            freeze_non_lora_parameters(model)
            lora_rows = list_lora_parameters(model)
            total_trainable = int(sum(int(param.numel()) for param in model.parameters() if param.requires_grad))
            base_trainable = int(sum(int(param.numel()) for name, param in model.named_parameters() if "lora_" not in name and param.requires_grad))
            result.update(
                {
                    "success": True,
                    "policy_load": load_result,
                    "lora_scope": lora_scope,
                    "target_modules": resolved["target_modules"],
                    "target_selection": resolved.get("target_selection"),
                    "rank": int(lora_rank),
                    "alpha": float(lora_alpha),
                    "injections": [inj.__dict__ for inj in injections],
                    "lora_param_count": count_lora_parameters(model),
                    "total_trainable_param_count": total_trainable,
                    "base_trainable_param_count": base_trainable,
                    "base_params_frozen": base_trainable == 0,
                    "reference_params_frozen": "not loaded in injection dry-run",
                    "lora_param_rows": lora_rows[:50],
                    "target_modules_camera_related": all(any(token in name.lower() for token in ("cam_", "camera", "c2ws", "plucker", "wancamctrl", "control")) for name in resolved["target_modules"]),
                    "safe_to_run_backward_only": total_trainable > 0 and total_trainable <= int(max_lora_params) and base_trainable == 0,
                    "memory": _gpu_memory(),
                }
            )
            for param in model.parameters():
                if param.grad is not None:
                    param.grad = None
                param.requires_grad_(False)
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "inject_lora_dryrun_failed", "memory": _gpu_memory()})
        write_json(_jsonable(result), out / "lora_injection_summary.json")
        return result

    def _select_trainable_params(self, model: Any, *, scope: str, max_trainable_params: int) -> dict[str, Any]:
        for param in model.parameters():
            param.requires_grad_(False)

        selected: list[tuple[str, Any]] = []
        count = 0
        skipped_reason: str | None = None
        if scope in {"camera_adapter", "lora", "head_only", "plucker_projection_only", "action_scale_shift_tiny", "camera_lora_tiny", "camera_control_lora_tiny", "qkv_lora_tiny"}:
            rows = [(name, param) for name, param in model.named_parameters() if _scope_match(name, scope)]
            if scope in {"camera_adapter", "plucker_projection_only", "action_scale_shift_tiny", "head_only"}:
                rows = sorted(rows, key=lambda item: _scope_selection_key(item[0], scope))
            if scope in {"camera_lora_tiny", "camera_control_lora_tiny", "qkv_lora_tiny"} and not rows:
                skipped_reason = "no existing LoRA/PEFT parameters were found; this adapter does not inject or save LoRA in a backward-only smoke"
            for name, param in rows:
                numel = int(param.numel())
                if numel > max_trainable_params:
                    continue
                if count + numel > max_trainable_params:
                    continue
                selected.append((name, param))
                count += numel
                if count >= max_trainable_params:
                    break
            if not selected and rows and scope in {"plucker_projection_only", "action_scale_shift_tiny"}:
                skipped_reason = f"all {scope} tensors exceeded max_trainable_params={max_trainable_params}"
        elif scope == "tiny_subset":
            # Only a fallback to localize gradient plumbing; not a training plan.
            rows = list(model.named_parameters())
            preferred = []
            fallback = []
            for name, param in reversed(rows):
                lname = name.lower()
                if "physics_" in lname:
                    continue
                numel = int(param.numel())
                if numel <= max_trainable_params:
                    if any(token in lname for token in ("head", "output", "proj_out", "final")):
                        preferred.append((name, param))
                    fallback.append((name, param))
            pool = preferred or fallback
            if pool:
                name, param = pool[0]
                selected.append((name, param))
                count += int(param.numel())
                # Include an adjacent bias if present and still tiny.
                stem = name.rsplit(".", 1)[0]
                for other_name, other_param in rows:
                    if other_name.startswith(stem + ".") and other_name != name:
                        other_numel = int(other_param.numel())
                        if count + other_numel <= max_trainable_params:
                            selected.append((other_name, other_param))
                            count += other_numel
        elif scope == "none":
            selected = []
        else:
            raise ValueError(f"unknown trainable scope: {scope}")

        for _, param in selected:
            param.requires_grad_(True)

        total = 0
        frozen = 0
        trainable = 0
        for param in model.parameters():
            total += int(param.numel())
            if param.requires_grad:
                trainable += int(param.numel())
            else:
                frozen += int(param.numel())
        return {
            "scope": scope,
            "selected_names": [name for name, _ in selected],
            "selected_name_sample": [name for name, _ in selected[:50]],
            "selected_tensor_count": len(selected),
            "trainable_param_count": trainable,
            "frozen_param_count": frozen,
            "total_param_count": total,
            "max_trainable_params": int(max_trainable_params),
            "camera_related": _scope_is_camera_related(scope),
            "memory_risk": _scope_memory_risk(scope, trainable),
            "skipped_reason": skipped_reason,
            "trainable_dtype_device_sample": [
                {"name": name, "dtype": str(param.dtype).replace("torch.", ""), "device": str(param.device), "numel": int(param.numel())}
                for name, param in selected[:25]
            ],
        }

    def _snapshot_selected_params(self, model: Any, names: list[str]) -> dict[str, Any]:
        param_map = dict(model.named_parameters())
        before: dict[str, Any] = {}
        for name in names:
            param = param_map.get(name)
            if param is None:
                continue
            before[name] = param.detach().float().cpu().clone()
        return before

    def _grad_summary(self, model: Any, before: dict[str, Any]) -> dict[str, Any]:
        import torch  # type: ignore

        grad_norms: list[float] = []
        params_with_grad: list[str] = []
        params_without_grad: list[str] = []
        any_nan = False
        any_inf = False
        changed_max = 0.0
        param_map = dict(model.named_parameters())
        for name, param in param_map.items():
            if not param.requires_grad:
                continue
            if param.grad is None:
                params_without_grad.append(name)
            else:
                grad = param.grad.detach().float()
                any_nan = any_nan or bool(torch.isnan(grad).any().item())
                any_inf = any_inf or bool(torch.isinf(grad).any().item())
                grad_norms.append(float(grad.norm().item()))
                params_with_grad.append(name)
            if name in before:
                diff = (param.detach().float().cpu() - before[name]).abs()
                if diff.numel():
                    changed_max = max(changed_max, float(diff.max().item()))
        return {
            "params_with_grad": len(params_with_grad),
            "params_without_grad": len(params_without_grad),
            "params_with_grad_sample": params_with_grad[:50],
            "params_without_grad_sample": params_without_grad[:50],
            "grad_norm_min": float(min(grad_norms)) if grad_norms else None,
            "grad_norm_max": float(max(grad_norms)) if grad_norms else None,
            "grad_norm_mean": float(sum(grad_norms) / len(grad_norms)) if grad_norms else None,
            "any_nan_grad": any_nan,
            "any_inf_grad": any_inf,
            "policy_params_changed_check": {
                "max_abs_diff_before_after_backward_no_step": changed_max,
                "expected": 0.0,
                "passed": changed_max == 0.0,
            },
        }

    def _snapshot_param_samples(self, model: Any, names: list[str], *, max_elements: int = 4096) -> dict[str, Any]:
        snap: dict[str, Any] = {}
        param_map = dict(model.named_parameters())
        for name in names:
            param = param_map.get(name)
            if param is None:
                continue
            flat = param.detach().float().flatten()
            sample = flat[: min(int(max_elements), int(flat.numel()))].cpu().clone()
            snap[name] = {
                "sample": sample,
                "numel": int(param.numel()),
                "shape": list(param.shape),
                "dtype": str(param.dtype).replace("torch.", ""),
                "device": str(param.device),
                "sample_numel": int(sample.numel()),
                "norm": float(flat.norm().item()) if flat.numel() else 0.0,
            }
        return snap

    def _diff_param_samples(self, model: Any, before: dict[str, Any]) -> dict[str, Any]:
        import torch  # type: ignore

        param_map = dict(model.named_parameters())
        rows: list[dict[str, Any]] = []
        max_abs = 0.0
        abs_sum = 0.0
        count = 0
        changed = 0
        any_nan = False
        any_inf = False
        for name, payload in before.items():
            param = param_map.get(name)
            if param is None:
                rows.append({"name": name, "missing_after": True})
                continue
            sample_before = payload["sample"]
            flat_after = param.detach().float().flatten()
            sample_after = flat_after[: int(sample_before.numel())].cpu()
            diff = (sample_after - sample_before).abs()
            local_max = float(diff.max().item()) if diff.numel() else 0.0
            local_mean = float(diff.mean().item()) if diff.numel() else 0.0
            max_abs = max(max_abs, local_max)
            abs_sum += float(diff.sum().item()) if diff.numel() else 0.0
            count += int(diff.numel())
            if local_max > 0.0:
                changed += 1
            if sample_after.numel():
                any_nan = any_nan or bool(torch.isnan(sample_after).any().item())
                any_inf = any_inf or bool(torch.isinf(sample_after).any().item())
            rows.append({"name": name, "max_abs_diff": local_max, "mean_abs_diff": local_mean, "sample_numel": int(diff.numel())})
        return {
            "param_count": len(before),
            "params_changed_count": changed,
            "max_abs_diff": max_abs,
            "mean_abs_diff": abs_sum / count if count else 0.0,
            "any_nan": any_nan,
            "any_inf": any_inf,
            "rows": rows[:50],
            "sampled_elements_total": count,
        }

    def _param_norm_summary(self, model: Any, names: list[str]) -> dict[str, Any]:
        import torch  # type: ignore

        param_map = dict(model.named_parameters())
        norms: list[float] = []
        any_nan = False
        any_inf = False
        for name in names:
            param = param_map.get(name)
            if param is None:
                continue
            t = param.detach().float()
            norms.append(float(t.norm().item()) if t.numel() else 0.0)
            if t.numel():
                any_nan = any_nan or bool(torch.isnan(t).any().item())
                any_inf = any_inf or bool(torch.isinf(t).any().item())
        return {
            "param_count": len(norms),
            "norm_min": float(min(norms)) if norms else None,
            "norm_max": float(max(norms)) if norms else None,
            "norm_mean": float(sum(norms) / len(norms)) if norms else None,
            "any_nan": any_nan,
            "any_inf": any_inf,
        }

    def _sample_base_param_names(self, model: Any, *, preferred_targets: list[str] | None = None, limit: int = 8) -> list[str]:
        names: list[str] = []
        preferred_targets = preferred_targets or []
        for target in preferred_targets:
            for suffix in ("base.weight", "base.bias"):
                candidate = f"{target}.{suffix}"
                if candidate in dict(model.named_parameters()):
                    names.append(candidate)
        for name, _ in model.named_parameters():
            if "lora_" in name or name in names:
                continue
            names.append(name)
            if len(names) >= limit:
                break
        return names[:limit]

    def _restore_params_from_snapshot(self, model: Any, before: dict[str, Any]) -> None:
        param_map = dict(model.named_parameters())
        for name, value in before.items():
            param = param_map.get(name)
            if param is None:
                continue
            param.data.copy_(value.to(device=param.device, dtype=param.dtype))

    def _diff_full_snapshot(self, model: Any, before: dict[str, Any]) -> dict[str, Any]:
        import torch  # type: ignore

        param_map = dict(model.named_parameters())
        rows: list[dict[str, Any]] = []
        max_abs = 0.0
        abs_sum = 0.0
        count = 0
        changed = 0
        any_nan = False
        any_inf = False
        for name, before_tensor in before.items():
            param = param_map.get(name)
            if param is None:
                rows.append({"name": name, "missing_after": True})
                continue
            after = param.detach().float().cpu()
            diff = (after - before_tensor).abs()
            local_max = float(diff.max().item()) if diff.numel() else 0.0
            local_mean = float(diff.mean().item()) if diff.numel() else 0.0
            max_abs = max(max_abs, local_max)
            abs_sum += float(diff.sum().item()) if diff.numel() else 0.0
            count += int(diff.numel())
            if local_max > 0.0:
                changed += 1
            if after.numel():
                any_nan = any_nan or bool(torch.isnan(after).any().item())
                any_inf = any_inf or bool(torch.isinf(after).any().item())
            rows.append({"name": name, "max_abs_diff": local_max, "mean_abs_diff": local_mean, "numel": int(diff.numel())})
        return {
            "param_count": len(before),
            "params_changed_count": changed,
            "max_abs_diff": max_abs,
            "mean_abs_diff": abs_sum / count if count else 0.0,
            "any_nan": any_nan,
            "any_inf": any_inf,
            "rows": rows[:50],
            "elements_total": count,
        }

    def _total_grad_norm(self, params: list[Any]) -> float:
        import torch  # type: ignore

        total = torch.zeros((), dtype=torch.float32)
        for param in params:
            if param.grad is None:
                continue
            grad = param.grad.detach().float()
            total = total + grad.pow(2).sum().cpu()
        return float(torch.sqrt(total).item())

    def compute_dpo_backward_only_dryrun(
        self,
        *,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        beta: float = 0.1,
        device: str = "cuda",
        dtype: str = "bf16",
        num_frames: int = 8,
        resolution: str = "480x832",
        trainable_scope: str = "camera_adapter",
        max_trainable_params: int = 50_000_000,
        no_optimizer: bool = True,
        no_step: bool = True,
        save_grad_summary: bool = True,
        lora_rank: int = 2,
        lora_alpha: float = 4.0,
        target_modules: str = "auto",
    ) -> dict[str, Any]:
        import torch  # type: ignore

        if not no_optimizer or not no_step:
            raise RuntimeError("backward-only dry-run requires --no_optimizer true and --no_step true")
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result: dict[str, Any] = {
            "success": False,
            "mode": "dpo_backward_only_dryrun",
            "beta": float(beta),
            "no_optimizer": True,
            "no_step": True,
            "no_checkpoint": True,
            "training_allowed": False,
            "trainable_scope_requested": trainable_scope,
        }

        try:
            # Compute frozen reference constants first, then release the
            # reference before building the policy graph. This keeps the dry-run
            # to one active DiT graph and avoids pretending that a reward/model
            # surrogate is the reference.
            with torch.no_grad():
                ref_load = self.load_reference_model(device=device, dtype=dtype, defer=False)
                ref_pipe = ref_load.pop("object", None)
                ref_energy = self._compute_energy_with_pipe(
                    pipe=ref_pipe,
                    pair=pair,
                    batch_dir=batch_dir,
                    out_dir=out / "reference",
                    device=device,
                    dtype=dtype,
                    num_frames=num_frames,
                    resolution=resolution,
                )
                reference_params_with_grad = 0
                ref_model = getattr(ref_pipe, "model", None)
                if ref_model is not None:
                    reference_params_with_grad = sum(1 for p in ref_model.parameters() if p.grad is not None)
                del ref_model
            del ref_pipe
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            policy_load = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
            pipe = policy_load.pop("object", None)
            model = getattr(pipe, "model", None)
            if model is None:
                raise RuntimeError("policy pipeline has no .model")
            model.eval()
            lora_injection: dict[str, Any] | None = None
            if trainable_scope == "camera_control_lora_tiny":
                resolved = self._resolve_lora_targets(
                    model,
                    target_modules=target_modules,
                    lora_scope=trainable_scope,
                    rank=int(lora_rank),
                    max_lora_params=int(max_trainable_params),
                )
                injections = inject_lora_into_modules(
                    model,
                    resolved["target_modules"],
                    rank=int(lora_rank),
                    alpha=float(lora_alpha),
                )
                lora_injection = {
                    "scope": trainable_scope,
                    "target_modules": resolved["target_modules"],
                    "target_selection": resolved.get("target_selection"),
                    "rank": int(lora_rank),
                    "alpha": float(lora_alpha),
                    "injections": [inj.__dict__ for inj in injections],
                    "lora_param_count": count_lora_parameters(model),
                    "note": "runtime-only injection into policy model; no LoRA weights are saved",
                }
            trainable = self._select_trainable_params(model, scope=trainable_scope, max_trainable_params=max_trainable_params)
            if trainable["trainable_param_count"] <= 0:
                raise RuntimeError(f"no trainable parameters selected for scope={trainable_scope}")
            before = self._snapshot_selected_params(model, trainable["selected_names"])
            policy_energy = self._compute_energy_tensors_with_pipe(
                pipe=pipe,
                pair=pair,
                batch_dir=batch_dir,
                out_dir=out / "policy",
                device=device,
                dtype=dtype,
                num_frames=num_frames,
                resolution=resolution,
                enable_grad=True,
            )
            e_policy_w = policy_energy["E_winner_tensor"]
            e_policy_l = policy_energy["E_loser_tensor"]
            e_ref_w = float(ref_energy["E_winner"])
            e_ref_l = float(ref_energy["E_loser"])
            delta_policy = e_policy_l - e_policy_w
            delta_ref_value = e_ref_l - e_ref_w
            delta_ref = torch.tensor(delta_ref_value, device=delta_policy.device, dtype=torch.float32)
            loss = -torch.nn.functional.logsigmoid(torch.tensor(float(beta), device=delta_policy.device, dtype=torch.float32) * (delta_policy.float() - delta_ref))
            loss.backward()
            grad_summary = self._grad_summary(model, before)
            base_params_with_grad = sum(1 for name, param in model.named_parameters() if "lora_" not in name and param.grad is not None)
            lora_params_with_grad = sum(1 for name, param in model.named_parameters() if "lora_" in name and param.grad is not None)
            for param in model.parameters():
                if param.grad is not None:
                    param.grad = None
            result.update(
                {
                    "success": bool(torch.isfinite(loss.detach()).item())
                    and grad_summary["params_with_grad"] > 0
                    and not grad_summary["any_nan_grad"]
                    and not grad_summary["any_inf_grad"]
                    and (trainable_scope != "camera_control_lora_tiny" or base_params_with_grad == 0),
                    "loss": float(loss.detach().cpu().item()),
                    "loss_finite": bool(torch.isfinite(loss.detach()).item()),
                    "E_policy_winner": float(e_policy_w.detach().cpu().item()),
                    "E_policy_loser": float(e_policy_l.detach().cpu().item()),
                    "E_ref_winner": e_ref_w,
                    "E_ref_loser": e_ref_l,
                    "Delta_policy": float(delta_policy.detach().cpu().item()),
                    "Delta_ref": float(delta_ref_value),
                    "dpo_argument": float((float(beta) * (delta_policy.detach().cpu().float() - torch.tensor(delta_ref_value))).item()),
                    "reference_energy": {k: v for k, v in ref_energy.items() if not k.endswith("_tensor")},
                    "policy_energy": {k: v for k, v in policy_energy.items() if not k.endswith("_tensor")},
                    "reference_load": ref_load,
                    "reference_frozen_confirmed": (ref_load.get("model_param_summary_after_freeze") or {}).get("requires_grad_count") == 0,
                    "reference_no_grad_confirmed": True,
                    "reference_params_with_grad": reference_params_with_grad,
                    "policy_load": policy_load,
                    "lora_injection": lora_injection,
                    "trainable_scope": trainable,
                    "grad_summary": grad_summary,
                    "lora_params_with_grad": lora_params_with_grad,
                    "base_params_with_grad": base_params_with_grad,
                    "no_optimizer_confirmed": True,
                    "no_step_confirmed": True,
                    "no_param_update_confirmed": bool(grad_summary["policy_params_changed_check"]["passed"]),
                    "memory": _gpu_memory(),
                }
            )
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "dpo_backward_only_failed", "memory": _gpu_memory()})
        if save_grad_summary:
            write_json(_jsonable(result), out / "grad_summary.json")
        return result

    def compute_dpo_optimizer_step_dryrun(
        self,
        *,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        beta: float = 0.1,
        device: str = "cuda",
        dtype: str = "bf16",
        num_frames: int = 8,
        resolution: str = "480x832",
        trainable_scope: str = "camera_control_lora_tiny",
        max_trainable_params: int = 1_000_000,
        lora_rank: int = 2,
        lora_alpha: float = 4.0,
        target_modules: str = "auto",
        learning_rate: float = 1e-5,
        optimizer_name: str = "adamw",
        max_grad_norm: float = 1.0,
        save_param_diff: bool = True,
        no_save_lora: bool = True,
        no_checkpoint: bool = True,
        restore_after_step: bool = True,
        recompute_after_step: bool = True,
        command: list[str] | None = None,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        if trainable_scope != "camera_control_lora_tiny":
            raise RuntimeError("optimizer-step dry-run is only allowed for camera_control_lora_tiny")
        if not no_save_lora or not no_checkpoint:
            raise RuntimeError("optimizer-step dry-run requires --no_save_lora true and --no_checkpoint true")
        if str(optimizer_name).lower() != "adamw":
            raise RuntimeError(f"unsupported optimizer for dry-run: {optimizer_name}")

        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "command.txt").write_text(" ".join(command or sys.argv) + "\n", encoding="utf-8")
        (out / "stdout_stderr.log").write_text("stdout/stderr is captured by the caller when this module is run from a shell.\n", encoding="utf-8")
        result: dict[str, Any] = {
            "success": False,
            "mode": "dpo_optimizer_step_dryrun",
            "beta": float(beta),
            "learning_rate": float(learning_rate),
            "optimizer": "adamw",
            "max_grad_norm": float(max_grad_norm),
            "step_count": 0,
            "limit_pairs": 1,
            "no_save_lora": True,
            "no_checkpoint": True,
            "training_allowed": False,
            "trainable_scope_requested": trainable_scope,
            "restore_after_step_requested": bool(restore_after_step),
            "save_param_diff": bool(save_param_diff),
        }

        try:
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()

            with torch.no_grad():
                ref_load = self.load_reference_model(device=device, dtype=dtype, defer=False)
                ref_pipe = ref_load.pop("object", None)
                ref_model = getattr(ref_pipe, "model", None)
                ref_names = self._sample_base_param_names(ref_model, limit=8) if ref_model is not None else []
                ref_before = self._snapshot_param_samples(ref_model, ref_names) if ref_model is not None else {}
                ref_energy = self._compute_energy_with_pipe(
                    pipe=ref_pipe,
                    pair=pair,
                    batch_dir=batch_dir,
                    out_dir=out / "reference",
                    device=device,
                    dtype=dtype,
                    num_frames=num_frames,
                    resolution=resolution,
                )
                reference_params_with_grad = 0
                if ref_model is not None:
                    reference_params_with_grad = sum(1 for p in ref_model.parameters() if p.grad is not None)
                    reference_param_diff = self._diff_param_samples(ref_model, ref_before)
                else:
                    reference_param_diff = {"param_count": 0, "params_changed_count": 0, "max_abs_diff": 0.0}
                del ref_model
            del ref_pipe
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            policy_load = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
            pipe = policy_load.pop("object", None)
            model = getattr(pipe, "model", None)
            if model is None:
                raise RuntimeError("policy pipeline has no .model")
            model.eval()
            resolved = self._resolve_lora_targets(
                model,
                target_modules=target_modules,
                lora_scope=trainable_scope,
                rank=int(lora_rank),
                max_lora_params=int(max_trainable_params),
            )
            injections = inject_lora_into_modules(
                model,
                resolved["target_modules"],
                rank=int(lora_rank),
                alpha=float(lora_alpha),
            )
            freeze_non_lora_parameters(model)
            trainable = self._select_trainable_params(model, scope=trainable_scope, max_trainable_params=max_trainable_params)
            if trainable["trainable_param_count"] <= 0:
                raise RuntimeError(f"no trainable LoRA parameters selected for scope={trainable_scope}")
            if trainable["trainable_param_count"] > int(max_trainable_params):
                raise RuntimeError(f"trainable params exceed max_trainable_params={max_trainable_params}")
            param_map = dict(model.named_parameters())
            optimizer_params = [param_map[name] for name in trainable["selected_names"] if name in param_map]
            if len(optimizer_params) != len(trainable["selected_names"]):
                raise RuntimeError("optimizer param name mismatch after LoRA injection")
            optimizer_only_lora = all("lora_" in name for name in trainable["selected_names"])
            if not optimizer_only_lora:
                raise RuntimeError(f"optimizer dry-run selected non-LoRA params: {trainable['selected_names']}")

            lora_before = self._snapshot_selected_params(model, trainable["selected_names"])
            lora_norm_before = self._param_norm_summary(model, trainable["selected_names"])
            base_names = self._sample_base_param_names(model, preferred_targets=resolved["target_modules"], limit=12)
            base_before = self._snapshot_param_samples(model, base_names)
            base_trainable_before = int(sum(int(p.numel()) for name, p in model.named_parameters() if "lora_" not in name and p.requires_grad))

            optimizer = torch.optim.AdamW(optimizer_params, lr=float(learning_rate))
            optimizer.zero_grad(set_to_none=True)
            policy_energy = self._compute_energy_tensors_with_pipe(
                pipe=pipe,
                pair=pair,
                batch_dir=batch_dir,
                out_dir=out / "policy_before_step",
                device=device,
                dtype=dtype,
                num_frames=num_frames,
                resolution=resolution,
                enable_grad=True,
            )
            e_policy_w = policy_energy["E_winner_tensor"]
            e_policy_l = policy_energy["E_loser_tensor"]
            e_ref_w = float(ref_energy["E_winner"])
            e_ref_l = float(ref_energy["E_loser"])
            delta_policy = e_policy_l - e_policy_w
            delta_ref_value = e_ref_l - e_ref_w
            delta_ref = torch.tensor(delta_ref_value, device=delta_policy.device, dtype=torch.float32)
            loss = -torch.nn.functional.logsigmoid(torch.tensor(float(beta), device=delta_policy.device, dtype=torch.float32) * (delta_policy.float() - delta_ref))
            loss.backward()
            grad_summary_before_clip = self._grad_summary(model, lora_before)
            base_params_with_grad = sum(1 for name, param in model.named_parameters() if "lora_" not in name and param.grad is not None)
            lora_params_with_grad = sum(1 for name, param in model.named_parameters() if "lora_" in name and param.grad is not None)
            grad_norm_before_clip = self._total_grad_norm(optimizer_params)
            clip_returned_norm = None
            if max_grad_norm and float(max_grad_norm) > 0:
                clip_returned_norm = float(torch.nn.utils.clip_grad_norm_(optimizer_params, float(max_grad_norm)).item())
            grad_norm_after_clip = self._total_grad_norm(optimizer_params)
            grad_summary_after_clip = self._grad_summary(model, lora_before)
            if grad_summary_after_clip["any_nan_grad"] or grad_summary_after_clip["any_inf_grad"]:
                raise RuntimeError("NaN/Inf gradient detected before optimizer step")

            optimizer.step()
            result["step_count"] = 1

            lora_diff_after_step = self._diff_full_snapshot(model, lora_before)
            base_diff_after_step = self._diff_param_samples(model, base_before)
            lora_norm_after = self._param_norm_summary(model, trainable["selected_names"])
            recompute_result: dict[str, Any] = {"attempted": False}
            if recompute_after_step:
                try:
                    with torch.no_grad():
                        after_energy = self._compute_energy_with_pipe(
                            pipe=pipe,
                            pair=pair,
                            batch_dir=batch_dir,
                            out_dir=out / "policy_after_step",
                            device=device,
                            dtype=dtype,
                            num_frames=num_frames,
                            resolution=resolution,
                        )
                    delta_after = float(after_energy["Delta_loser_minus_winner"])
                    loss_after = -torch.nn.functional.logsigmoid(
                        torch.tensor(float(beta) * (delta_after - float(delta_ref_value)), dtype=torch.float32)
                    )
                    recompute_result = {
                        "attempted": True,
                        "success": True,
                        "L_DPO_after": float(loss_after.item()),
                        "E_policy_winner_after": float(after_energy["E_winner"]),
                        "E_policy_loser_after": float(after_energy["E_loser"]),
                        "Delta_policy_after": delta_after,
                        "policy_energy_after": after_energy,
                    }
                except Exception as exc:
                    recompute_result = {"attempted": True, "success": False, "error": repr(exc), "error_type": "post_step_recompute_failed"}

            restore_diff_after_restore: dict[str, Any] | None = None
            if restore_after_step:
                self._restore_params_from_snapshot(model, lora_before)
                restore_diff_after_restore = self._diff_full_snapshot(model, lora_before)

            optimizer.zero_grad(set_to_none=True)
            for param in model.parameters():
                if param.grad is not None:
                    param.grad = None

            lora_changed = lora_diff_after_step["params_changed_count"] > 0 and lora_diff_after_step["max_abs_diff"] > 0.0
            base_unchanged = base_diff_after_step["max_abs_diff"] == 0.0 and base_diff_after_step["params_changed_count"] == 0
            ref_unchanged = reference_param_diff.get("max_abs_diff", 0.0) == 0.0 and reference_param_diff.get("params_changed_count", 0) == 0
            restored_ok = True
            if restore_after_step and restore_diff_after_restore is not None:
                restored_ok = restore_diff_after_restore["max_abs_diff"] == 0.0 and restore_diff_after_restore["params_changed_count"] == 0
            loss_finite = bool(torch.isfinite(loss.detach()).item())
            result.update(
                {
                    "success": bool(
                        loss_finite
                        and lora_changed
                        and base_unchanged
                        and ref_unchanged
                        and restored_ok
                        and base_params_with_grad == 0
                        and reference_params_with_grad == 0
                        and lora_params_with_grad > 0
                        and not grad_summary_after_clip["any_nan_grad"]
                        and not grad_summary_after_clip["any_inf_grad"]
                        and not lora_diff_after_step["any_nan"]
                        and not lora_diff_after_step["any_inf"]
                    ),
                    "L_DPO_before": float(loss.detach().cpu().item()),
                    "loss_finite": loss_finite,
                    "E_policy_winner_before": float(e_policy_w.detach().cpu().item()),
                    "E_policy_loser_before": float(e_policy_l.detach().cpu().item()),
                    "E_ref_winner": e_ref_w,
                    "E_ref_loser": e_ref_l,
                    "Delta_policy_before": float(delta_policy.detach().cpu().item()),
                    "Delta_ref": float(delta_ref_value),
                    "dpo_argument_before": float((float(beta) * (delta_policy.detach().cpu().float() - torch.tensor(delta_ref_value))).item()),
                    "policy_energy_before": {k: v for k, v in policy_energy.items() if not k.endswith("_tensor")},
                    "reference_energy": ref_energy,
                    "reference_load": ref_load,
                    "reference_frozen_confirmed": (ref_load.get("model_param_summary_after_freeze") or {}).get("requires_grad_count") == 0,
                    "reference_no_grad_confirmed": True,
                    "reference_params_with_grad": reference_params_with_grad,
                    "reference_param_diff": reference_param_diff,
                    "policy_load": policy_load,
                    "lora_injection": {
                        "scope": trainable_scope,
                        "target_modules": resolved["target_modules"],
                        "target_selection": resolved.get("target_selection"),
                        "rank": int(lora_rank),
                        "alpha": float(lora_alpha),
                        "injections": [inj.__dict__ for inj in injections],
                        "lora_param_count": count_lora_parameters(model),
                        "note": "runtime-only injection into policy model; LoRA weights are not saved",
                    },
                    "trainable_scope": trainable,
                    "optimizer_param_groups": {
                        "group_count": len(optimizer.param_groups),
                        "param_count": len(optimizer_params),
                        "contains_only_lora": optimizer_only_lora,
                        "learning_rate": float(optimizer.param_groups[0]["lr"]),
                        "optimizer_class": type(optimizer).__name__,
                    },
                    "base_trainable_param_count_before_step": base_trainable_before,
                    "base_params_with_grad": base_params_with_grad,
                    "lora_params_with_grad": lora_params_with_grad,
                    "grad_norm_before_clip": grad_norm_before_clip,
                    "clip_returned_norm": clip_returned_norm,
                    "grad_norm_after_clip": grad_norm_after_clip,
                    "grad_summary_before_clip": grad_summary_before_clip,
                    "grad_summary_after_clip": grad_summary_after_clip,
                    "lora_param_norm_before": lora_norm_before,
                    "lora_param_norm_after": lora_norm_after,
                    "lora_param_diff": lora_diff_after_step,
                    "base_param_diff": base_diff_after_step,
                    "recompute_after_step": recompute_result,
                    "restore_after_step": {
                        "requested": bool(restore_after_step),
                        "completed": bool(restore_after_step),
                        "post_restore_diff": restore_diff_after_restore,
                        "passed": restored_ok,
                    },
                    "parameter_safety": {
                        "lora_params_changed": lora_changed,
                        "base_params_unchanged": base_unchanged,
                        "reference_params_unchanged": ref_unchanged,
                        "no_nan_inf_grad": not grad_summary_after_clip["any_nan_grad"] and not grad_summary_after_clip["any_inf_grad"],
                        "no_nan_inf_updated_lora": not lora_diff_after_step["any_nan"] and not lora_diff_after_step["any_inf"],
                        "no_checkpoint_saved": True,
                        "no_lora_saved": True,
                        "no_local_assets_weights_write": True,
                    },
                    "memory": _gpu_memory(),
                }
            )
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "dpo_optimizer_step_dryrun_failed", "memory": _gpu_memory()})

        write_json(_jsonable(result), out / "summary.json")
        write_json(_jsonable(result.get("grad_summary_after_clip") or result.get("grad_summary_before_clip") or {}), out / "grad_summary.json")
        write_json(
            _jsonable(
                {
                    "lora_param_diff": result.get("lora_param_diff"),
                    "base_param_diff": result.get("base_param_diff"),
                    "reference_param_diff": result.get("reference_param_diff"),
                    "restore_after_step": result.get("restore_after_step"),
                    "parameter_safety": result.get("parameter_safety"),
                }
            ),
            out / "param_diff_summary.json",
        )
        return result

    def compute_dpo_1pair_overfit_miniloop(
        self,
        *,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        beta: float = 0.1,
        device: str = "cuda",
        dtype: str = "bf16",
        num_frames: int = 8,
        resolution: str = "480x832",
        trainable_scope: str = "camera_control_lora_tiny",
        max_trainable_params: int = 1_000_000,
        lora_rank: int = 2,
        lora_alpha: float = 4.0,
        target_modules: str = "auto",
        learning_rate: float = 1e-5,
        optimizer_name: str = "adamw",
        max_grad_norm: float = 1.0,
        num_steps: int = 5,
        resample_noise_each_step: bool = True,
        resample_timestep_each_step: bool = True,
        fixed_noise_seed: int | None = None,
        fixed_timestep: int | None = None,
        save_param_diff: bool = True,
        no_save_lora: bool = True,
        no_checkpoint: bool = True,
        restore_after_loop: bool = True,
        log_every_step: bool = True,
        command: list[str] | None = None,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        if trainable_scope != "camera_control_lora_tiny":
            raise RuntimeError("1-pair mini-loop is only allowed for camera_control_lora_tiny")
        max_steps = 10 if (not resample_noise_each_step and not resample_timestep_each_step) else 5
        if int(num_steps) < 1 or int(num_steps) > max_steps:
            raise RuntimeError(f"num_steps must be in [1, {max_steps}] for this dry-run, got {num_steps}")
        if not no_save_lora or not no_checkpoint:
            raise RuntimeError("1-pair mini-loop requires --no_save_lora true and --no_checkpoint true")
        if str(optimizer_name).lower() != "adamw":
            raise RuntimeError(f"unsupported optimizer for mini-loop dry-run: {optimizer_name}")

        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        metrics_path = out / "per_step_metrics.jsonl"
        metrics_path.write_text("", encoding="utf-8")
        (out / "command.txt").write_text(" ".join(command or sys.argv) + "\n", encoding="utf-8")
        (out / "stdout_stderr.log").write_text("stdout/stderr is captured by the caller when this module is run from a shell.\n", encoding="utf-8")
        result: dict[str, Any] = {
            "success": False,
            "mode": "dpo_1pair_overfit_miniloop",
            "beta": float(beta),
            "learning_rate": float(learning_rate),
            "optimizer": "adamw",
            "max_grad_norm": float(max_grad_norm),
            "num_steps_requested": int(num_steps),
            "steps_completed": 0,
            "limit_pairs": 1,
            "resample_noise_each_step": bool(resample_noise_each_step),
            "resample_timestep_each_step": bool(resample_timestep_each_step),
            "fixed_noise_seed": int(fixed_noise_seed) if fixed_noise_seed is not None else None,
            "fixed_timestep": int(fixed_timestep) if fixed_timestep is not None else None,
            "fixed_noise_diagnostic": bool(not resample_noise_each_step and not resample_timestep_each_step),
            "no_save_lora": True,
            "no_checkpoint": True,
            "training_allowed": False,
            "trainable_scope_requested": trainable_scope,
            "restore_after_loop_requested": bool(restore_after_loop),
            "save_param_diff": bool(save_param_diff),
            "per_step_metrics_path": str(metrics_path),
        }

        try:
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()

            step_batches: list[dict[str, Any]] = []
            reference_step_metrics: list[dict[str, Any]] = []
            with torch.no_grad():
                ref_load = self.load_reference_model(device=device, dtype=dtype, defer=False)
                ref_pipe = ref_load.pop("object", None)
                ref_model = getattr(ref_pipe, "model", None)
                ref_names = self._sample_base_param_names(ref_model, limit=8) if ref_model is not None else []
                ref_before = self._snapshot_param_samples(ref_model, ref_names) if ref_model is not None else {}
                base_batch = self._load_batch_tensors(batch_dir, device=device, dtype=dtype)
                num_train_timesteps = int(getattr(ref_pipe, "num_train_timesteps", 1000) or 1000)
                for step_idx in range(int(num_steps)):
                    step_batch = self._make_step_batch_override(
                        base_batch,
                        step_index=step_idx,
                        resample_noise=bool(resample_noise_each_step),
                        resample_timestep=bool(resample_timestep_each_step),
                        num_train_timesteps=num_train_timesteps,
                        fixed_noise_seed=fixed_noise_seed,
                        fixed_timestep=fixed_timestep,
                    )
                    step_batches.append(step_batch)
                    if (
                        step_idx > 0
                        and not resample_noise_each_step
                        and not resample_timestep_each_step
                        and reference_step_metrics
                    ):
                        cached_ref = dict(reference_step_metrics[0])
                        cached_ref["cached_from_step"] = 0
                        cached_ref["cache_reason"] = "fixed_noise_fixed_timestep_reference"
                        reference_step_metrics.append(cached_ref)
                        continue
                    ref_energy = self._compute_energy_with_pipe(
                        pipe=ref_pipe,
                        pair=pair,
                        batch_dir=batch_dir,
                        out_dir=out / f"reference_step_{step_idx:04d}",
                        device=device,
                        dtype=dtype,
                        num_frames=num_frames,
                        resolution=resolution,
                        batch_override=step_batch,
                    )
                    reference_step_metrics.append(ref_energy)
                reference_params_with_grad = 0
                if ref_model is not None:
                    reference_params_with_grad = sum(1 for p in ref_model.parameters() if p.grad is not None)
                    reference_param_diff = self._diff_param_samples(ref_model, ref_before)
                else:
                    reference_param_diff = {"param_count": 0, "params_changed_count": 0, "max_abs_diff": 0.0}
                del ref_model
            del ref_pipe
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            policy_load = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
            pipe = policy_load.pop("object", None)
            model = getattr(pipe, "model", None)
            if model is None:
                raise RuntimeError("policy pipeline has no .model")
            model.eval()
            resolved = self._resolve_lora_targets(
                model,
                target_modules=target_modules,
                lora_scope=trainable_scope,
                rank=int(lora_rank),
                max_lora_params=int(max_trainable_params),
            )
            injections = inject_lora_into_modules(
                model,
                resolved["target_modules"],
                rank=int(lora_rank),
                alpha=float(lora_alpha),
            )
            freeze_non_lora_parameters(model)
            trainable = self._select_trainable_params(model, scope=trainable_scope, max_trainable_params=max_trainable_params)
            if trainable["trainable_param_count"] <= 0:
                raise RuntimeError(f"no trainable LoRA parameters selected for scope={trainable_scope}")
            if trainable["trainable_param_count"] > int(max_trainable_params):
                raise RuntimeError(f"trainable params exceed max_trainable_params={max_trainable_params}")
            param_map = dict(model.named_parameters())
            optimizer_params = [param_map[name] for name in trainable["selected_names"] if name in param_map]
            if len(optimizer_params) != len(trainable["selected_names"]):
                raise RuntimeError("optimizer param name mismatch after LoRA injection")
            optimizer_only_lora = all("lora_" in name for name in trainable["selected_names"])
            if not optimizer_only_lora:
                raise RuntimeError(f"mini-loop selected non-LoRA params: {trainable['selected_names']}")

            lora_initial = self._snapshot_selected_params(model, trainable["selected_names"])
            base_names = self._sample_base_param_names(model, preferred_targets=resolved["target_modules"], limit=12)
            base_before = self._snapshot_param_samples(model, base_names)
            base_trainable_before = int(sum(int(p.numel()) for name, p in model.named_parameters() if "lora_" not in name and p.requires_grad))
            optimizer = torch.optim.AdamW(optimizer_params, lr=float(learning_rate))

            per_step: list[dict[str, Any]] = []
            stopped_early_reason: str | None = None
            for step_idx in range(int(num_steps)):
                if torch.cuda.is_available():
                    torch.cuda.reset_peak_memory_stats()
                optimizer.zero_grad(set_to_none=True)
                policy_energy = self._compute_energy_tensors_with_pipe(
                    pipe=pipe,
                    pair=pair,
                    batch_dir=batch_dir,
                    out_dir=out / f"policy_step_{step_idx:04d}",
                    device=device,
                    dtype=dtype,
                    num_frames=num_frames,
                    resolution=resolution,
                    enable_grad=True,
                    batch_override=step_batches[step_idx],
                )
                e_policy_w = policy_energy["E_winner_tensor"]
                e_policy_l = policy_energy["E_loser_tensor"]
                ref_energy = reference_step_metrics[step_idx]
                e_ref_w = float(ref_energy["E_winner"])
                e_ref_l = float(ref_energy["E_loser"])
                delta_policy = e_policy_l - e_policy_w
                delta_ref_value = e_ref_l - e_ref_w
                delta_ref = torch.tensor(delta_ref_value, device=delta_policy.device, dtype=torch.float32)
                preference_logit = torch.tensor(float(beta), device=delta_policy.device, dtype=torch.float32) * (delta_policy.float() - delta_ref)
                loss = -torch.nn.functional.logsigmoid(preference_logit)
                loss.backward()
                grad_summary_before_clip = self._grad_summary(model, lora_initial)
                base_params_with_grad = sum(1 for name, param in model.named_parameters() if "lora_" not in name and param.grad is not None)
                lora_params_with_grad = sum(1 for name, param in model.named_parameters() if "lora_" in name and param.grad is not None)
                grad_norm_before_clip = self._total_grad_norm(optimizer_params)
                clip_returned_norm = None
                if max_grad_norm and float(max_grad_norm) > 0:
                    clip_returned_norm = float(torch.nn.utils.clip_grad_norm_(optimizer_params, float(max_grad_norm)).item())
                grad_norm_after_clip = self._total_grad_norm(optimizer_params)
                grad_summary_after_clip = self._grad_summary(model, lora_initial)
                finite_ok = (
                    bool(torch.isfinite(loss.detach()).item())
                    and not grad_summary_after_clip["any_nan_grad"]
                    and not grad_summary_after_clip["any_inf_grad"]
                )
                if not finite_ok:
                    stopped_early_reason = "nonfinite_loss_or_gradient"
                    step_record = {
                        "step_index": step_idx,
                        "success": False,
                        "L_DPO": float(loss.detach().cpu().item()) if torch.isfinite(loss.detach()).item() else None,
                        "error_type": stopped_early_reason,
                    }
                    per_step.append(step_record)
                    if log_every_step:
                        with metrics_path.open("a", encoding="utf-8") as handle:
                            handle.write(json.dumps(_jsonable(step_record), sort_keys=True) + "\n")
                    break

                optimizer.step()
                lora_diff_from_initial = self._diff_full_snapshot(model, lora_initial)
                lora_norm = self._param_norm_summary(model, trainable["selected_names"])
                step_record = {
                    "step_index": step_idx,
                    "success": True,
                    "timestep": step_batches[step_idx]["summary"].get("winner_timestep"),
                    "noise_resampled": step_batches[step_idx]["noise_resampled"],
                    "timestep_resampled": step_batches[step_idx]["timestep_resampled"],
                    "step_seed": step_batches[step_idx]["step_seed"],
                    "L_DPO": float(loss.detach().cpu().item()),
                    "E_policy_winner": float(e_policy_w.detach().cpu().item()),
                    "E_policy_loser": float(e_policy_l.detach().cpu().item()),
                    "E_ref_winner": e_ref_w,
                        "E_ref_loser": e_ref_l,
                        "Delta_policy": float(delta_policy.detach().cpu().item()),
                        "Delta_ref": float(delta_ref_value),
                        "preference_logit": float(preference_logit.detach().cpu().item()),
                        "sign_convention": "lower energy is better; DPO improves when Delta_policy exceeds Delta_ref under E_loser - E_winner",
                        "grad_norm_before_clip": grad_norm_before_clip,
                    "clip_returned_norm": clip_returned_norm,
                    "grad_norm_after_clip": grad_norm_after_clip,
                    "lora_param_norm": lora_norm,
                    "lora_param_diff_from_initial": {
                        k: lora_diff_from_initial.get(k)
                        for k in ["param_count", "params_changed_count", "max_abs_diff", "mean_abs_diff", "any_nan", "any_inf", "elements_total"]
                    },
                    "base_params_with_grad": base_params_with_grad,
                    "lora_params_with_grad": lora_params_with_grad,
                    "any_nan_grad": grad_summary_after_clip["any_nan_grad"],
                    "any_inf_grad": grad_summary_after_clip["any_inf_grad"],
                    "peak_memory": _gpu_memory(),
                }
                per_step.append(step_record)
                if log_every_step:
                    with metrics_path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(_jsonable(step_record), sort_keys=True) + "\n")
                for param in model.parameters():
                    if param.grad is not None:
                        param.grad = None
                del policy_energy, loss, e_policy_w, e_policy_l, delta_policy, delta_ref, preference_logit

            optimizer.zero_grad(set_to_none=True)
            lora_diff_after_loop = self._diff_full_snapshot(model, lora_initial)
            base_diff_after_loop = self._diff_param_samples(model, base_before)
            restore_diff_after_restore: dict[str, Any] | None = None
            if restore_after_loop:
                self._restore_params_from_snapshot(model, lora_initial)
                restore_diff_after_restore = self._diff_full_snapshot(model, lora_initial)

            for param in model.parameters():
                if param.grad is not None:
                    param.grad = None

            losses = [float(row["L_DPO"]) for row in per_step if row.get("success")]
            delta_policies = [float(row["Delta_policy"]) for row in per_step if row.get("success")]
            preference_logits = [float(row["preference_logit"]) for row in per_step if row.get("success")]
            monotonic_nonincreasing = all(losses[idx] <= losses[idx - 1] for idx in range(1, len(losses))) if len(losses) >= 2 else None
            lora_changed = lora_diff_after_loop["params_changed_count"] > 0 and lora_diff_after_loop["max_abs_diff"] > 0.0
            base_unchanged = base_diff_after_loop["max_abs_diff"] == 0.0 and base_diff_after_loop["params_changed_count"] == 0
            ref_unchanged = reference_param_diff.get("max_abs_diff", 0.0) == 0.0 and reference_param_diff.get("params_changed_count", 0) == 0
            restored_ok = True
            if restore_after_loop and restore_diff_after_restore is not None:
                restored_ok = restore_diff_after_restore["max_abs_diff"] == 0.0 and restore_diff_after_restore["params_changed_count"] == 0
            all_steps_ok = len(losses) == int(num_steps) and stopped_early_reason is None and all(math.isfinite(v) for v in losses)
            any_nan_inf_step = any(row.get("any_nan_grad") or row.get("any_inf_grad") for row in per_step)
            result.update(
                {
                    "success": bool(
                        all_steps_ok
                        and lora_changed
                        and base_unchanged
                        and ref_unchanged
                        and restored_ok
                        and not any_nan_inf_step
                    ),
                    "steps_completed": len(losses),
                    "stopped_early_reason": stopped_early_reason,
                    "loss_values": losses,
                    "loss_first": losses[0] if losses else None,
                    "loss_last": losses[-1] if losses else None,
                    "loss_min": min(losses) if losses else None,
                    "loss_max": max(losses) if losses else None,
                    "loss_delta_last_minus_first": (losses[-1] - losses[0]) if len(losses) >= 2 else None,
                    "loss_monotonic_nonincreasing": monotonic_nonincreasing,
                    "delta_policy_values": delta_policies,
                    "delta_policy_delta_last_minus_first": (delta_policies[-1] - delta_policies[0]) if len(delta_policies) >= 2 else None,
                    "preference_logit_values": preference_logits,
                    "preference_logit_delta_last_minus_first": (preference_logits[-1] - preference_logits[0]) if len(preference_logits) >= 2 else None,
                    "loss_trend_interpretation": (
                        "not expected to be monotonic because noise/timestep are resampled each step"
                        if (resample_noise_each_step or resample_timestep_each_step)
                        else "fixed noise/timestep makes loss trend more directly interpretable"
                    ),
                    "trend_meaningful": bool((not resample_noise_each_step and not resample_timestep_each_step) and len(losses) >= 2),
                    "overfit_signal_observed": bool(len(delta_policies) >= 2 and abs(delta_policies[-1] - delta_policies[0]) > 0.0),
                    "sign_convention": "energy is MSE to flow target; lower winner energy and higher Delta=E_loser-E_winner are preferred",
                    "reference_step_metrics": reference_step_metrics,
                    "per_step_metrics": per_step,
                    "policy_load": policy_load,
                    "reference_load": ref_load,
                    "reference_frozen_confirmed": (ref_load.get("model_param_summary_after_freeze") or {}).get("requires_grad_count") == 0,
                    "reference_no_grad_confirmed": True,
                    "reference_params_with_grad": reference_params_with_grad,
                    "reference_param_diff": reference_param_diff,
                    "lora_injection": {
                        "scope": trainable_scope,
                        "target_modules": resolved["target_modules"],
                        "target_selection": resolved.get("target_selection"),
                        "rank": int(lora_rank),
                        "alpha": float(lora_alpha),
                        "injections": [inj.__dict__ for inj in injections],
                        "lora_param_count": count_lora_parameters(model),
                        "note": "runtime-only injection into policy model; LoRA weights are not saved",
                    },
                    "trainable_scope": trainable,
                    "optimizer_param_groups": {
                        "group_count": len(optimizer.param_groups),
                        "param_count": len(optimizer_params),
                        "contains_only_lora": optimizer_only_lora,
                        "learning_rate": float(optimizer.param_groups[0]["lr"]),
                        "optimizer_class": type(optimizer).__name__,
                    },
                    "base_trainable_param_count_before_loop": base_trainable_before,
                    "lora_param_diff": lora_diff_after_loop,
                    "base_param_diff": base_diff_after_loop,
                    "restore_after_loop": {
                        "requested": bool(restore_after_loop),
                        "completed": bool(restore_after_loop),
                        "post_restore_diff": restore_diff_after_restore,
                        "passed": restored_ok,
                    },
                    "parameter_safety": {
                        "lora_params_changed": lora_changed,
                        "base_params_unchanged": base_unchanged,
                        "reference_params_unchanged": ref_unchanged,
                        "no_nan_inf_grad": not any_nan_inf_step,
                        "no_nan_inf_updated_lora": not lora_diff_after_loop["any_nan"] and not lora_diff_after_loop["any_inf"],
                        "no_checkpoint_saved": True,
                        "no_lora_saved": True,
                        "no_local_assets_weights_write": True,
                    },
                    "memory": _gpu_memory(),
                }
            )
            del model
            del pipe
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "dpo_1pair_overfit_miniloop_failed", "memory": _gpu_memory()})

        write_json(_jsonable(result), out / "summary.json")
        write_json(
            _jsonable(
                {
                    "per_step_metrics_path": str(metrics_path),
                    "per_step_metrics": result.get("per_step_metrics", []),
                    "loss_values": result.get("loss_values"),
                    "delta_policy_values": result.get("delta_policy_values"),
                    "success": result.get("success"),
                }
            ),
            out / "grad_summary.json",
        )
        write_json(
            _jsonable(
                {
                    "lora_param_diff": result.get("lora_param_diff"),
                    "base_param_diff": result.get("base_param_diff"),
                    "reference_param_diff": result.get("reference_param_diff"),
                    "restore_after_loop": result.get("restore_after_loop"),
                    "parameter_safety": result.get("parameter_safety"),
                }
            ),
            out / "param_diff_summary.json",
        )
        return result

    def _lora_scaling_snapshot(self, model: Any) -> dict[str, float]:
        return {name: float(module.scaling) for name, module in model.named_modules() if isinstance(module, LoRALinear)}

    def _set_lora_scaling(self, model: Any, scaling: dict[str, float], *, multiplier: float = 1.0) -> None:
        for name, module in model.named_modules():
            if isinstance(module, LoRALinear) and name in scaling:
                module.scaling = float(scaling[name]) * float(multiplier)

    def _compute_energy_with_pred_tensors(
        self,
        *,
        pipe: Any,
        pair: dict[str, Any],
        batch: dict[str, Any],
        out_dir: str | Path,
        device: str,
        dtype: str,
        num_frames: int,
        resolution: str,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        tensors = batch["tensors"]
        condition = self._build_forward_condition(
            pair=pair,
            pipe=pipe,
            latent_shape=list(tensors["winner_latent"].shape),
            out_dir=out_dir,
            num_frames=num_frames,
            resolution=resolution,
            device=device,
            dtype=dtype,
        )
        winner_pred, winner_target, target_info = self._model_forward_once(
            pipe=pipe,
            x0=tensors["winner_latent"],
            noise=tensors["winner_noise"],
            timestep=tensors["winner_timestep"],
            forward_condition=condition,
        )
        loser_pred, loser_target, _ = self._model_forward_once(
            pipe=pipe,
            x0=tensors["loser_latent"],
            noise=tensors["loser_noise"],
            timestep=tensors["loser_timestep"],
            forward_condition=condition,
        )
        e_winner = torch.mean((winner_pred.float() - winner_target.float()) ** 2)
        e_loser = torch.mean((loser_pred.float() - loser_target.float()) ** 2)
        return {
            "batch_summary": batch["summary"],
            "condition_summary": condition["summary"],
            "target_info": target_info,
            "E_winner": float(e_winner.detach().cpu().item()),
            "E_loser": float(e_loser.detach().cpu().item()),
            "Delta_loser_minus_winner": float((e_loser - e_winner).detach().cpu().item()),
            "winner_pred": _tensor_summary(winner_pred),
            "loser_pred": _tensor_summary(loser_pred),
            "winner_target": _tensor_summary(winner_target),
            "loser_target": _tensor_summary(loser_target),
            "finite_check": {
                "winner": bool(torch.isfinite(e_winner.detach()).item()),
                "loser": bool(torch.isfinite(e_loser.detach()).item()),
            },
            "_winner_pred_tensor": winner_pred.detach().float().cpu(),
            "_loser_pred_tensor": loser_pred.detach().float().cpu(),
        }

    def _strip_internal_tensors(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in payload.items() if not k.startswith("_")}

    def lora_functional_influence_probe(
        self,
        *,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        beta: float = 0.1,
        device: str = "cuda",
        dtype: str = "bf16",
        num_frames: int = 8,
        resolution: str = "480x832",
        trainable_scope: str = "camera_control_lora_tiny",
        max_trainable_params: int = 1_000_000,
        lora_rank: int = 2,
        lora_alpha: float = 4.0,
        target_modules: str = "auto",
        fixed_noise_seed: int | None = 123,
        fixed_timestep: int | None = 579,
        no_backward: bool = True,
        no_optimizer: bool = True,
        no_save_lora: bool = True,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        if not no_backward or not no_optimizer or not no_save_lora:
            raise RuntimeError("functional influence probe requires no backward/optimizer/LoRA save")
        if trainable_scope != "camera_control_lora_tiny":
            raise RuntimeError("functional influence probe is only allowed for camera_control_lora_tiny")

        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result: dict[str, Any] = {
            "success": False,
            "mode": "lora_functional_influence_probe",
            "beta": float(beta),
            "fixed_noise_seed": int(fixed_noise_seed) if fixed_noise_seed is not None else None,
            "fixed_timestep": int(fixed_timestep) if fixed_timestep is not None else None,
            "no_backward": True,
            "no_optimizer": True,
            "no_save_lora": True,
            "training_allowed": False,
            "variants": [],
        }

        def _pred_diff(row: dict[str, Any], baseline: dict[str, Any] | None) -> dict[str, Any] | None:
            if baseline is None:
                return None
            winner_diff = row["_winner_pred_tensor"] - baseline["_winner_pred_tensor"]
            loser_diff = row["_loser_pred_tensor"] - baseline["_loser_pred_tensor"]
            return {
                "winner_l2": float(torch.linalg.vector_norm(winner_diff).item()),
                "winner_mean_abs": float(winner_diff.abs().mean().item()),
                "winner_max_abs": float(winner_diff.abs().max().item()),
                "loser_l2": float(torch.linalg.vector_norm(loser_diff).item()),
                "loser_mean_abs": float(loser_diff.abs().mean().item()),
                "loser_max_abs": float(loser_diff.abs().max().item()),
            }

        try:
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
            lora_load = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
            pipe = lora_load.pop("object", None)
            model = getattr(pipe, "model", None)
            if model is None:
                raise RuntimeError("policy pipeline has no .model")
            model.eval()
            resolved = self._resolve_lora_targets(
                model,
                target_modules=target_modules,
                lora_scope=trainable_scope,
                rank=int(lora_rank),
                max_lora_params=int(max_trainable_params),
            )
            injections = inject_lora_into_modules(model, resolved["target_modules"], rank=int(lora_rank), alpha=float(lora_alpha))
            freeze_non_lora_parameters(model)
            trainable = self._select_trainable_params(model, scope=trainable_scope, max_trainable_params=max_trainable_params)
            lora_snapshot = self._snapshot_selected_params(model, trainable["selected_names"])
            scaling_snapshot = self._lora_scaling_snapshot(model)
            # Build one deterministic step after the single policy load. The
            # "no_lora" variant below is represented by scaling all injected
            # LoRA modules to zero, which is functionally equivalent for these
            # frozen base Linear layers and avoids multiple expensive shard
            # loads just for this no-backward probe.
            base_batch = self._load_batch_tensors(batch_dir, device=device, dtype=dtype)
            num_train_timesteps = int(getattr(pipe, "num_train_timesteps", 1000) or 1000)
            step_batch = self._make_step_batch_override(
                base_batch,
                step_index=0,
                resample_noise=False,
                resample_timestep=False,
                num_train_timesteps=num_train_timesteps,
                fixed_noise_seed=fixed_noise_seed,
                fixed_timestep=fixed_timestep,
            )
            baseline_row: dict[str, Any] | None = None

            def _record_variant(name: str, scaling_multiplier: float, *, zero_lora: bool = False) -> None:
                nonlocal baseline_row
                self._restore_params_from_snapshot(model, lora_snapshot)
                self._set_lora_scaling(model, scaling_snapshot, multiplier=scaling_multiplier)
                if zero_lora:
                    for param_name, param in model.named_parameters():
                        if "lora_" in param_name:
                            param.data.zero_()
                energy = self._compute_energy_with_pred_tensors(
                    pipe=pipe,
                    pair=pair,
                    batch=step_batch,
                    out_dir=out / name,
                    device=device,
                    dtype=dtype,
                    num_frames=num_frames,
                    resolution=resolution,
                )
                result["variants"].append(
                    {
                        "variant": name,
                        "scaling_multiplier": float(scaling_multiplier),
                        "zero_lora": bool(zero_lora),
                        "energy": self._strip_internal_tensors(energy),
                        "prediction_diff_vs_no_lora": _pred_diff(energy, baseline_row),
                        "delta_energy_vs_no_lora": {
                            "winner": float(energy["E_winner"] - baseline_row["E_winner"]),
                            "loser": float(energy["E_loser"] - baseline_row["E_loser"]),
                            "delta": float(energy["Delta_loser_minus_winner"] - baseline_row["Delta_loser_minus_winner"]),
                        } if baseline_row is not None else {"winner": 0.0, "loser": 0.0, "delta": 0.0},
                    }
                )
                if baseline_row is None:
                    baseline_row = energy

            _record_variant("no_lora", 0.0, zero_lora=False)
            _record_variant("lora_zero", 1.0, zero_lora=True)
            _record_variant("lora_default", 1.0, zero_lora=False)
            _record_variant("lora_scaled_10x", 10.0, zero_lora=False)
            _record_variant("lora_scaled_100x", 100.0, zero_lora=False)
            self._restore_params_from_snapshot(model, lora_snapshot)
            self._set_lora_scaling(model, scaling_snapshot, multiplier=1.0)

            default_row = next((row for row in result["variants"] if row["variant"] == "lora_default"), None)
            scaled_10 = next((row for row in result["variants"] if row["variant"] == "lora_scaled_10x"), None)
            scaled_100 = next((row for row in result["variants"] if row["variant"] == "lora_scaled_100x"), None)
            default_delta = abs(float((default_row or {}).get("delta_energy_vs_no_lora", {}).get("delta", 0.0)))
            scaled_delta = max(
                abs(float((scaled_10 or {}).get("delta_energy_vs_no_lora", {}).get("delta", 0.0))),
                abs(float((scaled_100 or {}).get("delta_energy_vs_no_lora", {}).get("delta", 0.0))),
            )
            result.update(
                {
                    "success": bool(all((row.get("energy") or {}).get("finite_check", {}).get("winner", False) for row in result["variants"])),
                    "lora_injection": {
                        "scope": trainable_scope,
                        "target_modules": resolved["target_modules"],
                        "rank": int(lora_rank),
                        "alpha": float(lora_alpha),
                        "injections": [inj.__dict__ for inj in injections],
                        "lora_param_count": count_lora_parameters(model),
                    },
                    "trainable_scope": trainable,
                    "default_delta_abs": default_delta,
                    "scaled_delta_abs_max": scaled_delta,
                    "forward_path_active": bool(scaled_delta > 0.0),
                    "normal_scale_signal_strong": bool(default_delta > 1e-7),
                    "interpretation": (
                        "scaled LoRA changes energy, so target modules are active; default contribution remains tiny"
                        if scaled_delta > 0.0 and default_delta <= 1e-7
                        else "LoRA changes energy at default scale"
                        if default_delta > 1e-7
                        else "LoRA did not measurably change energy in this probe"
                    ),
                    "memory": _gpu_memory(),
                }
            )
            del model
            del pipe
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "lora_functional_influence_probe_failed", "memory": _gpu_memory()})
        write_json(_jsonable(result), out / "summary.json")
        return result

    def compute_dpo_lr_sensitivity_sweep(
        self,
        *,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        learning_rates: list[float],
        steps_per_lr: int = 10,
        beta: float = 0.1,
        device: str = "cuda",
        dtype: str = "bf16",
        num_frames: int = 8,
        resolution: str = "480x832",
        trainable_scope: str = "camera_control_lora_tiny",
        max_trainable_params: int = 1_000_000,
        lora_rank: int = 2,
        lora_alpha: float = 4.0,
        target_modules: str = "auto",
        fixed_noise_seed: int | None = 123,
        fixed_timestep: int | None = 579,
        max_grad_norm: float = 1.0,
        no_save_lora: bool = True,
        no_checkpoint: bool = True,
        restore_after_each_lr: bool = True,
    ) -> dict[str, Any]:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result: dict[str, Any] = {
            "success": False,
            "mode": "dpo_lr_sensitivity_sweep",
            "learning_rates_requested": [float(x) for x in learning_rates],
            "steps_per_lr": int(steps_per_lr),
            "beta": float(beta),
            "fixed_noise_seed": int(fixed_noise_seed) if fixed_noise_seed is not None else None,
            "fixed_timestep": int(fixed_timestep) if fixed_timestep is not None else None,
            "no_save_lora": True,
            "no_checkpoint": True,
            "training_allowed": False,
            "lr_results": [],
        }
        stop_higher = False
        for lr in [float(x) for x in learning_rates]:
            if stop_higher:
                result["lr_results"].append({"learning_rate": lr, "status": "skipped", "skipped_reason": "previous_lr_failed_or_unstable"})
                continue
            steps = min(int(steps_per_lr), 5) if lr >= 5e-4 else int(steps_per_lr)
            lr_dir = out / f"lr_{lr:.0e}".replace("+", "")
            loop = self.compute_dpo_1pair_overfit_miniloop(
                pair=pair,
                batch_dir=batch_dir,
                out_dir=lr_dir,
                beta=beta,
                device=device,
                dtype=dtype,
                num_frames=num_frames,
                resolution=resolution,
                trainable_scope=trainable_scope,
                max_trainable_params=max_trainable_params,
                lora_rank=lora_rank,
                lora_alpha=lora_alpha,
                target_modules=target_modules,
                learning_rate=lr,
                optimizer_name="adamw",
                max_grad_norm=max_grad_norm,
                num_steps=steps,
                resample_noise_each_step=False,
                resample_timestep_each_step=False,
                fixed_noise_seed=fixed_noise_seed,
                fixed_timestep=fixed_timestep,
                no_save_lora=no_save_lora,
                no_checkpoint=no_checkpoint,
                restore_after_loop=restore_after_each_lr,
                log_every_step=True,
                command=["dpo_lr_sensitivity_sweep", f"lr={lr}"],
            )
            row = {
                "learning_rate": lr,
                "steps_requested": steps,
                "status": "passed" if loop.get("success") else ("oom" if "out of memory" in str(loop.get("error", "")).lower() else "failed"),
                "success": bool(loop.get("success")),
                "loss_first": loop.get("loss_first"),
                "loss_last": loop.get("loss_last"),
                "loss_delta": loop.get("loss_delta_last_minus_first"),
                "loss_min": loop.get("loss_min"),
                "loss_max": loop.get("loss_max"),
                "delta_policy_first": (loop.get("delta_policy_values") or [None])[0],
                "delta_policy_last": (loop.get("delta_policy_values") or [None])[-1],
                "delta_policy_delta": loop.get("delta_policy_delta_last_minus_first"),
                "lora_max_diff": (loop.get("lora_param_diff") or {}).get("max_abs_diff"),
                "grad_norm_first": ((loop.get("per_step_metrics") or [{}])[0]).get("grad_norm_after_clip"),
                "grad_norm_last": ((loop.get("per_step_metrics") or [{}])[-1]).get("grad_norm_after_clip"),
                "any_nan_inf": not (loop.get("parameter_safety") or {}).get("no_nan_inf_grad", False),
                "oom": "out of memory" in str(loop.get("error", "")).lower(),
                "memory": loop.get("memory"),
                "summary_path": str(lr_dir / "summary.json"),
            }
            result["lr_results"].append(row)
            if row["status"] in {"failed", "oom"} or row["any_nan_inf"]:
                stop_higher = True
        passed = [row for row in result["lr_results"] if row.get("status") == "passed"]
        stable = [row for row in passed if not row.get("any_nan_inf")]
        strongest = None
        if stable:
            strongest = max(stable, key=lambda row: abs(float(row.get("delta_policy_delta") or 0.0)))
        result.update(
            {
                "success": bool(stable),
                "passed_learning_rates": [row["learning_rate"] for row in passed],
                "recommended_lr": strongest.get("learning_rate") if strongest else None,
                "recommendation_reason": (
                    "Use the stable lr with the largest fixed-noise Delta_policy movement for the next tiny smoke."
                    if strongest
                    else "No stable lr produced a usable signal."
                ),
            }
        )
        write_json(_jsonable(result), out / "lr_sensitivity_summary.json")
        return result

    def compute_dpo_scope_sensitivity_sweep(
        self,
        *,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        scope_names: list[str],
        learning_rate: float = 1e-4,
        num_steps: int = 5,
        beta: float = 0.1,
        device: str = "cuda",
        dtype: str = "bf16",
        num_frames: int = 8,
        resolution: str = "480x832",
        max_trainable_params: int = 1_000_000,
        lora_rank: int = 2,
        lora_alpha: float = 4.0,
        fixed_noise_seed: int | None = 123,
        fixed_timestep: int | None = 579,
        max_grad_norm: float = 1.0,
        no_save_lora: bool = True,
        no_checkpoint: bool = True,
        restore_after_each_scope: bool = True,
    ) -> dict[str, Any]:
        scope_targets = {
            "current": "blocks.39.cam_shift_layer,blocks.39.cam_scale_layer",
            "last2_blocks_camera": "blocks.38.cam_shift_layer,blocks.38.cam_scale_layer,blocks.39.cam_shift_layer,blocks.39.cam_scale_layer",
            "last4_blocks_camera": ",".join(
                f"blocks.{idx}.{name}"
                for idx in range(36, 40)
                for name in ("cam_shift_layer", "cam_scale_layer")
            ),
        }
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result: dict[str, Any] = {
            "success": False,
            "mode": "dpo_scope_sensitivity_sweep",
            "scope_names_requested": list(scope_names),
            "learning_rate": float(learning_rate),
            "num_steps": int(num_steps),
            "beta": float(beta),
            "fixed_noise_seed": int(fixed_noise_seed) if fixed_noise_seed is not None else None,
            "fixed_timestep": int(fixed_timestep) if fixed_timestep is not None else None,
            "no_save_lora": True,
            "no_checkpoint": True,
            "training_allowed": False,
            "scope_results": [],
        }
        stop_broader = False
        for scope_name in scope_names:
            if stop_broader:
                result["scope_results"].append({"scope_name": scope_name, "status": "skipped", "skipped_reason": "previous_broader_scope_failed_or_oom"})
                continue
            target_modules = scope_targets.get(scope_name)
            if not target_modules:
                result["scope_results"].append({"scope_name": scope_name, "status": "skipped", "skipped_reason": "unknown scope"})
                continue
            target_count = len([x for x in target_modules.split(",") if x])
            estimated_lora_params = target_count * int(lora_rank) * (5120 + 5120)
            if estimated_lora_params > int(max_trainable_params):
                result["scope_results"].append(
                    {
                        "scope_name": scope_name,
                        "status": "skipped",
                        "skipped_reason": "estimated LoRA params exceed max_trainable_params",
                        "estimated_lora_params": estimated_lora_params,
                    }
                )
                continue
            scope_dir = out / scope_name
            loop = self.compute_dpo_1pair_overfit_miniloop(
                pair=pair,
                batch_dir=batch_dir,
                out_dir=scope_dir,
                beta=beta,
                device=device,
                dtype=dtype,
                num_frames=num_frames,
                resolution=resolution,
                trainable_scope="camera_control_lora_tiny",
                max_trainable_params=max_trainable_params,
                lora_rank=lora_rank,
                lora_alpha=lora_alpha,
                target_modules=target_modules,
                learning_rate=learning_rate,
                optimizer_name="adamw",
                max_grad_norm=max_grad_norm,
                num_steps=num_steps,
                resample_noise_each_step=False,
                resample_timestep_each_step=False,
                fixed_noise_seed=fixed_noise_seed,
                fixed_timestep=fixed_timestep,
                no_save_lora=no_save_lora,
                no_checkpoint=no_checkpoint,
                restore_after_loop=restore_after_each_scope,
                log_every_step=True,
                command=["dpo_scope_sensitivity_sweep", f"scope={scope_name}"],
            )
            row = {
                "scope_name": scope_name,
                "target_modules": target_modules.split(","),
                "target_module_count": target_count,
                "estimated_lora_params": estimated_lora_params,
                "status": "passed" if loop.get("success") else ("oom" if "out of memory" in str(loop.get("error", "")).lower() else "failed"),
                "success": bool(loop.get("success")),
                "loss_first": loop.get("loss_first"),
                "loss_last": loop.get("loss_last"),
                "loss_delta": loop.get("loss_delta_last_minus_first"),
                "delta_policy_delta": loop.get("delta_policy_delta_last_minus_first"),
                "lora_max_diff": (loop.get("lora_param_diff") or {}).get("max_abs_diff"),
                "memory": loop.get("memory"),
                "summary_path": str(scope_dir / "summary.json"),
            }
            result["scope_results"].append(row)
            if row["status"] == "oom":
                stop_broader = True
        passed = [row for row in result["scope_results"] if row.get("status") == "passed"]
        best = None
        if passed:
            best = max(passed, key=lambda row: abs(float(row.get("delta_policy_delta") or 0.0)))
        result.update(
            {
                "success": bool(passed),
                "passed_scopes": [row["scope_name"] for row in passed],
                "recommended_scope": best.get("scope_name") if best else None,
                "recommendation_reason": (
                    "Use the passed scope with the largest fixed-noise Delta_policy movement."
                    if best
                    else "No broader scope produced a safe signal."
                ),
            }
        )
        write_json(_jsonable(result), out / "scope_sensitivity_summary.json")
        return result

    def compute_dpo_backward_scope_sweep(
        self,
        *,
        pair: dict[str, Any],
        batch_dir: str | Path,
        out_dir: str | Path,
        scopes: list[str],
        beta: float = 0.1,
        device: str = "cuda",
        dtype: str = "bf16",
        num_frames: int = 8,
        resolution: str = "480x832",
        max_trainable_params: int = 5_000_000,
        no_optimizer: bool = True,
        no_step: bool = True,
        save_grad_summary: bool = True,
    ) -> dict[str, Any]:
        import torch  # type: ignore

        if not no_optimizer or not no_step:
            raise RuntimeError("scope sweep requires --no_optimizer true and --no_step true")
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result: dict[str, Any] = {
            "success": False,
            "mode": "dpo_backward_scope_sweep",
            "beta": float(beta),
            "scopes_requested": list(scopes),
            "max_trainable_params": int(max_trainable_params),
            "no_optimizer": True,
            "no_step": True,
            "no_checkpoint": True,
            "no_lora_save": True,
            "training_allowed": False,
            "scope_results": [],
        }

        ref_load: dict[str, Any] = {}
        ref_energy: dict[str, Any] | None = None
        reference_params_with_grad = 0
        try:
            with torch.no_grad():
                ref_load = self.load_reference_model(device=device, dtype=dtype, defer=False)
                ref_pipe = ref_load.pop("object", None)
                ref_energy = self._compute_energy_with_pipe(
                    pipe=ref_pipe,
                    pair=pair,
                    batch_dir=batch_dir,
                    out_dir=out / "reference",
                    device=device,
                    dtype=dtype,
                    num_frames=num_frames,
                    resolution=resolution,
                )
                ref_model = getattr(ref_pipe, "model", None)
                if ref_model is not None:
                    reference_params_with_grad = sum(1 for p in ref_model.parameters() if p.grad is not None)
                del ref_model
            del ref_pipe
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "reference_energy_failed_before_scope_sweep", "memory": _gpu_memory()})
            write_json(_jsonable(result), out / "scope_sweep_summary.json")
            return result

        policy_load: dict[str, Any] = {}
        pipe = None
        model = None
        try:
            policy_load = self.load_policy_model(device=device, dtype=dtype, dry_run=False)
            pipe = policy_load.pop("object", None)
            model = getattr(pipe, "model", None)
            if model is None:
                raise RuntimeError("policy pipeline has no .model")
            model.eval()
        except Exception as exc:
            result.update({"success": False, "error": repr(exc), "error_type": "policy_load_failed_before_scope_sweep", "memory": _gpu_memory()})
            write_json(_jsonable(result), out / "scope_sweep_summary.json")
            return result

        for scope in scopes:
            scope_dir = out / scope
            scope_dir.mkdir(parents=True, exist_ok=True)
            scope_result: dict[str, Any] = {
                "scope": scope,
                "status": "failed",
                "success": False,
                "camera_related": _scope_is_camera_related(scope),
                "no_optimizer": True,
                "no_step": True,
                "no_checkpoint": True,
                "reference_params_with_grad": reference_params_with_grad,
            }
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                trainable = self._select_trainable_params(model, scope=scope, max_trainable_params=max_trainable_params)
                if trainable["trainable_param_count"] <= 0:
                    scope_result.update(
                        {
                            "status": "skipped",
                            "success": False,
                            "skipped_reason": trainable.get("skipped_reason") or "no trainable parameters selected",
                            "trainable_scope": trainable,
                            "policy_load": policy_load,
                            "memory": _gpu_memory(),
                        }
                    )
                    write_json(_jsonable(scope_result), scope_dir / "grad_summary.json")
                    result["scope_results"].append(scope_result)
                    continue
                before = self._snapshot_selected_params(model, trainable["selected_names"])
                policy_energy = self._compute_energy_tensors_with_pipe(
                    pipe=pipe,
                    pair=pair,
                    batch_dir=batch_dir,
                    out_dir=scope_dir / "policy",
                    device=device,
                    dtype=dtype,
                    num_frames=num_frames,
                    resolution=resolution,
                    enable_grad=True,
                )
                e_policy_w = policy_energy["E_winner_tensor"]
                e_policy_l = policy_energy["E_loser_tensor"]
                e_ref_w = float(ref_energy["E_winner"]) if ref_energy is not None else math.nan
                e_ref_l = float(ref_energy["E_loser"]) if ref_energy is not None else math.nan
                delta_policy = e_policy_l - e_policy_w
                delta_ref_value = e_ref_l - e_ref_w
                delta_ref = torch.tensor(delta_ref_value, device=delta_policy.device, dtype=torch.float32)
                loss = -torch.nn.functional.logsigmoid(torch.tensor(float(beta), device=delta_policy.device, dtype=torch.float32) * (delta_policy.float() - delta_ref))
                loss.backward()
                grad_summary = self._grad_summary(model, before)
                for param in model.parameters():
                    if param.grad is not None:
                        param.grad = None
                passed = bool(torch.isfinite(loss.detach()).item()) and grad_summary["params_with_grad"] > 0 and not grad_summary["any_nan_grad"] and not grad_summary["any_inf_grad"]
                scope_result.update(
                    {
                        "status": "passed" if passed else "failed",
                        "success": passed,
                        "loss": float(loss.detach().cpu().item()),
                        "loss_finite": bool(torch.isfinite(loss.detach()).item()),
                        "E_policy_winner": float(e_policy_w.detach().cpu().item()),
                        "E_policy_loser": float(e_policy_l.detach().cpu().item()),
                        "E_ref_winner": e_ref_w,
                        "E_ref_loser": e_ref_l,
                        "Delta_policy": float(delta_policy.detach().cpu().item()),
                        "Delta_ref": float(delta_ref_value),
                        "dpo_argument": float((float(beta) * (delta_policy.detach().cpu().float() - torch.tensor(delta_ref_value))).item()),
                        "policy_energy": {k: v for k, v in policy_energy.items() if not k.endswith("_tensor")},
                        "reference_energy": ref_energy,
                        "policy_load": policy_load,
                        "reference_load": ref_load,
                        "reference_frozen_confirmed": (ref_load.get("model_param_summary_after_freeze") or {}).get("requires_grad_count") == 0,
                        "reference_no_grad_confirmed": True,
                        "trainable_scope": trainable,
                        "trainable_param_count": trainable["trainable_param_count"],
                        "params_with_grad": grad_summary["params_with_grad"],
                        "grad_norm_mean": grad_summary["grad_norm_mean"],
                        "grad_norm_max": grad_summary["grad_norm_max"],
                        "any_nan_grad": grad_summary["any_nan_grad"],
                        "any_inf_grad": grad_summary["any_inf_grad"],
                        "param_update_check": grad_summary["policy_params_changed_check"],
                        "grad_summary": grad_summary,
                        "peak_memory": _gpu_memory(),
                        "no_optimizer_confirmed": True,
                        "no_step_confirmed": True,
                        "no_param_update_confirmed": bool(grad_summary["policy_params_changed_check"]["passed"]),
                    }
                )
            except Exception as exc:
                error = repr(exc)
                status = "oom" if "out of memory" in error.lower() or "cuda oom" in error.lower() else "failed"
                scope_result.update({"status": status, "success": False, "error": error, "error_type": f"scope_{status}", "memory": _gpu_memory()})
            finally:
                try:
                    if model is not None:
                        for param in model.parameters():
                            if param.grad is not None:
                                param.grad = None
                except Exception:
                    pass
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            if save_grad_summary:
                write_json(_jsonable(scope_result), scope_dir / "grad_summary.json")
            result["scope_results"].append(scope_result)

        try:
            for param in model.parameters():
                param.requires_grad_(False)
                if param.grad is not None:
                    param.grad = None
        except Exception:
            pass
        del model
        del pipe
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        passed_scopes = [row["scope"] for row in result["scope_results"] if row.get("status") == "passed"]
        meaningful_passed = [
            row["scope"]
            for row in result["scope_results"]
            if row.get("status") == "passed" and row.get("camera_related")
        ]
        result.update(
            {
                "success": bool(passed_scopes),
                "passed_scopes": passed_scopes,
                "meaningful_camera_scopes_passed": meaningful_passed,
                "recommended_next_scope": meaningful_passed[0] if meaningful_passed else (passed_scopes[0] if passed_scopes else None),
                "recommendation_reason": (
                    "Use the first passed camera-related scope for any future user-approved 1-pair optimizer-step dry-run."
                    if meaningful_passed
                    else "No camera-related scope passed; do not proceed beyond plumbing scopes."
                ),
                "final_memory": _gpu_memory(),
            }
        )
        write_json(_jsonable(result), out / "scope_sweep_summary.json")
        return result

    def sample_same_noise_timestep(self, *args, **kwargs):
        raise NotImplementedError("Use collate_winner_loser_batch for tensor-level dry-run. Scheduler-specific timestep sampling is not wired.")

    def save_lora_adapter(self, *args, **kwargs):
        raise NotImplementedError("LoRA save path belongs to the future training adapter.")

    def load_lora_adapter(self, *args, **kwargs):
        raise NotImplementedError("LoRA load path belongs to the future training adapter.")

    def status(self) -> dict[str, Any]:
        fast = inspect_checkpoint(self.paths["lingbot_fast"], label="LingBot-Fast")
        base = inspect_checkpoint(self.paths["lingbot_base"], label="LingBot-Base")
        methods = [
            AdapterStatus("load_policy_model", True, "wan.WanI2VFast + runtime symlink bundle", "paths/config", "frozen eval policy model", True, True, False, "real LingBot-Fast runtime load; no optimizer/backward"),
            AdapterStatus("load_reference_model", True, "same as load_policy_model", "paths/config", "deferred frozen ref status", True, True, False, "explicitly deferred for 1-pair energy dry-run to avoid duplicate model memory"),
            AdapterStatus("load_vae", True, "LingBot/Wan VAE", "paths/config", "VAE object + metadata", False, False, False, "real VAE class is dynamically loaded from wan.modules.vae2_1/vae2_2"),
            AdapterStatus("encode_video_to_latent", True, "LingBot Wan VAE", "mp4/video tensor", "latent tensor", False, False, False, "real VAE encode is attempted; no fake latent"),
            AdapterStatus("encode_condition", True, "cam-only sample files + LingBot cam utils", "sample/pair condition", "condition summary + camera control shape", True, True, True, "text embedding deferred; Plucker/control tensor smoke attempted"),
            AdapterStatus("collate_winner_loser_batch", True, "VideoGPA pair JSON + LingBot latents", "pair dict + latent files", "batch summary", True, True, True, "same-noise/same-timestep tensor dry-run"),
            AdapterStatus("sample_same_noise_timestep", True, "LingBot flow target contract", "batch size + latent shape", "same tensor noise + timestep", False, False, False, "implemented inside collate_winner_loser_batch"),
            AdapterStatus("model_forward_probe", True, "LingBot Fast WanModelFast.forward", "winner/loser latent + condition", "velocity prediction tensor", True, True, False, "no target/loss in this mode"),
            AdapterStatus("compute_dpo_energy_or_logprob", True, "LingBot flow target noise-x0", "winner/loser latents + condition", "finite policy energies if forward passes", True, True, False, "no DPO loss/backward/optimizer; reference deferred"),
            AdapterStatus("compute_reference_energy", True, "same frozen LingBot-Fast checkpoint", "winner/loser latents + condition", "finite reference energies if forward passes", True, True, False, "sequential no_grad reference dry-run; not LingBot-Base"),
            AdapterStatus("compute_dpo_scalar_loss_dryrun", True, "policy/reference energy summaries", "finite energies", "scalar loss", False, False, False, "no backward/optimizer; formula smoke only"),
            AdapterStatus("list_trainable_candidates", True, "frozen LingBot-Fast model parameters", "model", "candidate param report", True, False, False, "reports LoRA/camera/tiny scopes; no backward/optimizer"),
            AdapterStatus("compute_dpo_backward_only_dryrun", True, "LingBot flow target + frozen reference", "1-pair batch", "loss + gradient summary", True, True, False, "calls backward only; no optimizer, no step, no save"),
            AdapterStatus("list_camera_trainable_scopes", True, "frozen LingBot-Fast model parameters", "model modules", "camera/control scope inventory", True, False, False, "reports camera/plucker/action scopes and memory risk; no backward/optimizer"),
            AdapterStatus("inspect_lora_targets", True, "frozen LingBot-Fast model modules", "model Linear modules", "LoRA target recommendation", True, False, False, "no backward/optimizer; ranks and params are estimated only"),
            AdapterStatus("inject_lora_dryrun", True, "runtime LoRALinear wrapper", "policy model", "LoRA trainable param summary", True, False, False, "runtime-only injection; no optimizer, no step, no save"),
            AdapterStatus("compute_dpo_backward_scope_sweep", True, "LingBot flow target + frozen reference", "1-pair batch + scope list", "per-scope backward matrix", True, True, False, "calls backward scope-by-scope only; no optimizer, no step, no save"),
            AdapterStatus("compute_dpo_optimizer_step_dryrun", True, "runtime LoRA + AdamW", "1-pair batch + LoRA params", "single-step safety summary", True, True, False, "exactly one optimizer.step on LoRA params only; no save/checkpoint"),
            AdapterStatus("compute_dpo_1pair_overfit_miniloop", True, "runtime LoRA + AdamW", "1-pair batch + LoRA params", "5-step smoke metrics", True, True, False, "bounded overfit mini-loop; no save/checkpoint and max 5 steps"),
            AdapterStatus("lora_functional_influence_probe", True, "runtime LoRA + LingBot forward", "1-pair fixed noise/timestep", "energy/pred-diff variants", True, True, False, "no backward/optimizer/save; checks whether LoRA target affects policy energy"),
            AdapterStatus("compute_dpo_lr_sensitivity_sweep", True, "runtime LoRA + AdamW", "1-pair fixed noise/timestep + lr list", "per-lr learning-signal matrix", True, True, False, "bounded diagnostic; LoRA restored after each lr and no save/checkpoint"),
            AdapterStatus("compute_dpo_scope_sensitivity_sweep", True, "runtime LoRA + AdamW", "1-pair fixed noise/timestep + scope list", "per-scope learning-signal matrix", True, True, False, "bounded diagnostic; broader camera scopes only and no save/checkpoint"),
        ]
        return {
            "paths": self.paths,
            "runtime_paths": self.runtime_paths,
            "fast": fast.to_dict(),
            "base": base.to_dict(),
            "vae_candidate": str(self._vae_path()),
            "methods": [m.to_dict() for m in methods],
            "training_allowed": False,
            "reason": "Only bounded smoke/dry-run plumbing is implemented; real DPO training remains disabled.",
        }


def _compression_summary(video_tensor: Any, latent: Any) -> dict[str, Any]:
    input_shape = list(video_tensor.shape)
    latent_shape = list(latent.shape)
    return {
        "input_shape_cthw": input_shape,
        "latent_shape": latent_shape,
        "temporal_ratio": _ratio(input_shape[1] if len(input_shape) > 1 else None, _infer_latent_dim(latent_shape, "t")),
        "height_ratio": _ratio(input_shape[2] if len(input_shape) > 2 else None, _infer_latent_dim(latent_shape, "h")),
        "width_ratio": _ratio(input_shape[3] if len(input_shape) > 3 else None, _infer_latent_dim(latent_shape, "w")),
        "note": "Ratios are inferred from tensor dimensions and should be verified against LingBot VAE source.",
    }


def _infer_latent_dim(shape: list[int], kind: str) -> int | None:
    if len(shape) == 4:
        return {"t": shape[1], "h": shape[2], "w": shape[3]}.get(kind)
    if len(shape) == 5:
        return {"t": shape[2], "h": shape[3], "w": shape[4]}.get(kind)
    return None


def _ratio(a: int | None, b: int | None) -> float | None:
    if not a or not b:
        return None
    return float(a) / float(b)


def _match_latent_shapes(winner: Any, loser: Any):
    import torch  # type: ignore

    if list(winner.shape) == list(loser.shape):
        return winner, loser, {"changed": False, "shape": list(winner.shape)}
    mins = [min(int(a), int(b)) for a, b in zip(winner.shape, loser.shape)]
    slices = tuple(slice(0, m) for m in mins)
    return winner[slices], loser[slices], {"changed": True, "winner_original": list(winner.shape), "loser_original": list(loser.shape), "matched_shape": mins}


def _inspect_forward_paths(config: str) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(config)
    root = _add_lingbot_path(adapter.paths)
    result: dict[str, Any] = {"lingbot_code_root": root, "modules": {}, "candidate_methods": []}
    for name in ["wan.image2video_fast", "wan.modules.model", "wan.modules.vae", "wan.modules.vae2_1", "wan.modules.vae2_2"]:
        try:
            module = importlib.import_module(name)
            info = {"file": getattr(module, "__file__", None), "members": []}
            for member_name, obj in inspect.getmembers(module):
                lname = member_name.lower()
                if any(token in lname for token in ["flow", "velocity", "denois", "loss", "scheduler", "forward", "timestep", "noise"]):
                    info["members"].append(member_name)
            result["modules"][name] = info
        except Exception as exc:
            result["modules"][name] = {"error": repr(exc)}
    result["status"] = "not_implemented"
    result["reason"] = "A real LingBot training forward target was not identified/wired in this adapter. compute_dpo_energy_or_logprob remains NotImplementedError."
    return result


def _write_doc(path: str | Path, title: str, payload: dict[str, Any]) -> None:
    lines = [f"# {title}", "", "```json", json.dumps(payload, indent=2, sort_keys=True), "```", ""]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _mode_load_vae(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    result = adapter.load_vae(device=args.device, dtype=args.dtype, dry_run=False)
    obj = result.pop("object", None)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_json(result, out / "vae_load_summary.json")
    return result


def _mode_encode_pair(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _normalize_pair(_load_first_pair(args.pairs))
    vae_result = adapter.load_vae(device=args.device, dtype=args.dtype, dry_run=False)
    vae = vae_result.pop("object", None)
    out = Path(args.out) / str(pair.get("pair_id"))
    out.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"pair_id": pair.get("pair_id"), "vae": vae_result, "success": False}
    if vae is None or not vae_result.get("success"):
        result["error"] = "vae_load_failed"
        write_json(result, out / "latent_encode_summary.json")
        return result
    winner = pair.get("winner") or {}
    loser = pair.get("loser") or {}
    try:
        result["winner"] = adapter.encode_video_to_latent(
            winner.get("video"),
            vae=vae,
            out_path=out / "winner_latent.pt",
            num_frames=args.num_frames,
            resolution=args.resolution,
            dtype=args.dtype,
            device=args.device,
        )
        result["loser"] = adapter.encode_video_to_latent(
            loser.get("video"),
            vae=vae,
            out_path=out / "loser_latent.pt",
            num_frames=args.num_frames,
            resolution=args.resolution,
            dtype=args.dtype,
            device=args.device,
        )
        result["camera_metadata_preserved"] = bool((pair.get("condition") or {}).get("poses") and (pair.get("condition") or {}).get("intrinsics"))
        result["success"] = True
    except Exception as exc:
        result["error"] = repr(exc)
    write_json(result, out / "latent_encode_summary.json")
    write_json({"pair_id": pair.get("pair_id"), "condition": pair.get("condition"), "metadata": pair.get("metadata")}, out / "condition_sidecar.json")
    return result


def _mode_condition(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _normalize_pair(_load_first_pair(args.pairs))
    result = adapter.encode_condition(pair, device=args.device, dtype=args.dtype, out_dir=args.out)
    return result


def _mode_batch(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _normalize_pair(_load_first_pair(args.pairs))
    return adapter.collate_winner_loser_batch(
        pair,
        latent_root=args.latents,
        out_dir=args.out,
        device=args.device,
        dtype=args.dtype,
        same_noise=_bool_arg(args.same_noise),
        same_timestep=_bool_arg(args.same_timestep),
    )


def _mode_policy_reference(args) -> dict[str, Any]:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    adapter = LingBotFastVideoGPAAdapter(args.config)
    result: dict[str, Any] = {"success": False, "no_backward": True, "no_optimizer": True}
    try:
        policy = adapter.load_policy_model(device=args.device, dtype=args.dtype, dry_run=False)
        policy.pop("object", None)
        reference = adapter.load_reference_model(device=args.device, dtype=args.dtype, defer=True)
        result.update({"success": True, "policy": policy, "reference": reference})
    except Exception as exc:
        result.update({"success": False, "error": repr(exc), "error_type": "policy_reference_load_failed", "memory": _gpu_memory()})
    write_json(_jsonable(result), out / "policy_reference_load_summary.json")
    return result


def _mode_model_forward_probe(args) -> dict[str, Any]:
    if not _bool_arg(args.no_backward) or not _bool_arg(args.no_optimizer):
        raise RuntimeError("model_forward_probe requires --no_backward true and --no_optimizer true")
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _load_pair_from_args_or_batch(args)
    return adapter.model_forward_probe(
        pair=pair,
        batch_dir=args.batch,
        out_dir=args.out,
        device=args.device,
        dtype=args.dtype,
        num_frames=args.num_frames,
        resolution=args.resolution,
    )


def _mode_energy(args) -> dict[str, Any]:
    if not _bool_arg(args.no_backward) or not _bool_arg(args.no_optimizer):
        raise RuntimeError("energy_logprob_dryrun requires --no_backward true and --no_optimizer true")
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _load_pair_from_args_or_batch(args)
    return adapter.compute_dpo_energy_or_logprob(
        pair=pair,
        batch_dir=args.batch,
        out_dir=args.out,
        device=args.device,
        dtype=args.dtype,
        num_frames=args.num_frames,
        resolution=args.resolution,
        require_real_target=_bool_arg(args.require_real_target),
    )


def _mode_reference_energy(args) -> dict[str, Any]:
    if not _bool_arg(args.no_backward) or not _bool_arg(args.no_optimizer):
        raise RuntimeError("reference_energy_dryrun requires --no_backward true and --no_optimizer true")
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _load_pair_from_args_or_batch(args)
    return adapter.compute_reference_energy(
        pair=pair,
        batch_dir=args.batch,
        out_dir=args.out,
        device=args.device,
        dtype=args.dtype,
        num_frames=args.num_frames,
        resolution=args.resolution,
        sequential_reference_if_needed=_bool_arg(args.sequential_reference_if_needed),
    )


def _mode_dpo_scalar_loss(args) -> dict[str, Any]:
    if not _bool_arg(args.no_backward) or not _bool_arg(args.no_optimizer):
        raise RuntimeError("dpo_scalar_loss_dryrun requires --no_backward true and --no_optimizer true")
    adapter = LingBotFastVideoGPAAdapter(args.config)
    return adapter.compute_dpo_scalar_loss_dryrun(
        policy_energy_dir=args.policy_energy,
        reference_energy_dir=args.reference_energy,
        out_dir=args.out,
        beta=float(args.beta),
    )


def _mode_list_trainable_candidates(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    return adapter.list_trainable_candidates(
        out_dir=args.out,
        device=args.device,
        dtype=args.dtype,
        max_trainable_params=int(args.max_trainable_params),
    )


def _mode_list_camera_trainable_scopes(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    return adapter.list_camera_trainable_scopes(
        out_dir=args.out,
        device=args.device,
        dtype=args.dtype,
        max_trainable_params=int(args.max_trainable_params),
    )


def _mode_inspect_lora_targets(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    return adapter.inspect_lora_targets(
        out_dir=args.out,
        device=args.device,
        dtype=args.dtype,
        rank_candidates=[int(x) for x in (args.rank_candidates or [2, 4])],
    )


def _mode_inject_lora_dryrun(args) -> dict[str, Any]:
    if not _bool_arg(args.no_optimizer) or not _bool_arg(args.no_step):
        raise RuntimeError("inject_lora_dryrun requires --no_optimizer true and --no_step true")
    adapter = LingBotFastVideoGPAAdapter(args.config)
    return adapter.inject_lora_dryrun(
        out_dir=args.out,
        device=args.device,
        dtype=args.dtype,
        lora_scope=args.lora_scope,
        lora_rank=int(args.lora_rank),
        lora_alpha=float(args.lora_alpha),
        target_modules=args.target_modules,
        max_lora_params=int(args.max_lora_params),
    )


def _mode_dpo_backward_only(args) -> dict[str, Any]:
    if not _bool_arg(args.no_optimizer) or not _bool_arg(args.no_step):
        raise RuntimeError("dpo_backward_only_dryrun requires --no_optimizer true and --no_step true")
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _load_pair_from_args_or_batch(args)
    return adapter.compute_dpo_backward_only_dryrun(
        pair=pair,
        batch_dir=args.batch,
        out_dir=args.out,
        beta=float(args.beta),
        device=args.device,
        dtype=args.dtype,
        num_frames=args.num_frames,
        resolution=args.resolution,
        trainable_scope=args.trainable_scope,
        max_trainable_params=int(args.max_trainable_params),
        no_optimizer=_bool_arg(args.no_optimizer),
        no_step=_bool_arg(args.no_step),
        save_grad_summary=_bool_arg(args.save_grad_summary),
        lora_rank=int(args.lora_rank),
        lora_alpha=float(args.lora_alpha),
        target_modules=args.target_modules,
    )


def _mode_dpo_backward_scope_sweep(args) -> dict[str, Any]:
    if not _bool_arg(args.no_optimizer) or not _bool_arg(args.no_step):
        raise RuntimeError("dpo_backward_scope_sweep requires --no_optimizer true and --no_step true")
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _load_pair_from_args_or_batch(args)
    return adapter.compute_dpo_backward_scope_sweep(
        pair=pair,
        batch_dir=args.batch,
        out_dir=args.out,
        scopes=list(args.scopes or []),
        beta=float(args.beta),
        device=args.device,
        dtype=args.dtype,
        num_frames=args.num_frames,
        resolution=args.resolution,
        max_trainable_params=int(args.max_trainable_params),
        no_optimizer=_bool_arg(args.no_optimizer),
        no_step=_bool_arg(args.no_step),
        save_grad_summary=_bool_arg(args.save_grad_summary),
    )


def _mode_dpo_optimizer_step(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _load_pair_from_args_or_batch(args)
    return adapter.compute_dpo_optimizer_step_dryrun(
        pair=pair,
        batch_dir=args.batch,
        out_dir=args.out,
        beta=float(args.beta),
        device=args.device,
        dtype=args.dtype,
        num_frames=args.num_frames,
        resolution=args.resolution,
        trainable_scope=args.trainable_scope,
        max_trainable_params=int(args.max_trainable_params),
        lora_rank=int(args.lora_rank),
        lora_alpha=float(args.lora_alpha),
        target_modules=args.target_modules,
        learning_rate=float(args.learning_rate),
        optimizer_name=args.optimizer,
        max_grad_norm=float(args.max_grad_norm),
        save_param_diff=_bool_arg(args.save_param_diff),
        no_save_lora=_bool_arg(args.no_save_lora),
        no_checkpoint=_bool_arg(args.no_checkpoint),
        restore_after_step=_bool_arg(args.restore_after_step),
        recompute_after_step=_bool_arg(args.recompute_after_step),
        command=sys.argv,
    )


def _mode_dpo_1pair_overfit_miniloop(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _load_pair_from_args_or_batch(args)
    return adapter.compute_dpo_1pair_overfit_miniloop(
        pair=pair,
        batch_dir=args.batch,
        out_dir=args.out,
        beta=float(args.beta),
        device=args.device,
        dtype=args.dtype,
        num_frames=args.num_frames,
        resolution=args.resolution,
        trainable_scope=args.trainable_scope,
        max_trainable_params=int(args.max_trainable_params),
        lora_rank=int(args.lora_rank),
        lora_alpha=float(args.lora_alpha),
        target_modules=args.target_modules,
        learning_rate=float(args.learning_rate),
        optimizer_name=args.optimizer,
        max_grad_norm=float(args.max_grad_norm),
        num_steps=int(args.num_steps),
        resample_noise_each_step=_bool_arg(args.resample_noise_each_step),
        resample_timestep_each_step=_bool_arg(args.resample_timestep_each_step),
        fixed_noise_seed=args.fixed_noise_seed,
        fixed_timestep=args.fixed_timestep,
        save_param_diff=_bool_arg(args.save_param_diff),
        no_save_lora=_bool_arg(args.no_save_lora),
        no_checkpoint=_bool_arg(args.no_checkpoint),
        restore_after_loop=_bool_arg(args.restore_after_loop),
        log_every_step=_bool_arg(args.log_every_step),
        command=sys.argv,
    )


def _mode_lora_functional_influence_probe(args) -> dict[str, Any]:
    if not _bool_arg(args.no_backward) or not _bool_arg(args.no_optimizer) or not _bool_arg(args.no_save_lora):
        raise RuntimeError("lora_functional_influence_probe requires no backward/optimizer/LoRA save")
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _load_pair_from_args_or_batch(args)
    return adapter.lora_functional_influence_probe(
        pair=pair,
        batch_dir=args.batch,
        out_dir=args.out,
        beta=float(args.beta),
        device=args.device,
        dtype=args.dtype,
        num_frames=args.num_frames,
        resolution=args.resolution,
        trainable_scope=args.trainable_scope,
        max_trainable_params=int(args.max_trainable_params),
        lora_rank=int(args.lora_rank),
        lora_alpha=float(args.lora_alpha),
        target_modules=args.target_modules,
        fixed_noise_seed=args.fixed_noise_seed,
        fixed_timestep=args.fixed_timestep,
        no_backward=_bool_arg(args.no_backward),
        no_optimizer=_bool_arg(args.no_optimizer),
        no_save_lora=_bool_arg(args.no_save_lora),
    )


def _mode_dpo_lr_sensitivity_sweep(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _load_pair_from_args_or_batch(args)
    return adapter.compute_dpo_lr_sensitivity_sweep(
        pair=pair,
        batch_dir=args.batch,
        out_dir=args.out,
        learning_rates=[float(x) for x in (args.learning_rates or [])],
        steps_per_lr=int(args.steps_per_lr),
        beta=float(args.beta),
        device=args.device,
        dtype=args.dtype,
        num_frames=args.num_frames,
        resolution=args.resolution,
        trainable_scope=args.trainable_scope,
        max_trainable_params=int(args.max_trainable_params),
        lora_rank=int(args.lora_rank),
        lora_alpha=float(args.lora_alpha),
        target_modules=args.target_modules,
        fixed_noise_seed=args.fixed_noise_seed,
        fixed_timestep=args.fixed_timestep,
        max_grad_norm=float(args.max_grad_norm),
        no_save_lora=_bool_arg(args.no_save_lora),
        no_checkpoint=_bool_arg(args.no_checkpoint),
        restore_after_each_lr=_bool_arg(args.restore_after_each_lr),
    )


def _mode_dpo_scope_sensitivity_sweep(args) -> dict[str, Any]:
    adapter = LingBotFastVideoGPAAdapter(args.config)
    pair = _load_pair_from_args_or_batch(args)
    return adapter.compute_dpo_scope_sensitivity_sweep(
        pair=pair,
        batch_dir=args.batch,
        out_dir=args.out,
        scope_names=list(args.scope_names or []),
        learning_rate=float(args.learning_rate),
        num_steps=int(args.num_steps),
        beta=float(args.beta),
        device=args.device,
        dtype=args.dtype,
        num_frames=args.num_frames,
        resolution=args.resolution,
        max_trainable_params=int(args.max_trainable_params),
        lora_rank=int(args.lora_rank),
        lora_alpha=float(args.lora_alpha),
        fixed_noise_seed=args.fixed_noise_seed,
        fixed_timestep=args.fixed_timestep,
        max_grad_norm=float(args.max_grad_norm),
        no_save_lora=_bool_arg(args.no_save_lora),
        no_checkpoint=_bool_arg(args.no_checkpoint),
        restore_after_each_scope=_bool_arg(args.restore_after_each_scope),
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/cam_physgeo/videogpa_adapter.yaml")
    ap.add_argument(
        "--mode",
        default="status",
        choices=[
            "status",
            "load_vae_dryrun",
            "encode_pair_latent_smoke",
            "encode_condition_smoke",
            "dpo_batch_shape_dryrun",
            "load_policy_reference_dryrun",
            "model_forward_probe",
            "energy_logprob_dryrun",
            "reference_energy_dryrun",
            "dpo_scalar_loss_dryrun",
            "list_trainable_candidates",
            "list_camera_trainable_scopes",
            "inspect_lora_targets",
            "inject_lora_dryrun",
            "dpo_backward_only_dryrun",
            "dpo_backward_scope_sweep",
            "dpo_optimizer_step_dryrun",
            "dpo_1pair_overfit_miniloop",
            "lora_functional_influence_probe",
            "dpo_lr_sensitivity_sweep",
            "dpo_scope_sensitivity_sweep",
        ],
    )
    ap.add_argument("--sample", default="")
    ap.add_argument("--pair", default="")
    ap.add_argument("--pairs", default="")
    ap.add_argument("--latents", default="")
    ap.add_argument("--batch", default="")
    ap.add_argument("--policy_energy", default="")
    ap.add_argument("--reference_energy", default="")
    ap.add_argument("--out", default="docs/lingbot_fast_videogpa_minimal_adapter_plan.md")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="bf16")
    ap.add_argument("--num_frames", type=int, default=8)
    ap.add_argument("--resolution", default="480x832")
    ap.add_argument("--limit_pairs", type=int, default=1)
    ap.add_argument("--same_noise", default="true")
    ap.add_argument("--same_timestep", default="true")
    ap.add_argument("--preserve_camera_metadata", default="true")
    ap.add_argument("--no_backward", default="true")
    ap.add_argument("--no_optimizer", default="true")
    ap.add_argument("--no_step", default="true")
    ap.add_argument("--require_real_target", default="true")
    ap.add_argument("--sequential_reference_if_needed", default="true")
    ap.add_argument("--beta", type=float, default=0.1)
    ap.add_argument("--trainable_scope", default="camera_adapter", choices=list(_TRAINABLE_SCOPES))
    ap.add_argument("--scopes", nargs="+", default=["tiny_subset", "head_only", "plucker_projection_only", "action_scale_shift_tiny", "camera_lora_tiny"])
    ap.add_argument("--max_trainable_params", type=int, default=50_000_000)
    ap.add_argument("--rank_candidates", nargs="+", type=int, default=[2, 4])
    ap.add_argument("--lora_scope", default="camera_control_lora_tiny")
    ap.add_argument("--lora_rank", type=int, default=2)
    ap.add_argument("--lora_alpha", type=float, default=4.0)
    ap.add_argument("--target_modules", default="auto")
    ap.add_argument("--max_lora_params", type=int, default=1_000_000)
    ap.add_argument("--save_grad_summary", default="true")
    ap.add_argument("--learning_rate", type=float, default=1e-5)
    ap.add_argument("--optimizer", default="adamw")
    ap.add_argument("--max_grad_norm", type=float, default=1.0)
    ap.add_argument("--save_param_diff", default="true")
    ap.add_argument("--no_save_lora", default="true")
    ap.add_argument("--no_checkpoint", default="true")
    ap.add_argument("--restore_after_step", default="true")
    ap.add_argument("--recompute_after_step", default="true")
    ap.add_argument("--num_steps", type=int, default=5)
    ap.add_argument("--steps_per_lr", type=int, default=10)
    ap.add_argument("--learning_rates", nargs="+", type=float, default=[1e-5, 5e-5, 1e-4, 5e-4])
    ap.add_argument("--scope_names", nargs="+", default=["current", "last2_blocks_camera", "last4_blocks_camera"])
    ap.add_argument("--resample_noise_each_step", default="true")
    ap.add_argument("--resample_timestep_each_step", default="true")
    ap.add_argument("--fixed_noise_seed", type=int, default=None)
    ap.add_argument("--fixed_timestep", type=int, default=None)
    ap.add_argument("--restore_after_loop", default="true")
    ap.add_argument("--restore_after_each_lr", default="true")
    ap.add_argument("--restore_after_each_scope", default="true")
    ap.add_argument("--log_every_step", default="true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if args.mode == "load_vae_dryrun":
        result = _mode_load_vae(args)
    elif args.mode == "encode_pair_latent_smoke":
        result = _mode_encode_pair(args)
    elif args.mode == "encode_condition_smoke":
        result = _mode_condition(args)
    elif args.mode == "dpo_batch_shape_dryrun":
        result = _mode_batch(args)
    elif args.mode == "load_policy_reference_dryrun":
        result = _mode_policy_reference(args)
    elif args.mode == "model_forward_probe":
        result = _mode_model_forward_probe(args)
    elif args.mode == "energy_logprob_dryrun":
        result = _mode_energy(args)
    elif args.mode == "reference_energy_dryrun":
        result = _mode_reference_energy(args)
    elif args.mode == "dpo_scalar_loss_dryrun":
        result = _mode_dpo_scalar_loss(args)
    elif args.mode == "list_trainable_candidates":
        result = _mode_list_trainable_candidates(args)
    elif args.mode == "list_camera_trainable_scopes":
        result = _mode_list_camera_trainable_scopes(args)
    elif args.mode == "inspect_lora_targets":
        result = _mode_inspect_lora_targets(args)
    elif args.mode == "inject_lora_dryrun":
        result = _mode_inject_lora_dryrun(args)
    elif args.mode == "dpo_backward_only_dryrun":
        result = _mode_dpo_backward_only(args)
    elif args.mode == "dpo_backward_scope_sweep":
        result = _mode_dpo_backward_scope_sweep(args)
    elif args.mode == "dpo_optimizer_step_dryrun":
        result = _mode_dpo_optimizer_step(args)
    elif args.mode == "dpo_1pair_overfit_miniloop":
        result = _mode_dpo_1pair_overfit_miniloop(args)
    elif args.mode == "lora_functional_influence_probe":
        result = _mode_lora_functional_influence_probe(args)
    elif args.mode == "dpo_lr_sensitivity_sweep":
        result = _mode_dpo_lr_sensitivity_sweep(args)
    elif args.mode == "dpo_scope_sensitivity_sweep":
        result = _mode_dpo_scope_sensitivity_sweep(args)
    else:
        adapter = LingBotFastVideoGPAAdapter(args.config)
        result = adapter.status()
        if args.sample:
            result["condition_dry_run"] = adapter.encode_condition(args.sample, device=args.device, dtype=args.dtype)
        if args.pair:
            result["batch_dry_run"] = adapter.collate_winner_loser_batch(_load_first_pair(args.pair), latent_root=args.latents or ".", device=args.device, dtype=args.dtype) if args.latents else adapter.prepare_winner_loser_batch(_load_first_pair(args.pair))
    if args.out and args.out.endswith(".md"):
        write_plan(result, args.out)
    print(json.dumps(_jsonable(result), indent=2, sort_keys=True))
    return 0


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items() if k != "object"}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    return value


def write_plan(status: dict[str, Any], out: str | Path) -> None:
    lines = [
        "# LingBot-Fast VideoGPA Minimal Adapter Plan",
        "",
        "This document defines the minimum adapter surface. It is not a trainer and does not fake DPO logprobs.",
        "",
        "## Method Status",
    ]
    for m in status.get("methods", []):
        lines.append(f"- `{m['name']}`: implemented={m['implemented']}; dependency={m['dependency']}; input={m['input_shape']}; output={m['output_shape']}; camera={m['supports_camera_poses']}; intrinsics={m['supports_intrinsics']}; dummy_action={m['uses_dummy_action']}; notes={m['notes']}")
    lines.extend(
        [
            "",
            "## Gate",
            f"- Training allowed: {status.get('training_allowed', False)}",
            f"- Reason: {status.get('reason', 'dry-run only')}",
            "",
            "## Contract",
            "- Winner and loser must share prompt, image condition, camera Plucker/control, timestep, and noise.",
            "- `use_action=false` remains mandatory; dummy zero action is compatibility only.",
            "- `compute_dpo_energy_or_logprob` must stay `NotImplementedError` until a real LingBot denoising/velocity forward target is wired.",
        ]
    )
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
