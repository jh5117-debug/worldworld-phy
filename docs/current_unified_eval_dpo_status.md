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
