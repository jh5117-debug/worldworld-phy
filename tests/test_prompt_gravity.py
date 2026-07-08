from cam_physgeo.data.prompt_gravity import build_prompt_gravity, validate_prompt


def test_prompt_gravity_v0_has_token_and_no_future_leak():
    prompt = build_prompt_gravity(0.25)
    assert "gravity: 0.25g" in prompt
    assert validate_prompt(prompt) == []


def test_prompt_rejects_future_leak():
    assert "future_answer_leak" in validate_prompt("gravity: 1.0g and will land at frame 20")
