from cam_physgeo.orchestration.physeditworld_root_onboarding_sequence import OnboardingStep, derive_decision, next_action_for_decision


def test_onboarding_waits_for_filled_template():
    steps = [
        OnboardingStep("write_template_if_missing", "PASS", "PHYS_EDITWORLD_ROOT_SUBMISSION_TEMPLATE_READY", "x"),
        OnboardingStep("validate_submission", "PASS", "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE", "x"),
        OnboardingStep("sample_evidence", "PASS", "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_WAITING_FOR_FILLED_TEMPLATE", "x"),
    ]
    assert derive_decision(steps) == "PHYS_EDITWORLD_ROOT_ONBOARDING_WAITING_FOR_FILLED_TEMPLATE"


def test_onboarding_ready_only_when_validation_and_sampler_ready():
    steps = [
        OnboardingStep("validate_submission", "PASS", "PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_READY_FOR_SCHEMA_PROBE", "x"),
        OnboardingStep("sample_evidence", "PASS", "PHYS_EDITWORLD_ROOT_EVIDENCE_SAMPLER_READY_FOR_SCHEMA_PROBE", "x"),
    ]
    assert derive_decision(steps) == "PHYS_EDITWORLD_ROOT_ONBOARDING_READY_FOR_SCHEMA_PROBE"


def test_next_action_mentions_fill_for_waiting():
    assert "fill" in next_action_for_decision("PHYS_EDITWORLD_ROOT_SUBMISSION_VALIDATION_WAITING_FOR_FILLED_TEMPLATE")
