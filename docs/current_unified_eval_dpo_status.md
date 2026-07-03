Current Status: MIXED

## 2026-07-04 Ready500 Loser Quality and Metrics Backend Update

- Re-audited all 500 v11 ready pairs for LOSE trainability.
- 497/500 are training-usable after loser quality audit.
- 3 TypeA_plus pairs are rejected/review-only due `too_subtle_metric`.
- Use `manifests/dpo_pair_factory_v11_ready500_trainable_after_loser_audit.jsonl` for any next tiny DPO data pass.
- LPIPS backend is now available and smoke-tested.
- FVD remains blocked by missing real temporal FVD backend/local I3D weights.
- VBench package/CLI is available but real scoring requires explicit project config and checkpoint/cache policy.

<!-- DPO_PAIR_FACTORY_V11_SCALE500:START -->
Current Status: PAIR_FACTORY_V11_READY_500

## DPO Pair Factory v11 Scale-500

- Ready pairs: 500
- Train/val/test: 400 / 50 / 50
- Reviewed contact sheets: 931
- Source breakdown: `{'rollout_derived': 15, 'TypeA_plus': 3, 'synthetic_controlled': 482}`
- Data card: `docs/dpo_pair_factory_v11_data_card.md`
- Ready manifest: `manifests/dpo_pair_factory_v11_ready_500.jsonl`
- Caveat: controlled synthetic negatives dominate; real rollout DPO still needs rollout expansion.
- No DPO/training was run.
<!-- DPO_PAIR_FACTORY_V11_SCALE500:END -->

<!-- DPO_PAIR_FACTORY_V10B_FINAL_AUDIT:START -->
Current Status: PASS

## DPO Pair Factory v10b Final Audit (2026-07-03 22:16:34)

- v10b frozen ready pairs: 81 / 81 strict-ready.
- Rollout-derived trainable pairs: 15.
- Controlled synthetic TypeM-v10 pairs: 63.
- TypeA_plus controlled pairs: 3.
- Top50 balanced manifest: `manifests/dpo_pair_factory_v10b_top50_balanced.jsonl`.
- Caveat: synthetic controlled pairs are not real rollout losers.
- Decision: pair-data gate passes for anchored tiny DPO data, but real rollout DPO remains blocked by low rollout-derived count and WanI2VFast init.
- No training or DPO was run in v10b.
<!-- DPO_PAIR_FACTORY_V10B_FINAL_AUDIT:END -->

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


<!-- V8M_STATUS:START -->
## v8m Pair Cache (2026-07-03T02:38:45.438241+00:00)

Status: `PAIR_CACHE10_VALIDATED_FOR_TINY_OBJECTIVE`.

Built and validated a reviewed 10-pair winner+loser cache from `manifests/dpo_smoke_v7_gt_c_10.jsonl`. Build PASS: 10/10. Validation PASS: 10/10. Delta_ref positive: 8/10; non-positive: 2/10. Next stage may run tiny objective diagnostics with filtering/weighting, but large DPO remains blocked.
<!-- V8M_STATUS:END -->

<!-- V8L_STATUS:START -->
## v8l Objective Preflight (2026-07-03T01:50:54.681158+00:00)

Status: `V8L_BLOCKED_WINNER_ONLY_CACHE_NO_LOSER_ENERGY`.

v8k passed cache-only winner-anchor for 10 pairs / 20 steps, but v8l found the reusable cache is winner-only. It has no loser latent tensor and no `E_ref_loser`, while SDPO / Linear-DPO require loser energies. No DPO objective was run. Next required step is v8m reviewed winner+loser cache construction before any Strict SDPO / Linear-DPO run.
<!-- V8L_STATUS:END -->

Current Status Update (2026-07-03T09:42:30): V8K_WINNER_ANCHOR_CACHE10_PASS

v8k cache-only winner-anchor completed 20/20 steps on 10 reviewed GT>C pairs. Mean and final post-update winner improvement were positive. This permits only tiny v8l objective diagnosis; DPO is not yet scale-ready.

Current Status Update (2026-07-03T09:15:05): V8J_CACHE10_VALIDATED_PASS

