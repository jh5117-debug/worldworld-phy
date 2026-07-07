
from pathlib import Path

import torch

from cam_physgeo.dpo.latent_relation_monitor_v14 import audit, map_dinov2_vits14_state_dict, pick_frame_indices

class Args:
    search_roots = ["/path/that/does/not/exist"]
    output_dir = "/tmp/v14_latent_monitor_test"
    max_dirs = 10
    max_seconds = 1.0
    include_known_candidates = False

def test_latent_audit_no_fake_values():
    result = audit(Args())
    assert "decision" in result
    assert "candidate_files" in result
    assert "candidate_weight_files" in result
    assert result["decision"] == "LATENT_MONITOR_BLOCKED_BY_ENV"

def test_latent_audit_requires_weight_file(tmp_path):
    code = tmp_path / "vjepa2_encoder.py"
    code.write_text("# code only\n")
    class CodeOnlyArgs:
        search_roots = [str(tmp_path)]
        output_dir = str(tmp_path / "out")
        max_dirs = 10
        max_seconds = 1.0
        include_known_candidates = False
    result = audit(CodeOnlyArgs())
    assert str(code) in result["candidate_files"]
    assert result["candidate_weight_files"] == []
    assert result["decision"] == "LATENT_MONITOR_BLOCKED_BY_ENV"

def test_latent_audit_detects_local_weight_candidate(tmp_path):
    weight = tmp_path / "vjepa2_small.pt"
    weight.write_bytes(b"x")
    class WeightArgs:
        search_roots = [str(tmp_path)]
        output_dir = str(tmp_path / "out")
        max_dirs = 10
        max_seconds = 1.0
        include_known_candidates = False
    result = audit(WeightArgs())
    assert str(weight) in result["candidate_weight_files"]
    assert result["decision"] == "LATENT_MONITOR_BACKEND_FOUND_NEEDS_SCORING"


def test_map_dinov2_qkv_keys():
    sd = {
        "cls_token": torch.zeros(1, 1, 384),
        "pos_embed": torch.zeros(1, 1370, 384),
        "patch_embed.proj.weight": torch.zeros(384, 3, 14, 14),
        "blocks.0.attn.qkv.weight": torch.cat([
            torch.full((384, 384), 1.0),
            torch.full((384, 384), 2.0),
            torch.full((384, 384), 3.0),
        ], dim=0),
        "blocks.0.attn.qkv.bias": torch.cat([
            torch.full((384,), 4.0),
            torch.full((384,), 5.0),
            torch.full((384,), 6.0),
        ], dim=0),
    }
    mapped = map_dinov2_vits14_state_dict(sd)
    assert "embeddings.cls_token" in mapped
    assert mapped["encoder.layer.0.attention.attention.query.weight"].mean().item() == 1.0
    assert mapped["encoder.layer.0.attention.attention.key.weight"].mean().item() == 2.0
    assert mapped["encoder.layer.0.attention.attention.value.weight"].mean().item() == 3.0
    assert mapped["encoder.layer.0.attention.attention.query.bias"].mean().item() == 4.0
    assert mapped["encoder.layer.0.attention.attention.key.bias"].mean().item() == 5.0
    assert mapped["encoder.layer.0.attention.attention.value.bias"].mean().item() == 6.0


def test_pick_frame_indices_spans_future():
    pair = {"winner": {"future_frame_indices": list(range(5, 81))}}
    assert pick_frame_indices(pair, 5) == [5, 24, 43, 61, 80]
