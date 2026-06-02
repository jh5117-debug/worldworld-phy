# LoRA Functional Influence Probe Report

## Summary

- Status: passed.
- Pair count: `1`.
- Fixed noise seed: `123`.
- Fixed timestep: `579`.
- No backward: yes.
- No optimizer: yes.
- No LoRA/checkpoint save: yes.
- Target modules:
  - `blocks.39.cam_shift_layer`
  - `blocks.39.cam_scale_layer`
- Rank/alpha: `2 / 4.0`.

## Result

The target modules are in the forward path. Scaled LoRA changes both prediction
tensors and policy energies. At normal rank-2/alpha-4 scale, however, the energy
movement is extremely small.

| variant | E_winner | E_loser | Delta | Delta change vs no_lora | winner pred L2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| no_lora | 0.1394616365 | 0.1332639754 | -0.0061976612 | 0.0 | n/a |
| lora_zero | 0.1394616365 | 0.1332639754 | -0.0061976612 | 0.0 | 0.0 |
| lora_default | 0.1394614577 | 0.1332638562 | -0.0061976016 | 5.960e-08 | 0.265935 |
| lora_scaled_10x | 0.1394625008 | 0.1332677454 | -0.0061947554 | 2.906e-06 | 0.469572 |
| lora_scaled_100x | 0.1394594461 | 0.1332598627 | -0.0061995834 | -1.922e-06 | 0.796730 |

## Interpretation

- LoRA contribution is not dead.
- `lora_zero` matches `no_lora`, confirming the wrapper does not perturb the
  frozen base path when its contribution is zeroed.
- `lora_default` affects predictions but energy movement is around `6e-08`.
- Scaling LoRA produces larger energy changes, so the weak fixed-noise
  mini-loop signal is likely due to normal-scale contribution being tiny, not
  because the modules are absent from the forward path.

## Raw Output

Remote output path, not committed:

`local_assets/outputs/smoke/lingbot_lora_functional_influence_probe/summary.json`