v8j built and validated 10 reviewed GT>C winner-anchor cache rows with scalar reference winner energy. No DPO was run. DPO remains blocked until v8k proves cache-only 10-pair winner-anchor produces positive winner improvement.

Current Status Update (2026-07-03T08:48:33): V8I_FIRST_ROW_CACHE_PASS

v8i split `ensure_runtime_ready` and resolved the T5 runtime bottleneck with a checkpoint fast-init patch. A full-condition one-pair minimal cache row was written with text and VAE enabled. Cache10 is not yet validated, so DPO remains blocked until v8j/v8k pass.

Current Status Update (2026-07-03T08:48:18): V8I_FIRST_ROW_CACHE_PASS

v8i split `ensure_runtime_ready` and resolved the T5 runtime bottleneck with a checkpoint fast-init patch. A full-condition one-pair minimal cache row was written with text and VAE enabled. Cache10 is not yet validated, so DPO remains blocked until v8j/v8k pass.

Current Status Update (2026-07-03T08:47:32): V8I_FIRST_ROW_CACHE_PASS

v8i split `ensure_runtime_ready` and resolved the T5 runtime bottleneck with a checkpoint fast-init patch. A full-condition one-pair minimal cache row was written with text and VAE enabled. Cache10 is not yet validated, so DPO remains blocked until v8j/v8k pass.

Current Status Update (2026-07-02 21:58:17): V8G_POLICY_RUNTIME_HELPER_STILL_BLOCKED

v8g localized the v8f blocker further. Direct safe WanModelFast.from_pretrained can load CPU and move to GPU7, but the integrated Stage1 helper policy runtime still times out at 14_construct_policy_model_cpu before runtime_ready. No DPO-family training was run; DPO remains blocked until the helper/cache path uses the proven direct safe loader or is split further.

Current Status:
POLICY_RUNTIME_LOAD_BLOCKED_14_CONSTRUCT_POLICY_MODEL_CPU

## 2026-07-02 v8f Unified Status

v7 DPO smoke remains engineering-pass / objective-signal-fail. v8b sigma mapping passed. v8c proved 1-pair/window49 winner-anchor can work. v8f now shows cache/runtime scale is blocked before training: policy-only runtime loading times out at `WanModelFast.from_pretrained` with 0 GB GPU allocation. Do not scale DPO.

Current Status:
GPU_POLICY_UPDATED_H20_0_3_AUTHORIZED_BLOCKED_BUSY

## 2026-07-02 v8e GPU Policy Correction

The v8e GPU policy has been updated after user authorization: H20 physical GPU0-3 may be used for this task. At the latest check, GPU0-3 were occupied by existing root FastWAM jobs, so no GPU run was launched. PAI GPU0/1 is not used unless separately authorized again.

Current Status:
GPU_BLOCKED_BEFORE_RUNTIME_READY_RUN

## 2026-07-02 v8e Status

Runtime-ready diagnostics were implemented, but the currently authorized H20 GPU0-3 were occupied, so runtime preflight/cache build/training were not run. DPO remains blocked.

Current Status:
BLOCKED_CACHE_BUILD_RUNTIME_READY_TIMEOUT

## 2026-07-02 v8d Status

Reusable cache code is implemented, but cache build did not reach runtime ready; cache validation and cache10 winner-anchor were not run. Do not run SDPO / Linear-DPO next.

Current Status:
BLOCKED_10PAIR_WINNER_ANCHOR_CACHE_TOO_SLOW

## 2026-07-02 07:45 CST v8c Memory-Safe Winner Anchor

- H20-2 direct SSH recovered; previous hal-9000 attempt did not execute.
- Memory audit PASS: no separate ref model, no loser branch, cached winner input.
- 1-pair window49 winner-anchor PASS, final winner_improvement_post +0.00006324052810668945.
- 10-pair expansion NOT PASS: interrupted during multi-winner VAE/cache construction before optimizer steps.
- DPO remains blocked; do not run strict SDPO or Linear-DPO until persistent cache makes 10-pair winner-anchor pass.

Current Status:
BLOCKED

## 2026-07-02 v8b Bounded Sigma / Winner Anchor

Current Status: BLOCKED_WINNER_ANCHOR_1PAIR_OOM

