from __future__ import annotations

import contextlib
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

import torch
import torch.nn.functional as F


def strict_future_latent_indices(
    *,
    total_frames: int,
    prefix_len: int,
    latent_frames: int,
    temporal_compression: int = 4,
) -> list[int]:
    """Return latent slots that are safe to score for future-only DPO.

    Raw prefix frame 4 and future frame 5 can share one latent slot under Wan's
    temporal compression.  To keep prefix frames out of the DPO target, this
    function drops every latent slot touched by a raw prefix frame.  For 81 raw
    frames and prefix_len=5, the scored latent slots are 2..20.
    """

    if prefix_len < 1 or prefix_len >= total_frames:
        raise ValueError(f"invalid prefix_len={prefix_len} for total_frames={total_frames}")
    if latent_frames <= 0:
        raise ValueError("latent_frames must be positive")
    if temporal_compression <= 0:
        raise ValueError("temporal_compression must be positive")
    visible_latents = min((int(prefix_len) - 1) // int(temporal_compression) + 1, int(latent_frames))
    return list(range(visible_latents, int(latent_frames)))


def _repo_src() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def _ensure_src_path() -> None:
    src = str(_repo_src())
    if src not in sys.path:
        sys.path.insert(0, src)


def _cfg_get(cfg: dict[str, Any], key: str, default: Any) -> Any:
    value = cfg.get(key, default)
    return default if value is None else value


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        if value == "":
            return ()
        return tuple(part.strip() for part in value.split(",") if part.strip())
    return tuple(str(item).strip() for item in value if str(item).strip())


def build_stage1_args(cfg: dict[str, Any]) -> SimpleNamespace:
    shared = str(_cfg_get(cfg, "shared_assets_dir", _cfg_get(cfg, "base_model_dir", "/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam")))
    rank = int(_cfg_get(cfg, "student_lora_rank", 4))
    return SimpleNamespace(
        base_model_dir=shared,
        shared_assets_dir=shared,
        fast_checkpoint_dir=str(_cfg_get(cfg, "fast_checkpoint_dir", "/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam/lingbot_world_fast")),
        stage1_ckpt_dir=shared,
        lingbot_code_dir=str(_cfg_get(cfg, "lingbot_code_dir", "/home/nvme03/workspace/lingbot-world")),
        model_family="lingbot_world_fast",
        control_type="cam",
        student_tuning_mode="lora",
        student_lora_rank=rank,
        student_lora_alpha=int(_cfg_get(cfg, "student_lora_alpha", rank)),
        student_lora_dropout=float(_cfg_get(cfg, "student_lora_dropout", 0.0)),
        student_lora_block_start=int(_cfg_get(cfg, "student_lora_block_start", 0)),
        student_lora_block_end=_cfg_get(cfg, "student_lora_block_end", None),
        student_lora_chunk_size=int(_cfg_get(cfg, "student_lora_chunk_size", 1024) or 0),
        student_lora_merge_mode=str(_cfg_get(cfg, "student_lora_merge_mode", "out_of_place")),
        student_lora_target_groups=_as_tuple(_cfg_get(cfg, "student_lora_target_groups", ["camera_conditioning"])),
        student_lora_required_groups=_as_tuple(_cfg_get(cfg, "student_lora_required_groups", ["camera_conditioning"])),
        student_lora_include_patterns=_as_tuple(_cfg_get(cfg, "student_lora_include_patterns", [])),
        student_lora_exclude_patterns=_as_tuple(_cfg_get(cfg, "student_lora_exclude_patterns", [])),
        student_memory_efficient_modulation=bool(_cfg_get(cfg, "student_memory_efficient_modulation", True)),
        student_ffn_chunk_size=int(_cfg_get(cfg, "student_ffn_chunk_size", 4096) or 0),
        student_norm_chunk_size=int(_cfg_get(cfg, "student_norm_chunk_size", 0) or 0),
        skip_runtime_components_on_load=bool(_cfg_get(cfg, "dpo_skip_runtime_components_on_load", False)),
    )


@dataclass(slots=True)
class PreparedEnergyInput:
    target: torch.Tensor
    noisy_latent: torch.Tensor
    context: list[torch.Tensor]
    y: torch.Tensor
    dit_cond: dict[str, tuple[torch.Tensor, ...]]
    seq_len: int
    latent_loss_indices: list[int]


@dataclass(slots=True)
class PairEnergyResult:
    policy_winner_energy: torch.Tensor
    policy_loser_energy: torch.Tensor
    ref_winner_energy: torch.Tensor
    ref_loser_energy: torch.Tensor
    same_noise: bool
    same_timestep: bool
    prefix_len: int
    prediction_start_frame: int
    timestep_index: int
    sigma: float
    timestep: float
    timestep_weight: float
    latent_loss_indices: list[int]
    reference_trainable_params: int
    policy_trainable_params: int


class LingBotFastDpoEnergy:
    def __init__(self, cfg: dict[str, Any], *, device: str = "cuda", prefix_len: int = 5) -> None:
        _ensure_src_path()
        from physical_consistency.trainers.stage1_components import (
            LingBotStage1Helper,
            configure_stage1_precision_env,
            resolve_stage1_low_precision_dtype,
        )

        configure_stage1_precision_env(
            str(_cfg_get(cfg, "student_precision_profile", "mixed_safe")),
            str(_cfg_get(cfg, "student_low_precision_dtype", "bf16")),
        )
        self.lowp_dtype = resolve_stage1_low_precision_dtype()
        self.device = torch.device(device)
        self.prefix_len = int(prefix_len)
        self.num_frames = int(_cfg_get(cfg, "num_frames", 81))
        self.height = int(_cfg_get(cfg, "height", 480))
        self.width = int(_cfg_get(cfg, "width", 832))
        self.temporal_compression = int(_cfg_get(cfg, "temporal_compression", 4))
        self.args = build_stage1_args(cfg)
        self.helper = LingBotStage1Helper(self.args)
        self.model = self.helper.load_model(self.device, "high_only", checkpoint_dir=self.args.shared_assets_dir, control_type="cam")
        self.model.to(self.device)
        if bool(_cfg_get(cfg, "gradient_checkpointing", True)):
            from physical_consistency.trainers.stage1_components import apply_gradient_checkpointing
            apply_gradient_checkpointing(
                self.model,
                model_name="lingbot_fast_dpo_policy",
                use_reentrant=False,
                memory_efficient_mode=str(_cfg_get(cfg, "student_memory_efficient_checkpoint_mode", "full")),
            )
        self.model.train()
        self.runtime_device = torch.device(str(_cfg_get(cfg, "dpo_runtime_device", "cpu")))
        self._move_runtime_components(self.runtime_device)
        self._trainable = [p for p in self.model.parameters() if p.requires_grad]
        if not self._trainable:
            raise RuntimeError("LingBot-Fast DPO policy has no trainable LoRA parameters")
        self.policy_trainable_params = int(sum(p.numel() for p in self._trainable))
        self.lora_inventory = self._lora_inventory()

    def _move_runtime_components(self, device: torch.device) -> None:
        """Move VAE/T5 runtime away from GPU after Fast policy load."""
        vae = getattr(self.helper, "vae", None)
        if vae is not None and device.type == "cpu":
            if hasattr(vae, "model"):
                vae.model.to(device)
            vae.device = device
            vae.mean = vae.mean.to(device)
            vae.std = vae.std.to(device)
            vae.scale = [vae.mean, 1.0 / vae.std]
        t5 = getattr(self.helper, "t5", None)
        if t5 is not None and hasattr(t5, "model") and device.type == "cpu":
            t5.model.to(device)
        if self.device.type == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _encode_video(self, video_tensor: torch.Tensor) -> torch.Tensor:
        if self.runtime_device.type == "cpu":
            with torch.no_grad():
                latent = self.helper.vae.encode([video_tensor.cpu()])[0]
            return latent.to(self.device, dtype=self.lowp_dtype)
        return self.helper.encode_video(video_tensor.to(self.device))

    def _encode_text(self, prompt: str) -> list[torch.Tensor]:
        if self.runtime_device.type == "cpu":
            if prompt in self.helper._t5_cache:
                return [tensor.to(self.device) for tensor in self.helper._t5_cache[prompt]]
            with torch.no_grad():
                context = self.helper.t5([prompt], torch.device("cpu"))
            self.helper._t5_cache[prompt] = [tensor.cpu() for tensor in context]
            return [tensor.to(self.device) for tensor in context]
        return self.helper.encode_text(prompt)

    def _prepare_y(self, video_tensor: torch.Tensor, latent: torch.Tensor) -> torch.Tensor:
        if self.runtime_device.type != "cpu":
            return self.helper.prepare_y(video_tensor.to(self.device), latent, prefix_len=self.prefix_len)
        lat_h, lat_w = int(latent.shape[2]), int(latent.shape[3])
        frame_total = int(video_tensor.shape[1])
        height, width = int(video_tensor.shape[2]), int(video_tensor.shape[3])
        prefix = video_tensor[:, : self.prefix_len].cpu()
        zeros = torch.zeros(3, frame_total - self.prefix_len, height, width, device="cpu", dtype=prefix.dtype)
        y_input = torch.cat([prefix, zeros], dim=1)
        with torch.no_grad():
            y_latent = self.helper.vae.encode([y_input])[0].to(self.device, dtype=self.lowp_dtype)
        mask = torch.zeros(4, y_latent.shape[1], lat_h, lat_w, device=self.device, dtype=y_latent.dtype)
        visible_latents = min((self.prefix_len - 1) // self.temporal_compression + 1, int(y_latent.shape[1]))
        mask[:, :visible_latents] = 1
        return torch.cat([mask, y_latent])

    def _module_for_lora(self):
        return getattr(self.model, "module", self.model)

    def _lora_modules(self) -> list[tuple[str, torch.nn.Module]]:
        return [
            (name, module)
            for name, module in self._module_for_lora().named_modules()
            if hasattr(module, "lora_A") and hasattr(module, "lora_B") and hasattr(module, "scaling")
        ]

    def _lora_inventory(self) -> dict[str, Any]:
        rows = []
        groups: dict[str, int] = {}
        for name, module in self._lora_modules():
            group = str(getattr(module, "_pc_lora_group", "unknown"))
            groups[group] = groups.get(group, 0) + 1
            rows.append({"name": name, "group": group, "rank": int(getattr(module, "rank", 0))})
        return {"count": len(rows), "groups": groups, "modules": rows[:200]}

    @contextlib.contextmanager
    def reference_mode(self) -> Iterator[None]:
        modules = self._lora_modules()
        scalings = [float(module.scaling) for _, module in modules]
        was_training = self.model.training
        try:
            for _, module in modules:
                module.scaling = 0.0
            self.model.eval()
            with torch.no_grad():
                yield
        finally:
            for (_, module), scaling in zip(modules, scalings):
                module.scaling = scaling
            self.model.train(was_training)

    def trainable_parameters(self) -> list[torch.nn.Parameter]:
        return self._trainable

    def sample_timestep_and_noise(self, latent_shape: tuple[int, ...], *, seed: int) -> tuple[Any, torch.Tensor]:
        generator = torch.Generator(device=self.device)
        generator.manual_seed(int(seed))
        timestep_sample = self.helper.sample_timestep("high_only")
        noise = torch.randn(latent_shape, device=self.device, dtype=self.lowp_dtype, generator=generator)
        return timestep_sample, noise

    def prepare(
        self,
        video: torch.Tensor,
        *,
        prompt: str,
        poses: torch.Tensor,
        intrinsics: torch.Tensor,
        source_height: int,
        source_width: int,
        timestep_sample: Any | None = None,
        noise: torch.Tensor | None = None,
    ) -> PreparedEnergyInput:
        video = video.to(self.device)
        poses = poses.to(self.device)
        intrinsics = intrinsics.to(self.device)
        height, width = int(video.shape[2]), int(video.shape[3])
        with torch.no_grad():
            latent = self._encode_video(video)
            context = self._encode_text(prompt)
            y = self._prepare_y(video, latent)
            lat_f, lat_h, lat_w = int(latent.shape[1]), int(latent.shape[2]), int(latent.shape[3])
            seq_len = lat_f * lat_h * lat_w // (self.helper.patch_size[1] * self.helper.patch_size[2])
            dit_cond = self.helper.prepare_control_signal(
                poses,
                None,
                intrinsics,
                height,
                width,
                lat_f,
                lat_h,
                lat_w,
                control_type="cam",
                source_height=int(source_height),
                source_width=int(source_width),
            )
            if timestep_sample is None or noise is None:
                timestep_sample, noise = self.sample_timestep_and_noise(tuple(latent.shape), seed=123)
            noise = noise.to(device=self.device, dtype=latent.dtype)
            noisy_latent = (1.0 - float(timestep_sample.sigma)) * latent + float(timestep_sample.sigma) * noise
            target = noise - latent
            latent_loss_indices = strict_future_latent_indices(
                total_frames=self.num_frames,
                prefix_len=self.prefix_len,
                latent_frames=lat_f,
                temporal_compression=self.temporal_compression,
            )
        return PreparedEnergyInput(
            target=target,
            noisy_latent=noisy_latent,
            context=context,
            y=y,
            dit_cond=dit_cond,
            seq_len=int(seq_len),
            latent_loss_indices=latent_loss_indices,
        )

    def energy(self, prepared: PreparedEnergyInput, timestep_sample: Any) -> torch.Tensor:
        device_type = self.device.type
        autocast_ctx = (
            torch.amp.autocast(device_type=device_type, dtype=self.lowp_dtype)
            if device_type == "cuda"
            else torch.autocast(device_type=device_type, enabled=False)
        )
        with autocast_ctx:
            pred = self.model(
                [prepared.noisy_latent],
                t=timestep_sample.timestep,
                context=prepared.context,
                seq_len=prepared.seq_len,
                y=[prepared.y],
                dit_cond_dict=prepared.dit_cond,
            )[0]
        idx = torch.as_tensor(prepared.latent_loss_indices, device=pred.device, dtype=torch.long)
        if idx.numel() <= 0:
            raise RuntimeError("empty DPO future latent loss mask")
        loss = F.mse_loss(pred.index_select(1, idx).float(), prepared.target.index_select(1, idx).float())
        return loss * float(timestep_sample.weight)

    def pair_energies(self, example, *, seed: int) -> PairEnergyResult:
        winner_video = example.winner_video.to(self.device)
        loser_video = example.loser_video.to(self.device)
        with torch.no_grad():
            winner_latent = self._encode_video(winner_video)
        timestep_sample, noise = self.sample_timestep_and_noise(tuple(winner_latent.shape), seed=seed)
        winner = self.prepare(
            winner_video,
            prompt=example.prompt,
            poses=example.poses,
            intrinsics=example.intrinsics,
            source_height=example.source_height,
            source_width=example.source_width,
            timestep_sample=timestep_sample,
            noise=noise,
        )
        loser = self.prepare(
            loser_video,
            prompt=example.prompt,
            poses=example.poses,
            intrinsics=example.intrinsics,
            source_height=example.source_height,
            source_width=example.source_width,
            timestep_sample=timestep_sample,
            noise=noise,
        )
        policy_winner = self.energy(winner, timestep_sample)
        policy_loser = self.energy(loser, timestep_sample)
        with self.reference_mode():
            ref_winner = self.energy(winner, timestep_sample).detach()
            ref_loser = self.energy(loser, timestep_sample).detach()
        finite = all(torch.isfinite(x).all().item() for x in [policy_winner, policy_loser, ref_winner, ref_loser])
        if not finite:
            raise FloatingPointError("nonfinite LingBot-Fast DPO energies")
        try:
            timestep_float = float(timestep_sample.timestep.detach().flatten()[0].item())
        except Exception:
            timestep_float = float(timestep_sample.timestep)
        return PairEnergyResult(
            policy_winner_energy=policy_winner,
            policy_loser_energy=policy_loser,
            ref_winner_energy=ref_winner,
            ref_loser_energy=ref_loser,
            same_noise=True,
            same_timestep=True,
            prefix_len=int(example.prefix_len),
            prediction_start_frame=int(example.prediction_start_frame),
            timestep_index=int(timestep_sample.index),
            sigma=float(timestep_sample.sigma),
            timestep=timestep_float,
            timestep_weight=float(timestep_sample.weight),
            latent_loss_indices=list(winner.latent_loss_indices),
            reference_trainable_params=0,
            policy_trainable_params=int(self.policy_trainable_params),
        )


def extract_lora_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    module = getattr(model, "module", model)
    return {
        key: value.detach().cpu()
        for key, value in module.state_dict().items()
        if ".lora_A.weight" in key or ".lora_B.weight" in key
    }


def load_lora_state(model: torch.nn.Module, state: dict[str, torch.Tensor]) -> None:
    module = getattr(model, "module", model)
    current = module.state_dict()
    update = {key: value.to(current[key].device, dtype=current[key].dtype) for key, value in state.items() if key in current}
    current.update(update)
    module.load_state_dict(current, strict=False)
