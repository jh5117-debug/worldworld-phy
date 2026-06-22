# Fast StageA High-Only Preflight Report

Status: partial_in_progress

Date: 2026-06-22

## Completed

- Invalid Base low/high StageA sessions were stopped earlier in this run.
- GPU0 TDW sessions remained alive.
- LingBot-World-Fast loader smoke passed on physical GPU7.
- Fast loader fingerprint was recorded in `docs/lingbot_fast_training_loader_audit.md`.
- Basic BF16 kernel diagnostic passed on physical GPU7.
- GPU0 launcher guard passed: `CUDA_VISIBLE_DEVICES=0` exits with code 2 before model import.
- Fixed validation bug was patched: validation noise no longer depends on `global_step`.
- Fixed timestep bug was patched: `high_only` validation now samples high-noise band.
- Targeted pytest passed: `tests/test_stageA_broad_lora.py` reports 5 passed.

## Pending

Formal Fast StageA training has not started yet.

Pending gates:

1. generated_v5 conversion workers finish enough completed chunks for a richer immutable snapshot.
2. Snapshot must include completed chunks only and exclude active TDW chunk.
3. Fast single-GPU 20-step high-only preflight.
4. Fast 2-GPU DDP 20-step high-only preflight.
5. Fast 7-GPU DDP 20-step high-only preflight.
6. Adapter save/load round trip.
7. Fixed validation reproducibility check.

## Safety State

- No StageB was run.
- No DPO was run.
- No reward scoring was run.
- No rollout was run.
- GPU0 was not used for training.

## 2026-06-22 Fast high-only preflight update

Status: `FAST_STAGEA_PREFLIGHT_PASS_DATA_WAIT`.

- Stopped and quarantined the earlier Base/low-to-high StageA path; it is not a valid StageA result.
- Correct StageA definition is now LingBot-World-Fast with `branch_mode=high_only`, `noise_policy=high_only`, `high_noise_probability=1.0`, `low_noise_probability=0.0`.
- Single-GPU preflight on physical GPU7 completed 20/20 optimizer steps with finite loss and nonzero gradients for camera-conditioning, self-attention, cross-attention and FFN LoRA groups.
- Two-GPU DDP fixed-val preflight on physical GPU6/7 completed 4/4 optimizer steps; fixed validation ran at steps 2 and 4 and remained finite.
- Seven-GPU DDP fixed-val preflight on physical GPU1-7 completed 2/2 optimizer steps; fixed validation ran at steps 1 and 2 and remained finite.
- Final logs now preserve `branch_mode=high_only` instead of collapsing the Fast run to `branch_mode=high`.
- GPU0 was not used for training; TDW generation tmux sessions remained alive.
- Formal StageA is not started yet because the current generated_v5 converted snapshot is still drop/orbit_left only, so it is not balanced enough for the official warmup run.
