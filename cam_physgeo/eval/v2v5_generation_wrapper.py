"""Real prefix-aware V2V-5 generation wrapper for LingBot-Fast.

This module intentionally does not call ``WanI2VFast.generate`` directly because
that method constructs an image-only condition. The implementation mirrors the
native LingBot-Fast denoising loop while replacing the condition tensor with a
prefix-video condition: raw frames 0..4 are visible, frames 5..80 are zeroed,
and only prefix-touched latent slots are marked visible.
"""
from __future__ import annotations

import gc
import math
import random
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from einops import rearrange
from tqdm import tqdm

from cam_physgeo.eval.prefix_video_condition import (
    PrefixConditionInfo,
    prepare_prefix_condition_latent,
    validate_prefix_plan,
)


@dataclass(frozen=True)
class V2V5GenerationProof:
    prefix_len: int
    prediction_start_frame: int
    num_frames: int
    latent_frames: int
    visible_latent_indices: tuple[int, ...]
    future_frame_indices: tuple[int, ...]
    condition_mode: str
    condition_prefix_nonzero: bool
    condition_future_zero: bool
    camera_condition_present: bool


def assert_v2v5_generation_plan(*, prefix_len: int, prediction_start_frame: int, num_frames: int) -> None:
    validate_prefix_plan(prefix_len=prefix_len, prediction_start_frame=prediction_start_frame, num_frames=num_frames)


def _condition_proof(condition_video: torch.Tensor, info: PrefixConditionInfo, *, camera_condition_present: bool) -> V2V5GenerationProof:
    prefix = condition_video[:, : info.prefix_len]
    future = condition_video[:, info.prefix_len :]
    return V2V5GenerationProof(
        prefix_len=info.prefix_len,
        prediction_start_frame=info.prediction_start_frame,
        num_frames=info.num_frames,
        latent_frames=info.latent_frames,
        visible_latent_indices=info.visible_latent_indices,
        future_frame_indices=info.future_frame_indices,
        condition_mode=info.mode,
        condition_prefix_nonzero=bool(prefix.detach().float().abs().sum().item() > 0),
        condition_future_zero=bool(future.detach().float().abs().max().item() == 0.0) if future.numel() else True,
        camera_condition_present=bool(camera_condition_present),
    )


def build_prefix_y_for_pipe(
    pipe: Any,
    *,
    prefix_video: torch.Tensor,
    prefix_len: int,
    num_frames: int,
    latent_height: int,
    latent_width: int,
    resize_hw: tuple[int, int],
) -> tuple[torch.Tensor, V2V5GenerationProof]:
    y, info, condition_video = prepare_prefix_condition_latent(
        vae=pipe.vae,
        video=prefix_video,
        prefix_len=prefix_len,
        num_frames=num_frames,
        latent_height=latent_height,
        latent_width=latent_width,
        device=pipe.device,
        resize_hw=resize_hw,
    )
    return y, _condition_proof(condition_video, info, camera_condition_present=False)


