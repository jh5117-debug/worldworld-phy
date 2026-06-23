"""Epipolar geometry diagnostics for camera-conditioned video rollouts."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass(slots=True)
class EpipolarResult:
    status: str
    backend: str
    mean_sampson: float | None
    median_sampson: float | None
    trimmed_sampson: float | None
    p90_sampson: float | None
    valid_count: int
    background_ratio: float
    confidence: float
    reason: str
    pose_convention: str
    frame_i: int
    frame_j: int
    translation_norm: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def skew(v: np.ndarray) -> np.ndarray:
    x, y, z = [float(a) for a in v.reshape(3)]
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=np.float64)


def relative_pose(pose_i: np.ndarray, pose_j: np.ndarray, *, convention: str = "c2w") -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(pose_i, dtype=np.float64)[:3, :4]
    b = np.asarray(pose_j, dtype=np.float64)[:3, :4]
    Ra, ta = a[:3, :3], a[:3, 3]
    Rb, tb = b[:3, :3], b[:3, 3]
    convention = convention.lower()
    if convention == "c2w":
        R = Rb.T @ Ra
        t = Rb.T @ (ta - tb)
    elif convention == "w2c":
        R = Rb @ Ra.T
        t = tb - R @ ta
    else:
        raise ValueError(f"Unsupported pose convention: {convention}")
    return R, t.reshape(3)




def intrinsics_to_matrix(K: np.ndarray) -> np.ndarray:
    arr = np.asarray(K, dtype=np.float64)
    if arr.shape == (3, 3) or arr.shape == (4, 4):
        return arr[:3, :3]
    flat = arr.reshape(-1)
    if flat.size >= 4:
        fx, fy, cx, cy = flat[:4]
        return np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]], dtype=np.float64)
    raise ValueError(f"Unsupported intrinsics shape: {arr.shape}")


def fundamental_from_pose(K_i: np.ndarray, K_j: np.ndarray, pose_i: np.ndarray, pose_j: np.ndarray, *, convention: str = "c2w") -> tuple[np.ndarray, float]:
    K_i = intrinsics_to_matrix(K_i)
    K_j = intrinsics_to_matrix(K_j)
    R, t = relative_pose(pose_i, pose_j, convention=convention)
    E = skew(t) @ R
    F = np.linalg.inv(K_j).T @ E @ np.linalg.inv(K_i)
    norm = np.linalg.norm(F)
    if norm > 0:
        F = F / norm
    return F, float(np.linalg.norm(t))


def sampson_distance(F: np.ndarray, pts_i: np.ndarray, pts_j: np.ndarray) -> np.ndarray:
    pts_i = np.asarray(pts_i, dtype=np.float64)
    pts_j = np.asarray(pts_j, dtype=np.float64)
    ones = np.ones((pts_i.shape[0], 1), dtype=np.float64)
    x1 = np.concatenate([pts_i, ones], axis=1)
    x2 = np.concatenate([pts_j, ones], axis=1)
    Fx1 = (F @ x1.T).T
    Ftx2 = (F.T @ x2.T).T
    numer = np.sum(x2 * Fx1, axis=1) ** 2
    denom = Fx1[:, 0] ** 2 + Fx1[:, 1] ** 2 + Ftx2[:, 0] ** 2 + Ftx2[:, 1] ** 2
    return numer / np.maximum(denom, 1.0e-12)


def read_video_frames(path: str | Path, *, max_frames: int = 81, width: int | None = None, height: int | None = None) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(path))
    frames: list[np.ndarray] = []
    while len(frames) < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if width and height and (frame.shape[1] != width or frame.shape[0] != height):
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        frames.append(frame)
    cap.release()
    return frames


def _flow_correspondences(frame_i: np.ndarray, frame_j: np.ndarray, *, stride: int, max_points: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gray_i = cv2.cvtColor(frame_i, cv2.COLOR_BGR2GRAY)
    gray_j = cv2.cvtColor(frame_j, cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(gray_i, gray_j, None, 0.5, 3, 25, 3, 5, 1.2, 0)
    h, w = gray_i.shape
    ys, xs = np.mgrid[stride // 2:h:stride, stride // 2:w:stride]
    pts_i = np.stack([xs.reshape(-1), ys.reshape(-1)], axis=1).astype(np.float32)
    flow_sample = flow[pts_i[:, 1].astype(int), pts_i[:, 0].astype(int)]
    pts_j = pts_i + flow_sample
    inside = (pts_j[:, 0] >= 0) & (pts_j[:, 0] < w) & (pts_j[:, 1] >= 0) & (pts_j[:, 1] < h)
    mag = np.linalg.norm(flow_sample, axis=1)
    finite = np.isfinite(pts_j).all(axis=1) & np.isfinite(mag)
    keep = inside & finite
    if keep.sum() > max_points:
        idx = np.linspace(0, keep.sum() - 1, max_points).astype(int)
        ids = np.flatnonzero(keep)[idx]
    else:
        ids = np.flatnonzero(keep)
    mask = np.zeros(len(pts_i), dtype=bool); mask[ids] = True
    return pts_i[ids], pts_j[ids], mask


def evaluate_epipolar_video(
    video_path: str | Path,
    poses: np.ndarray,
    intrinsics: np.ndarray,
    *,
    frame_i: int = 0,
    frame_j: int = 40,
    pose_convention: str = "c2w",
    stride: int = 24,
    max_points: int = 4000,
    low_translation_epsilon: float = 1.0e-5,
    width: int | None = None,
    height: int | None = None,
    visualization_path: str | Path | None = None,
) -> EpipolarResult:
    frames = read_video_frames(video_path, max_frames=max(frame_i, frame_j) + 1, width=width, height=height)
    if len(frames) <= max(frame_i, frame_j):
        return EpipolarResult("failed", "farneback", None, None, None, None, 0, 0.0, 0.0, "not_enough_frames", pose_convention, frame_i, frame_j, 0.0)
    F, t_norm = fundamental_from_pose(intrinsics[frame_i], intrinsics[frame_j], poses[frame_i], poses[frame_j], convention=pose_convention)
    if t_norm < low_translation_epsilon:
        return EpipolarResult("degenerate", "farneback", None, None, None, None, 0, 0.0, 0.15, "low_translation_or_pure_rotation", pose_convention, frame_i, frame_j, t_norm)
    pts_i, pts_j, _ = _flow_correspondences(frames[frame_i], frames[frame_j], stride=stride, max_points=max_points)
    if len(pts_i) < 32:
        return EpipolarResult("failed", "farneback", None, None, None, None, int(len(pts_i)), 0.0, 0.0, "too_few_correspondences", pose_convention, frame_i, frame_j, t_norm)
    dist = sampson_distance(F, pts_i, pts_j)
    dist = dist[np.isfinite(dist)]
    if len(dist) < 32:
        return EpipolarResult("failed", "farneback", None, None, None, None, int(len(dist)), 0.0, 0.0, "nonfinite_sampson", pose_convention, frame_i, frame_j, t_norm)
    trimmed = np.sort(dist)[: max(1, int(0.9 * len(dist)))]
    mean = float(np.mean(dist)); median = float(np.median(dist)); p90 = float(np.percentile(dist, 90)); trim = float(np.mean(trimmed))
    confidence = float(np.clip(len(dist) / 1000.0, 0.1, 1.0) * np.clip(1.0 / (1.0 + median / 100.0), 0.05, 1.0))
    if visualization_path:
        vis = frames[frame_j].copy()
        sample = np.linspace(0, len(pts_i) - 1, min(500, len(pts_i))).astype(int)
        for a, b, d in zip(pts_i[sample], pts_j[sample], dist[sample]):
            color = (0, int(max(0, 255 - min(d, 255))), int(min(d, 255)))
            cv2.line(vis, tuple(np.round(a).astype(int)), tuple(np.round(b).astype(int)), color, 1)
        Path(visualization_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(visualization_path), vis)
    return EpipolarResult("ok", "farneback", mean, median, trim, p90, int(len(dist)), 1.0, confidence, "", pose_convention, frame_i, frame_j, t_norm)
