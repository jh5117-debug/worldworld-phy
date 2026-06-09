# TDW v5 200 LingBot Component Load Smoke

Date: 2026-06-09

Status: passed true component load.

Ran on H20 helper worktree:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work`

Command used physical GPU7 via `CUDA_VISIBLE_DEVICES=7`.

## Loaded Components

| Component | Result |
|---|---|
| Tokenizer | loaded, `T5TokenizerFast`, vocab size 256300 |
| Policy pipeline | loaded, `WanI2VFast` |
| Policy model | loaded, `WanModelFast` |
| Scheduler | loaded, `FlowUniPCMultistepScheduler` |
| Train timesteps | 1000 |
| VAE | loaded, `Wan2_1_VAE` |
| Camera condition helper | deferred to forward condition build |
| Expert route | `unavailable_in_fast_or_not_exposed` |

Checkpoint inspection:

- Base checkpoint has high-noise / low-noise layout: yes.
- Fast checkpoint has explicit high/low branches: no.

Runtime:

- elapsed: 488.8 seconds;
- GPU7 memory during load: about 46878 MiB;
- GPU7 memory after cleanup: released to idle.

Safety:

- no backward;
- no optimizer;
- no checkpoint;
- no LoRA save;
- no model update.

Raw report path:

`local_assets/experiments/exp_tdw_v5_200_true_forward_loss_gate/component_load_smoke/component_load_smoke_report.json`