Sampler-only sigma and 1-pair real-energy smoke both separated low/mid/high sigma values. Winner-anchor-only 1-pair completed 1/5 steps, then hit CUDA OOM on physical GPU4; completed winner_improvement was 0.0. Do not run strict SDPO or Linear-DPO until winner-anchor-only passes in a memory-safe 1-pair gate.


## 2026-07-02 v8 Sigma Check Blocker
- v8 PRDs were committed and pushed before execution.
- The full 10-pair real-energy sigma-bin check on GPU4 reached latent precompute and model-shard load, then saturated GPU4 in the energy loop for 60 minutes without producing actual sigma rows.
- Status: `SIGMA_ENERGY_CHECK_TIMEOUT`; actual sigma values were not fabricated.
- Winner-anchor-only and all follow-on objective variants were not run.
- DPO remains blocked; next fix is a bounded/progress-writing sigma check before any objective training.


## 2026-07-01 v8 Winner-Preserving Diagnosis Start
- v7 tiny SDPO-anchor smoke is engineering PASS but objective-signal FAIL: final winner improvement is negative and final winner contribution ratio is 0.0.
- v8 will not rerun the same SDPO-anchor objective as a scale path. It first checks low/mid/high sigma mapping, then runs winner-anchor-only. If winner-anchor-only fails, the remaining objective variants stop early.
- Pair factory v8 is scoped to recovering reviewed GT>C pairs only; no unreviewed C loser may enter any DPO-ready manifest.
- Authorized GPU scope has been updated to H20 physical GPU0-3 after user authorization; launch only if an authorized GPU is actually free.
- Explicitly not run in v8 PRD stage: large DPO, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, data/weight/video push.


## 2026-07-01 v7 SDPO Smoke Update
- Tiny SDPO-anchor smoke on reviewed GT>C pairs completed on physical GPU6: runtime PASS, 20/20 steps, no OOM/SIGFPE/NaN, save/load OK, nonzero gradients.
- Final DPO loss: 0.6931381226; final winner improvement: -0.0002626628; final loser degradation: 0.0004442334; final winner contribution ratio: 0.0.
- Decision: ENGINEERING_PASS_OBJECTIVE_SIGNAL_FAIL. Do not scale DPO.
- Checkpoint video smoke generated true V2V-5 videos for step000/005/010/020 on one reviewed GT>C condition. Step010 had best one-sample PSNR/SSIM, but all checkpoints visually hallucinated extra balls/fragments; step020 degraded.
- Pair factory v7 was not launched; only 21 runnable conditions are currently recovered for the v7 80-condition target.


<!-- dpo_smoke_pair_factory_v7_update -->
## DPO Smoke and GT>C Pair Factory v7 Update

Current Status: BLOCKED_GPU_BUSY_SUBSET_READY / PAIR_FACTORY_CONDITION_EXPANSION_PARTIAL

Updated: 2026-07-01 16:05:00 CST

- Visual audit policy and v7 PRDs were committed and pushed before experiment work.
- Tiny smoke subset is ready: 10 reviewed GT>C pairs, loser reward mean 0.759517, reward margin mean 0.240483.
- Loser visual audit is complete for the smoke subset: 10 / 10 reviewed and DPO-ready.
- DPO smoke training did not start because the authorized H20 GPUs were occupied at launch time; no PAI GPU was used.
- Pair factory condition expansion from existing v6b candidate rows produced 21 unique runnable conditions, below the 80 target.
- Pair factory rollout did not start because authorized H20 GPUs were occupied and more condition recovery is still needed.
- No large-scale DPO, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint deletion, or checkpoint modification was run.
<!-- /dpo_smoke_pair_factory_v7_update -->
<!-- targeted_BC_loser_mining_v6b_update -->
# Targeted B/C Loser Mining v6b Update

Current Status: READY_FOR_TINY_DPO_SMOKE

Updated: 2026-07-01 09:20:29 CST

