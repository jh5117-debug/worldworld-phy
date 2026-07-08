Current Status:
V8N_BLOCKED_WINNER_ANCHOR_REPEAT_SIGNAL_FAIL

# DPO Objective Diagnosis v8n Status

Updated: 2026-07-03T14:27:15.960283

v8n used the validated v8m winner+loser cache and selected only Delta_ref-positive rows for objective testing.

Results:
- Pair selection: 8 positive Delta_ref rows, 2 nonpositive rows diagnostic-only.
- Forward sanity: PASS on 8/8 positive rows.
- Winner-anchor repeat 5-step: runtime PASS, objective signal FAIL.
- Mean winner_improvement_post: -5.207061767578125e-05.
- Final winner_improvement_post: -6.175041198730469e-05.

Decision:
- DPO cannot proceed.
- Strict SDPO / Linear-DPO / Safe-linear are not allowed next until winner-anchor repeat passes on multi-pair cache.
- v8o checkpoint video eval was not run.


<!-- V8M_ROOT_CAUSE:START -->
## v8m Pair Cache (2026-07-03T02:38:45.438241+00:00)

Status: `PAIR_CACHE10_VALIDATED_FOR_TINY_OBJECTIVE`.

Built and validated a reviewed 10-pair winner+loser cache from `manifests/dpo_smoke_v7_gt_c_10.jsonl`. Build PASS: 10/10. Validation PASS: 10/10. Delta_ref positive: 8/10; non-positive: 2/10. Next stage may run tiny objective diagnostics with filtering/weighting, but large DPO remains blocked.
<!-- V8M_ROOT_CAUSE:END -->

<!-- V8L_ROOT_CAUSE:START -->
## v8l Objective Preflight (2026-07-03T01:50:54.681158+00:00)

Status: `V8L_BLOCKED_WINNER_ONLY_CACHE_NO_LOSER_ENERGY`.

v8k passed cache-only winner-anchor for 10 pairs / 20 steps, but v8l found the reusable cache is winner-only. It has no loser latent tensor and no `E_ref_loser`, while SDPO / Linear-DPO require loser energies. No DPO objective was run. Next required step is v8m reviewed winner+loser cache construction before any Strict SDPO / Linear-DPO run.
<!-- V8L_ROOT_CAUSE:END -->

Current Status Update (2026-07-03T09:42:30): V8K_WINNER_ANCHOR_SCALABLE_CACHE10_PASS

v8k cache-only winner-anchor completed 20/20 steps on 10 reviewed GT>C pairs. Mean and final post-update winner improvement were positive. This permits only tiny v8l objective diagnosis; DPO is not yet scale-ready.

Current Status Update (2026-07-03T09:15:05): V8J_CACHE10_RUNTIME_BLOCKER_RESOLVED

v8j built and validated 10 reviewed GT>C winner-anchor cache rows with scalar reference winner energy. No DPO was run. DPO remains blocked until v8k proves cache-only 10-pair winner-anchor produces positive winner improvement.

Current Status Update (2026-07-03T08:48:33): V8I_T5_FAST_INIT_RESOLVED_FIRST_ROW

v8i split `ensure_runtime_ready` and resolved the T5 runtime bottleneck with a checkpoint fast-init patch. A full-condition one-pair minimal cache row was written with text and VAE enabled. Cache10 is not yet validated, so DPO remains blocked until v8j/v8k pass.

Current Status Update (2026-07-03T08:48:18): V8I_T5_FAST_INIT_RESOLVED_FIRST_ROW

v8i split `ensure_runtime_ready` and resolved the T5 runtime bottleneck with a checkpoint fast-init patch. A full-condition one-pair minimal cache row was written with text and VAE enabled. Cache10 is not yet validated, so DPO remains blocked until v8j/v8k pass.

Current Status Update (2026-07-03T08:47:32): V8I_T5_FAST_INIT_RESOLVED_FIRST_ROW

v8i split `ensure_runtime_ready` and resolved the T5 runtime bottleneck with a checkpoint fast-init patch. A full-condition one-pair minimal cache row was written with text and VAE enabled. Cache10 is not yet validated, so DPO remains blocked until v8j/v8k pass.

Current Status Update (2026-07-02 21:58:17): V8G_FROM_PRETRAINED_SAFE_PASS_HELPER_TIMEOUT

v8g localized the v8f blocker further. Direct safe WanModelFast.from_pretrained can load CPU and move to GPU7, but the integrated Stage1 helper policy runtime still times out at 14_construct_policy_model_cpu before runtime_ready. No DPO-family training was run; DPO remains blocked until the helper/cache path uses the proven direct safe loader or is split further.

