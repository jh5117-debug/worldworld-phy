# LingBot DPO LoRA Backward-Only Report

## Status

- Result: passed.
- Mode: `dpo_backward_only_dryrun`
- Pair count: `1`
- Training: no.
- Optimizer: no.
- Optimizer step: no.
- LoRA save: no.
- Checkpoint save: no.
- Reference: frozen/no-grad same LingBot-Fast checkpoint.

## Target Scope

- Scope: `camera_control_lora_tiny`
- Target modules:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- LoRA rank: `2`
- LoRA alpha: `4.0`
- Trainable LoRA params: `40,960`
- Selected trainable tensors:
  - `blocks.39.cam_scale_layer.lora_A`
  - `blocks.39.cam_scale_layer.lora_B`
  - `blocks.39.cam_shift_layer.lora_A`
  - `blocks.39.cam_shift_layer.lora_B`

## Backward Result

- `L_DPO`: `0.6931474208831787`
- Loss finite: yes.
- Params with grad: `4`
- Params without grad among trainable tensors: `0`
- LoRA params with grad: `4`
- Base params with grad: `0`
- Reference params with grad: `0`
- Grad norm min: `1.3558941702740412e-07`
- Grad norm max: `1.8463962987880222e-05`
- Grad norm mean: `7.5887910888639e-06`
- Any NaN grad: no.
- Any Inf grad: no.
- Parameter update check max diff: `0.0`
- Parameter update check: passed.

## Energy / Loss Context

Policy and reference are still the same frozen LingBot-Fast base checkpoint in
this dry-run. A loss near `log(2)` is therefore expected and only validates
the plumbing and gradient path.

## Memory

- CUDA visible devices: `6,7`
- Max allocated bytes: `54,447,969,792`
- Reserved bytes after run summary: `56,600,035,328`
- The successful rank-2 LoRA run used a peak similar to the earlier
  `tiny_subset` backward path and did not OOM.
- A stale rank-1 fallback process from an interrupted combined script was
  detected and stopped. No adapter process remained afterward; remaining GPU
  jobs were unrelated processes outside this project.

## Raw Outputs

- Summary JSON:
  `local_assets/outputs/smoke/lingbot_dpo_lora_backward_only_dryrun/rank2_explicit_late_shift_scale/grad_summary.json`
- Raw log:
  `local_assets/outputs/smoke/lingbot_dpo_lora_backward_only_dryrun/rank2_explicit_late_shift_scale/stdout_stderr.log`

## Conclusion

Meaningful camera-control LoRA backward-only passed. This is stronger than
`tiny_subset`/`head_only` plumbing and safer than full `camera_adapter`.

Next round may ask the user whether to run a 1-pair optimizer-step dry-run on
this LoRA scope only. Real DPO training remains disallowed.