- Runnable prefix5 recovery PASS: 32 / 32 conditions recovered from quant benchmark full videos by materializing prefix frames 0-4 and GT future frames 5-80.
- Previous v6 had only 5 runnable rows because it only used already-materialized DPO prefix5 asset dirs; quant benchmark rows needed prefix/future video recovery.
- Smoke rollout PASS for M0/B/C.
- 16-condition rollout PASS for M0/B/C.
- 32-condition rollout PASS for B camera-r8 and C camera+self-temporal-r4. M0 32cond baseline remains PARTIAL (first16 only) and was not needed for GT>C pair construction.
- B camera-r8 conclusion: stable candidate generator / control baseline.
- C camera+self-temporal-r4 conclusion: usable medium-hard loser source.
- Codex visually reviewed first16 and remaining16 overview sheets.
- Medium-hard C loser candidates selected: 16.
- DPO-ready GT>C pairs: 15, exceeding the >=10 tiny DPO smoke gate.
- Final v6b pair manifest: `manifests/dpo_typeB_C_loser_pairs_v6b.jsonl`.
- PPT showcase generated locally: `reports/ppt_winlose_showcase_latest/BC_medium_hard_loser_v6b_for_ppt.mp4` (not for Git).
- No DPO training, StageB, GRPO, full-data StageA, broad-LoRA, checkpoint edits, or checkpoint deletion were run.

<!-- /targeted_BC_loser_mining_v6b_update -->

<!-- targeted_BC_loser_mining_v6_update -->
# Targeted B/C Loser Mining v6 Update

Current Status: BLOCKED_INSUFFICIENT_MEDIUM_HARD_ROLLOUTS

Updated: 2026-06-30 20:50:46 CST

- Safe GPU status and deterministic V2V-5 runner discovery are fixed.
- 1-condition smoke PASS for M0/B/C.
- Available-condition rollout PARTIAL_PASS: 15 videos from 5 runnable prefix5 conditions.
- C produced 4 visually meaningful medium-hard loser candidates.
- Final DPO-ready pair count is 4, below the >=10 DPO-smoke gate.
- 8/32-condition rollout could not be faithfully executed because only 5 runnable prefix5 conditions are present in this tree.
- Do not start DPO smoke until more runnable conditions or an external rollout source raises the pair count.

<!-- /targeted_BC_loser_mining_v6_update -->



## Targeted B/C Loser Mining v6 Update - 2026-06-30

Current Status: BLOCKED_BY_GPU_OR_RUNNER_DISCOVERY

B and C checkpoints were found. B camera-r8 remains the stable candidate generator/control baseline; C camera+self/temporal-r4 remains the intended loser mining scope. New rollout did not start because GPU/process queries were unsafe/hung under high GPU occupancy. No DPO-ready TypeB-C pairs were produced, and no saved sweep video was promoted to DPO-ready.


## Small-LoRA Sweep Loser Source Audit Update - 2026-06-30

Current Status: MIXED / DIAGNOSTIC_ONLY

Recovered saved A/B/C/D sweep video-audit rows from `reports/candidate_generator_v2/video_audit.csv` and inspected A/B/C/D overview contact sheets. Existing TypeB quality-gate pass count is 0 across the recovered rows, so saved sweep outputs are not directly DPO-ready TypeB losers.

Decision: B camera-r8 is the best stable candidate generator/control; C camera+self/temporal-r4 is the best next loser-source mining scope; D is diagnostic runner-up; A is too conservative/too similar. No training or checkpoint modification was performed.

# Current Unified Eval / DPO Status


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


## Current Reward Visual Alignment v5 Status (2026-06-30 13:33:20)

Current Status: PROTOCOL_V4_NOT_READY_TOO_SUBTLE

- v4 pairs checked: 42
- Human-visible strict count: 3
- DPO-ready after visual gate: 3
- Too subtle: 39
- TypeA_plus too subtle: 31
- TypeM true medium-hard: 0
- New ready manifest: `reports/reward_visual_alignment_v5/dpo_ready_pairs_visual_v5.jsonl`
- New PPT diagnostic: `reports/ppt_winlose_showcase_latest/winlose_showcase_visible_mediumhard_v5_for_ppt.mp4`

Conclusion: reward-guided v4 is not ready for DPO; proxy reward margins do not yet guarantee human-visible medium-hard failures.



## Current Protocol v4 Status (2026-06-30 12:09:54)

