import csv
from pathlib import Path

from cam_physgeo.dpo.dpo_v12b_winner_anchor_diag import summarize_pair, sanitize, append_rows


def test_sanitize_keeps_safe_chars():
    assert sanitize('a/b c:1') == 'a_b_c_1'


def test_summarize_pair_pass():
    rows = [
        {'status': 'PASS', 'winner_improvement_post': '0.1', 'grad_norm': '1', 'update_norm': '1', 'finite': 'True'},
        {'status': 'PASS', 'winner_improvement_post': '0.2', 'grad_norm': '1', 'update_norm': '1', 'finite': 'True'},
    ]
    assert summarize_pair(rows, 2)['decision'] == 'S_PASS'


def test_append_rows_writes_header(tmp_path: Path):
    out = tmp_path / 'rows.csv'
    append_rows(out, [{'pair_index': 0, 'pair_id': 'p0', 'status': 'PASS'}])
    with out.open() as f:
        rows = list(csv.DictReader(f))
    assert rows[0]['pair_id'] == 'p0'
