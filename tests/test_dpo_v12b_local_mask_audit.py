
from cam_physgeo.dpo.dpo_v12b_local_mask_audit import audit_mask


def test_local_mask_ready_requires_time_and_space():
    out = audit_mask({'pair_id': 'p', 'loser': {'affected_region': [0,0,1,1], 'affected_time_span': [5,10]}})
    assert out['localdpo_ready']
    assert not out['time_only']
