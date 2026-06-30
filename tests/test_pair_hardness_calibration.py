from cam_physgeo.dpo.pair_hardness import classify_hardness, summarize_hardness


def test_medium_hard_candidate_passes():
    decision = classify_hardness(
        reward_margin=0.22,
        sharpness_ratio=0.9,
        visual_quality=2,
        alignment_pass=True,
        main_failure="object_deformation_local",
        lpips_future=0.12,
        ssim_future=0.75,
    )
    assert decision["hardness"] == "MEDIUM_HARD"
    assert decision["medium_hard"] is True


def test_too_subtle_from_low_margin():
    decision = classify_hardness(
        reward_margin=0.04,
        sharpness_ratio=0.9,
        visual_quality=2,
        alignment_pass=True,
        main_failure="background_drift_local",
    )
    assert decision["hardness"] == "TOO_SUBTLE"


def test_too_degraded_from_blur():
    decision = classify_hardness(
        reward_margin=0.25,
        sharpness_ratio=0.4,
        visual_quality=0,
        alignment_pass=True,
        main_failure="blur",
    )
    assert decision["hardness"] == "TOO_DEGRADED"
    assert "sharpness_ratio_lt_min" in decision["reasons"]


def test_summary_counts():
    summary = summarize_hardness([
        {"hardness": "MEDIUM_HARD"},
        {"hardness": "TOO_SUBTLE"},
        {"hardness": "TOO_DEGRADED"},
        {"hardness": "UNKNOWN"},
    ])
    assert summary == {"MEDIUM_HARD": 1, "TOO_SUBTLE": 1, "TOO_DEGRADED": 1, "OTHER": 1}
