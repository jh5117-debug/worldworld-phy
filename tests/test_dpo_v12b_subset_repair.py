import json
from pathlib import Path

from cam_physgeo.dpo.dpo_v12b_subset_repair import is_clean, has_region, has_time, source


def test_clean_gate_accepts_reviewed_pair():
    row = {'medium_hard': True, 'codex_visual_audit': {'reviewed': True, 'is_dpo_ready': True, 'medium_hard': True, 'written_reason': 'clear visible failure'}}
    assert is_clean(row)


def test_local_flags():
    assert has_region({'loser': {'affected_region': [0, 0, 1, 1]}})
    assert has_time({'loser': {'affected_time_span': [5, 20]}})


def test_gt_c_is_rollout_source():
    assert source({'pair_type': 'GT_C', 'is_synthetic': True}) == 'rollout'


def test_typem_is_synthetic_source():
    assert source({'pair_type': 'TypeM_v10_synthetic_visible'}) == 'synthetic'