Current Status:
POLICY_RUNTIME_LOAD_BLOCKED_14_CONSTRUCT_POLICY_MODEL_CPU

## 2026-07-02 v8f Root Cause Update

The current blocker is not sigma/timestep and not 1-pair winner-anchor objective sign. v8f shows the policy-only runtime path blocks at CPU-side `WanModelFast.from_pretrained` before GPU allocation. T5 CPU load is also slow, but the exact v8e policy-only blocker is policy model construction / shard loading. DPO should not proceed.

Current Status:
GPU_BLOCKED_BEFORE_RUNTIME_READY_RUN

## 2026-07-02 v8e Root Cause Update

v8e implementation is ready to isolate runtime-ready stages, but execution is blocked by GPU4-7 occupancy. No DPO objective variant should run until runtime-ready preflight and cache10 winner-anchor pass.

Current Status:
BLOCKED_CACHE_BUILD_RUNTIME_READY_TIMEOUT

## 2026-07-02 v8d Root Cause Update

The active blocker moved one step earlier than optimizer behavior: reusable winner cache construction cannot reach runtime ready in a bounded window. DPO variants remain blocked until cache build and 10-pair winner-anchor pass.

Current Status:
BLOCKED_10PAIR_WINNER_ANCHOR_CACHE_TOO_SLOW

## 2026-07-02 07:45 CST v8c Root Cause Update

v8c shows sigma mapping is fixed and winner-anchor-only can produce a positive post-update winner improvement on 1 reviewed pair when using a memory-safe window49 path. The blocker moved from pure OOM to scalability/runtime: full81 reached backward but was too slow, and 10-pair expansion was interrupted during VAE/cache construction before optimizer steps. The next root-cause fix is persistent winner latent/control/text cache so 10-pair winner-anchor can run without repeated VAE/T5 work.

Current Status:
BLOCKED

## 2026-07-02 v8b Root Cause Update

Current Status: BLOCKED_WINNER_ANCHOR_1PAIR_OOM

v8b shows sigma mapping itself is not collapsed when checked with bounded sampler-only and one-pair real-energy smoke. The active blocker moved to winner-anchor-only: one reviewed pair completed a single optimization step, then OOMed before 5 steps; winner improvement stayed 0.0 on the completed row. Root-cause hypotheses now prioritize memory pressure in the train graph, optimizer/checkpointing/offload, and whether the winner energy sign/scope can produce a positive update once the run is memory-safe.


## 2026-07-02 v8 Sigma Check Blocker
- v8 PRDs were committed and pushed before execution.
- The full 10-pair real-energy sigma-bin check on GPU4 reached latent precompute and model-shard load, then saturated GPU4 in the energy loop for 60 minutes without producing actual sigma rows.
- Status: `SIGMA_ENERGY_CHECK_TIMEOUT`; actual sigma values were not fabricated.
- Winner-anchor-only and all follow-on objective variants were not run.
- DPO remains blocked; next fix is a bounded/progress-writing sigma check before any objective training.


## 2026-07-01 v8 Diagnosis Plan
The next diagnosis is explicitly winner-preserving. Before running any new objective, the backend must verify requested low/mid/high sigma bins map to distinct actual sigma values. The first objective is winner-anchor-only (`loss = E_policy_winner`, `lambda_loser = 0`). If that cannot reduce winner energy relative to the frozen reference, strict SDPO, linear-DPO, and safe-linear variants are blocked and should not be treated as meaningful DPO evidence.

Pair quantity remains a separate blocker: pair factory v8 may recover more reviewed GT>C pairs, but no unreviewed C rollout loser can enter a DPO-ready manifest.

Safety: no large DPO, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or data/weight/video push is authorized by this v8 plan.

## 2026-07-01 v7 Failure Evidence
Tiny SDPO-anchor on cleaner GT>C medium-hard losers is engineering-stable but still not winner-preserving enough to scale. Final winner improvement is negative (-0.0002626628), final loser degradation is positive (0.0004442334), and final winner contribution ratio is 0.0. Checkpoint videos show persistent hallucinated extra objects/fragments. This strengthens the prior diagnosis that DPO objective/data still produce weak or conflicting winner-side signal.

# DPO Failure Root-Cause Report

## Current Protocol v3 Status (2026-06-29 15:38:49)