Current Status: PASS_REWARD_GUIDED_PROTOCOL_READY_FOR_SMALL_SMOKE

- Protocol v4 manifest: `manifests/dpo_preference_protocol_v4_pairs.jsonl`
- Total pairs: 42
- TypeA_plus: 34
- TypeM: 8
- TypeB_usable: 0
- TypeB remains blocked by rollout blur/quality.
- No DPO training, StageB, GRPO, or full-data StageA was run in v4.


## Current Protocol v3 / DPO Smoke Status (2026-06-30 05:14:29)

- Candidate generator v2: CANDIDATE_GENERATOR_FAILED_TYPEB_STILL_BLOCKED; audited 208 existing true V2V-5 small-LoRA rollout candidates, selected 0 usable TypeB rollout losers.
- Protocol v3: MIXED_TYPEA_READY_TYPEB_FAILED_CANDIDATE_GENERATOR; 34 valid TypeA local-corruption pairs, 0 TypeB, 0 TypeC.
- LocalDPO spatial mask v2: PASS; 34/34 TypeA pairs have usable spatial+time masks.
- DPO smoke v3: ENGINEERING_PASS_OBJECTIVE_SIGNAL_FAIL on 8 TypeA pairs for 10 steps. Runtime/save-load/nonzero-grad checks passed, but winner improvement remains weak/unstable and checkpoint video smoke shows no visual improvement.
- Checkpoint video smoke: step000/005/010 generated true prefix5 V2V-5 videos on 1 screen16 sample each; PSNR/SSIM/LPIPS PASS; FVD/VBench remain BLOCKED_BY_ENV.
- Decision: do not scale DPO. Do not use TypeB rollout losers until blur/sharpness quality is fixed.



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


<!-- DPO_FAILURE_DIAG_20260629_START -->
## Current Status: DPO Failure Root-Cause Diagnosis Completed (2026-06-29)

- S0_sanity_8 objective ablation failed the signal gate, so S1/S2 were not launched.
- Winner-only overfit on the strongest Type B pair did not robustly improve winner energy relative to the reference: mean winner improvement = -2.27876e-05, final = -4.29377e-05.
- Loser-only maximization was weak/non-monotonic: mean loser degradation = 1.04467e-04, final = -1.55047e-04.
- Gradient decomposition found mixed winner/loser alignment: mean cosine(g_w,g_l) = 0.065 and winner/loser grad norm ratio ranged from 0.417 to 10.228.
- Timestep/sigma sensitivity is currently blocked for low/mid bins because all requested bins map to actual sigma about 0.947 in the DPO backend.
- Beta/utility analysis shows `u = Delta_policy - Delta_ref` is effectively zero at initialization, so standard sigmoid DPO starts at the no-margin 0.693 point.
- LocalDPO metadata contains affected spatial masks for 34 / 34 local-corruption pairs, but the current LocalDPO objective only used affected-time masking; spatial-token masking remains TODO.
- Decision: do not proceed with standard DPO or scale DPO. Next probe should use an explicit winner-anchor objective plus conservative loser lambda, and only after spatial LocalDPO masks / sigma sampling are fixed.
- Report: `docs/dpo_failure_root_cause_report.md`.

Safety: no large DPO, no StageB, no GRPO, no full-data StageA, no checkpoint deletion, and no data/weight/video push.
<!-- DPO_FAILURE_DIAG_20260629_END -->


<!-- ENERGY_AUDIT_20260628_START -->
## Current Status: Full Real-Energy Audit Completed (2026-06-28)

- Protocol v1 pair manifest: `manifests/dpo_preference_protocol_v1_pairs.jsonl`.
- Full real LingBot-Fast energy audit completed for 66 / 66 V2V-5 pairs.
- Real energy outputs: `reports/dpo_preference_protocol_v1/full_real_energy_audit.csv` and `.jsonl`.
- DPO-ready selection: 50 pairs total = 34 Type A local corruption + 16 Type B GT vs medium-hard rollout.
- LocalDPO-ready subset: 34 Type A pairs with affected region/time metadata and positive usable energy margin.
- Type B pairs have stronger real-energy margins (Delta_ref median 0.075306) than Type A local corruptions (Delta_ref median 0.009849), but Type A is better aligned with region-aware LocalDPO.
- Recommendation: tiny standard energy-DPO is unblocked only as a controlled probe; use SDPO-style winner-preserving monitoring and consider Linear-DPO for weak-margin Type A pairs.
- No DPO training, StageB, GRPO, full-data StageA, checkpoint deletion, or data/weight push was run for this audit.

