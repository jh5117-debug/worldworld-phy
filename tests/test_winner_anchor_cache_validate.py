from __future__ import annotations

import json
from pathlib import Path

import torch

from cam_physgeo.dpo.winner_anchor_cache_builder import sha256_file
from cam_physgeo.dpo.winner_anchor_cache_validate import validate_cache_root


def test_cache_validator_accepts_minimal_valid_cache(tmp_path: Path):
    cache = tmp_path / "cache"
    cache.mkdir()
    payload = {
        "target": torch.zeros(1, 4, 2, 2, 2),
        "noisy_latent": torch.zeros(1, 4, 2, 2, 2),
        "context": [torch.zeros(1, 2)],
        "y": torch.zeros(1, 4, 2, 2, 2),
        "dit_cond": {"cam": (torch.zeros(1, 2),)},
        "seq_len": 4,
        "latent_loss_indices": [2, 3],
        "timestep_tensor": torch.tensor([1.0]),
        "timestep_index": 1,
        "actual_sigma": 0.35,
        "timestep_weight": 1.0,
    }
    tensor_path = cache / "row.pt"
    torch.save(payload, tensor_path)
    row = {
        "pair_id": "pair0",
        "cache_tensor_path": "row.pt",
        "sha256": sha256_file(tensor_path),
        "used_window_frames": 49,
        "prefix_len": 5,
        "prediction_start_frame": 5,
        "E_ref_winner_cached": 0.1,
        "actual_sigma": 0.35,
        "status": "PASS",
    }
    (cache / "cache_index.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    result = validate_cache_root(cache, tmp_path / "validation.csv")
    assert result["status"] == "CACHE_VALIDATION_PASS"
    assert result["pass"] == 1
