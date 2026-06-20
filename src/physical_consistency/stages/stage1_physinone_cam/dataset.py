"""Processed PhysInOne camera-only dataset loader."""

from __future__ import annotations

import csv
import os

import random

import numpy as np
import torch
from torch.utils.data import Dataset


class PhysInOneCamDataset(Dataset):
    """Load standardized PhysInOne camera clips for pure Stage-1 training."""

    def __init__(
        self,
        dataset_dir: str,
        *,
        split: str = "train",
        num_frames: int = 81,
        height: int = 480,
        width: int = 480,
        repeat: int = 1,
        temporal_window_mode: str = "random_window",
    ) -> None:
        self.dataset_dir = dataset_dir
        self.split = split
        self.height = int(height)
        self.width = int(width)
        self.num_frames = int(num_frames)
        self.repeat = int(repeat)
        self.temporal_window_mode = str(temporal_window_mode or "random_window")

        csv_path = os.path.join(dataset_dir, f"metadata_{split}.csv")
        with open(csv_path, "r", encoding="utf-8", newline="") as handle:
            self.samples = list(csv.DictReader(handle))
        if split == "train" and not self.samples:
            raise ValueError(f"No samples found in {csv_path}")

    def __len__(self) -> int:
        return len(self.samples) * self.repeat

    def __getitem__(self, index: int) -> dict[str, torch.Tensor | str | int]:
        import cv2

        sample = self.samples[index % len(self.samples)]
        clip_dir = os.path.join(self.dataset_dir, sample["clip_path"])
        video_path = os.path.join(clip_dir, "video.mp4")

        cap = cv2.VideoCapture(video_path)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_LANCZOS4)
            frame = torch.from_numpy(frame).permute(2, 0, 1).float() / 127.5 - 1.0
            frames.append(frame)
        cap.release()
        if not frames:
            raise RuntimeError(f"Could not decode any frame from {video_path}")
        source_num_frames = len(frames)
        window_start = self._window_start(index, source_num_frames)
        frames = frames[window_start : window_start + self.num_frames]
        while len(frames) < self.num_frames:
            frames.append(frames[-1].clone())
        video_tensor = torch.stack(frames, dim=1)

        poses = np.load(os.path.join(clip_dir, "poses.npy"))
        intrinsics = np.load(os.path.join(clip_dir, "intrinsics.npy"))
        intrinsics = self._normalize_intrinsics(
            intrinsics,
            source_width=int(sample.get("source_width", self.width) or self.width),
            source_height=int(sample.get("source_height", self.height) or self.height),
        )
        return {
            "clip_name": os.path.basename(clip_dir),
            "video": video_tensor,
            "prompt": sample["prompt"],
            "poses": torch.from_numpy(self._slice_pad_or_truncate(poses, window_start)).float(),
            "intrinsics": torch.from_numpy(self._slice_pad_or_truncate(intrinsics, window_start)).float(),
            "temporal_window_start": int(window_start),
            "source_num_frames": int(source_num_frames),
            "source_height": int(sample.get("source_height", self.height) or self.height),
            "source_width": int(sample.get("source_width", self.width) or self.width),
            "camera_id": sample.get("camera_id", ""),
            "trajectory_name": sample.get("trajectory_name", ""),
        }

    def _window_start(self, index: int, source_num_frames: int) -> int:
        if source_num_frames <= self.num_frames:
            return 0
        max_start = source_num_frames - self.num_frames
        mode = self.temporal_window_mode
        if self.split == "train" and mode in {"random", "random_window"}:
            return random.randint(0, max_start)
        if mode in {"middle", "center", "center_window"}:
            return max_start // 2
        if mode in {"cycle", "cycle_window"}:
            return int(index) % (max_start + 1)
        return 0

    def _slice_pad_or_truncate(self, array: np.ndarray, start: int) -> np.ndarray:
        if len(array) > start:
            array = array[start : start + self.num_frames]
        if len(array) >= self.num_frames:
            return array[: self.num_frames]
        rep_shape = (self.num_frames - len(array),) + (1,) * (array.ndim - 1)
        pad = np.tile(array[-1:], rep_shape)
        return np.concatenate([array, pad], axis=0)

    @staticmethod
    def _normalize_intrinsics(array: np.ndarray, *, source_width: int, source_height: int) -> np.ndarray:
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
