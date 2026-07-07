def test_v14_scheme_config_reads_recommended_scale():
    from cam_physgeo.dpo.dpo_objective_search_v14 import scheme_config
    cfg = scheme_config('E02', {'recommended_beta': 1000})
    assert cfg['objective'] == 'calibrated_winner_detached_log'
    assert cfg['beta'] == 1000
