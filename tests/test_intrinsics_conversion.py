from __future__ import annotations

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cam_physgeo.utils.camera import convert_projection_to_lingbot_intrinsics


def test_projection_stack_to_lingbot_vector():
    mats = np.repeat(np.eye(4, dtype=np.float32)[None], 3, axis=0)
    mats[:, 0, 0] = 1.25
    mats[:, 1, 1] = 2.0
    converted, meta = convert_projection_to_lingbot_intrinsics(mats, width=832, height=480, convention="tdw_opengl")
    assert converted.shape == (3, 4)
    assert np.all(np.isfinite(converted))
    assert np.all(converted[:, 0] > 0)
    assert np.all(converted[:, 1] > 0)
    assert np.allclose(converted[:, 0], 1.25 * 832 / 2)
    assert np.allclose(converted[:, 1], 2.0 * 480 / 2)
    assert np.allclose(converted[:, 2], 832 / 2)
    assert np.allclose(converted[:, 3], 480 / 2)
    assert meta["source_format"] == "projection4x4_to_pixel_vector"


def test_vector_intrinsics_pass_through_without_mutation():
    raw = np.array([[500.0, 510.0, 416.0, 240.0], [501.0, 511.0, 416.0, 240.0]], dtype=np.float32)
    before = raw.copy()
    converted, meta = convert_projection_to_lingbot_intrinsics(raw, width=832, height=480)
    assert converted.shape == (2, 4)
    assert np.allclose(converted, raw)
    assert np.allclose(raw, before)
    assert meta["source_format"] == "vector_per_frame"


def test_single_projection_expands_to_one_frame():
    mat = np.eye(4, dtype=np.float32)
    converted, meta = convert_projection_to_lingbot_intrinsics(mat, width=832, height=480, convention="tdw_opengl")
    assert converted.shape == (1, 4)
    assert meta["expanded_single_matrix"] is True


def test_bad_shape_raises():
    bad = np.zeros((2, 5), dtype=np.float32)
    try:
        convert_projection_to_lingbot_intrinsics(bad, width=832, height=480)
    except ValueError as exc:
        assert "unsupported intrinsics shape" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("bad shape should raise ValueError")


if __name__ == "__main__":
    test_projection_stack_to_lingbot_vector()
    test_vector_intrinsics_pass_through_without_mutation()
    test_single_projection_expands_to_one_frame()
    test_bad_shape_raises()
