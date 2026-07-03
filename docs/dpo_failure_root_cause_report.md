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
