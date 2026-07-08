# EXP: DPO Utility Calibration and Latent Monitor v14

## Current Status

- Canonical repaired ready500 manifest exists.
- v13b failed to find a valid DPO recipe.
- `S07_linear_winner_detached` had the best winner-positive training signal, but failed the checkpoint metric gate because VBench temporal_flickering worsened.
- Most v13b schemes had preference utility around 1e-4 and DPO loss near 0.693.
- Current blocker is utility / gap scale, not data availability.
- This run uses only H20 physical GPU4 and GPU5.
- No large DPO is allowed.

## Problem

DPO preference training is not yet entering a useful optimization regime. Likely failure modes include signal dilution from energy reduction, too-small beta, policy/reference closeness, mild synthetic pairs, full-future mask dilution, win/lose gap noise-scale mismatch, uncalibrated normalized gaps, and unvalidated V-JEPA / VideoREPA / TRD latent relation signal.

## Hypothesis

Per-sigma/per-pair normalization, empirical beta calibration, local/time masks, pair-source weighting, and latent relation monitoring can identify a usable preference objective or prove the exact blocker before any scale.

## Inputs

- `manifests/dpo_pair_factory_v11_ready_500_canonical.jsonl`
- `manifests/dpo_pair_factory_v11_train400_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_val50_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_test50_repaired.jsonl`
- `manifests/dpo_pair_factory_v11_top50_demo_repaired.jsonl`
- `manifests/dpo_v12b_subsets/s_pass_winner_anchor.jsonl`
- `manifests/dpo_v12b_subsets/s_fail_winner_anchor.jsonl`
- `manifests/dpo_v12b_subsets/val_video_4.jsonl`
- `manifests/dpo_v13b_subsets/s4_pass.jsonl` if present
- `manifests/dpo_v13b_subsets/s8_pass_expand.jsonl` if present
- `manifests/dpo_v13b_subsets/s16_confident.jsonl` if present
- `manifests/dpo_v13b_subsets/s4_local_mask.jsonl` if present
- v12b warm-start LoRA: `local_assets/dpo_objective_repair_v12b/winner_curriculum/checkpoints/winner_anchor_repeat_L0_camera_r4_step020_lora_state.pt`

## GPU Policy

Allowed physical GPUs: 4 and 5. Forbidden physical GPUs: 0, 1, 2, 3, 6, 7. Every GPU command must set `CUDA_VISIBLE_DEVICES=4` or `CUDA_VISIBLE_DEVICES=5`. Two single-GPU jobs may run in parallel. DDP is not used. Unknown GPU processes are never killed.

## Phase A: Pair Inventory

Build v14 subsets: all500, s_pass, s_fail, rollout_only, synthetic_controlled, stratified100, and local_mask. Report source, failure, reward-margin, visual-audit, local-mask, rollout, and synthetic distributions.

## Phase B: Offline Energy / Utility Calibration

For required subsets, compute real LingBot energy when runtime allows: raw energies, raw gaps, winner/loser directions, `u_raw`, `u_log`, `u_z`, `u_mad`, per-token/reduction variants, local-mask variants, sigma/timestep/bin metadata, and source/failure/reward metadata. Rows must append incrementally and failed rows must record status/error_reason. No fake energy.

## Phase C: Beta / Lambda / Loss Response Sweep

Sweep beta from 0.01 to 1000 for raw/log/z/MAD/local utilities. Report logit, DPO loss response, gradient scale, near-zero/effective/saturation ratios, and recommended utility/beta/clip/pair filter. Must explain why beta=0.1 was ineffective.

## Phase D: V-JEPA / VideoREPA / TRD Latent Monitor

Audit local V-JEPA / VideoREPA / VideoMAE / DINOv2 / CLIP-video / feature-cache availability. Do not download models. If no backend exists, write `LATENT_MONITOR_BLOCKED`. If backend exists, compute winner/loser distance margins and correlation with reward/visual audit. Monitor only, no training.

## Phase E: Normalization / Regularization Design

Recommend per-token/local/sigma-bin reduction, log/z/MAD normalization, empirical beta, clipped/detached loser handling, winner protection, local mask rules, and v15 latent auxiliary preconditions.

## Phase F: 10 Calibrated Objective Schemes

Only after `recommended_dpo_scale.json` exists. Candidate schemes E01-E10 cover raw/log/z calibrated winner-detached, normalized winner-only, clipped loser alpha 0.02/0.05, linear best utility, local time mask, source-weighted rollout priority, and L2 camera-temporal calibrated. Each scheme is <=200 steps, starts on S4/S8, and never exceeds S16 in this round.

