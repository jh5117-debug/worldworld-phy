# TDW v5 1000 combined_prompt_v2 Dataset Audit

## Counts

| split | count | templates | top camera variants |
| --- | ---: | --- | --- |
| all | 1000 | drop: 300, collision: 300, roll: 200, containment: 200 | orbit_left_72: 300, orbit_right_60: 200, orbit_left_44: 200, orbit_right_64: 150, strafe_left_180: 150 |
| train | 800 | collision: 240, containment: 160, drop: 240, roll: 160 | orbit_left_72: 240, orbit_left_44: 160, orbit_right_60: 160, orbit_right_64: 120, strafe_left_180: 120 |
| val | 100 | collision: 30, containment: 20, drop: 30, roll: 20 | orbit_left_72: 30, orbit_left_44: 20, orbit_right_60: 20, orbit_right_64: 15, strafe_left_180: 15 |
| test | 100 | collision: 30, containment: 20, drop: 30, roll: 20 | orbit_left_72: 30, orbit_left_44: 20, orbit_right_60: 20, orbit_right_64: 15, strafe_left_180: 15 |

## Prompt and action checks

- prompt_variant distribution: combined_v2: 1000
- generic prompt count: 0
- use_action=false count: 1000 / 1000
- Ready for Stage A: yes

## Example paths

- Manifest: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_lingbot_manifest_combined_prompt_v2.jsonl`
- Train split: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2/train.jsonl`
- Val split: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2/val.jsonl`
- Test split: `local_assets/data/physion/generated_v3/manifests/tdw_v5_1000_splits_combined_prompt_v2/test.jsonl`
