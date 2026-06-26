from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import cv2
import json
import numpy as np
import torch


def resolve_asset_path(path: str | Path | None, *, repo_root: str | Path = ".") -> Path:
    if path in {None, ""}:
        raise ValueError("empty asset path")
    p = Path(str(path))
    if p.is_absolute():
        return p
    return Path(repo_root) / p


def read_prompt(value: str | Path, *, repo_root: str | Path = ".") -> str:
    p = resolve_asset_path(value, repo_root=repo_root)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8").strip()
    return str(value)


def decode_video_tensor(
    path: str | Path,
    *,
    repo_root: str | Path = ".",
    num_frames: int = 81,
    height: int = 480,
    width: int = 832,
) -> tuple[torch.Tensor, dict[str, int | float]]:
    p = resolve_asset_path(path, repo_root=repo_root)
    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {p}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 16.0)
    frames: list[torch.Tensor] = []
    source_height = 0
    source_width = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if source_height <= 0 or source_width <= 0:
            source_height, source_width = int(frame.shape[0]), int(frame.shape[1])
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if int(frame.shape[0]) != int(height) or int(frame.shape[1]) != int(width):
            frame = cv2.resize(frame, (int(width), int(height)), interpolation=cv2.INTER_LANCZOS4)
        frames.append(torch.from_numpy(frame).permute(2, 0, 1).float() / 127.5 - 1.0)
    cap.release()
    if not frames:
        raise RuntimeError(f"empty video: {p}")
    decoded = len(frames)
    if len(frames) > num_frames:
        frames = frames[:num_frames]
    while len(frames) < num_frames:
        frames.append(frames[-1].clone())
    return torch.stack(frames, dim=1), {
        "decoded_frames": decoded,
        "fps": fps,
        "source_height": int(source_height or height),
        "source_width": int(source_width or width),
    }


def normalize_intrinsics(array: np.ndarray, *, source_width: int, source_height: int) -> np.ndarray:
    arr = np.asarray(array, dtype=np.float32)
    if arr.ndim == 2 and arr.shape[-1] == 4:
        return arr
    if arr.ndim == 3 and arr.shape[-2:] == (4, 4):
        width = float(source_width)
        height = float(source_height)
        fx = np.abs(arr[:, 0, 0]) * width * 0.5
        fy = np.abs(arr[:, 1, 1]) * height * 0.5
        cx = (1.0 - arr[:, 0, 2]) * width * 0.5
        cy = (1.0 + arr[:, 1, 2]) * height * 0.5
        out = np.stack([fx, fy, cx, cy], axis=-1).astype(np.float32)
        if not np.isfinite(out).all():
            raise ValueError("nonfinite intrinsics after projection-matrix conversion")
        return out
    raise ValueError(f"unsupported intrinsics shape {arr.shape}; expected [T,4] or [T,4,4]")


def load_array(path: str | Path, *, repo_root: str | Path = ".", num_frames: int = 81) -> np.ndarray:
    arr = np.load(resolve_asset_path(path, repo_root=repo_root))
    if len(arr) > num_frames:
        arr = arr[:num_frames]
    if len(arr) < num_frames:
        rep_shape = (num_frames - len(arr),) + (1,) * (arr.ndim - 1)
        arr = np.concatenate([arr, np.tile(arr[-1:], rep_shape)], axis=0)
    return arr