<!-- ENERGY_AUDIT_20260628_END -->

Updated: 2026-06-28T00:20:04

## Current Protocol State

- DPO training: not running.
- New pair protocol: `manifests/dpo_preference_protocol_v1_pairs.jsonl`.
- Valid pairs: 66.
- Type A local corruption: 50.
- Type B medium-hard rollout: 16.
- Prior DPO probe remains failed for scale-up; this protocol is the data repair step.

## Decision

Pair protocol v1 is ready for review and selected-subset real-energy audit. It is not approval to launch DPO automatically.

---

# Current Unified Eval / DPO Status

Updated: 2026-06-27T07:14:17

## Current Status

- Prefix-aware V2V-5 pairs: READY (`manifests/anchored_dpo_probe_pairs_prefix5.jsonl`, 50/50 visual-audited valid prefix5 pairs).
- Real LingBot-Fast prefix5 DPO energy backend: READY for preflight.
- DPO BF16 runtime: **DPO_BF16_READY**.
- Tiny DPO probe: **BLOCKED** until a verified V2V-5 LingBot-Fast generation wrapper is implemented for checkpoint video evaluation.
- No large-scale DPO, StageB, GRPO, or full-data long StageA was run in this step.

## Latest BF16 Preflight Outputs

- Matrix: `reports/dpo_bf16_preflight/matrix.csv`
- Energy summary: `reports/dpo_bf16_preflight/energy_checks_summary.csv`
- Single: `reports/dpo_bf16_preflight/lingbot_fast_single_gpu7_20260627_053617/`
- DDP2: `reports/dpo_bf16_preflight/lingbot_fast_ddp2_gpu67_20260627_060736/`
- DDP8: `reports/dpo_bf16_preflight/lingbot_fast_ddp8_gpu01234567_20260627_063825/`

## Why Probe Is Not Started Yet

The DPO trainer can now compute real energy and update LoRA. However the probe specification requires real V2V-5 rollout videos for every checkpoint. The current inference wrapper is image-first and would be I2V, not V2V-5. Running it would invalidate the probe.


## 2026-06-28 DPO Objective Ablation S0

- S0_sanity_8 and S_localdpo_16 completed with real LingBot-Fast V2V-5 energy.
- Runtime/BF16 path was stable for Standard, SDPO-style, Linear-DPO-style, and LocalDPO-style diagnostics.
- Research signal failed: losses stayed near 0.693, Standard/Linear/LocalDPO showed winner-worse or loser-only behavior, and SDPO-style was only borderline at final step but failed mean winner-preservation gate.
- S1_probe_20 was not launched.
- No StageB, GRPO, large-scale DPO, or full-data StageA was run.
- Report: docs/dpo_objective_ablation_report.md


## v8h Update - 2026-07-03T06:46:04

Policy runtime safe loader now reaches runtime-ready on H20 physical GPU7. The first-row cache smoke then blocks after `after_policy_load` and before `after_runtime_ready`, localizing the next blocker to `ensure_runtime_ready` / runtime component initialization. DPO remains not ready; no DPO/SDPO/Linear-DPO was run.


<!-- dpo_pair_factory_v10_update -->
## DPO Pair Factory v10 Update

Current Status: PAIR_FACTORY_V10_READY_50_SYNTHETIC_MIXED

- Runnable prefix5 conditions recovered: 102.
- Existing strict DPO-ready pairs: 18.
- Synthetic visible TypeM-v10 ready pairs: 63.
- Combined ready pairs: 81.
- Combined manifest: `manifests/dpo_pair_factory_v10_ready_pairs.jsonl`.
- Caveat: 63 new pairs are controlled synthetic visible negatives, not true rollout TypeB losers.
- No DPO / SDPO / Linear-DPO / StageA / StageB / GRPO / broad-LoRA was run.
<!-- /dpo_pair_factory_v10_update -->
