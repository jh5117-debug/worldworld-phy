# Final Report: LingBot VAE / Energy Dry-Run

## Gates

- Gate A: passed. LingBot-Fast 1-sample inference already passed.
- Gate B: passed. 3 Fast rollout smoke already passed.
- Gate C: partial/pass. Camera embedding/control and strong stress video effect passed; ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke. Reward v5 clean > Fast passed with RAFT and DINO active, but generated depth/mask/physics are still incomplete.
- Gate E: partial/pass. LingBot VAE latent encode, condition encode, and same-noise/same-timestep batch shape dry-run passed. Energy/logprob remains blocked.
- Gate F: no. DPO training is still disallowed.

## VAE Path Audit

- VAE class: `Wan2_1_VAE`
- VAE module: `local_assets/third_party/lingbot_world/wan/modules/vae2_1.py`
- Runtime checkpoint: `local_assets/cache/lingbot_fast_cam_runtime/Wan2.1_VAE.pth`
- Companion Base candidate: `local_assets/weights/lingbot_base/Wan2.1_VAE.pth`
- VideoGPA native VAE compatibility: not assumed. Native VideoGPA encoders do not prove LingBot-Fast Wan2.1 camera-conditioned latent compatibility.
- Input convention: `C,T,H,W`
- Successful input shape: `[3, 8, 480, 832]`
- Latent shape: `[16, 2, 60, 104]`
- Inferred compression: temporal `4x`, spatial `8x`.

## VAE Load

- Status: passed.
- Device: `cuda` under `CUDA_VISIBLE_DEVICES=6,7`
- Requested dtype: `bf16`
- Init pattern: `vae_pth_device`
- Load time: about `17s`
- Peak VAE-only allocation: about `531 MB`
- Peak pair-encode allocation: about `6.50 GB`

## Latent Encode

- Status: passed for one `gt_vs_fast_rollout` pair.
- Pair id: `pair_2a77384981ab`
- Winner latent shape: `[16, 2, 60, 104]`
- Loser latent shape: `[16, 2, 60, 104]`
- Latent dtype returned by VAE: `float32`
- Winner latent mean/std: `-0.0452 / 0.5787`
- Loser latent mean/std: `-0.0372 / 0.5229`
- NaN/Inf: none.
- Decode reconstruction: not attempted; decode path is not wired in this dry-run.
- Camera metadata sidecar: preserved.

## Condition Encode

- Status: passed.
- Image condition: read.
- Prompt: read.
- Text embedding: deferred to LingBot runtime; not generated in this dry-run.
- Poses shape: `[81, 4, 4]`
- Raw intrinsics shape: `[81, 4, 4]`
- Converted intrinsics shape: `[81, 4]`
- Dummy action shape: `[81, 4]`
- Dummy action norm: `0.0`
- `use_action=false`: preserved.
- Plucker/control tensor: `[1, 448, 2, 60, 104]`, CPU dry-run, nonzero and finite.
- `can_use_for_training_forward`: true at condition-pack shape level.

## Batch Dry-Run

- Status: passed.
- Winner/loser latent shape: `[16, 2, 60, 104]`
- Batch dtype: `bfloat16`
- Noise shape: `[16, 2, 60, 104]`
- Same noise: confirmed.
- Same timestep: confirmed.
- Timestep value in this run: `579`
- Reward margin: `0.5240882262358174`
- Condition keys preserved, including image, prompt, poses, intrinsics, metadata, action, and `use_action`.
- No model forward, backward, optimizer, LoRA save, or parameter update was run.

## Energy / Logprob Dry-Run

- Status: `NotImplemented`.
- Real forward found: not yet.
- Energy values finite: not applicable; no energy values were produced.
- Reference model status: deferred.
- Policy LoRA status: deferred.
- Exact blocker: the adapter has not wired LingBot-Fast's real denoising / velocity / flow-matching training target, so `compute_dpo_energy_or_logprob` intentionally remains `NotImplementedError`.

## Next Round Permission

- 1-pair DPO loss scalar dry-run: not yet allowed. The next round should first wire the real LingBot forward/velocity target and keep the run no-backward/no-optimizer unless separately approved.
- Real DPO training: no.

## Next Minimal Action

Fix only the energy/logprob interface next:

- identify LingBot-Fast latent forward layout;
- identify timestep/noise scheduler contract;
- identify velocity or denoising target;
- load a frozen reference without updating it;
- compute real prediction-error energy for winner/loser without backward.

Do not jump to training.

