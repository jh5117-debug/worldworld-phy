from __future__ import annotations

import numpy as np

from cam_physgeo.rewards.epipolar import fundamental_from_pose, sampson_distance


def test_epipolar_sampson_zero_for_projected_static_point_c2w() -> None:
    K = np.array([[100.0, 0.0, 32.0], [0.0, 100.0, 24.0], [0.0, 0.0, 1.0]])
    p0 = np.eye(4)
    p1 = np.eye(4); p1[0, 3] = 0.2
    point_world = np.array([0.1, 0.0, 3.0, 1.0])
    x0_cam = np.linalg.inv(p0) @ point_world
    x1_cam = np.linalg.inv(p1) @ point_world
    x0 = (K @ x0_cam[:3])[:2] / x0_cam[2]
    x1 = (K @ x1_cam[:3])[:2] / x1_cam[2]
    F, t = fundamental_from_pose(K, K, p0, p1, convention="c2w")
    d = sampson_distance(F, x0[None], x1[None])
    assert t > 0
    assert float(d[0]) < 1e-8


def test_epipolar_wrong_correspondence_has_larger_error() -> None:
    K = np.array([[100.0, 0.0, 32.0], [0.0, 100.0, 24.0], [0.0, 0.0, 1.0]])
    p0 = np.eye(4); p1 = np.eye(4); p1[0, 3] = 0.2
    F, _ = fundamental_from_pose(K, K, p0, p1, convention="c2w")
    good = sampson_distance(F, np.array([[35.0, 24.0]]), np.array([[28.333333, 24.0]]))[0]
    bad = sampson_distance(F, np.array([[35.0, 24.0]]), np.array([[60.0, 40.0]]))[0]
    assert bad > good + 1.0
