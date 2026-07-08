# v14 Self Review

Updated: `2026-07-07T23:12:51Z`

## What Improved

- The beta/no-signal root cause is now understood: old beta=0.1 was far too small for observed utility scale.
- CUDA runtime repaired the one-pair real-energy path and calibration4 produced 4/4 real LingBot energy rows.
- DINOv2 and V-JEPA2 local latent monitors now produce real scores without downloads.
- V-JEPA2 distinguishes every available WIN/LOSE pair in broad monitor coverage: 74/74 positive token-relation margins.

## What Still Fails

- v14 did not find a DPO recipe that passes both scalar and true-video gates.
- Scalar-improving schemes still degrade V2V-5 checkpoint videos.
- E07/E09/E10 are not valid recipes despite good winner/gap metrics.
- S_pass and rollout-only latent scoring are blocked by missing old loser video assets.
- all500 real LingBot energy is still blocked by runtime/cache cost and asset completeness.

## Decision

`DPO_RECIPE_NOT_FOUND_V14` and `NO_SCALE` remain correct. Do not run S16/S32/train400/large DPO from v14.

## Next Safe Action

Start v15 as a monitor/regularizer experiment: use V-JEPA2/DINO latent margins to gate or penalize artifact amplification before another tiny calibrated DPO search.

## Artifact Hygiene

Only source/tests/docs and small CSV/JSON/MD summaries were pushed. No videos, images, local_assets, checkpoints, weights, or large logs were pushed.


## Calibration8 real-energy extension

A bounded follow-up run extended real LingBot energy coverage from 4 to 8 asset-complete v11 synthetic controlled pairs on physical GPU5. This strengthens the gap-scale evidence and shows one negative Delta_ref case, but it still does not satisfy all500/S_pass/rollout real-energy coverage and does not change the `DPO_RECIPE_NOT_FOUND_V14` decision.


## Calibration12 real-energy extension

A bounded resume run extended real LingBot energy coverage from 8 to 12 asset-complete v11 synthetic controlled pairs on physical GPU5. The expanded sample still has exactly zero policy-reference utility at initialization, while Delta_ref spans a useful range including one negative row. This strengthens calibration evidence but still does not satisfy all500/S_pass/rollout real-energy coverage and does not change the `DPO_RECIPE_NOT_FOUND_V14` decision.

## v14 Diverse12 Real-Energy Calibration Update (2026-07-08T09:35:00+08:00)

- Built `manifests/dpo_v14_subsets/asset_complete_prefix5_diverse12.jsonl` from 47 asset-complete candidates covering 12 failure types.
- Ran real LingBot energy on physical GPU5 only with `CUDA_VISIBLE_DEVICES=5` and `--runtime_device cuda`.
- Result: `REAL_ENERGY_DIVERSE12_PASS`, 12/12 ok, no OOM/NaN/SIGFPE.
- Delta_ref min / median / mean / max: `-0.0174915` / `0.0086480` / `0.0104745` / `0.0376557`.
- Positive / negative rows: `10 / 2`; the main negative contradiction is `object_duplicate_or_fragment`.
- Beta response: `NONE_ZERO_UTILITY` at policy=reference, expected because policy and frozen reference are identical before update.
- This improves calibration diversity but does not change final DPO decision: `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400/large DPO.

## v14 V-JEPA2 Checkpoint Regression Update (2026-07-08T09:45:00+08:00)

- Built `manifests/dpo_v14_subsets/checkpoint_regression_e09_e10_vjepa_pairs.jsonl` from E09/E10 checkpoint rollouts.
- Ran local V-JEPA2 on physical GPU4 only with `CUDA_VISIBLE_DEVICES=4`; no training.
- Result: 8/8 ok, 8/8 positive V-JEPA margins, 8/8 positive token-relation margins.
- 6/8 rows were Codex-worse-than-step0; V-JEPA2 detected drift for all of them.
- Decision: `CHECKPOINT_REGRESSION_MONITOR_PASS_AS_DRIFT_DETECTOR` for v15 monitor/gate design, not a v14 DPO recipe.
- v14 remains `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400/large DPO.

## v14 V-JEPA2 Gate Statistics Update (2026-07-08T09:55:00+08:00)

