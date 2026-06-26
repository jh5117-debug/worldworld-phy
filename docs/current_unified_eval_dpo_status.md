# Current Unified Eval / DPO Status

Updated: 2026-06-27 00:55 CST

## Repository

- Repo: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work`
- Branch: `research/quant-small-lora-dpo-probe-20260624`
- HEAD observed: `a4b8b68 Fix overnight video audit CSV handling`
- Remote: `git@github-worldworld-phy-deploy:jh5117-debug/worldworld-phy.git`

## Supervisor State

State file:
`local_assets/overnight_quant_lora_dpo_20260624_overnight_test/pipeline_state.json`

Observed PASS stages:

- small-LoRA sweep A/B/C/D
- screen16 rollout
- screen16 video audit
- screen16 quantitative screen
- candidate selection
- selected-candidate full80 benchmark
- anchored pair build
- reward calibration v2

Observed BLOCKED stages:

- DPO BF16 single GPU
- DPO BF16 DDP2
- DPO BF16 DDP8
- DPO probe
- post-DPO eval

Current DPO blocker:

`cam_physgeo/training/train_stage2_anchored_dpo.py` is still a guarded skeleton. It loads the pair dataset and prints a plan, but `--run` raises a RuntimeError instead of running a real LingBot-Fast policy/reference DPO step.

## Model / Checkpoint State

Original Fast is available.

Small-LoRA checkpoints are available for:

- A camera-only rank4: steps 50 / 100 / 200
- B camera-only rank8: steps 50 / 100 / 200
- C camera + limited self-attention rank4: steps 50 / 100 / 200
- D camera + limited cross-attention rank4: steps 50 / 100 / 200

Selected candidate from the existing screen16 diagnostic selection:

- `D_step050`

Selection note:

The existing candidate decision explicitly says it is a screen16 proxy/diagnostic selection and that final full80 plus visual audit are still required.

Old camera-only tiny LoRA:

- Legacy adapter path exists from the previous week, but strict Fast adapter loading currently blocks it because it lacks `adapter_metadata.json`.
- It must not be silently treated as Original Fast.

## Existing Rollout / Metrics State

Existing screen16 rollout:

- 13 labels: Original Fast plus A/B/C/D step50/100/200
- 208 videos total

Existing full80 rollout:

- Original Fast: 80 videos
- D_step050: 80 videos

Missing for this task:

- full80 rollout for the remaining small-LoRA checkpoints
- traditional metrics beyond the current PSNR/SSIM/proxy set: LPIPS, FVD, VBench
- full Codex visual audit for the newly generated full80 videos
- prefix-aware I2V/V2V support
- real LingBot-Fast anchored DPO trainer and BF16 DPO preflight

## GPU / Disk

Observed GPU0-7 all available at start of this round.

Disk:

- `/home/nvme04` free space observed around 336 GB.

## Immediate Next Work

1. Launch missing full80 rollouts for all available small-LoRA checkpoints without overwriting existing outputs.
2. Build a unified model inventory and metric report.
3. Add or wire LPIPS/FVD/VBench reporting, marking VBench as blocked if the official environment is unavailable.
4. Implement prefix-aware conditioning manifests and masks.
5. Replace the guarded DPO skeleton with a real, tiny LingBot-Fast anchored DPO preflight path.
6. Run DPO BF16 preflight before any DPO probe.