def prefix5_schema_errors(pair: dict[str, Any], *, repo_root: str | Path = ".") -> list[str]:
    errors: list[str] = []
    condition = pair.get("condition") or {}
    if int(condition.get("prefix_len", -1)) != 5:
        errors.append("prefix_len_not_5")
    if int(condition.get("prediction_start_frame", -1)) != 5:
        errors.append("prediction_start_not_5")
    expected = list(range(5, 81))
    if pair.get("loss_frame_indices") != expected:
        errors.append("loss_indices_not_5_80")
    if pair.get("reward_frame_indices") != expected:
        errors.append("reward_indices_not_5_80")
    for key in ("same_prefix", "same_prompt", "same_poses", "same_intrinsics"):
        if pair.get(key) is not True:
            errors.append(f"{key}_not_true")
    for key in ("prefix_video_path", "image", "prompt", "poses", "intrinsics"):
        try:
            if not resolve_asset_path(condition.get(key), repo_root=repo_root).exists():
                errors.append(f"missing_condition_{key}")
        except Exception:
            errors.append(f"missing_condition_{key}")
    for side in ("winner", "loser"):
        payload = pair.get(side) or {}
        for key in ("full_video_path", "future_video_path"):
            try:
                if not resolve_asset_path(payload.get(key), repo_root=repo_root).exists():
                    errors.append(f"missing_{side}_{key}")
            except Exception:
                errors.append(f"missing_{side}_{key}")
        if payload.get("future_frame_indices") != expected:
            errors.append(f"{side}_future_indices_not_5_80")
    return errors


@dataclass(slots=True)
class Prefix5DpoExample:
    pair: dict[str, Any]
    pair_id: str
    prompt: str
    winner_video: torch.Tensor
    loser_video: torch.Tensor
    poses: torch.Tensor
    intrinsics: torch.Tensor
    prefix_len: int
    prediction_start_frame: int
    source_height: int
    source_width: int


class Prefix5DpoDataset:
    def __init__(
        self,
        pair_manifest: str | Path,
        *,
        repo_root: str | Path = ".",
        limit_pairs: int = 0,
        num_frames: int = 81,
        height: int = 480,
        width: int = 832,
        min_margin: float = 0.0,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.num_frames = int(num_frames)
        self.height = int(height)
        self.width = int(width)
        rows: list[dict[str, Any]] = []
        with Path(pair_manifest).open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                if float(row.get("margin") or 0.0) < float(min_margin):
                    continue
                rows.append(row)
        if limit_pairs > 0:
            rows = rows[: int(limit_pairs)]
        self.rows = rows

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[Prefix5DpoExample]:
        for idx in range(len(self)):
            yield self[idx]

    def __getitem__(self, index: int) -> Prefix5DpoExample:
        pair = self.rows[int(index)]
        errors = prefix5_schema_errors(pair, repo_root=self.repo_root)
        if errors:
            raise ValueError(f"invalid prefix5 pair {pair.get('pair_id')}: {errors}")
        condition = pair["condition"]
        winner_video, meta = decode_video_tensor(
            pair["winner"].get("full_video_path") or pair["winner"].get("video"),
            repo_root=self.repo_root,
            num_frames=self.num_frames,
            height=self.height,
            width=self.width,
        )
        loser_video, loser_meta = decode_video_tensor(
            pair["loser"].get("full_video_path") or pair["loser"].get("video"),
            repo_root=self.repo_root,
            num_frames=self.num_frames,
            height=self.height,
            width=self.width,
        )
        source_height = int(meta.get("source_height") or loser_meta.get("source_height") or self.height)
        source_width = int(meta.get("source_width") or loser_meta.get("source_width") or self.width)
        poses = load_array(condition["poses"], repo_root=self.repo_root, num_frames=self.num_frames).astype(np.float32)
        intrinsics = normalize_intrinsics(
            load_array(condition["intrinsics"], repo_root=self.repo_root, num_frames=self.num_frames),
            source_width=source_width,
            source_height=source_height,
        )
        return Prefix5DpoExample(
            pair=pair,
            pair_id=str(pair.get("pair_id") or f"pair_{index}"),
            prompt=read_prompt(condition["prompt"], repo_root=self.repo_root),
            winner_video=winner_video,
            loser_video=loser_video,
            poses=torch.from_numpy(poses).float(),
            intrinsics=torch.from_numpy(intrinsics).float(),
            prefix_len=5,
            prediction_start_frame=5,
            source_height=source_height,
            source_width=source_width,
        )
