
from cam_physgeo.dpo.pair_cache_builder_v8m import _sanitize


def test_sanitize_pair_id_keeps_safe_chars():
    assert _sanitize('a/b c') == 'a_b_c'
    assert _sanitize('pair-01_ok.pt') == 'pair-01_ok.pt'
