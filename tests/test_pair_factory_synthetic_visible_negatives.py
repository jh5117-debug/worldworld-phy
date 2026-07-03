
from cam_physgeo.dpo.pair_factory_synthetic_visible_negatives import stable_int, bbox_for


def test_stable_int_reproducible():
    assert stable_int("abc") == stable_int("abc")


def test_bbox_within_frame():
    x, y, w, h = bbox_for("sample", 832, 480)
    assert 0 <= x < 832
    assert 0 <= y < 480
    assert x + w <= 832
    assert y + h <= 480
