from cam_physgeo.dpo.dpo_objective_search_v13b import SCHEMES, scheme_config

def test_scheme_count():
    assert 6 <= len(SCHEMES) <= 10

def test_scheme_mapping():
    assert scheme_config("S01_winner_detached_pref_low")["objective"] == "winner_detached_preference"
    assert scheme_config("S05_normalized_clipped_loser_alpha005")["objective"] == "normalized_clipped_loser"
