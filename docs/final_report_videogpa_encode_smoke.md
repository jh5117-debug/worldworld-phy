# Final Report: VideoGPA Encode Smoke

## Gates

- Gate A: passed. LingBot-Fast 1-sample inference works.
- Gate B: passed. Three Fast rollout smoke videos exist.
- Gate C: partial/pass. Camera embedding, DiT camera/control path, and strong stress video-level effect are confirmed; ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke. Reward v5 has clean > Fast on 3/3 with RAFT and DINO active, but generated depth/mask/physics are still incomplete.
- Gate E: partial. Pair export and encode-readiness smoke passed; native latent encode did not run.
- Gate F: no. DPO remains disallowed.

## Pair Export

- Fresh `gt_vs_corrupt` with the requested settings kept `0` pairs and rejected `10`; this was not used for encode smoke.
- Fresh `gt_vs_fast_rollout` kept `2` pairs using reward v5 confidence-weighted margins.
- Existing old `gt_vs_corrupt` rows were checked as a fallback, but their older schema lacks complete camera condition fields, so they are not the primary source.
- Primary exported JSON: `local_assets/data/physion/processed/dpo_pairs/videogpa_encode_smoke/videogpa_gt_vs_fast_pairs.json`
- Pair count: `2`
- Winner: clean Physion GT `target.mp4`
- Loser: LingBot-Fast zero-shot `generated.mp4`
- Reward breakdown: preserved from reward v5 rows.
- Camera metadata: preserved in `extra_condition` and sidecars.
- `use_action=false`: preserved.

## VideoGPA Dry-Run

- Pair JSON readable: yes.
- Winner/loser videos readable: yes.
- Prompt readable: yes.
- Condition image readable: yes.
- `poses.npy` and `intrinsics.npy` metadata readable: yes.
- Output directory writable: yes.
- Native encode scripts found:
  - `train/CogVideoX-5B/02_encode.py`
  - `train/CogVideoX-I2V-5B/02_encode.py`
  - `train/CogVideoX1.5-5B/02_encode.py`
  - `train/Wan2.2-TI2V-5B/02_encode.py`
- Native train scripts were found but not run.

## Encode Smoke

- Status: partial.
- Encoded pair count: `0`
- Latent paths: none.
- Latent shape: none.
- Prompt preserved: yes.
- Image preserved: yes.
- Poses/intrinsics sidecar preserved: yes.
- Sidecars: `local_assets/outputs/smoke/videogpa_encode_gt_vs_fast/sidecars/`
- VAE compatibility: not established.

Native VideoGPA encode is model-specific and expects CogVideoX/Wan2.2 VAE/model configs. LingBot-Fast uses project-local WanI2VFast, companion LingBot VAE/T5 assets, and camera Plucker conditioning. Because `LingBotFastVideoGPAAdapter.load_vae` and `encode_video_to_latent` are still `NotImplementedError`, this round intentionally stopped before latent writing.

## LingBot-Fast Adapter Plan

Implemented:

- `encode_condition(...)` shape/metadata dry-run.
- `collate_winner_loser_batch(...)` metadata batch contract.

Not implemented:

- `load_policy_model(...)`
- `load_reference_model(...)`
- `load_vae(...)`
- `encode_video_to_latent(...)`
- `sample_same_noise_timestep(...)`
- `compute_dpo_energy_or_logprob(...)`
- LoRA save/load

The future DPO batch must use the same prompt, image, poses/intrinsics-derived Plucker camera control, timestep, and noise for winner and loser. `compute_dpo_energy_or_logprob` must be real; no fake loss path is allowed.

## DPO Decision

Next round may not do real DPO training. It may only do a DPO batch/energy dry-run if it first implements real LingBot VAE latent encode, same-noise/same-timestep sampling, and a non-fake energy/logprob path.

Real DPO training remains disallowed.

## Validation

- Local code compile: passed.
- Local `tests/test_reward_confidence.py`: `4 passed`.
- Remote VideoGPA inspect: passed.
- Remote pair export: partial/pass; `gt_vs_fast` valid, requested new `gt_vs_corrupt` empty.
- Remote encode smoke: partial; metadata/video read passed, native latent encode blocked by missing LingBot VAE adapter.

## Next Minimal Action

If continuing, do only a LingBot-Fast VideoGPA adapter dry-run:

1. Implement `load_vae` and `encode_video_to_latent` with LingBot/Wan VAE.
2. Preserve image/prompt/poses/intrinsics sidecar as a real condition batch.
3. Implement same-noise/same-timestep sampling.
4. Implement real `compute_dpo_energy_or_logprob`.
5. Run a 1-pair, 1-step dry-run only.

Do not jump to training.
