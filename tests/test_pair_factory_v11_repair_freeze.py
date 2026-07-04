from cam_physgeo.dpo.pair_factory_v11_repair_freeze import condition_id, pair_source, truth


def test_truth_parser():
    assert truth(True)
    assert truth("true")
    assert truth("1")
    assert not truth("false")


def test_condition_and_source_helpers():
    row = {"pair_id": "p", "pair_type": "GT_C", "condition": {"condition_id": "c"}}
    assert condition_id(row) == "c"
    assert pair_source(row) == "rollout_derived"
