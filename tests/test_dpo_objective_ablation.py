from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import torch

from cam_physgeo.dpo.objective_ablation import (
    affected_latent_indices,
    build_subsets,
    compute_objective_loss,
    reward_to_pair_weight,
)


def _pair(pair_id: str, pair_type: str, energy: float, reward: float, corruption: str = "local") -> dict:
    return {
        "pair_id": pair_id,
        "pair_type": pair_type,
        "same_prefix": True,
        "same_prompt": True,
        "same_poses": True,
        "same_intrinsics": True,
        "energy_audit": {"Delta_ref": energy, "Delta_policy": energy, "reference_relative_margin": 0.0},
        "winner": {"reward": {"R_total": reward}},
        "loser": {
            "reward": {"R_total": 0.0},
            "corruption_type": corruption,
            "affected_time_span": "future_frames_5_80",
            "affected_region": "mask",
        },
        "condition": {"prefix_len": 5, "prediction_start_frame": 5, "image": "x", "prompt": "p", "poses": "poses.npy", "intrinsics": "intr.npy"},
        "codex_audit": {"valid_preference": True},
        "medium_hard": True,
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_subset_builder_counts(tmp_path: Path) -> None:
    type_b = [_pair(f"b{i}", "gt_vs_medium_hard_rollout", 1.0 + i, 0.2 + i * 0.01) for i in range(16)]
    type_a = [_pair(f"a{i}", "local_corruption", 0.1 + i, 0.15 + i * 0.01, corruption=f"c{i % 4}") for i in range(34)]
    ready = tmp_path / "ready.jsonl"
    local = tmp_path / "local.jsonl"
    _write_jsonl(ready, type_b + type_a)
    _write_jsonl(local, type_a)
    build_subsets(
        Namespace(
            ready_pairs=str(ready),
            localdpo_pairs=str(local),
            condition_manifest=str(tmp_path / "missing.jsonl"),
            out_dir=str(tmp_path / "subsets"),
            summary_csv=str(tmp_path / "summary.csv"),
        )
    )
    assert sum(1 for _ in (tmp_path / "subsets" / "s0_sanity_8.jsonl").open()) == 8
    assert sum(1 for _ in (tmp_path / "subsets" / "s1_probe_20.jsonl").open()) == 20
    assert sum(1 for _ in (tmp_path / "subsets" / "s_localdpo_16.jsonl").open()) == 16


def test_sdpo_style_reduces_loser_when_winner_worsens() -> None:
    result = compute_objective_loss(
        "sdpo",
        policy_winner=torch.tensor(1.2),
        policy_loser=torch.tensor(1.5),
        ref_winner=torch.tensor(1.0),
        ref_loser=torch.tensor(1.1),
        beta=0.1,
    )
    assert torch.isfinite(result.loss)
    assert result.lambda_loser == 0.0


def test_linear_objective_has_clipped_finite_loss() -> None:
    result = compute_objective_loss(
        "linear",
        policy_winner=torch.tensor(0.8),
        policy_loser=torch.tensor(2.2),
        ref_winner=torch.tensor(1.0),
        ref_loser=torch.tensor(1.1),
        beta=0.1,
        reward_margin=0.45,
        u_clip=1.0,
    )
    assert torch.isfinite(result.loss)
    assert result.pair_weight == reward_to_pair_weight(0.45)
    assert abs(result.u_clipped) <= 1.0


def test_localdpo_affected_indices_exclude_prefix() -> None:
    indices = affected_latent_indices((20, 40), total_frames=81, prefix_len=5, latent_frames=21, temporal_compression=4)
    assert indices
    assert all(idx * 4 <= 40 and (idx + 1) * 4 - 1 >= 20 for idx in indices)
    full = affected_latent_indices("future_frames_5_80", total_frames=81, prefix_len=5, latent_frames=21, temporal_compression=4)
    assert min(full) >= 1
