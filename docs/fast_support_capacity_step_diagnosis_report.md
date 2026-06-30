# Fast Support / Capacity / Step Diagnosis Report

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
- Too few steps: possible, but longer training is not justified until camera-condition use and pair visibility are fixed.
- High-noise only: likely a real issue for detail/sharpness because it does not strongly supervise low-noise detail.
- Camera condition problem: still unknown; must run correct/frozen/reversed/exaggerated/shuffled camera audit.
- Domain support problem: plausible because Original/Fast rollout negatives remain blurry/degraded in this physical moving-camera domain.

## Decision

Do not run DPO and do not launch longer warmup yet. The exact next experiment should be a small Original Fast camera-condition sensitivity audit on 16 fixed V2V-5 conditions, followed only then by small-LoRA capacity/step scaling if camera has measurable effect.