- Metrics backend v2: PSNR/SSIM/LPIPS PASS; FVD/VBench BLOCKED_BY_ENV with attempted fixes recorded.
- LocalDPO spatial mask v2: PASS, 34/34 Type A pairs have usable spatial+time masks.
- Protocol v3: 34 valid Type A pairs, 0 Type B, 0 Type C.
- Candidate generator v2: waiting for GPU capacity; current GPUs are occupied by unrelated workloads.
- DPO smoke v3: not run yet because GPU capacity is unavailable; no scale DPO.



## Current DPO Protocol v2 Status (2026-06-29 14:18:28)

- Protocol v2 manifest: `manifests/dpo_preference_protocol_v2_pairs.jsonl`
- Valid v2 pairs: 34 total, 34 Type A, 0 Type B, 0 Type C.
- Type B rollout losers are currently blocked by blur/sharpness gates; do not use them for DPO.
- Metrics backend: PSNR/SSIM/LPIPS pass; FVD and VBench are BLOCKED_BY_ENV.
- DPO engineering run-through: PASS_ENGINEERING_ONLY on 8 Type A pairs for 10 steps with checkpoint video eval. Learning signal remains loser-dominant, so do not scale DPO.
- Explicitly not run: StageB, GRPO, full-data long StageA, large-scale DPO.


Updated: 2026-06-29 05:33:05

## Executive Summary

S0 failed because the current energy-DPO update does not reliably improve winner energy. Runtime, BF16, and prefix5 data plumbing are not the bottleneck. The bottleneck is objective signal geometry: policy/reference start with near-zero utility, winner-only overfit is weak, DPO variants find loser-dominant margins, and sigma sampling currently exposes only a high-noise sigma around 0.947.

## Diagnostic Answers

1. Winner-only can reduce raw policy energy over sampled steps, but winner_improvement relative to the reference is not stable: mean=-2.27876e-05, last=-4.29377e-05, positive ratio=0.46.
2. Loser-only is also weak/non-monotonic: mean loser_degradation=0.000104467, last=-0.000155047, positive ratio=0.50.
3. Winner/loser gradients show mixed alignment: mean cosine(g_w,g_l)=0.065, mean ratio=2.880, ratio range=0.417-10.228.
4. Timestep/sigma sensitivity is blocked for low/mid bins: all requested bins map to actual sigma about 0.947 with the current helper schedule. This confirms the current DPO path is effectively high-noise only.
5. Beta analysis shows u = Delta_policy - Delta_ref is effectively zero at initialization, so standard sigmoid DPO starts at the no-margin 0.693 point. Increasing beta changes scale, but does not solve winner preservation.
6. LoRA capacity: camera-only rank4 has weak positive mean winner improvement; rank8 and camera+cross are not better; camera+self rank4 has positive mean but unstable final. Capacity alone is not a clean fix.
7. LocalDPO mask audit: {'True': 34} affected masks available, but the current LocalDPO-style objective only applied affected-time masking in the energy backend. Spatial token masking still needs implementation.

## LoRA Capacity

| scope | trainable params | mean winner improvement | last winner improvement | positive ratio |
|---|---:|---:|---:|---:|
| L0_camera_r4 | 6553600 | 0.000330903 | 5.74701e-05 | 0.80 |
| L1_camera_r8 | 13107200 | -0.000228145 | 3.15858e-05 | 0.30 |
| L2_camera_self_r4 | 1638400 | 0.000287365 | -2.6417e-06 | 0.50 |
| L3_camera_cross_r4 | 1638400 | -4.29165e-05 | -0.000101514 | 0.30 |

## Root Cause

Primary root cause: the current objective does not contain a strong enough winner-preserving term. At policy/reference equality the DPO utility is near zero; the gradients do not reliably move winner energy down, and local/time-only masking still lets loser-driven or unstable updates dominate.

Secondary root causes:

- The timestep schedule available to the DPO backend is effectively high-noise only, so low/mid-noise preference signal is untested and unavailable.
- LocalDPO spatial masks exist in metadata but are not yet connected to spatial-token loss masking.
- Camera-only LoRA rank4 is not obviously too weak, but it is not reliably winner-improving either; limited self-attention may deserve a follow-up, but broad LoRA remains inappropriate.

## Recommendation

Do not proceed with standard DPO. The next tiny probe should use an explicit winner-anchor objective, for example `L = L_SDPO + lambda_w * E_policy_winner`, with loser lambda capped at 0.25 until winner_improvement is positive. Also connect spatial LocalDPO masks before claiming LocalDPO. Use the strongest Type B subset first, with high-noise-only clearly documented, and do not scale until winner_improvement mean > 0 and winner contribution ratio > 0.30.

