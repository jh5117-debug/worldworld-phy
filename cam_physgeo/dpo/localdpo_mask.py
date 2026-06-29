from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass
class LocalDPOMaskResult:
    pair_id: str
    status: str
    reason: str
    latent_temporal_indices: list[int]
    raw_time_span: dict[str, int]
    spatial_mask_available: bool
    temporal_mask_available: bool
    latent_height: int
    latent_width: int
    latent_frames: int
    spatial_mask_ratio: float
    local_mask_ratio: float
    affected_tokens_count: int
    full_future_tokens_count: int
    fallback_time_only: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def infer_latent_hw(raw_height: int = 480, raw_width: int = 832, vae_downsample: int = 8) -> tuple[int, int]:
    return int(math.ceil(raw_height / vae_downsample)), int(math.ceil(raw_width / vae_downsample))


def raw_span_to_latent_indices(
    raw_start: int,
    raw_end: int,
    *,
    prediction_start_frame: int = 5,
    num_frames: int = 81,
    latent_frames: int = 21,
    temporal_stride: int = 4,
) -> list[int]:
    if raw_end < raw_start:
        return []
    start = max(prediction_start_frame, raw_start)
    end = min(num_frames - 1, raw_end)
    if end < start:
        return []
    latent_start = int(math.ceil(start / temporal_stride))
    latent_end = int(math.floor(end / temporal_stride))
    latent_start = max(0, min(latent_frames - 1, latent_start))
    latent_end = max(0, min(latent_frames - 1, latent_end))
    return list(range(latent_start, latent_end + 1))


def region_to_spatial_mask(region: dict[str, Any], *, raw_height: int, raw_width: int, latent_height: int, latent_width: int) -> np.ndarray:
    mask = np.zeros((raw_height, raw_width), dtype=np.uint8)
    x0 = max(0, min(raw_width, int(region.get("x0", 0))))
    x1 = max(0, min(raw_width, int(region.get("x1", raw_width))))
    y0 = max(0, min(raw_height, int(region.get("y0", 0))))
    y1 = max(0, min(raw_height, int(region.get("y1", raw_height))))
    if x1 <= x0 or y1 <= y0:
        return np.zeros((latent_height, latent_width), dtype=bool)
    mask[y0:y1, x0:x1] = 255
    return cv2.resize(mask, (latent_width, latent_height), interpolation=cv2.INTER_NEAREST) > 0


def load_spatial_mask(pair: dict[str, Any], *, raw_height: int, raw_width: int, latent_height: int, latent_width: int) -> tuple[np.ndarray, bool, str]:
    loser = pair.get("loser", {})
    path = loser.get("affected_mask_path")
    if path and Path(path).exists():
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is not None and img.size:
            resized = cv2.resize(img, (latent_width, latent_height), interpolation=cv2.INTER_NEAREST) > 0
            return resized, True, "mask_file"
    region = loser.get("affected_region")
    if isinstance(region, dict):
        return region_to_spatial_mask(region, raw_height=raw_height, raw_width=raw_width, latent_height=latent_height, latent_width=latent_width), True, "region_box"
    return np.ones((latent_height, latent_width), dtype=bool), False, "time_only_fallback"


def build_localdpo_mask(
    pair: dict[str, Any],
    *,
    raw_height: int = 480,
    raw_width: int = 832,
    latent_height: int | None = None,
    latent_width: int | None = None,
    latent_frames: int = 21,
    temporal_stride: int = 4,
) -> LocalDPOMaskResult:
    if latent_height is None or latent_width is None:
        latent_height, latent_width = infer_latent_hw(raw_height, raw_width)
    condition = pair.get("condition", {})
    loser = pair.get("loser", {})
    time_span = loser.get("affected_time_span") or {}
    raw_start = int(time_span.get("raw_frame_start", condition.get("prediction_start_frame", 5)))
    raw_end = int(time_span.get("raw_frame_end", 80))
    temporal_indices = raw_span_to_latent_indices(
        raw_start,
        raw_end,
        prediction_start_frame=int(condition.get("prediction_start_frame", 5)),
        latent_frames=latent_frames,
        temporal_stride=temporal_stride,
    )
    spatial, spatial_available, spatial_source = load_spatial_mask(
        pair,
        raw_height=raw_height,
        raw_width=raw_width,
        latent_height=latent_height,
        latent_width=latent_width,
    )
    temporal_available = bool(time_span)
    spatial_tokens = int(spatial.sum())
    affected_tokens = spatial_tokens * len(temporal_indices)
    future_indices = raw_span_to_latent_indices(5, 80, prediction_start_frame=5, latent_frames=latent_frames, temporal_stride=temporal_stride)
    full_future_tokens = latent_height * latent_width * len(future_indices)
    spatial_ratio = float(spatial_tokens / max(1, latent_height * latent_width))
    local_ratio = float(affected_tokens / max(1, full_future_tokens))
    status = "ok"
    reasons: list[str] = []
    if not temporal_indices:
        status = "invalid"
        reasons.append("empty_temporal_mask")
    if spatial_tokens <= 0:
        status = "invalid"
        reasons.append("empty_spatial_mask")
    if spatial_ratio >= 0.98:
        reasons.append("near_full_spatial_mask")
    if not spatial_available:
        reasons.append("time_only_fallback")
    return LocalDPOMaskResult(
        pair_id=str(pair.get("pair_id", "")),
        status=status,
        reason=";".join(reasons) if reasons else spatial_source,
        latent_temporal_indices=temporal_indices,
        raw_time_span={"raw_frame_start": raw_start, "raw_frame_end": raw_end},
        spatial_mask_available=spatial_available,
        temporal_mask_available=temporal_available,
        latent_height=latent_height,
        latent_width=latent_width,
        latent_frames=latent_frames,
        spatial_mask_ratio=spatial_ratio,
        local_mask_ratio=local_ratio,
        affected_tokens_count=affected_tokens,
        full_future_tokens_count=full_future_tokens,
        fallback_time_only=not spatial_available,
    )


def audit_pairs_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        pair = json.loads(line)
        rows.append(build_localdpo_mask(pair).to_dict())
    return rows
