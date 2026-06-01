# Prior Art: Reference Energy and DPO Scalar Dry-Run

## Problem

Gate E already has LingBot-compatible video latents, camera-conditioned
conditions, same noise, same timestep, and real policy energy. The remaining
question is whether a frozen LingBot-Fast reference can compute the same
energy and whether a 1-pair scalar DPO objective can be evaluated without
training.

## Files Checked

LingBot / Wan local files:

- `local_assets/third_party/lingbot_world/wan/image2video_fast.py`
- `local_assets/third_party/lingbot_world/wan/modules/model_fast.py`
- `local_assets/third_party/lingbot_world/scripts/train_lingbot_physics_predictor.py`
- `/home/nvme03/workspace/lingbot-world`
- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`

VideoGPA local files:

- `local_assets/third_party/VideoGPA/official_repo/train/loss.py`
- `local_assets/third_party/VideoGPA/official_repo/train/Wan2.2-TI2V-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/dataset.py`

External primary references checked:

- https://github.com/Hongyang-Du/VideoGPA
- https://github.com/CIntellifusion/VideoDPO
- https://github.com/Wan-Video/Wan2.1

## Target and Reference Treatment

LingBot-Fast uses Wan-style flow matching. The local training helper
`sample_flow_batch` defines:

- `z_t = (1 - sigma) * x0 + sigma * noise`
- `target = noise - x0`
- energy as prediction MSE against the target.

VideoGPA's `train/loss.py` computes DPO from winner/loser prediction errors
relative to reference prediction errors. The reference is a frozen model, used
under no-grad/eval semantics. VideoGPA's Wan2.2 training script uses the same
flow target convention and shared noise/timestep for winner and loser.

For this adapter, the reference must be the same frozen LingBot-Fast checkpoint
as the policy base. It must not be LingBot-Base, a reward model, VideoGPA's
native model, or a placeholder.

## Scalar Formula

Energy is MSE, so lower energy means higher likelihood under the denoising
error proxy. Define:

- `Delta_policy = E_policy_loser - E_policy_winner`
- `Delta_ref = E_ref_loser - E_ref_winner`
- `L_DPO = -log sigmoid(beta * (Delta_policy - Delta_ref))`

Positive delta means the model gives the winner lower energy than the loser.
If policy and reference are identical, deltas should match and the scalar loss
should be close to `log(2)`.

## Reuse and Incompatibilities

Reusable:

- LingBot `WanModelFast.forward` for prediction.
- LingBot/Wan VAE latents.
- LingBot camera Plucker/control tensor.
- VideoGPA DPO error-difference formula.

Not directly reusable:

- VideoGPA native CogVideo/Wan2.2 latent encode for LingBot-Fast.
- VideoGPA native train scripts, because this round forbids training and
  LingBot-Fast has a different condition path.
- LingBot-Base as teacher/reference.

## Minimal Implementation Plan

1. Load frozen same-checkpoint LingBot-Fast reference sequentially.
2. Reuse the exact policy-energy path: same batch tensors, same noise, same
   timestep, same camera-conditioned condition, same target.
3. Compute `E_ref_winner` and `E_ref_loser` under `torch.no_grad()`.
4. If finite, compute scalar DPO loss only; no backward, no optimizer.
5. If the reference cannot load or forward, keep reference deferred and do not
   compute scalar loss.
