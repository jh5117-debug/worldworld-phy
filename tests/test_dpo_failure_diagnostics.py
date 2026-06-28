from __future__ import annotations

import csv
import json
from argparse import Namespace
from pathlib import Path

from cam_physgeo.dpo.failure_diagnostics import build_subsets, run_beta_utility, run_local_mask_audit


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _pair(i: int, pair_type: str, margin: float) -> dict:
    return {
        "pair_id": f"p{i}",
        "pair_type": pair_type,
        "Delta_ref": margin,
        "Delta_policy": margin,
        "winner": {"reward": {"R_total": 1.0}},
        "loser": {
            "reward": {"R_total": 0.7},
            "corruption_type": "wrong_camera_motion_local",
            "affected_time_span": {"start_frame": 20, "end_frame": 40},
            "affected_region": "object_mask",
        },
        "condition": {"image": "x", "prompt": "p", "poses": "pose.npy", "intrinsics": "intr.npy"},
        "codex_audit": {"valid_preference": True},
        "medium_hard": True,
    }


def test_failure_diagnostic_subset_counts(tmp_path: Path) -> None:
    rows = [_pair(i, "gt_vs_medium_hard_rollout", 1.0 + i) for i in range(8)]
    rows += [_pair(100 + i, "local_corruption", 0.1 + i) for i in range(8)]
    ready = tmp_path / "ready.jsonl"
    _write_jsonl(ready, rows)
    build_subsets(
        Namespace(
            ready_pairs=str(ready),
            condition_manifest=str(tmp_path / "missing.jsonl"),
            out_dir=str(tmp_path / "diag"),
            summary_csv=str(tmp_path / "summary.csv"),
        )
    )
    assert sum(1 for _ in (tmp_path / "diag" / "d0_one_pair_typeB.jsonl").open()) == 1
    assert sum(1 for _ in (tmp_path / "diag" / "d1_five_typeB.jsonl").open()) == 5
    assert sum(1 for _ in (tmp_path / "diag" / "d2_five_typeA.jsonl").open()) == 5
    assert sum(1 for _ in (tmp_path / "diag" / "d3_mixed8.jsonl").open()) == 8


def test_beta_utility_outputs_all_betas(tmp_path: Path) -> None:
    inp = tmp_path / "pairs.jsonl"
    _write_jsonl(inp, [_pair(1, "local_corruption", 0.2)])
    out = tmp_path / "beta.csv"
    run_beta_utility(Namespace(inputs=str(inp), out_csv=str(out)))
    rows = list(csv.DictReader(out.open()))
    assert len(rows) == 8
    assert {float(r["beta"]) for r in rows} == {0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0}


def test_local_mask_audit_classifies_missing_spatial_mask(tmp_path: Path) -> None:
    inp = tmp_path / "local.jsonl"
    _write_jsonl(inp, [_pair(1, "local_corruption", 0.2)])
    out = tmp_path / "mask.csv"
    run_local_mask_audit(Namespace(pair_manifest=str(inp), out_csv=str(out)))
    row = list(csv.DictReader(out.open()))[0]
    assert row["affected_time_span_exists"] == "True"
    assert row["affected_region_exists"] == "True"
    assert row["affected_mask_exists"] == "False"
    assert row["current_localdpo_level"] == "metadata_region_only"
