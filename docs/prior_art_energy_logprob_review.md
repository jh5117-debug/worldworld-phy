# Prior Art Energy / Logprob Review

## Problem

The adapter already has LingBot-compatible winner/loser latents, the same noise,
the same timestep, and the same camera-conditioned condition pack. The remaining
question is whether those tensors can enter LingBot-Fast's real forward target
without inventing a fake DPO energy.

## Files Reviewed

- LingBot local source: `local_assets/third_party/lingbot_world/wan/image2video_fast.py`
- LingBot local source: `local_assets/third_party/lingbot_world/wan/modules/model_fast.py`
- LingBot local source: `local_assets/third_party/lingbot_world/scripts/train_lingbot_physics_predictor.py`
- VideoGPA official source: `local_assets/third_party/VideoGPA/official_repo/train/loss.py`
- VideoGPA official source: `local_assets/third_party/VideoGPA/official_repo/train/Wan2.2-TI2V-5B/03_train.py`
- Local adapter: `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`

No internet implementation was used as an authority for the target. The usable
evidence is present in the local LingBot and VideoGPA source trees.

## LingBot-Fast Target Evidence

LingBot-Fast inference converts model output back to `x0` with a flow-matching
formula. In `wan/image2video_fast.py::_convert_flow_pred_to_x0`, the comments
define `pred = noise - x0` and `x_t = (1-sigma_t) * x0 + sigma_t * noise`.

LingBot's local physics predictor training script gives the clearest training
target:

- `sample_flow_batch(...)` samples `t` and `noise`.
- It builds `z_t = (1 - sigma) * x0 + sigma * noise`.
- It sets `target = noise - x0`.
- The optional diffusion loss is `mse_loss(pred, target)`.

That means the real target for this dry-run is flow / velocity prediction,
`noise - x0`, not reward score, not VideoGPA-native latent score, and not a
random placeholder.

## VideoGPA Prior Art

VideoGPA's `train/loss.py` implements DPO using prediction-error energies:
winner and loser model errors are MSE against velocity targets, and the
reference model provides the baseline error. VideoGPA's Wan2.2 TI2V training
script also uses shared noise/timestep for winner and loser and defines the
velocity target as `noise - z_0`.

## Compatibility Notes

- Winner/loser must use the same condition, same noise, and same timestep.
- LingBot-Fast model output is a flow/velocity prediction tensor with the same
latent shape as the input latent.
- The camera condition enters `dit_cond_dict["c2ws_plucker_emb"]`.
- The current dry-run may defer the reference model to avoid loading a second
full LingBot-Fast model; that means only policy energies can be produced now.

## Minimal Implementation Plan

1. Load the real LingBot-Fast runtime model in eval mode with all parameters
   frozen.
2. Reuse the already encoded LingBot latents and same noise/timestep batch.
3. Build `x_t` using the local LingBot training script formula.
4. Build the same image/text/camera condition pack used by LingBot-Fast.
5. Forward winner and loser through `WanModelFast.forward`.
6. Compute policy energy as MSE between prediction and `noise - x0`.
7. Keep reference energy deferred unless a second frozen model is explicitly
   loaded later.
8. Do not compute DPO loss, backward, optimizer steps, or LoRA updates.

## Guardrail

If the real forward or target cannot be executed, the adapter must return an
explicit failure or keep `NotImplementedError`. It must not return fake energy,
zero energy, reward-as-energy, or VideoGPA-native energy as a substitute.
