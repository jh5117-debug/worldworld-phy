from __future__ import annotations

from cam_physgeo.data.physeditworld_split import leakage_rows, split_by_replay_group


def test_split_keeps_replay_group_together():
    rows = [
        {"sample_id": "a", "replay_group_id": "g1"},
        {"sample_id": "b", "replay_group_id": "g1"},
        {"sample_id": "c", "replay_group_id": "g2"},
    ]
    splits = split_by_replay_group(rows, val_ratio=0.2, test_ratio=0.2)
    leaks = leakage_rows(splits)
    assert all(row["status"] == "OK" for row in leaks)
    locations = {split for split, values in splits.items() if any(v["replay_group_id"] == "g1" for v in values)}
    assert len(locations) == 1
