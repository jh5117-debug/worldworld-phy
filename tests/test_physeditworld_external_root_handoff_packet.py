from cam_physgeo.orchestration.physeditworld_external_root_handoff_packet import PacketRow, derive_decision, next_action


def test_packet_waits_for_filled_template():
    rows = [PacketRow("root_onboarding", "x", True, "PHYS_EDITWORLD_ROOT_ONBOARDING_WAITING_FOR_FILLED_TEMPLATE")]
    assert derive_decision(rows) == "PHYS_EDITWORLD_EXTERNAL_ROOT_HANDOFF_WAITING_FOR_FILLED_TEMPLATE"


def test_packet_ready_when_onboarding_ready():
    rows = [PacketRow("root_onboarding", "x", True, "PHYS_EDITWORLD_ROOT_ONBOARDING_READY_FOR_SCHEMA_PROBE")]
    assert derive_decision(rows) == "PHYS_EDITWORLD_EXTERNAL_ROOT_HANDOFF_READY_FOR_SCHEMA_PROBE"


def test_next_action_for_template_ready_mentions_tsv():
    assert "TSV" in next_action("root_template", "PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY")
