
from pathlib import Path

from cam_physgeo.dpo.latent_relation_monitor_v14 import audit

class Args:
    search_roots = ["/path/that/does/not/exist"]
    output_dir = "/tmp/v14_latent_monitor_test"
    max_dirs = 10
    max_seconds = 1.0

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
    result = audit(WeightArgs())
    assert str(weight) in result["candidate_weight_files"]
    assert result["decision"] == "LATENT_MONITOR_BACKEND_FOUND_NEEDS_SCORING"
