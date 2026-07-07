# E06 Fixed V2V-5 Visual Audit

Status: `VISUAL_GATE_FAIL_STEP20_WORSE`

What changed:
- `run_v2v5_inference.py` now supports `.pt` LoRA state checkpoints as `--adapter_path`/`--lora_state` inputs.
- E06 step020 true V2V-5 smoke completed with exit code 0.
- E06 step000 true V2V-5 smoke completed with exit code 0 on the same condition.

Visual decision:
- Step0 is already imperfect: foreground clutter and wall/label artifacts appear in generated future frames.
- Step20 is worse: more chain-like foreground fragments, white line artifacts, right-side duplicate objects, and stronger scene contamination.
- Therefore E06 remains a training-signal candidate only, not a valid DPO recipe.

Current conclusion:
- Training metrics alone are misleading here.
- E06 does not solve the DPO training problem because checkpoint video quality regresses.
- No scale / no train400 / no large DPO is allowed from this result.
