# Final Report: TDW v5 200 Stage A Balanced Warmup

Date: 2026-06-09

## Why Rerun

The previous Stage A high-noise pilot passed as a real training-chain stability smoke, but it was unbalanced: the first 20 train rows were all `collision + orbit_right_64`. That proved model load, VAE, camera condition, backward, optimizer, and tiny LoRA update stability, but it did not prove coverage across templates/camera variants.

## Sampler

Implemented sampler controls in `cam_physgeo/training/lingbot_warmup_smoke.py`:

- `--mode sampler_dryrun`;
- `--sampler sequential|shuffle|balanced`;
- `--balance_keys template,camera_variant`;
- `--shuffle_seed`;
- `--sample_without_replacement`;
- `--log_sample_ids`;
- `--log_template_camera_stats`.

Dry-run passed:

- first 20 templates: `drop:5`, `collision:5`, `roll:5`, `containment:5`;
- first 60 templates: `drop:15`, `collision:15`, `roll:15`, `containment:15`;
- first 60 camera variants: 5 variants;
- duplicate samples: `0`.

## Training

Balanced Stage A pilot passed.

- GPU: GPU7 only;
- model: LingBot-Fast (`WanI2VFast` / `WanModelFast`);
- timestep mode: diagnostic high-noise;
- timestep / sigma: `799 / 0.799`;
- trainable scope: `camera_control_lora_tiny`;
- LoRA targets: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`;
- trainable params: `40,960`;
- optimizer: AdamW, LoRA params only;
- steps: `60 / 60`;
- runtime: about `9028` seconds.

Train loss:

- first: `0.065782`;
- last: `0.053271`;
- min: `0.033201`;
- max: `0.067220`.

Val loss:

- step 20: `0.037449`;
- step 40: `0.046542`;
- step 60: `0.057670`.

Grad norm:

- first: `0.002388`;
- last: `0.007207`;
- max: `0.012527`.

There was no NaN, Inf, or OOM.

## Coverage

All 60 train steps:

- `drop`: 15;
- `collision`: 15;
- `roll`: 15;
- `containment`: 15.

Camera variants:

- `orbit_left_72`: 15;
- `strafe_left_180`: 8;
- `orbit_right_60`: 15;
- `orbit_left_44`: 15;
- `orbit_right_64`: 7.

Representative first samples:

- `tdw_v3_00047_drop_orbit_left_72_seed22047_0000`;
- `tdw_v3_00069_collision_strafe_left_180_seed22069_0000`;
- `tdw_v3_00131_roll_orbit_right_60_seed22131_0000`;
- `tdw_v3_00176_containment_orbit_left_44_seed22176_0000`.

Note: validation sampling remains sequential and all three val probes were `collision + orbit_right_64`. Future Stage B / rollout evaluation should use balanced validation or one-per-template rollout selection.

## Checkpoint

Exactly one tiny adapter checkpoint was saved:

`local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`

Size: `166,809` bytes.

It contains only four LoRA tensors:

- `blocks.39.cam_scale_layer.lora_A`;
- `blocks.39.cam_scale_layer.lora_B`;
- `blocks.39.cam_shift_layer.lora_A`;
- `blocks.39.cam_shift_layer.lora_B`.

No full model checkpoint, optimizer state, base model weights, rollout output, or generated data was saved.

LoRA tensors changed: `4`.

Sampled frozen base tensors changed: `0`.

## Safety

- No DPO.
- No VideoGPA `03_train`.
- No Stage1.
- No rollout.
- No reward calibration.
- No new TDW generation.
- No full model checkpoint.
- No optimizer state.
- No GPU0 use.
- No `local_assets` committed.

## Next

Recommended next step: request approval for a tiny rollout smoke comparing base LingBot-Fast vs the Stage A balanced adapter on 4 samples, one per template.

Do not run Stage B, rollout, reward calibration, or DPO without explicit user approval.