@torch.no_grad()
def generate_v2v5_fast(
    pipe: Any,
    *,
    input_prompt: str,
    prefix_video: torch.Tensor,
    action_path: str | Path,
    prefix_len: int = 5,
    prediction_start_frame: int = 5,
    chunk_size: int = 3,
    max_area: int = 480 * 832,
    frame_num: int = 81,
    timesteps_index: list[int] | tuple[int, ...] = (0, 179, 358, 679),
    shift: float = 5.0,
    seed: int = -1,
    offload_model: bool = True,
    max_sequence_length: int = 512,
    max_attention_size: int | None = None,
    stop_after_first_step: bool = False,
) -> tuple[torch.Tensor | dict[str, Any] | None, V2V5GenerationProof]:
    """Generate a full video from a 5-frame prefix condition.

    ``prefix_video`` must be shaped ``[3,T,H,W]`` in [-1,1]. Evaluation callers
    should compare only future frames ``prediction_start_frame..80``.
    """

    assert_v2v5_generation_plan(prefix_len=prefix_len, prediction_start_frame=prediction_start_frame, num_frames=frame_num)
    action_path = Path(action_path)
    if not (action_path / "poses.npy").exists() or not (action_path / "intrinsics.npy").exists():
        raise FileNotFoundError(f"action_path must contain poses.npy and intrinsics.npy: {action_path}")
    if prefix_video.ndim != 4 or int(prefix_video.shape[0]) != 3:
        raise ValueError(f"prefix_video must be [3,T,H,W], got {tuple(prefix_video.shape)}")
    if int(prefix_video.shape[1]) < prefix_len:
        raise ValueError(f"prefix_video has fewer frames than prefix_len: {tuple(prefix_video.shape)} vs {prefix_len}")

    batch_size = 1
    c2ws = np.load(action_path / "poses.npy")
    len_c2ws = ((len(c2ws) - 1) // 4) * 4 + 1
    frame_num = ((frame_num - 1) // 4) * 4 + 1
    frame_num = min(frame_num, len_c2ws)
    assert_v2v5_generation_plan(prefix_len=prefix_len, prediction_start_frame=prediction_start_frame, num_frames=frame_num)
    c2ws = c2ws[:frame_num]

    condition_height = int(prefix_video.shape[2])
    condition_width = int(prefix_video.shape[3])
    F = int(frame_num)
    aspect_ratio = condition_height / condition_width
    size_eps = 1e-6
    lat_h = round((np.sqrt(max_area * aspect_ratio) + size_eps) // pipe.vae_stride[1] // pipe.patch_size[1] * pipe.patch_size[1])
    lat_w = round((np.sqrt(max_area / aspect_ratio) + size_eps) // pipe.vae_stride[2] // pipe.patch_size[2] * pipe.patch_size[2])
    h = int(lat_h * pipe.vae_stride[1])
    w = int(lat_w * pipe.vae_stride[2])
    lat_f = (F - 1) // pipe.vae_stride[0] + 1
    lat_f = int(lat_f - (lat_f % chunk_size))
    F = int((lat_f - 1) * 4 + 1)
    assert_v2v5_generation_plan(prefix_len=prefix_len, prediction_start_frame=prediction_start_frame, num_frames=F)
    max_seq_len = chunk_size * lat_h * lat_w // (pipe.patch_size[1] * pipe.patch_size[2])
    max_seq_len = int(math.ceil(max_seq_len / pipe.sp_size)) * pipe.sp_size

    seed = int(seed if seed >= 0 else random.randint(0, sys.maxsize))
    seed_g = torch.Generator(device=pipe.device)
    seed_g.manual_seed(seed)
    noise = torch.randn(16, lat_f, lat_h, lat_w, dtype=torch.float32, generator=seed_g, device=pipe.device)

    pipe.scheduler.set_timesteps(pipe.num_train_timesteps, shift=shift)
    timesteps = pipe.scheduler.timesteps[list(timesteps_index)]

    if not pipe.t5_cpu:
        pipe.text_encoder.model.to(pipe.device)
        context = pipe.text_encoder([input_prompt], pipe.device)
        if offload_model:
            pipe.text_encoder.model.cpu()
    else:
        context = pipe.text_encoder([input_prompt], torch.device("cpu"))
        context = [t.to(pipe.device) for t in context]

    from wan.utils.cam_utils import compute_relative_poses, get_Ks_transformed, get_plucker_embeddings, interpolate_camera_poses

    Ks = torch.from_numpy(np.load(action_path / "intrinsics.npy")).float()
    Ks = get_Ks_transformed(
        Ks,
        height_org=condition_height,
        width_org=condition_width,
        height_resize=h,
        width_resize=w,
        height_final=h,
        width_final=w,
    )[0]
    len_c2ws = len(c2ws)
    len_c2ws_latent = int((len_c2ws - 1) // 4) + 1
    len_c2ws_latent = int(len_c2ws_latent - (len_c2ws_latent % chunk_size))
    c2ws_infer = interpolate_camera_poses(
        src_indices=np.linspace(0, len_c2ws - 1, len_c2ws),
        src_rot_mat=c2ws[:, :3, :3],
        src_trans_vec=c2ws[:, :3, 3],
        tgt_indices=np.linspace(0, len_c2ws - 1, len_c2ws_latent),
    )
    c2ws_infer = compute_relative_poses(c2ws_infer, framewise=True).to(pipe.device)
    Ks = Ks.repeat(len(c2ws_infer), 1).to(pipe.device)
    c2ws_plucker_emb = get_plucker_embeddings(c2ws_infer, Ks, h, w, only_rays_d=False)
    c2ws_plucker_emb = rearrange(
        c2ws_plucker_emb,
        "f (h c1) (w c2) c -> (f h w) (c c1 c2)",
        c1=int(h // lat_h),
        c2=int(w // lat_w),
    )
    c2ws_plucker_emb = c2ws_plucker_emb[None]
    c2ws_plucker_emb = rearrange(c2ws_plucker_emb, "b (f h w) c -> b c f h w", f=lat_f, h=lat_h, w=lat_w).to(pipe.param_dtype)

    y, proof = build_prefix_y_for_pipe(
        pipe,
        prefix_video=prefix_video[:, :F],
        prefix_len=prefix_len,
        num_frames=F,
        latent_height=lat_h,
        latent_width=lat_w,
        resize_hw=(h, w),
    )
    proof = V2V5GenerationProof(
        prefix_len=proof.prefix_len,
        prediction_start_frame=proof.prediction_start_frame,
        num_frames=proof.num_frames,
        latent_frames=proof.latent_frames,
        visible_latent_indices=proof.visible_latent_indices,
        future_frame_indices=proof.future_frame_indices,
        condition_mode=proof.condition_mode,
        condition_prefix_nonzero=proof.condition_prefix_nonzero,
        condition_future_zero=proof.condition_future_zero,
        camera_condition_present=True,
    )
    if not proof.condition_prefix_nonzero or not proof.condition_future_zero:
        raise RuntimeError(f"invalid V2V-5 prefix condition proof: {proof}")

    @contextmanager
    def noop_no_sync():
        yield

    no_sync_model = getattr(pipe.model, "no_sync", noop_no_sync)
    if offload_model:
        pipe.model.to(pipe.device)

    model_args = pipe.model.config
    transformer_dtype = pipe.pipe_dtype
    frame_seqlen = int(noise.shape[-2] * noise.shape[-1] // 4)
    kv_size = frame_seqlen * lat_f
    head_dim = model_args.dim // model_args.num_heads
    local_num_heads = model_args.num_heads // pipe.sp_size
    self_kv_shape = [batch_size, kv_size, local_num_heads, head_dim]
    self_kv_cache = pipe._initialize_self_kv_cache(model_args.num_layers, self_kv_shape, transformer_dtype, pipe.device)
    cross_kv_shape = [batch_size, max_sequence_length, model_args.num_heads, head_dim]
    cross_kv_cache = pipe._initialize_crossattn_cache(model_args.num_layers, cross_kv_shape, transformer_dtype, pipe.device)

    with torch.amp.autocast("cuda", dtype=pipe.param_dtype), torch.no_grad(), no_sync_model():
        latent = noise
        latents_chunk = latent.split(chunk_size, dim=1)
        condition_chunk = y.split(chunk_size, dim=1)
        c2ws_plucker_emb_chunk = c2ws_plucker_emb.split(chunk_size, dim=2)
        pred_latent_chunks = []
        for chunk_id in tqdm(range(len(latents_chunk)), desc="v2v5_chunks"):
            current_latent = latents_chunk[chunk_id]
            current_condition = condition_chunk[chunk_id]
            current_c2ws = c2ws_plucker_emb_chunk[chunk_id]
            kwargs = {
                "context": [context[0]],
                "seq_len": max_seq_len,
                "y": [current_condition],
                "dit_cond_dict": {"c2ws_plucker_emb": current_c2ws.chunk(1, dim=0)},
                "kv_cache": self_kv_cache,
                "crossattn_cache": cross_kv_cache,
                "current_start": chunk_id * chunk_size * frame_seqlen,
                "max_attention_size": kv_size if max_attention_size is None else max_attention_size,
            }
            if offload_model:
                torch.cuda.empty_cache()
            x0 = None
            for timestep_idx in range(len(timesteps)):
                timestep = torch.stack([timesteps[timestep_idx]]).to(pipe.device)
                noise_pred = pipe.model(x=[current_latent.to(pipe.device)], t=timestep, **kwargs)[0]
                if stop_after_first_step and chunk_id == 0 and timestep_idx == 0:
                    return {"noise_pred": noise_pred.detach().cpu(), "proof": proof}, proof
                if offload_model:
                    torch.cuda.empty_cache()
                x0 = pipe._convert_flow_pred_to_x0(
                    flow_pred=noise_pred,
                    xt=current_latent,
                    timestep=timesteps[timestep_idx],
                    scheduler=pipe.scheduler,
                )
                if timestep_idx < len(timesteps) - 1:
                    next_timestep = timesteps[timestep_idx + 1]
                    current_latent = pipe.scheduler.add_noise(
                        x0,
                        torch.randn(x0.shape, generator=seed_g, device=x0.device, dtype=x0.dtype),
                        next_timestep,
                    )
            if x0 is None:
                raise RuntimeError("no denoising steps executed")
            pred_latent_chunks.append(x0)
            timestep = torch.stack([timesteps[-1] * 0.0]).to(pipe.device)
            pipe.model(x=[x0], t=timestep, **kwargs)
        pred_latent = torch.cat(pred_latent_chunks, dim=1)
        if offload_model:
            pipe.model.cpu()
            torch.cuda.empty_cache()
        videos = pipe.vae.decode([pred_latent])

    if offload_model:
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.synchronize()
    return videos[0], proof
