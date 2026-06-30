
import json
from pathlib import Path


def test_small_lora_scaling_not_started_after_reward_gate_fail():
    decision = json.loads(Path("reports/fast_support_diagnosis/small_lora_scaling/decision.json").read_text())
    assert decision["current_status"] == "BLOCKED_NOT_RUN_AFTER_REWARD_VISUAL_GATE_FAIL"
    assert decision["steps_run"] == 0
    assert decision["configs_run"] == []
    assert "camera-condition" in decision["next_required_experiment"]
