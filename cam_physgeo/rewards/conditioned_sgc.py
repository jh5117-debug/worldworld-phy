"""Camera-Conditioned SGC (C-SGC) diagnostics.

This is not a claim to reproduce an official SGC implementation. It checks
whether static-background regions move coherently and whether their local motion
is compatible with the supplied camera poses/intrinsics.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from cam_physgeo.rewards.epipolar import intrinsics_to_matrix, read_video_frames, relative_pose


@dataclass(slots=True)
class CSGCResult:
    status: str
    backend: str
    valid_region_count: int
    inter_region_rotation_error: float | None
    inter_region_translation_direction_error: float | None
    conditioned_rotation_error: float | None
    conditioned_translation_direction_error: float | None
    score: float
    confidence: float
    reason: str
    frame_i: int
    frame_j: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _rotation_flow(K_i: np.ndarray, K_j: np.ndarray, R_rel: np.ndarray, points: np.ndarray) -> np.ndarray:
    K_i = intrinsics_to_matrix(K_i)
    K_j = intrinsics_to_matrix(K_j)
    ones = np.ones((len(points), 1), dtype=np.float64)
    x = np.concatenate([points.astype(np.float64), ones], axis=1).T
    x2 = K_j @ R_rel @ np.linalg.inv(K_i) @ x
    x2 = (x2[:2] / np.maximum(x2[2:3], 1e-9)).T
    return x2 - points


def evaluate_csgc_video(
    video_path: str | Path,
    poses: np.ndarray,
    intrinsics: np.ndarray,
    *,
    frame_i: int = 0,
    frame_j: int = 40,
    pose_convention: str = "c2w",
    grid_rows: int = 3,
    grid_cols: int = 4,
    min_points_per_region: int = 20,
    visualization_path: str | Path | None = None,
) -> CSGCResult:
    frames = read_video_frames(video_path, max_frames=max(frame_i, frame_j) + 1)
    if len(frames) <= max(frame_i, frame_j):
        return CSGCResult("failed", "farneback_region", 0, None, None, None, None, 0.0, 0.0, "not_enough_frames", frame_i, frame_j)
    gray_i = cv2.cvtColor(frames[frame_i], cv2.COLOR_BGR2GRAY)
    gray_j = cv2.cvtColor(frames[frame_j], cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(gray_i, gray_j, None, 0.5, 3, 25, 3, 5, 1.2, 0)
    h, w = gray_i.shape
    R_rel, t_rel = relative_pose(poses[frame_i], poses[frame_j], convention=pose_convention)
    region_flows=[]; region_centers=[]; region_rot_flows=[]
    for gy in range(grid_rows):
        for gx in range(grid_cols):
            y0, y1 = int(h*gy/grid_rows), int(h*(gy+1)/grid_rows)
            x0, x1 = int(w*gx/grid_cols), int(w*(gx+1)/grid_cols)
            ys, xs = np.mgrid[y0:y1:12, x0:x1:12]
            pts = np.stack([xs.reshape(-1), ys.reshape(-1)], axis=1).astype(np.float64)
            if len(pts) < min_points_per_region:
                continue
            fl = flow[pts[:,1].astype(int), pts[:,0].astype(int)]
            good = np.isfinite(fl).all(axis=1)
            if good.sum() < min_points_per_region:
                continue
            pts = pts[good]; fl = fl[good]
            region_flows.append(np.median(fl, axis=0))
            region_centers.append(np.array([(x0+x1)/2, (y0+y1)/2], dtype=np.float64))
            region_rot_flows.append(np.median(_rotation_flow(intrinsics[frame_i], intrinsics[frame_j], R_rel, pts), axis=0))
    n = len(region_flows)
    if n < 3:
        return CSGCResult("failed", "farneback_region", n, None, None, None, None, 0.0, 0.0, "too_few_valid_regions", frame_i, frame_j)
    flows = np.asarray(region_flows, dtype=np.float64)
    rot = np.asarray(region_rot_flows, dtype=np.float64)
    residual = flows - rot
    inter_rot = float(np.median(np.linalg.norm(flows - np.median(flows, axis=0, keepdims=True), axis=1)))
    cond_rot = float(np.median(np.linalg.norm(flows - rot, axis=1)))
    t_norm = float(np.linalg.norm(t_rel))
    if t_norm < 1e-5:
        trans_dir_err = None; cond_trans_err = None; trans_score = 0.75
    else:
        residual_dirs = residual / np.maximum(np.linalg.norm(residual, axis=1, keepdims=True), 1e-6)
        median_dir = np.median(residual_dirs, axis=0)
        median_dir = median_dir / max(float(np.linalg.norm(median_dir)), 1e-6)
        dir_spread = np.linalg.norm(residual_dirs - median_dir[None], axis=1)
        trans_dir_err = float(np.median(dir_spread))
        cond_trans_err = trans_dir_err
        trans_score = float(np.exp(-trans_dir_err))
    rot_score = float(np.exp(-cond_rot / 25.0) * np.exp(-inter_rot / 30.0))
    score = float(np.clip(0.65 * rot_score + 0.35 * trans_score, 0.0, 1.0))
    confidence = float(np.clip(n / max(1, grid_rows * grid_cols), 0.0, 1.0))
    if visualization_path:
        vis = frames[frame_j].copy()
        for center, fl, rf in zip(region_centers, flows, rot):
            c = tuple(np.round(center).astype(int)); e = tuple(np.round(center + fl).astype(int)); r = tuple(np.round(center + rf).astype(int))
            cv2.arrowedLine(vis, c, e, (0, 0, 255), 2)
            cv2.arrowedLine(vis, c, r, (0, 255, 0), 2)
        Path(visualization_path).parent.mkdir(parents=True, exist_ok=True); cv2.imwrite(str(visualization_path), vis)
    return CSGCResult("ok", "farneback_region", n, inter_rot, trans_dir_err, cond_rot, cond_trans_err, score, confidence, "", frame_i, frame_j)
