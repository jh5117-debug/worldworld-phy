# LingBot-Fast VideoGPA Minimal Adapter Plan V2

This is an adapter plan and shape/metadata dry-run. It is not a trainer and does not fake DPO logprobs.

## Implemented Now

- `encode_condition(...)`: implemented as shape/metadata dry-run over image, prompt, poses, intrinsics, metadata, and dummy action presence.
- `collate_winner_loser_batch(...)`: implemented as a metadata batch contract over VideoGPA pair JSON.

## Not Implemented By Design

- `load_policy_model(...)`: `NotImplementedError`.
- `load_reference_model(...)`: `NotImplementedError`.
- `load_vae(...)`: `NotImplementedError`.
- `encode_video_to_latent(...)`: `NotImplementedError`.
- `sample_same_noise_timestep(...)`: `NotImplementedError`.
- `compute_dpo_energy_or_logprob(...)`: `NotImplementedError`.
- `save_lora_adapter(...)`: `NotImplementedError`.
- `load_lora_adapter(...)`: `NotImplementedError`.

## Batch Dry-Run Contract

For the first fresh `gt_vs_fast` pair:

- Winner video: clean Physion `target.mp4`.
- Loser video: LingBot-Fast zero-shot `generated.mp4`.
- Condition keys: camera sidecar, dummy action path, image, intrinsics, metadata, poses, prefix, `use_action`.
- Poses path: preserved.
- Intrinsics path: preserved.
- Prompt: preserved.
- Winner/loser latent contract: `B,C,F,H,W` after future LingBot VAE encode.
- Same noise / same timestep: required, not implemented.

## Camera Condition Forward Path

Camera poses and converted intrinsics must enter LingBot-Fast through the same condition path that produced `c2ws_plucker_emb` and DiT camera/control modulation in inference. VideoGPA native dataset code does not do this. A wrapper must collate image, prompt, poses, intrinsics, and dummy action metadata before calling LingBot-Fast policy/reference forwards.

## Dummy Action

`use_action=false` remains mandatory. Dummy zero `action.npy` is compatibility-only and must not replace camera condition.

## Reference Model

The reference model should be a frozen LingBot-Fast copy using the same VAE, text encoder, scheduler, and camera condition inputs as the policy. It must not be LingBot-Base teacher by default.

## LoRA / Adapter Plan

LoRA should attach only after a real loss path exists. Likely targets are policy DiT/control projection modules. Do not attach or train LoRA during encode smoke.

## Official VideoGPA Repo

Prefer a wrapper under `cam_physgeo/dpo/`. Do not edit `local_assets/third_party/VideoGPA/official_repo` directly. If a patch becomes unavoidable, create a small patch file and document it.

## Training Gate

Training remains blocked until real LingBot latent encode, same-noise/same-timestep sampling, and real DPO energy/logprob are implemented and tested in a 1-step dry-run.
