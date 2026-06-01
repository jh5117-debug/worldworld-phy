# Final Report: Tiny LoRA Camera-Control Backward

## Gates

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: passed for 1-pair plumbing and meaningful camera-control LoRA
  backward-only.
- Gate F: no. Real DPO training remains disallowed.

## Execution

- Local git worktree: `/tmp/local_assets_work`
- Remote execution worktree:
  `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_tiny_lora_work`
- Branch: `physion-dpo-tiny-lora-backward`
- Base branch: `physion-dpo-trainable-scope-sweep`
- `local_assets` on the remote worktree symlinks to:
  `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets`
- No data, weights, videos, latents, HDF5, NPY/NPZ/PT/PTH, safetensors, LoRA
  weights, or checkpoints were moved or deleted.
- No `local_assets` outputs were staged or committed.

## Prior Art

VideoGPA official scripts use PEFT/LoRA for trainable parameters and keep a
frozen reference model. LingBot/Wan local examples include LoRA-style wrappers,
but the loaded LingBot-Fast checkpoint had no pre-existing LoRA params. The
implemented path therefore uses an in-repo runtime `LoRALinear` wrapper and
does not modify third-party source or weight files.

## LoRA Target Inspection

Candidate camera/control modules:

- `patch_embedding_wancamctrl`
- `c2ws_hidden_states_layer1`
- `c2ws_hidden_states_layer2`
- `blocks.*.cam_injector_layer1`
- `blocks.*.cam_injector_layer2`
- `blocks.*.cam_scale_layer`
- `blocks.*.cam_shift_layer`

Chosen modules:

- `blocks.39.cam_shift_layer`
- `blocks.39.cam_scale_layer`

These are late-block camera scale/shift linears. They are camera-aware and much
smaller than full `camera_adapter`.

## LoRA Implementation

- File: `cam_physgeo/dpo/lora_utils.py`
- Wrapper: `LoRALinear`
- Formula: `base(x) + (alpha / rank) * B(A(x))`
- Base weight/bias: frozen.
- Trainable params: `lora_A`, `lora_B`.
- Rank: `2`
- Alpha: `4.0`
- Tests:
  - `python -m compileall -q cam_physgeo`: passed.
  - `PYTHONPATH=. pytest -q tests/test_lora_utils.py tests/test_reward_confidence.py`:
    passed locally, `7 passed`.
  - Remote LingBot env had no `pytest`; `python tests/test_lora_utils.py` fallback
    was used as an import/parse smoke only.

## LoRA Injection

- Scope: `camera_control_lora_tiny`
- Target modules:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- LoRA params per module: `20,480`
- Total LoRA params: `40,960`
- Base params per wrapped module: `26,219,520`
- Base params frozen: yes.
- Reference params frozen: yes.
- Adapter saved: no.

## Backward-Only Result

- Result: passed.
- Pair count: `1`
- `L_DPO`: `0.6931474208831787`
- Trainable param count: `40,960`
- Trainable tensors:
  - `blocks.39.cam_scale_layer.lora_A`
  - `blocks.39.cam_scale_layer.lora_B`
  - `blocks.39.cam_shift_layer.lora_A`
  - `blocks.39.cam_shift_layer.lora_B`
- Params with grad: `4`
- LoRA params with grad: `4`
- Base params with grad: `0`
- Reference params with grad: `0`
- Grad norm min: `1.3558941702740412e-07`
- Grad norm max: `1.8463962987880222e-05`
- Grad norm mean: `7.5887910888639e-06`
- Any NaN/Inf grad: no.
- Parameter update check max diff: `0.0`
- Optimizer: none.
- Optimizer step: none.
- LoRA/checkpoint save: none.
- OOM: no.

Remote summary path:

`local_assets/outputs/smoke/lingbot_dpo_lora_backward_only_dryrun/rank2_explicit_late_shift_scale/grad_summary.json`

## Comparison

| Scope | Params | Camera-related | Backward | OOM | Meaningful |
| --- | ---: | --- | --- | --- | --- |
| `tiny_subset` | 327,744 | no | passed | no | plumbing only |
| `head_only` | 337,984 | no | passed | no | plumbing only |
| `plucker_projection_only` | n/a | yes | failed | yes | too much activation memory |
| `action_scale_shift_tiny` | n/a | yes | failed | yes | too much activation memory |
| `camera_control_lora_tiny` | 40,960 | yes | passed | no | yes |

## Next Gate

Next round may request a 1-pair optimizer-step dry-run on
`camera_control_lora_tiny` only, with:

- no checkpoint save;
- no LoRA save;
- one pair only;
- before/after parameter diff;
- reference frozen;
- explicit user confirmation before running.

Real DPO training remains no.

## Next Minimal Action

If continuing DPO plumbing: ask before a 1-pair optimizer-step dry-run on the
rank-2 late camera scale/shift LoRA scope. If the user wants data work instead,
only a 1-sample TDW generation dry-run is appropriate. No real training yet.
