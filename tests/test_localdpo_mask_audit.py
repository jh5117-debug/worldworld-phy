from __future__ import annotations

import csv
import json
from argparse import Namespace
from pathlib import Path

from cam_physgeo.dpo.failure_diagnostics import run_local_mask_audit


def test_localdpo_mask_audit_detects_spatial_mask(tmp_path: Path) -> None:
    pair = {
        "pair_id": "p0",
        "pair_type": "local_corruption",
        "loser": {
            "corruption_type": "background_drift_local",
            "affected_time_span": {"start_frame": 5, "end_frame": 20},
            "affected_region": "background",
            "affected_mask_path": "mask.png",
        },
    }
    manifest = tmp_path / "pairs.jsonl"
    manifest.write_text(json.dumps(pair) + "\n")
    out = tmp_path / "audit.csv"
    run_local_mask_audit(Namespace(pair_manifest=str(manifest), out_csv=str(out)))
    row = list(csv.DictReader(out.open()))[0]
    assert row["affected_mask_exists"] == "True"
    assert row["current_localdpo_level"] == "spatial_region"