## Safety

No large DPO, StageB, GRPO, full-data StageA, checkpoint deletion, or data/weight push was performed.

## v8h Update - 2026-07-03T06:46:04

Policy runtime safe loader now reaches runtime-ready on H20 physical GPU7. The first-row cache smoke then blocks after `after_policy_load` and before `after_runtime_ready`, localizing the next blocker to `ensure_runtime_ready` / runtime component initialization. DPO remains not ready; no DPO/SDPO/Linear-DPO was run.

## DPO Training Sanity v12

Tiny guarded SDPO on S1 was stopped at step10: mean winner improvement turned negative and DPO loss remained near 0.693. Decision: `DPO_V12_FAILED_WINNER_WORSE_NO_SIGNAL`. Large DPO remains blocked.

<!-- V12B_OBJECTIVE_REPAIR_ROOT_CAUSE_UPDATE_START -->

## V12B OBJECTIVE REPAIR ROOT CAUSE UPDATE

v12 failure was not purely loader/runtime; after filtering pair conflicts, winner-anchor can improve on S_pass4. Root cause remains pair/objective interaction: half of S8 still worsens under winner-only, so unfiltered preference training is unsafe.

<!-- V12B_OBJECTIVE_REPAIR_ROOT_CAUSE_UPDATE_END -->

<!-- V12C_BLOCKER_UPDATE_START -->

## V12C BLOCKER UPDATE

v12c did not test the preference branch yet; current blocker is GPU scheduling, not objective signal. Objective signal remains to be tested once GPU4 is free.

<!-- V12C_BLOCKER_UPDATE_END -->

## v13b DPO Objective Search Update

- Updated: 2026-07-06T13:08:17+08:00.
- v13b objective search code and GPU4/5-only scheduler are prepared.
- Training did not launch because GPU4/5 were occupied by existing non-v13b jobs / GPU query timed out conservatively.
- Decision: `DPO_RECIPE_GPU_BLOCKED`; no scale, no train400, no large DPO.
## v13b Objective Search Root Cause Update

v13b did not find a valid DPO recipe. The dominant pattern is not loser degradation; instead, several schemes improve winner energy while preference utility remains too small to move the DPO loss away from ~0.693. This points to preference gap scale / reference normalization / beta-lambda calibration as the next blocker. Broader L2 camera+temporal LoRA was not proven because S10 timed out before first row.

## v14 Gap Scale Root Cause

The DPO preference branch in v13b was under-scaled: median |u_log| was about 2e-4, so beta=0.1 produced near-zero logits and loss around 0.693. v14 recommends calibrated log utility around beta=1000 only for a guarded tiny probe; all500 real energy remains blocked by runtime init timeout.

## v14 E02 Smoke10 Root Cause Update

Beta scaling addressed the no-signal branch, but final-step winner degradation remains. The next root-cause test is optimizer/update stability: lower LR or best-step early stopping, not more data or larger DPO.


## E02_best7 Checkpoint Video Audit Update (2026-07-07T02:37:56.080956Z)

- Candidate: `E02_best7` / `calibrated_winner_detached_log` / `beta=1000` / `L0_camera_r4`.
- Training signal: `TRAINING_SIGNAL_PASS`.
- Mean winner improvement post: `0.00010894877570016044`.
- Final winner improvement post: `0.00033855438232421875`.
- Mean winner contribution ratio: `0.6680136300480072`.
- True V2V-5 checkpoint videos generated: `12` (`step000`, `step005`, `step007` on 4 validation samples).
- Codex visual audit: `FAIL`. Final `step007` is worse than `step000` on multiple samples due to duplicate objects, hallucinated blobs/fragments, and foreground object-count/identity drift.
- Metrics: PSNR/SSIM rows `12/12`; LPIPS GPU smoke `PASS`; FVD remains `BLOCKED_BY_ENV`; VBench real checkpoint scoring not configured in this wrapper.
- Decision: `DPO_RECIPE_TRAINING_SIGNAL_ONLY_VIDEO_FAIL_V14`.
- Scale permission: `NO_SCALE`; do not run S16/S32/train400 from this recipe.

Relevant paths:
- `reports/dpo_utility_calibration_v14/objective_search/E02_best7/checkpoint_eval/video_audit.csv`
- `reports/dpo_utility_calibration_v14/objective_search/E02_best7/checkpoint_eval/video_audit_summary.md`
- `reports/dpo_utility_calibration_v14/objective_search/E02_best7/metrics/metrics_summary.md`

