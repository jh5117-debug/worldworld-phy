# LingBot Forward Path Audit

## Policy Model

- Runtime class: `wan.image2video_fast.WanI2VFast`
- DiT class: `wan.modules.model_fast.WanModelFast`
- VAE class used elsewhere in the adapter: `Wan2_1_VAE`
- The adapter now loads the real LingBot-Fast runtime bundle through
  `WanI2VFast`, not VideoGPA's native VAE/model.

## Forward Signature

`WanModelFast.forward` accepts:

- `x`: list of latent tensors, convention `C,F,H,W`
- `t`: timestep tensor
- `context`: T5/text context list
- `seq_len`: patch-token sequence length
- `y`: image-condition latent list
- `dit_cond_dict`: camera/control dictionary
- `kv_cache` / `crossattn_cache`
- `current_start`
- `max_attention_size`

It returns a list of float prediction tensors after `unpatchify`.

## Condition Path

LingBot-Fast generation builds:

- text context from `self.text_encoder([prompt], device)`;
- image condition `y` from VAE-encoded first image plus zero frames;
- camera/control tensor under `dit_cond_dict["c2ws_plucker_emb"]`;
- self/cross attention caches for causal Wan forward.

The camera/control tensor is used in `model_fast.py`: it is patch embedded,
passed through camera hidden layers, and then injected into attention blocks as
camera scale/shift. This confirms it is not merely read and discarded.

## Latent Convention

The previous LingBot VAE smoke encoded 8 video frames at `480x832` to latent
shape `[16, 2, 60, 104]`.

- Temporal compression: `4x`.
- Spatial compression: `8x`.
- The model forward uses one list element with shape `[16, 2, 60, 104]`.

## Scheduler / Loss Availability

The inference scheduler is `FlowUniPCMultistepScheduler`, but the local
LingBot training script provides the training target directly. It uses a
flow-matching target `noise - x0`. The adapter uses that target for the
1-pair policy-energy dry-run and records the evidence in output JSON.

## Open Risk

The forward adapter reconstructs an image-condition latent for the already
encoded winner/loser latents. It is shape-compatible with LingBot-Fast, but it
is still a smoke path, not a complete training dataloader.
