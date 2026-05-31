from __future__ import annotations

import argparse
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

    def load_policy_model(self):
        raise NotImplementedError("Policy loading for VideoGPA is not implemented. Reuse LingBot runtime loader only after the forward contract is known.")

    def load_reference_model(self):
        raise NotImplementedError("Frozen reference loading is not implemented. Do not start DPO before this is real.")

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

    def sample_same_noise_timestep(self, *args, **kwargs):
        raise NotImplementedError("Use collate_winner_loser_batch for tensor-level dry-run. Scheduler-specific timestep sampling is not wired.")

    def compute_dpo_energy_or_logprob(self, *args, **kwargs):
        raise NotImplementedError("No fake DPO energy/logprob. A real LingBot denoising/velocity forward target is not wired yet.")

    def save_lora_adapter(self, *args, **kwargs):
        raise NotImplementedError("LoRA save path belongs to the future training adapter.")

    def load_lora_adapter(self, *args, **kwargs):
        raise NotImplementedError("LoRA load path belongs to the future training adapter.")

    def status(self) -> dict[str, Any]:
        fast = inspect_checkpoint(self.paths["lingbot_fast"], label="LingBot-Fast")
        base = inspect_checkpoint(self.paths["lingbot_base"], label="LingBot-Base")
        methods = [
            AdapterStatus("load_policy_model", False, "wan.WanI2VFast + runtime symlink bundle", "paths/config", "policy model", True, True, False, "runtime inference exists separately; VideoGPA policy object not wired"),
            AdapterStatus("load_reference_model", False, "same as load_policy_model", "paths/config", "frozen ref model", True, True, False, "required before DPO"),
            AdapterStatus("load_vae", True, "LingBot/Wan VAE", "paths/config", "VAE object + metadata", False, False, False, "real VAE class is dynamically loaded from wan.modules.vae2_1/vae2_2"),
            AdapterStatus("encode_video_to_latent", True, "LingBot Wan VAE", "mp4/video tensor", "latent tensor", False, False, False, "real VAE encode is attempted; no fake latent"),
            AdapterStatus("encode_condition", True, "cam-only sample files + LingBot cam utils", "sample/pair condition", "condition summary + camera control shape", True, True, True, "text embedding deferred; Plucker/control tensor smoke attempted"),
            AdapterStatus("collate_winner_loser_batch", True, "VideoGPA pair JSON + LingBot latents", "pair dict + latent files", "batch summary", True, True, True, "same-noise/same-timestep tensor dry-run"),
            AdapterStatus("sample_same_noise_timestep", False, "LingBot scheduler", "batch size + latent shape", "scheduler-specific timestep", False, False, False, "generic tensor dry-run exists; scheduler-specific sampling deferred"),
            AdapterStatus("compute_dpo_energy_or_logprob", False, "LingBot forward/noise scheduler", "winner/loser latents + condition", "scalar energy/logprob delta", True, True, False, "must remain NotImplemented until real forward target is identified"),
        ]
        return {
            "paths": self.paths,
            "runtime_paths": self.runtime_paths,
            "fast": fast.to_dict(),
            "base": base.to_dict(),
            "vae_candidate": str(self._vae_path()),
            "methods": [m.to_dict() for m in methods],
            "training_allowed": False,
            "reason": "No optimizer/backward/training path is implemented.",
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


def _mode_energy(args) -> dict[str, Any]:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    inspect_result = _inspect_forward_paths(args.config)
    batch_summary = _read_json(Path(args.batch) / "batch_summary.json")
    result = {
        "status": "not_implemented",
        "energy_logprob_passed": False,
        "batch_summary_exists": bool(batch_summary),
        "forward_inspect": inspect_result,
        "no_backward": _bool_arg(args.no_backward),
        "no_optimizer": _bool_arg(args.no_optimizer),
        "error": "compute_dpo_energy_or_logprob remains NotImplementedError because a real LingBot denoising/velocity loss forward was not wired.",
    }
    write_json(result, out / "energy_logprob_summary.json")
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/cam_physgeo/videogpa_adapter.yaml")
    ap.add_argument("--mode", default="status", choices=["status", "load_vae_dryrun", "encode_pair_latent_smoke", "encode_condition_smoke", "dpo_batch_shape_dryrun", "energy_logprob_dryrun"])
    ap.add_argument("--sample", default="")
    ap.add_argument("--pair", default="")
    ap.add_argument("--pairs", default="")
    ap.add_argument("--latents", default="")
    ap.add_argument("--batch", default="")
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
    elif args.mode == "energy_logprob_dryrun":
        result = _mode_energy(args)
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