## v14 Objective Search Update (2026-07-07T03:56:37.931118Z)

- Added E04_screen5 and E05_screen5 screening runs on physical GPU4/GPU5 only.
- E04_screen5 (`no_lose_gap_normalized_win_only`) training signal PASS: mean winner improvement `0.00012879371643066407`, final `0.00013786554336547852`, WCR `0.7916`, loser degradation negative.
- E05_screen5 (`normalized_clipped_loser`, alpha_l=0.02) training signal PASS: mean winner improvement `0.00012555122375488282`, final `0.00012230873107910156`, WCR `0.8220`, slight loser degradation.
- E04 checkpoint videos generated: `8` true V2V-5 videos. Codex visual audit FAIL: step005 worsens object count/identity in multiple samples.
- Decision remains `DPO_RECIPE_NOT_FOUND_V14`; no S16/S32/train400.


## v14 E09/E10 Final Visual Gate Update (2026-07-07T17:56:59Z)

- E09 (, L0 camera r4) reached strong early scalar signal at step50: winner improvement , WCR , loser degradation negative. True V2V-5 audit failed: step50 was worse/not-better on 4/4 fixed validation samples, with foreground duplication, colored blob fragments, and line/text-like artifacts.
- E10 (, L2 camera-temporal r4) completed 100/100 steps with final winner improvement  and mean WCR . True V2V-5 audit failed: step100 was worse on 2/4 samples and not decisively better on the rest, with duplicate green balls, object identity clutter, and foreground fragments.
- Current decision: . The scalar no-signal / beta-scale issue is partially repaired, but energy/gap improvement does not yet predict rollout visual quality.
- Scale permission: ; no S16/S32/train400/large DPO from these recipes. Next direction is a rollout-quality or latent visual monitor/regularizer before further DPO scaling.

## v14 Completion Root Cause Correction (2026-07-08)

This supersedes the earlier E09/E10 note where several numeric fields were left blank.

- Final decision: `DPO_RECIPE_NOT_FOUND_V14`.
- Scale permission: `NO_SCALE`; do not run S16/S32/train400/large DPO from v14.
- E07 (`linear_winner_detached`, L0 camera r4) completed 200/200 rows with final winner improvement `+0.0161217451`, mean winner improvement `+0.0058058372`, mean winner contribution ratio about `0.985`, and mean loser degradation negative. It failed the true V2V-5 visual gate: step200 was worse on 4/4 fixed validation samples.
- E09 (`source_weighted_rollout_priority`, L0 camera r4) reached strong early signal at step50: winner improvement `+0.0014111996`, WCR `1.0`, loser degradation `-0.0013124943`, DPO loss `0.5111857`. It failed the true V2V-5 visual gate: step50 was worse on 3/4 samples and not better on the remaining sample.
- E10 (`calibrated_winner_detached_log`, L2 camera-temporal r4) completed 100/100 rows with final winner improvement `+0.0004041791`, mean winner improvement `+0.0001850957`, mean WCR about `0.8247`, and mean loser degradation negative. It failed the true V2V-5 visual gate: step100 was worse on 2/4 samples and not decisively better on the rest.
- Exact blocker: scalar energy/gap improvements do not yet predict real rollout visual quality. The observed update failure is artifact amplification: foreground duplication, line/text-like artifacts, object identity clutter, foreground fragments, and scene contamination.
- V-JEPA2 now provides a no-download monitor and high-recall checkpoint drift signal, but it is not a standalone quality approval metric. The safe next direction is v15 artifact-aware monitor/regularizer design before any more DPO scale.

## v14 Artifact Regression Aggregation (2026-07-08T10:25 CST)

- Added aggregation: `reports/dpo_utility_calibration_v14/artifact_regression/artifact_regression_summary.md`.
- Source audits: E07 step200, E09 step50, and E10 step100 true V2V-5 checkpoint visual audits.
- Result: scalar-positive schemes consistently fail visual gates. E07 is worse on 4/4, E09 is flagged worse on 4/4; one row is described as at-best-mixed/not-better, and E10 is worse on 2/4 and not decisively better on the rest.
- Dominant failure tags: identity clutter, foreground duplication/fragments, artifact/line-text contamination, with background/camera contamination in some E09 samples.
- Decision remains `DPO_RECIPE_NOT_FOUND_V14`; scale permission remains `NO_SCALE`.
