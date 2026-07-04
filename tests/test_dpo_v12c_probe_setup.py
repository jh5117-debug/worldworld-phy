
from cam_physgeo.dpo.dpo_v12c_probe_setup import pair_source, has_region, has_time


def test_gt_c_source_is_rollout():
    assert pair_source({'pair_type': 'GT_C', 'is_synthetic': True}) == 'rollout'


def test_typem_source_is_synthetic():
    assert pair_source({'pair_type': 'TypeM_v10_synthetic_visible'}) == 'synthetic'


def test_mask_helpers():
    row = {'loser': {'affected_region': [0, 0, 1, 1], 'affected_time_span': [5, 20]}}
    assert has_region(row)
    assert has_time(row)