## Checkpoint Video + Metrics Gate

Only training-signal-pass schemes get true V2V-5 checkpoint evaluation. Required: PSNR, SSIM, LPIPS, real FVD smoke if available, VBench temporal_flickering, PhysGeo, and Codex visual audit. No image-only or prefix_len=1 fallback.

## Success Gate

Offline calibration covers ready500 + S_pass + rollout/synthetic/local subsets; beta/u distribution is reported; best reduction and normalization are identified; latent monitor passes or reports exact blocker; 10 schemes are attempted or skipped with justified blockers; at least one scheme passes training + video + metrics to declare recipe found; no forbidden GPU use.

## Failure Gate

Missing all-pair statistics; fake VJEPA/TRD/FVD/VBench values; missing visual audit for promising checkpoint; scheme selected by loss only; any forbidden GPU use; large DPO/train400 starts accidentally.

## What Is Not Run

No train400, no large DPO, no S32/S64, no StageA, no StageB, no GRPO, no broad-LoRA, no checkpoint deletion, no video/image/checkpoint/local_assets push.

## Output Paths

- `reports/dpo_utility_calibration_v14/`
- `manifests/dpo_v14_subsets/`
- `docs/dpo_utility_calibration_v14_report.md`
- `configs/cam_physgeo/dpo_objective_v14_normalized.yaml`
- `configs/cam_physgeo/dpo_search_v14.yaml`
- `configs/cam_physgeo/dpo_v14_scheduler.yaml`

## Post-Run Update 2026-07-07

- Pair inventory completed for canonical ready500 and v14 subsets.
- Real LingBot energy smoke on one S_pass pair timed out after 300 seconds before writing a row, so all500 real-energy calibration remains blocked.
- v14 `energy_utility_*.csv` files currently mark `MISSING_REAL_ENERGY`; they are not real energy evidence.
- Beta/loss response from v13b real training CSVs shows beta=0.1 was under-scaled: median |beta*u_log| was about 2e-5 and near-zero ratio was 1.0.
- Recommended first calibrated tiny probe is log utility with beta around 1000, loser detached, explicit winner anchor, and mandatory video/metric/Codex audit.
- Latent monitor backend audit found local candidates but did not produce TRD/VJEPA scores; no latent auxiliary loss is enabled.
- No train400, large DPO, StageA, StageB, GRPO, or broad-LoRA was run.


## v14 E09/E10 Final Visual Gate Update (2026-07-07T17:56:59Z)

- E09 (, L0 camera r4) reached strong early scalar signal at step50: winner improvement , WCR , loser degradation negative. True V2V-5 audit failed: step50 was worse/not-better on 4/4 fixed validation samples, with foreground duplication, colored blob fragments, and line/text-like artifacts.
- E10 (, L2 camera-temporal r4) completed 100/100 steps with final winner improvement  and mean WCR . True V2V-5 audit failed: step100 was worse on 2/4 samples and not decisively better on the rest, with duplicate green balls, object identity clutter, and foreground fragments.
- Current decision: . The scalar no-signal / beta-scale issue is partially repaired, but energy/gap improvement does not yet predict rollout visual quality.
- Scale permission: ; no S16/S32/train400/large DPO from these recipes. Next direction is a rollout-quality or latent visual monitor/regularizer before further DPO scaling.

## v14 Scheduler Artifact Update (2026-07-07T18:24:43Z)

- Added `cam_physgeo/orchestration/gpu_scheduler_v14.py`.
- Added `scripts/launch_dpo_v14_scheduler.sh`.
- Added `tests/test_gpu_scheduler_v14.py`.
- Smoke output path: `reports/dpo_utility_calibration_v14/scheduler_state.json` and `scheduler_state_summary.md`.
- Scheduler decision: `NO_TRAINING_NO_SCALE`; it records GPU/state evidence and does not launch training after `DPO_RECIPE_NOT_FOUND_V14`.


## v14 Final Requirement Audit Update (2026-07-07T23:12:51Z)

- Current authoritative audit: `reports/dpo_utility_calibration_v14/requirement_audit.md`.
- Final decision remains `DPO_RECIPE_NOT_FOUND_V14` / `NO_SCALE`.
- V-JEPA2 monitor status is now `PASS_WITH_ASSET_BLOCKERS`, not backend-only blocked: 74/74 available rows have positive token-relation margins.
- Remaining blockers are true-video degradation for scalar-positive DPO schemes, missing old rollout loser assets, and all500 real-energy runtime/cache cost.
- No S16/S32/train400/large DPO is allowed from v14.

