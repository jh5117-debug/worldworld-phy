
from cam_physgeo.dpo.latent_relation_monitor_v14 import audit

class Args:
    search_roots = ["/path/that/does/not/exist"]
    output_dir = "/tmp/v14_latent_monitor_test"

def test_latent_audit_no_fake_values():
    result = audit(Args())
    assert "decision" in result
    assert "candidate_files" in result
