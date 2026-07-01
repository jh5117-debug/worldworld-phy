from __future__ import annotations

import csv
from pathlib import Path

from cam_physgeo.dpo.sigma_timestep_debug import (
    build_rows,
    default_sigma_schedule,
    distributions_are_separated,
    parse_bins,
    sigma_status_by_bin,
)


def test_parse_bins_rejects_unknown() -> None:
    try:
        parse_bins("low,bogus")
    except ValueError as exc:
        assert "bogus" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_default_schedule_covers_low_mid_high() -> None:
    rows = build_rows(
        bins=["low", "mid", "high"],
        num_samples_per_bin=20,
        schedule=default_sigma_schedule(1000),
        scheduler_name="test",
    )
    status = sigma_status_by_bin(rows)
    assert status == {"low": "PASS", "mid": "PASS", "high": "PASS"}
    assert distributions_are_separated(rows, ["low", "mid", "high"])
    means = []
    for bin_name in ["low", "mid", "high"]:
        vals = [float(row["actual_sigma"]) for row in rows if row["requested_bin"] == bin_name]
        means.append(sum(vals) / len(vals))
    assert means[0] < means[1] < means[2]


def test_rows_have_required_fields() -> None:
    rows = build_rows(
        bins=["low"],
        num_samples_per_bin=2,
        schedule=default_sigma_schedule(10),
        scheduler_name="test",
    )
    required = {
        "requested_bin",
        "sample_idx",
        "timestep",
        "actual_sigma",
        "scheduler_name",
        "sigma_min",
        "sigma_max",
        "bin_low",
        "bin_high",
        "status",
    }
    assert required <= set(rows[0])
