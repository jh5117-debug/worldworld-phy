
from cam_physgeo.dpo.pair_factory_existing_pair_audit import boolish, as_float


def test_boolish_values():
    assert boolish("true") is True
    assert boolish("yes") is True
    assert boolish("False") is False
    assert boolish("") is None


def test_as_float_defaults():
    assert as_float("0.25") == 0.25
    assert as_float("BLOCKED", 1.0) == 1.0
