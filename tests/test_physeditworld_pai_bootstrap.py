from pathlib import Path


def test_bootstrap_runs_backend_readiness_and_completion_audit():
    text = Path("scripts/migration/bootstrap_pai_physeditworld.sh").read_text(encoding="utf-8")
    assert "verify_pai_physeditworld_handoff.sh" in text
    assert "run_physeditworld_phase0_preflight.sh" in text
    assert "cam_physgeo.orchestration.physeditworld_backend_readiness" in text
    assert "run_physeditworld_completion_audit.sh" in text
    assert "run_physeditworld_pipeline_gates.sh" in text
    assert "run_physeditworld_pai_restore_packet.sh" in text
    assert "write_physeditworld_external_unblock_packet.sh" in text
    assert "physeditworld_50h/backend_readiness" in text
    assert "pai_restore_packet" in text
    assert text.count("run_physeditworld_pai_restore_packet.sh") >= 3
    assert text.rfind("run_physeditworld_pai_restore_packet.sh") > text.rfind("verify_pai_physeditworld_handoff.sh")


def test_bootstrap_remains_non_training():
    text = Path("scripts/migration/bootstrap_pai_physeditworld.sh").read_text(encoding="utf-8")
    forbidden = ["torchrun", "accelerate launch", "train_physeditworld_warmup", "tiny_dpo"]
    assert not any(item in text for item in forbidden)
