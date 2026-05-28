# LingBot-Fast VideoGPA Minimal Adapter Plan

This document defines the minimum adapter surface. It is not a trainer and does not fake DPO logprobs.

## Minimal Integration Path
1. Keep VideoGPA official code unchanged.
2. Export Physion clean/corrupt pairs as VideoGPA `groups` JSON.
3. Use this adapter to preserve image/prompt/poses/intrinsics and prepare winner/loser batch metadata.
4. Implement LingBot VAE latent encoding and camera-condition encoding in wrapper code.
5. Only after real `compute_dpo_energy_or_logprob` exists, call VideoGPA train logic through a wrapper.

## Method Status
- `load_model`: implemented=False; dependency=wan.WanI2VFast + runtime symlink bundle; input=paths/config; output=policy model; camera=True; intrinsics=True; dummy_action=False; notes=runtime inference exists separately; VideoGPA policy object not wired
- `load_reference_model`: implemented=False; dependency=same as load_model; input=paths/config; output=frozen ref model; camera=True; intrinsics=True; dummy_action=False; notes=required before DPO
- `encode_video_to_latent`: implemented=False; dependency=LingBot Wan2_1_VAE; input=mp4/video tensor; output=latent B,C,F,H,W; camera=False; intrinsics=False; dummy_action=False; notes=required for VideoGPA encode
- `encode_condition`: implemented=True; dependency=cam-only sample files; input=sample_dir; output=metadata + shape dict; camera=True; intrinsics=True; dummy_action=True; notes=shape dry-run only; dummy action is not a core condition
- `prepare_winner_loser_batch`: implemented=True; dependency=VideoGPA pair JSON; input=pair dict; output=batch contract dict; camera=True; intrinsics=True; dummy_action=True; notes=shape/metadata dry-run only
- `compute_dpo_energy_or_logprob`: implemented=False; dependency=LingBot forward/noise scheduler; input=winner/loser latents + condition; output=scalar energy/logprob delta; camera=True; intrinsics=True; dummy_action=False; notes=must be real before any DPO train

## Current Gate
- Training allowed: False
- Reason: DPO energy/logprob and latent encode are NotImplemented by design.

If VideoGPA source changes become unavoidable, prefer a small wrapper or patch file over editing `local_assets/third_party/VideoGPA/official_repo` directly.
