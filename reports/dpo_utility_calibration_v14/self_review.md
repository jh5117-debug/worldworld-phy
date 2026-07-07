# v14 Self Review Update

Timestamp: `2026-07-07T02:37:56.080956Z`

E02_best7 found a real training-signal improvement, but the visual audit failed. The final checkpoint step007 introduces visible object duplication/fragments and foreground identity/count drift on validation contact sheets. This is not a scalable DPO recipe.

Safeguards observed:
- No large DPO.
- No train400.
- No StageA/StageB/GRPO/broad-LoRA.
- No checkpoint deletion.
- No large files staged.
- No videos/weights pushed.

Next recommendation:
Continue objective search with a stronger visual regularizer / shorter best-step selection and require video gate before any scale.

## v14 Objective Search Update (2026-07-07T03:56:37.931118Z)

- Added E04_screen5 and E05_screen5 screening runs on physical GPU4/GPU5 only.
- E04_screen5 (`no_lose_gap_normalized_win_only`) training signal PASS: mean winner improvement `0.00012879371643066407`, final `0.00013786554336547852`, WCR `0.7916`, loser degradation negative.
- E05_screen5 (`normalized_clipped_loser`, alpha_l=0.02) training signal PASS: mean winner improvement `0.00012555122375488282`, final `0.00012230873107910156`, WCR `0.8220`, slight loser degradation.
- E04 checkpoint videos generated: `8` true V2V-5 videos. Codex visual audit FAIL: step005 worsens object count/identity in multiple samples.
- Decision remains `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400.

Safeguards: no large DPO, no train400, no StageA/StageB/GRPO, no checkpoint deletion, no videos/weights staged.

## v14 Requirement Audit (2026-07-07T18:10:35Z)

- Requirement audit path: `reports/dpo_utility_calibration_v14/requirement_audit.md`.
- Final decision remains `DPO_RECIPE_NOT_FOUND_V14`.
- All500 energy CSVs are coverage/blocker files with `MISSING_REAL_ENERGY`, not real energy calibration evidence.
- Latent monitor is `LATENT_MONITOR_BLOCKED` because no TRD/VJEPA margins were produced.
- Best scalar candidates E09/E10 failed true V2V-5 visual gates, so S16/S32/train400 remain blocked.
