from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class PrefixPlan:
    """Frame and latent masks for prefix-aware I2V/V2V conditioning."""

    num_frames: int
    prefix_len: int
    prediction_start_frame: int
    target_frame_indices: tuple[int, ...]
    loss_frame_indices: tuple[int, ...]
    reward_frame_indices: tuple[int, ...]
    visible_frame_mask: np.ndarray
    loss_frame_mask: np.ndarray
    reward_frame_mask: np.ndarray
    latent_visible_mask: np.ndarray
    latent_loss_mask: np.ndarray


def validate_prefix_len(prefix_len: int, num_frames: int) -> int:
    prefix_len = int(prefix_len)
    num_frames = int(num_frames)
    if num_frames <= 1:
        raise ValueError(f"num_frames must be >1, got {num_frames}")
    if prefix_len < 1:
        raise ValueError(f"prefix_len must be >=1, got {prefix_len}")
    if prefix_len >= num_frames:
        raise ValueError(f"prefix_len must be smaller than num_frames, got {prefix_len}/{num_frames}")
    return prefix_len


def frame_to_latent_index(frame_index: int, *, temporal_compression: int = 4) -> int:
    if temporal_compression <= 0:
        raise ValueError("temporal_compression must be positive")
    return int(frame_index) // int(temporal_compression)


def latent_count_for_frames(num_frames: int, *, temporal_compression: int = 4) -> int:
    if num_frames <= 0:
        raise ValueError("num_frames must be positive")
    return frame_to_latent_index(num_frames - 1, temporal_compression=temporal_compression) + 1


def build_prefix_plan(
    *,
    num_frames: int = 81,
    prefix_len: int = 1,
    temporal_compression: int = 4,
) -> PrefixPlan:
    prefix_len = validate_prefix_len(prefix_len, num_frames)
    prediction_start = prefix_len
    target = tuple(range(num_frames))
    future = tuple(range(prediction_start, num_frames))

    visible = np.zeros(num_frames, dtype=np.bool_)
    visible[:prefix_len] = True
    loss = np.zeros(num_frames, dtype=np.bool_)
    loss[prediction_start:] = True
    reward = loss.copy()

    n_latents = latent_count_for_frames(num_frames, temporal_compression=temporal_compression)
    latent_visible = np.zeros(n_latents, dtype=np.bool_)
    latent_loss = np.zeros(n_latents, dtype=np.bool_)
    for frame_idx in range(num_frames):
        latent_idx = frame_to_latent_index(frame_idx, temporal_compression=temporal_compression)
        if visible[frame_idx]:
            latent_visible[latent_idx] = True
        if loss[frame_idx]:
            latent_loss[latent_idx] = True

    return PrefixPlan(
        num_frames=num_frames,
        prefix_len=prefix_len,
        prediction_start_frame=prediction_start,
        target_frame_indices=target,
        loss_frame_indices=future,
        reward_frame_indices=future,
        visible_frame_mask=visible,
        loss_frame_mask=loss,
        reward_frame_mask=reward,
        latent_visible_mask=latent_visible,
        latent_loss_mask=latent_loss,
    )


def zero_future_condition(frames: np.ndarray, prefix_len: int) -> tuple[np.ndarray, np.ndarray]:
    """Return full-length condition frames with future frames zeroed.

    The input is expected to be shaped ``T,H,W,C`` or ``T,C,H,W``. The returned
    mask is frame-level and marks prefix frames as visible.
    """

    arr = np.asarray(frames).copy()
    if arr.ndim < 3:
        raise ValueError(f"frames must have a time dimension, got shape {arr.shape}")
    prefix_len = validate_prefix_len(prefix_len, arr.shape[0])
    arr[prefix_len:] = 0
    visible = np.zeros(arr.shape[0], dtype=np.bool_)
    visible[:prefix_len] = True
    return arr, visible


def enrich_manifest_row(
    row: dict,
    *,
    prefix_len: int,
    num_frames: int = 81,
    temporal_compression: int = 4,
) -> dict:
    plan = build_prefix_plan(
        num_frames=num_frames,
        prefix_len=prefix_len,
        temporal_compression=temporal_compression,
    )
    out = dict(row)
    out.update(
        {
            "prefix_len": plan.prefix_len,
            "prediction_start_frame": plan.prediction_start_frame,
            "target_frame_indices": list(plan.target_frame_indices),
            "loss_frame_indices": list(plan.loss_frame_indices),
            "reward_frame_indices": list(plan.reward_frame_indices),
            "prefix_condition_mode": f"v2v_prefix_{plan.prefix_len}",
            "eval_future_only": True,
            "temporal_compression": temporal_compression,
            "latent_visible_indices": [int(i) for i, v in enumerate(plan.latent_visible_mask) if bool(v)],
            "latent_loss_indices": [int(i) for i, v in enumerate(plan.latent_loss_mask) if bool(v)],
        }
    )
    video = out.get("target_video") or out.get("target_mp4") or out.get("video_path") or out.get("video")
    if video:
        out.setdefault("full_target_video_path", video)
        out.setdefault("prefix_video_path", "")
        out.setdefault("future_video_path", "")
    return out


def enrich_rows(
    rows: Iterable[dict],
    *,
    prefix_len: int,
    num_frames: int = 81,
    temporal_compression: int = 4,
) -> list[dict]:
    return [
        enrich_manifest_row(
            row,
            prefix_len=prefix_len,
            num_frames=num_frames,
            temporal_compression=temporal_compression,
        )
        for row in rows
    ]

