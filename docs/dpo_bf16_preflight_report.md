# DPO BF16 Preflight Report

Updated: 2026-06-27T07:14:17

## Status

**DPO_BF16_READY**

This report covers the real prefix-aware V2V-5 LingBot-Fast DPO energy backend. It is not the old diagnostic-energy skeleton.

## Prefix5 Input

- Pair manifest: `manifests/anchored_dpo_probe_pairs_prefix5.jsonl`
- Pair count: 50 total; preflight used 5-6 pairs per run.
- Condition: prefix frames 0-4, `prefix_len=5`, `prediction_start_frame=5`.
- Winner/loser target: future frames 5-80.
- Loss/reward frame indices: 5..80 at raw frame level; latent loss slots conservatively exclude prefix-contaminated latent slots (`2..20` for 81 frames).
- `use_action=false`; no action branch is used.

## Real Energy Backend

Implemented path:

1. Decode prefix5 pairs and videos.
2. Precompute VAE latents, text context, prefix-conditioned `y`, and camera Plucker/control tensors with LingBot-Fast Stage1 helper.
3. Release VAE/T5 runtime components.
4. Load LingBot-World-Fast policy only.
5. Apply camera-only LoRA rank 4.
6. Compute flow-matching energy for winner/loser on future latent slots only.
7. Use the same timestep and same noise for winner/loser.
8. Use frozen reference by evaluating the same Fast policy with LoRA scale set to zero under `no_grad`.

LoRA inventory: 160 camera-conditioning modules, 6,553,600 trainable parameters.

## Matrix

See `reports/dpo_bf16_preflight/matrix.csv`.

| Run | Status | World size | Steps | Pairs | Max reserved GB | Mean step sec | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| single_gpu7 | PASS | 1 | 2 | 5 | 88.01 | 192.57 | same_noise=True, same_timestep=True, finite=True, nonzero_grad=True |
| ddp2_gpu67 | PASS | 2 | 5 | 6 | 88.03 | 193.00 | same_noise=True, same_timestep=True, finite=True, nonzero_grad=True |
| ddp8_gpu01234567 | PASS | 8 | 5 | 5 | 88.03 | 194.04 | same_noise=True, same_timestep=True, finite=True, nonzero_grad=True |


## Result

- Single GPU7: PASS, no SIGFPE/OOM/NaN.
- DDP2 on GPU6,7: PASS, no SIGFPE/OOM/NaN.
- DDP8 on GPU0-7: PASS, no SIGFPE/OOM/NaN.
- All runs used the real LingBot-Fast flow-matching energy backend with prefix5 future-only mask.
- DPO loss was finite and gradients were non-zero.
- Rank0 adapter save/load passed.

## Caveats

- Step time is high: about 193 seconds per optimizer step because each DPO step evaluates policy/reference winner/loser energies over 81-frame LingBot-Fast latents.
- The 5-step preflight only verifies numerical/runtime readiness. It does not prove DPO preference learning quality.
- The early DPO signal is weak: loss remains close to 0.693 and winner/loser contribution is small over 2-5 steps.
- `find_unused_parameters=True` caused a DDP performance warning; camera-only LoRA did not show unused parameters. Future probe runs can set this false to reduce overhead after one more sanity check.

## Tiny Probe Status

**DPO_PROBE_BLOCKED_BY_V2V5_GENERATION_WRAPPER**

The real energy/training preflight is ready, but the required checkpoint video evaluation cannot yet be performed honestly: the available Fast inference wrapper is still image-first (`pipe.generate(prompt, image, action_path=...)`) and does not expose a verified V2V-5 generation path that conditions on prefix frames 0-4 and predicts frames 5-80. Therefore I did not run a tiny DPO probe and did not claim checkpoint video metrics.

Required next engineering step before tiny DPO probe:

1. Implement a V2V-5 Fast generation wrapper that passes prefix frames 0-4 as the visible video condition.
2. Verify generated future frames 5-80 are produced under the same prompt/poses/intrinsics.
3. Add checkpoint eval for step0/5/10/20: PSNR, SSIM, LPIPS if available, FVD if available, VBench if available, PhysGeo metrics, and Codex video audit.
4. Only then run the 5-pair/20-step tiny DPO probe.
