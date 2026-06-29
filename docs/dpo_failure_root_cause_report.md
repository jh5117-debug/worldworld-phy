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