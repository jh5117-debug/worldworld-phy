# Prior Art: LoRA Optimizer-Step Dry-Run

## Current Problem

The previous 1-pair DPO backward-only smoke passed for runtime LoRA injected into:

- `blocks.39.cam_shift_layer`
- `blocks.39.cam_scale_layer`

This round only checks whether one `optimizer.step()` can update those LoRA parameters while leaving LingBot-Fast base and reference parameters unchanged. This is not training, not multi-pair DPO, and not a LoRA/checkpoint save.

## Files And Repos Checked

Local checkout checks:

- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`
- `cam_physgeo/dpo/lora_utils.py`
- `configs/cam_physgeo/stage2_anchored_dpo.yaml`
- `configs/cam_physgeo/stage1_warmup.yaml`
- `cam_physgeo/training/model_loading.py`
- `cam_physgeo/training/lora_utils.py`

Local `/tmp/local_assets_work` does not contain `local_assets/third_party/VideoGPA/official_repo` or `local_assets/third_party/lingbot_world`; those paths exist on the remote/shared asset machine in prior runs, but the first SSH environment probe in this round was reset by the server. I therefore used the already-audited local adapter code plus official upstream sources:

- VideoGPA README: https://github.com/Hongyang-Du/VideoGPA
- VideoGPA DPO loss: https://raw.githubusercontent.com/Hongyang-Du/VideoGPA/main/train/loss.py
- VideoGPA Wan2.2 trainer: https://raw.githubusercontent.com/Hongyang-Du/VideoGPA/main/train/Wan2.2-TI2V-5B/03_train.py
- Wan2.1 official repo: https://github.com/Wan-Video/Wan2.1
- musubi-tuner Wan LoRA docs: https://github.com/kohya-ss/musubi-tuner/blob/main/docs/wan.md

## VideoGPA Optimizer Handling

VideoGPA official code structures DPO as three stages: preference pairs, latent encode, then `03_train.py`. Its README states that shared `train/loss.py` works across CogVideo and Wan, with CogVideo using v-prediction and Wan using flow matching.

The upstream `train/loss.py` defines DPO reward as negative prediction error. The loss uses:

`-log sigmoid(beta * (win_diff - lose_diff))`

where `win_diff = ref_win_err - model_win_err` and `lose_diff = ref_lose_err - model_lose_err`.

The upstream Wan2.2 trainer uses PEFT `LoraConfig`, wraps the Wan model with `get_peft_model`, keeps a frozen reference model, computes reference predictions under `torch.no_grad()`, then optimizes the LoRA-wrapped transformer with AdamW. It also uses gradient clipping through Lightning.

## LingBot/Wan Local Findings

Our local LingBot adapter already uses the same conceptual pieces, but not the upstream VideoGPA model:

- LingBot-Fast/Wan VAE latents are real LingBot latents.
- Condition includes prompt/image/camera Plucker control.
- The flow target is `noise - x0`.
- Reference energy is computed with the same frozen LingBot-Fast checkpoint, not Base, reward, or VideoGPA native model.
- Runtime LoRA is injected into camera-control layers only and is never saved.

The config files contain low learning-rate precedent (`1e-5`) for adapter/LoRA warm-up style work, and the upstream VideoGPA trainers use AdamW or an AdamW variant for LoRA parameters.

## Optimizer Choice

For this dry-run, use:

- optimizer: `torch.optim.AdamW`
- learning rate: `1e-5`
- max grad norm: `1.0`
- param group: LoRA parameters only

The lr is intentionally conservative because this is a one-step plumbing and safety check, not a learning-rate search. Runtime LoRA factors are kept in fp32 so an `lr=1e-5` AdamW update is numerically observable while the frozen LingBot base remains bf16.

## Safety Plan

The dry-run must:

- inject LoRA only into `blocks.39.cam_shift_layer` and `blocks.39.cam_scale_layer`;
- freeze every base parameter;
- compute reference energy under `no_grad`;
- build an AdamW optimizer over LoRA params only;
- run exactly one `loss.backward()`;
- optionally clip gradients at `1.0`;
- run exactly one `optimizer.step()`;
- record before/after LoRA diff;
- record before/after base/reference sample diff;
- verify reference grads are zero;
- verify base grads are zero;
- verify LoRA params changed;
- restore or discard the runtime LoRA object after the step;
- write only smoke summaries under `local_assets/outputs/smoke`;
- save no LoRA, no checkpoint, no model weights.

## Why Not More

This is still Gate E plumbing. It does not prove multi-pair stability, does not validate hyperparameters, and does not authorize real DPO training. If it passes, the next possible action is only a user-approved 1-pair mini-loop, for example 5 optimizer steps on the same pair with no checkpoint save.
