
from cam_physgeo.dpo.v14_pair_inventory import enrich, is_synthetic, is_rollout, local_ready

def test_v14_pair_inventory_flags():
    row = {"pair_id": "p", "pair_source": "synthetic controlled", "loser": {"affected_time_span": [5, 20]}, "codex_visual_audit": {"reviewed": True}}
    assert is_synthetic(row)
    assert not is_rollout(row)
    assert local_ready(row)
    out = enrich(row)
    assert out["v14_reviewed"] is True
