# Prior Art: DPO Backward and LoRA Scope

## Scope

This review is required before the backward-only dry-run. It does not authorize
training, optimizer steps, checkpoint saving, or LoRA saving.

## Files Checked

Local VideoGPA:

- `local_assets/third_party/VideoGPA/official_repo/train/loss.py`
- `local_assets/third_party/VideoGPA/official_repo/train/Wan2.2-TI2V-5B/03_train.py`
- `local_assets/third_party/VideoGPA/official_repo/train/dataset.py`
- `local_assets/third_party/VideoGPA/official_repo/replicate.py`

Local LingBot / Wan:

- `local_assets/third_party/lingbot_world/scripts/train_lingbot_dpo_lora.py`
- `/home/nvme03/workspace/lingbot-world/scripts/train_lingbot_dpo_lora.py`
- `local_assets/third_party/lingbot_world/scripts/train_lingbot_physics_predictor.py`
- `local_assets/third_party/lingbot_world/wan/image2video_fast.py`
- `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`

External primary references checked:

- `https://github.com/Hongyang-Du/VideoGPA`
- `https://raw.githubusercontent.com/Hongyang-Du/VideoGPA/main/train/loss.py`
- `https://raw.githubusercontent.com/Hongyang-Du/VideoGPA/main/train/Wan2.2-TI2V-5B/03_train.py`

## VideoGPA Backward Handling

VideoGPA's public README says its DPO pipeline has three steps: preference
scoring, latent encode, and DPO training. It also states that shared training
components support CogVideo and Wan, with CogVideo using v-prediction and Wan
using flow matching.

`train/loss.py` implements DPO using prediction errors:

- compute winner/loser model MSE against target;
- compute winner/loser reference MSE against target;
- compare model improvement over reference improvement;
- loss is `-logsigmoid(beta * (win_diff - lose_diff))`.

For Wan, `train/Wan2.2-TI2V-5B/03_train.py` uses flow matching:

- `z_t = (1 - sigma) * z_0 + sigma * noise`;
- target velocity is `noise - z_0`;
- reference transformer is loaded separately, set `requires_grad_(False)`, and
  put in `eval()`;
- reference predictions are computed under `torch.no_grad()`;
- policy predictions are differentiable;
- LoRA/PEFT is the intended trainable parameter mechanism;
- actual optimizer and checkpoint code are part of training and are explicitly
  not used in this dry-run.

## LingBot / Wan Trainable Params

LingBot contains `scripts/train_lingbot_dpo_lora.py`. It defines:

- `LoRALinear`;
- `inject_lora`;
- `set_lora_active`;
- freeze-then-open trainable parameters;
- target modes including control/camera-related modules.

The camera/control module names used by LingBot's LoRA selection include:

- `patch_embedding_wancamctrl`;
- `c2ws_hidden_states_layer1`;
- `c2ws_hidden_states_layer2`;
- `cam_injector_layer`;
- `cam_scale_layer`;
- `cam_shift_layer`.

Those names are the safest first scope for this backward-only smoke because the
current task is camera-conditioned LingBot-Fast plumbing. They are still not a
training recommendation; they are only a minimal gradient path check.

## Backward-Only Plan

The dry-run should:

- freeze every reference parameter;
- compute reference energy under `torch.no_grad()`;
- release the reference model before policy backward if needed for memory;
- freeze every policy parameter first;
- enable gradients only for the selected scope;
- compute the same scalar DPO loss already validated in the no-backward run;
- call `loss.backward()`;
- inspect gradients;
- verify reference gradients are absent;
- verify selected policy parameter values did not change;
- clear gradients;
- never construct an optimizer;
- never call `optimizer.step()`;
- never save LoRA or checkpoint.

Recommended scope: `camera_adapter`.

Fallback scopes:

- `tiny_subset` only if camera/control parameters are unavailable or backward
  OOMs;
- existing `lora` only if LoRA parameters have already been injected locally.

## Why No Optimizer Step

This gate only proves differentiability and frozen-reference isolation. An
optimizer step would be a training operation and is outside the current user
approval. If backward-only passes, the next round may ask the user whether to do
a separate 1-pair optimizer-step dry-run.
