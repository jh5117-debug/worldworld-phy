
from cam_physgeo.dpo.dpo_v12c_guarded_probe import mapped_objective


def test_warmstart_maps_to_winner_anchor_repeat():
    assert mapped_objective('winner_only_warmstart') == 'winner_anchor_repeat'


def test_winner_detached_objective_kept():
    assert mapped_objective('winner_detached_preference') == 'winner_detached_preference'