- Computed threshold/AUC stats for E09/E10 checkpoint-regression V-JEPA2 margins.
- Token-relation AUC vs Codex worse: `0.5833`; V-JEPA embedding AUC: `0.6667`.
- Conservative high-recall threshold catches all 6 worse rows but has 2 false positives on mixed/not-worse rows.
- Conclusion: V-JEPA2 should be v15 monitor/gate input, not a standalone approval metric.
- v14 remains `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400/large DPO.

## v14 Expanded V-JEPA2 Checkpoint Regression Update (2026-07-08T10:05:00+08:00)

- Built `manifests/dpo_v14_subsets/checkpoint_regression_all_available_vjepa_pairs.jsonl` covering E02/E04/E05/E07/E09/E10 checkpoint regressions.
- Ran local V-JEPA2 on physical GPU4 only with `CUDA_VISIBLE_DEVICES=4`; no training.
- Result: 24/24 ok, 24/24 positive V-JEPA and token-relation margins.
- Codex worse/not-worse rows: `19 / 5`.
- AUC vs Codex worse is low (`0.4632` token relation, `0.4842` embedding), so V-JEPA2 is a drift detector/inspection trigger, not a standalone quality PASS metric.
- v14 remains `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400/large DPO.

## v14 Completion Audit Update (2026-07-08)

- Completion matrix: `reports/dpo_utility_calibration_v14/completion_audit/v14_completion_matrix.md`.
- Current decision: `DPO_RECIPE_NOT_FOUND_V14`.
- Scale permission: `NO_SCALE`; no S16/S32/train400/large DPO is authorized.
- Best scalar candidates had training signal but failed true V2V-5 visual gates:
  - E07: scalar winner signal, but step200 videos were worse on 4/4 fixed-val samples.
  - E09: source-weighted rollout-priority signal, but step50 videos were worse on 4/4 samples.
  - E10: 100-step gap metrics passed, but step100 videos were worse on 2/4 samples and not clearly better on the rest.
- Root blocker: calibrated scalar energy/gap improvements do not yet predict real V2V-5 visual quality; updates amplify foreground duplication, fragments, identity clutter, line/text artifacts, and scene contamination.
- Real-energy calibration improved from one-pair smoke to diverse12: 12/12 ok rows across 12 synthetic failure types, but all500/S_pass/rollout real-energy coverage remains partial because of runtime/cache cost and missing old rollout loser assets.
- V-JEPA2 is useful as a high-recall checkpoint drift / inspection monitor, including 24/24 ok rows in the expanded checkpoint regression run, but it is not a standalone quality approval metric.
- Next safe direction: v15 monitor/regularizer design and artifact-aware checkpoint gating, not additional DPO scale.

## v14 Residual Blocker Plan Update (2026-07-08T10:22 CST)

- Added residual blocker plan: `reports/dpo_utility_calibration_v14/residual_blocker_plan.md`.
- This plan distinguishes completed evidence from partial requirements that remain unproven: all500/S_pass/rollout real-energy coverage, latent monitor approval calibration, metric-wrapper completeness, and pytest availability.
- Decision remains `DPO_RECIPE_NOT_FOUND_V14`; scale permission remains `NO_SCALE`.
- Safe next direction remains v15 artifact-aware monitor/regularizer design using existing E07/E09/E10 checkpoint videos, not additional DPO scale.

## v14 Artifact Regression Aggregation (2026-07-08T10:25 CST)

- Added aggregation: `reports/dpo_utility_calibration_v14/artifact_regression/artifact_regression_summary.md`.
- Source audits: E07 step200, E09 step50, and E10 step100 true V2V-5 checkpoint visual audits.
- Result: scalar-positive schemes consistently fail visual gates. E07 is worse on 4/4, E09 is flagged worse on 4/4; one row is described as at-best-mixed/not-better, and E10 is worse on 2/4 and not decisively better on the rest.
- Dominant failure tags: identity clutter, foreground duplication/fragments, artifact/line-text contamination, with background/camera contamination in some E09 samples.
- Decision remains `DPO_RECIPE_NOT_FOUND_V14`; scale permission remains `NO_SCALE`.
