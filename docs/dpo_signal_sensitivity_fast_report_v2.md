# DPO Signal Sensitivity Fast Report v2

Generated: 2026-06-04

## Command

The requested `dpo_signal_sensitivity_fast` command was launched with:

- `CUDA_VISIBLE_DEVICES=6,7`
- fixed noise seed `123`
- fixed timestep `579`
- LoRA target modules: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`
- rank / alpha: `2 / 4`
- learning rates: `1e-5`, `5e-5`, `1e-4`
- steps per LR: `5`
- no LoRA save
- no checkpoint
- no 5-pair run

## Runtime Result

Status: failed / interrupted as a runtime blocker.

Evidence:

- The process loaded the LingBot-Fast checkpoint and entered the DPO signal runner.
- GPU use was constrained to GPU6/7 through `CUDA_VISIBLE_DEVICES=6,7`.
- GPU6 reached approximately `46.5 GiB` during the run; GPU7 stayed idle.
- After roughly 25 minutes the process had not produced `signal_sensitivity_fast_summary.json`.
- The run was interrupted to avoid an uncontrolled long GPU diagnostic.
- GPU6/7 returned idle after interruption.

## Metrics

No complete LR result was written. Therefore:

| Metric | Value |
|---|---|
| Sweep completed | no |
| LR settings completed | 0 confirmed |
| loss delta per LR | unavailable |
| Delta_policy movement | unavailable |
| preference logit movement | unavailable |
| recommended LR | none |
| NaN/Inf | not observed in completed outputs; no final summary |
| OOM | no explicit OOM; runtime too long |

## Gate Decision

Signal gate: not passed.

The previous weak signal baseline is still the governing evidence:

- default rank-2 energy movement about `5.960e-08`
- preference logit about `2.831e-08`
- full LR/scope sweep still incomplete

5-pair tiny overfit remains no-go.
