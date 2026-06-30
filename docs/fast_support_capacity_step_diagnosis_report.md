# Fast Support / Capacity / Step Diagnosis Report


## Camera Condition Status Correction (2026-06-30 14:21:36)

Current Status: CAMERA_CONDITION_PATH_CONFIRMED_BUT_SENSITIVITY_PARTIAL

Corrected camera status:

- CAMERA_CONDITION_PATH_CONFIRMED
- CAMERA_SENSITIVITY_PARTIAL
- NORMAL_CAMERA_MOTION_RESPONSE_WEAK
- STRONG_CAMERA_PERTURBATION_AFFECTS_OUTPUT

Earlier camera ablation evidence from prior logs:

- repeat A vs B = 0.0
- correct vs frozen = 0.0
- correct vs reversed = 0.02218
- correct vs exaggerated_yaw = 0.03502
- correct vs exaggerated_translation = 0.03765

Interpretation: LingBot-Fast / LingBot supports camera/control and the camera path is not dead. Strong camera perturbations do change output. The remaining issue is not that camera condition never enters the model; it is that ordinary correct-vs-frozen motion has weak response, and reward/pair mining has not yet produced stable human-visible medium-hard camera-difference pairs.

Next work should focus on reward visual alignment and medium-hard pair construction. A future camera audit may refine sensitivity thresholds, but it should not be framed as re-proving the camera path from scratch.


Current Status: BLOCKED_NOT_RUN_AFTER_REWARD_VISUAL_GATE_FAIL

Updated: 2026-06-30 13:33:20

## What Was Run

No new LingBot-Fast camera-variant rollout and no new small-LoRA 500-step training were launched in this round. This is deliberate: the first required gate, reward visual alignment, found Protocol v4 NOT_READY for DPO. Only 3/42 v4 pairs passed strict human-visible medium-hard criteria, while 39 were too subtle.

## Existing Evidence

- DPO smoke v3: engineering path passed, but winner improvement remained weak/negative and loser degradation dominated.
- Candidate generator v2: failed to recover usable TypeB rollout losers; TypeB remains blur/quality blocked.
- StageA V2V-5 warmup: camera-only small LoRA and high-noise-focused warmup are unlikely to repair texture, foreground identity, object deformation, or low-level blur alone.

## Diagnosis

- Too many params: broad-LoRA is not supported and remains disallowed.
- Too few params: possible for camera-only rank4, but not proven; rank4 camera-only primarily affects camera conditioning, not full appearance/physics.
- Too few steps: possible, but longer training is not justified until camera sensitivity is calibrated and pair visibility is fixed.
- High-noise only: likely a real issue for detail/sharpness because it does not strongly supervise low-noise detail.
- Camera condition problem: path confirmed but sensitivity is partial; ordinary correct-vs-frozen response is weak, while strong perturbations affect output.
- Domain support problem: plausible because Original/Fast rollout negatives remain blurry/degraded in this physical moving-camera domain.

## Decision

Do not run DPO and do not launch longer warmup yet. The exact next experiment should be a small Original Fast camera-sensitivity calibration audit on 16 fixed V2V-5 conditions, followed only then by small-LoRA capacity/step scaling if camera has measurable effect.
