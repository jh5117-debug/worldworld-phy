# DPO Signal Sensitivity Fast Report v2

Date: 2026-06-04

## Scope

This report covers the requested `dpo_signal_sensitivity_fast` gate for the template-diverse TDW / DPO signal run.

No real DPO training, VideoGPA `03_train.py`, Stage1, checkpoint save, or LoRA save was run.

## Execution

The sweep was launched in `tmux` on GPU6/7 as requested:

- session: `dpo_signal_fast`;
- log: `local_assets/outputs/smoke/lingbot_dpo_signal_sensitivity_fast/tmux_stdout_stderr.log`;
- metrics: `local_assets/outputs/smoke/lingbot_dpo_signal_sensitivity_fast/per_lr_step_metrics.jsonl`;
- GPU0 was not used for DPO.

The process was stopped after a reasonable window because only `1e-5` had produced three steps and the sweep had not reached the required multi-LR evidence.

## LR Results

| LR | Status | Steps | Loss Delta | Delta_policy Movement | Preference Logit Movement | Notes |
|---:|---|---:|---:|---:|---:|---|
| 1e-5 | partial | 3 | about `-5.96e-08` | about `4.92e-07` | `1.31e-07` to `1.80e-07` | finite, no NaN/Inf |
| 5e-5 | not reached | 0 | n/a | n/a | n/a | sweep stopped before this LR |
| 1e-4 | not reached | 0 | n/a | n/a | n/a | sweep stopped before this LR |

Observed `1e-5` rows:

| Step | L_DPO | Delta_policy | Delta_ref | Preference Logit | Grad Norm | NaN/Inf |
|---:|---:|---:|---:|---:|---:|---|
| 0 | 0.6931471229 | -0.0061963499 | -0.0061976612 | 1.311e-07 | 2.422e-05 | no |
| 1 | 0.6931470633 | -0.0061959773 | -0.0061976612 | 1.684e-07 | 2.446e-05 | no |
| 2 | 0.6931470633 | -0.0061958581 | -0.0061976612 | 1.803e-07 | 2.425e-05 | no |

## Safety

| Check | Status |
|---|---|
| Real training | no |
| VideoGPA `03_train.py` | no |
| LoRA save | no |
| Checkpoint save | no |
| 5-pair overfit | not run |
| GPU0 use for DPO | no |
| GPU used | GPU6 under `CUDA_VISIBLE_DEVICES=6,7` |
| Peak observed memory | about 54 GiB on GPU6 |
| Final GPU6 memory after stop | 1 MiB |

## Gate Decision

`dpo_signal_sensitivity_fast`: **partial / no-go**.

`5-pair tiny overfit`: **no-go**.

Reason: only one LR setting produced partial metrics; the go condition requires at least two completed LR settings and a clear signal above the previous near-zero baseline.

Next action is to make the runner cheaper/faster or test a stronger camera-control LoRA scope before attempting 5-pair.