## v14 Calibration8 Real-Energy Update (2026-07-08T07:58:00+08:00)

- Built a larger asset-complete Prefix5 manifest: `manifests/dpo_v14_subsets/asset_complete_prefix5_calibration12.jsonl`.
- Adapter summary: `reports/dpo_utility_calibration_v14/blocker_retry/asset_complete_prefix5_calibration12_adapter_summary.json`.
- Ran bounded real LingBot energy on physical GPU5 with `CUDA_VISIBLE_DEVICES=5`, `--runtime_device cuda`, `--limit 8`.
- Real-energy output: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration12_cuda_runtime_limit8/shard_00_of_01.csv`.
- Summary: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration12_cuda_runtime_limit8/real_energy_calibration8_summary.md`.
- Result: `REAL_ENERGY_CALIBRATION8_PASS`, 8/8 rows ok, no OOM/NaN/SIGFPE.
- Delta_ref range: `-0.00189158` to `0.01883214`; mean `0.00802792`; median `0.00748671`; 7 positive rows and 1 negative row.
- Mean per-row energy time: about `184.01s`; peak CUDA memory about `50.43GB`.
- Standardized utility CSV: `reports/dpo_utility_calibration_v14/energy_utility_calibration8_real.csv`.
- Beta response: `reports/dpo_utility_calibration_v14/beta_loss_response_calibration8_real.csv` and `reports/dpo_utility_calibration_v14/recommended_dpo_scale_calibration8_real.json`.
- Beta conclusion: at policy=reference, observed `u_raw/u_log` is exactly zero, so recommendation is `NONE_ZERO_UTILITY`; beta cannot create preference signal without a nonzero policy-reference utility change.
- Scope: calibration only. No DPO training, no S16/S32/train400/large DPO. all500/S_pass/rollout real-energy coverage remains incomplete, but bounded real-energy evidence improved from 4 rows to 8 rows.

## v14 Calibration12 Real-Energy Update (2026-07-08T08:26:00+08:00)

- Resumed the bounded asset-complete real LingBot energy run on physical GPU5 with `CUDA_VISIBLE_DEVICES=5`, `--runtime_device cuda`, and `--resume`.
- Real-energy output: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration12_cuda_runtime_limit8/shard_00_of_01.csv`.
- Summary: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration12_cuda_runtime_limit8/real_energy_calibration12_summary.md`.
- Result: `REAL_ENERGY_CALIBRATION12_PASS`, 12/12 rows ok, no OOM/NaN/SIGFPE.
- Delta_ref range: `-0.00189158` to `0.02060417`; mean `0.00877969`; median `0.00718332`; 11 positive rows and 1 negative row.
- Mean per-row energy time: about `186.19s`; peak CUDA memory remains about `50.43GB`.
- Standardized utility CSV: `reports/dpo_utility_calibration_v14/energy_utility_calibration12_real.csv`.
- Beta response: `reports/dpo_utility_calibration_v14/beta_loss_response_calibration12_real.csv` and `reports/dpo_utility_calibration_v14/recommended_dpo_scale_calibration12_real.json`.
- Beta conclusion remains `NONE_ZERO_UTILITY` at policy=reference: beta cannot create preference signal without a nonzero policy-reference utility change.
- Scope: calibration only. No DPO training, no S16/S32/train400/large DPO. all500/S_pass/rollout real-energy coverage remains incomplete, but bounded asset-complete real-energy evidence improved to 12 rows.

## Diverse12 Calibration Completion Note (2026-07-08T09:35:00+08:00)

The v14 calibration scope was extended beyond the background-drift-heavy calibration12 subset. A 12-row asset-complete manifest with 12 unique synthetic controlled failure types was built and evaluated with real LingBot energy on physical GPU5. The run passed 12/12 rows and documented two energy-label contradictions. This satisfies an additional part of the offline calibration intent: synthetic failure type scale is now sampled more broadly, though all500/S_pass/rollout real-energy coverage remains incomplete because of runtime/cache and missing-asset blockers.

The experiment decision remains unchanged: calibration evidence alone does not authorize DPO scale; true checkpoint video, metrics, and Codex visual audit remain mandatory.

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
