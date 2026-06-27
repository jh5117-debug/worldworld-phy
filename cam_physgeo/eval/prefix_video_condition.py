"""Prefix-video conditioning helpers for honest V2V-5 LingBot-Fast rollout.

The project previously had image-first inference wrappers that only exposed raw
frame 0 to LingBot-Fast. These helpers build the same prefix-aware condition
contract used by StageA/DPO: raw frames 0..prefix_len-1 are visible, future
frames are zeroed, and the Wan latent mask marks only latent slots touched by
prefix frames as visible.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class VideoReadInfo:
    path: str
    decoded_frames: int
    fps: float
    source_height: int
    source_width: int
    height: int
    width: int


@dataclass(frozen=True)
class PrefixConditionInfo:
    prefix_len: int
    prediction_start_frame: int
    num_frames: int
    latent_frames: int
    temporal_compression: int
    visible_latent_indices: tuple[int, ...]
    future_frame_indices: tuple[int, ...]
    mode: str


def resolve_path(path: str | Path, *, repo_root: str | Path = ".") -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return Path(repo_root) / p


def validate_prefix_plan(*, prefix_len: int, prediction_start_frame: int, num_frames: int) -> None:
    prefix_len = int(prefix_len)
    prediction_start_frame = int(prediction_start_frame)
    num_frames = int(num_frames)
    if prefix_len != 5:
        raise ValueError(f"V2V-5 generation requires prefix_len=5, got {prefix_len}")
    if prediction_start_frame != prefix_len:
        raise ValueError(
            f"prediction_start_frame must equal prefix_len for V2V-5, got {prediction_start_frame}/{prefix_len}"
        )
    if num_frames <= prefix_len:
        raise ValueError(f"num_frames must exceed prefix_len, got {num_frames}/{prefix_len}")


def read_video_tensor(
    path: str | Path,
    *,
    repo_root: str | Path = ".",
    num_frames: int = 81,
    height: int = 480,
    width: int = 832,
) -> tuple[torch.Tensor, VideoReadInfo]:
    src = resolve_path(path, repo_root=repo_root)
    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {src}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 16.0)
    frames: list[torch.Tensor] = []
    source_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    source_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if not source_height or not source_width:
            source_height, source_width = int(frame.shape[0]), int(frame.shape[1])
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if int(frame.shape[0]) != int(height) or int(frame.shape[1]) != int(width):
            frame = cv2.resize(frame, (int(width), int(height)), interpolation=cv2.INTER_LANCZOS4)
        frames.append(torch.from_numpy(frame).permute(2, 0, 1).float() / 127.5 - 1.0)
    cap.release()
    if not frames:
        raise RuntimeError(f"empty video: {src}")
    decoded = len(frames)
    if len(frames) > int(num_frames):
        frames = frames[: int(num_frames)]
    while len(frames) < int(num_frames):
        frames.append(frames[-1].clone())
    tensor = torch.stack(frames, dim=1).contiguous()
    info = VideoReadInfo(
        path=str(src),
        decoded_frames=decoded,
        fps=fps,
        source_height=int(source_height or height),
        source_width=int(source_width or width),
        height=int(height),
        width=int(width),
    )
    return tensor, info


def tensor_to_uint8_frames(video: torch.Tensor) -> list[np.ndarray]:
    if video.ndim != 4 or int(video.shape[0]) != 3:
        raise ValueError(f"expected [3,T,H,W] tensor, got {tuple(video.shape)}")
    arr = ((video.detach().cpu().clamp(-1, 1) + 1.0) * 127.5).round().to(torch.uint8)
    arr = arr.permute(1, 2, 3, 0).numpy()
    return [frame for frame in arr]


def write_video_tensor(video: torch.Tensor, path: str | Path, *, fps: float = 16.0) -> None:
    frames = tensor_to_uint8_frames(video)
    if not frames:
        raise ValueError("cannot write empty video")
    dst = Path(path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    height, width = int(frames[0].shape[0]), int(frames[0].shape[1])
    writer = cv2.VideoWriter(str(dst), cv2.VideoWriter_fourcc(*"mp4v"), float(fps), (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"cannot open video writer: {dst}")
    for frame in frames:
        writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    writer.release()


def build_condition_video(video: torch.Tensor, *, prefix_len: int, num_frames: int | None = None) -> tuple[torch.Tensor, torch.Tensor]:
    if video.ndim != 4 or int(video.shape[0]) != 3:
        raise ValueError(f"expected [3,T,H,W] video tensor, got {tuple(video.shape)}")
    total = int(num_frames or video.shape[1])
    if int(video.shape[1]) < total:
        pad = video[:, -1:].repeat(1, total - int(video.shape[1]), 1, 1)
        video = torch.cat([video, pad], dim=1)
    video = video[:, :total]
    if int(prefix_len) < 1 or int(prefix_len) >= total:
        raise ValueError(f"prefix_len must be in [1,num_frames), got {prefix_len}/{total}")
    condition = torch.zeros_like(video)
    condition[:, : int(prefix_len)] = video[:, : int(prefix_len)]
    visible = torch.zeros(total, dtype=torch.bool)
    visible[: int(prefix_len)] = True
    return condition.contiguous(), visible


def latent_visible_indices(
    *,
    num_frames: int,
    prefix_len: int,
    latent_frames: int,
    temporal_compression: int | None = None,
) -> tuple[int, ...]:
    if temporal_compression is None:
        temporal_compression = max(int((int(num_frames) - 1) // max(int(latent_frames) - 1, 1)), 1)
    visible = min((int(prefix_len) - 1) // int(temporal_compression) + 1, int(latent_frames))
    return tuple(range(visible))


def build_wan_prefix_mask(
    *,
    num_frames: int,
    prefix_len: int,
    latent_frames: int,
    latent_height: int,
    latent_width: int,
    device: torch.device | str,
    dtype: torch.dtype,
) -> tuple[torch.Tensor, PrefixConditionInfo]:
    compression = max(int((int(num_frames) - 1) // max(int(latent_frames) - 1, 1)), 1)
    visible_indices = latent_visible_indices(
        num_frames=num_frames,
        prefix_len=prefix_len,
        latent_frames=latent_frames,
        temporal_compression=compression,
    )
    mask = torch.zeros(4, int(latent_frames), int(latent_height), int(latent_width), device=device, dtype=dtype)
    if visible_indices:
        mask[:, list(visible_indices)] = 1
    info = PrefixConditionInfo(
        prefix_len=int(prefix_len),
        prediction_start_frame=int(prefix_len),
        num_frames=int(num_frames),
        latent_frames=int(latent_frames),
        temporal_compression=int(compression),
        visible_latent_indices=visible_indices,
        future_frame_indices=tuple(range(int(prefix_len), int(num_frames))),
        mode=f"v2v_prefix_{int(prefix_len)}",
    )
    return mask, info


def prepare_prefix_condition_latent(
    *,
    vae,
    video: torch.Tensor,
    prefix_len: int,
    num_frames: int,
    latent_height: int,
    latent_width: int,
    device: torch.device | str,
    resize_hw: tuple[int, int] | None = None,
) -> tuple[torch.Tensor, PrefixConditionInfo, torch.Tensor]:
    condition, _ = build_condition_video(video, prefix_len=prefix_len, num_frames=num_frames)
    if resize_hw is not None:
        height, width = int(resize_hw[0]), int(resize_hw[1])
        condition = torch.nn.functional.interpolate(
            condition.transpose(0, 1), size=(height, width), mode="bicubic", align_corners=False
        ).transpose(0, 1)
    condition = condition.to(device)
    y_latent = vae.encode([condition])[0]
    mask, info = build_wan_prefix_mask(
        num_frames=num_frames,
        prefix_len=prefix_len,
        latent_frames=int(y_latent.shape[1]),
        latent_height=latent_height,
        latent_width=latent_width,
        device=device,
        dtype=y_latent.dtype,
    )
    return torch.cat([mask, y_latent]), info, condition


def extract_prefix_future(video: torch.Tensor, *, prefix_len: int = 5) -> tuple[torch.Tensor, torch.Tensor]:
    if video.ndim != 4 or int(video.shape[0]) != 3:
        raise ValueError(f"expected [3,T,H,W], got {tuple(video.shape)}")
    if int(video.shape[1]) <= int(prefix_len):
        raise ValueError(f"video shorter than prefix_len: {tuple(video.shape)} / {prefix_len}")
    return video[:, : int(prefix_len)].contiguous(), video[:, int(prefix_len) :].contiguous()


def make_prefix_future_contact_sheet(
    *,
    prefix: torch.Tensor,
    gt_future: torch.Tensor | None,
    generated_future: torch.Tensor,
    output_path: str | Path,
    title: str,
    columns: int = 8,
) -> None:
    def pick(frames: torch.Tensor, count: int) -> list[np.ndarray]:
        images = tensor_to_uint8_frames(frames)
        if len(images) <= count:
            return images
        idx = np.linspace(0, len(images) - 1, count).round().astype(int).tolist()
        return [images[i] for i in idx]

    rows: list[tuple[str, list[np.ndarray]]] = [("prefix 0-4", pick(prefix, min(5, int(prefix.shape[1]))))]
    if gt_future is not None:
        rows.append(("GT future 5-80", pick(gt_future, columns)))
    rows.append(("generated future", pick(generated_future, columns)))
    thumb_h = 120
    label_w = 180
    pad = 8
    title_h = 42
    max_cols = max(len(images) for _, images in rows)
    thumbs: list[tuple[str, list[Image.Image]]] = []
    for label, images in rows:
        pil_images = []
        for arr in images:
            img = Image.fromarray(arr)
            new_w = max(1, int(img.width * thumb_h / img.height))
            pil_images.append(img.resize((new_w, thumb_h)))
        thumbs.append((label, pil_images))
    cell_w = max((img.width for _, imgs in thumbs for img in imgs), default=180)
    width = label_w + max_cols * (cell_w + pad) + pad
    height = title_h + len(rows) * (thumb_h + pad) + pad
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 12), title, fill=(0, 0, 0))
    y = title_h
    for label, imgs in thumbs:
        draw.text((pad, y + 45), label, fill=(0, 0, 0))
        x = label_w
        for img in imgs:
            canvas.paste(img, (x, y))
            x += cell_w + pad
        y += thumb_h + pad
    dst = Path(output_path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst, quality=92)
