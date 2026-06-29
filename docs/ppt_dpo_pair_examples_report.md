# Selected DPO Pair Examples for PPT

Output folder: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/ppt_dpo_pair_examples_20260629_093540`

## Selection Summary

I reviewed the 16 Type B medium-hard rollout pairs and representative Type A local-corruption candidates using the existing reward, energy, and Codex visual-audit outputs. The final set contains 5 pairs: 4 Type B rollout-based medium-hard losers and 1 Type A controlled local corruption.

These are selected for presentation clarity, not just highest score. They cover hallucinated/extra objects, background/camera drift, object identity or deformation, weak physical event / partial freeze, and LocalDPO-style controlled corruption.

## Selected Pairs

### Pair 1: `protocol_v1_B_008_prefix5_anchored_95981b8f74bed0_background_drift_stageA_final`

- Type: `gt_vs_medium_hard_rollout`
- Failure: background drift + hallucinated fragments
- Reward margin: 0.336778
- Delta_ref: 0.117087
- Why selected: Main example: Type B containment case with strongest real energy margin; loser is plausible but has background/camera/extra-fragment issues.
- PPT caption: Winner preserves the containment scene, while loser remains plausible but introduces extra fragments and weaker camera/physical consistency.
- Contact sheet: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/ppt_dpo_pair_examples_20260629_093540/pair_01_protocol_v1_B_008_prefix5_anchored_95981b8f74bed0_background_drift_stageA_final/pair_contact_sheet_labeled.png`

### Pair 2: `protocol_v1_B_001_prefix5_anchored_1128e39109fc83_object_deformation_stageA_final`

- Type: `gt_vs_medium_hard_rollout`
- Failure: extra object / identity instability
- Reward margin: 0.305186
- Delta_ref: 0.100097
- Why selected: Type B collision case showing hallucinated/duplicated foreground and weakened physical event while remaining visually readable.
- PPT caption: Winner keeps the collision target clean; loser adds an extra foreground object and weakens the event progression.
- Contact sheet: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/ppt_dpo_pair_examples_20260629_093540/pair_02_protocol_v1_B_001_prefix5_anchored_1128e39109fc83_object_deformation_stageA_final/pair_contact_sheet_labeled.png`

### Pair 3: `protocol_v1_B_012_prefix5_anchored_dc458b2cf487d8_wrong_camera_motion_stageA_final`

- Type: `gt_vs_medium_hard_rollout`
- Failure: wrong camera following + weak event
- Reward margin: 0.336778
- Delta_ref: 0.034382
- Why selected: Type B containment case labeled wrong-camera motion; useful for explaining camera-following and physical relation failures.
- PPT caption: Winner follows the intended camera-conditioned scene; loser keeps visual quality but drifts in camera/physical consistency.
- Contact sheet: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/ppt_dpo_pair_examples_20260629_093540/pair_03_protocol_v1_B_012_prefix5_anchored_dc458b2cf487d8_wrong_camera_motion_stageA_final/pair_contact_sheet_labeled.png`

### Pair 4: `protocol_v1_A_030_02222_collision_orbit_right_64_seed41222_wrong_camera_motion_local`

- Type: `local_corruption`
- Failure: controlled local wrong-camera motion
- Reward margin: 0.260000
- Delta_ref: 0.028059
- Why selected: Type A controlled wrong-camera local corruption; useful for explaining affected-time/region preference construction.
- PPT caption: Clean GT future is preferred over a future-only wrong-camera local corruption, while the prefix remains untouched.
- Contact sheet: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/ppt_dpo_pair_examples_20260629_093540/pair_04_protocol_v1_A_030_02222_collision_orbit_right_64_seed41222_wrong_camera_motion_local/pair_contact_sheet_labeled.png`

### Pair 5: `protocol_v1_A_050_04204_containment_orbit_left_44_seed43204_background_drift_local`

- Type: `local_corruption`
- Failure: controlled local background drift
- Reward margin: 0.260000
- Delta_ref: 0.023901
- Why selected: Type A containment background-drift local corruption; useful as the clearest LocalDPO-style controlled negative.
- PPT caption: Clean GT future is preferred over a localized background drift corruption, illustrating LocalDPO-style controlled negatives.
- Contact sheet: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/ppt_dpo_pair_examples_20260629_093540/pair_05_protocol_v1_A_050_04204_containment_orbit_left_44_seed43204_background_drift_local/pair_contact_sheet_labeled.png`

## Best PPT Usage

- Main example: Pair 1 `protocol_v1_B_008_prefix5_anchored_95981b8f74bed0_background_drift_stageA_final`. It is Type B, has the strongest real-energy margin among selected examples, and clearly shows why medium-hard rollout losers are useful.
- LocalDPO / controlled corruption example: Pair 5 `protocol_v1_A_050_04204_containment_orbit_left_44_seed43204_background_drift_local`. It demonstrates a clean prefix with future-only local corruption.

## Safety

No training, DPO, StageB, GRPO, full-data StageA, checkpoint editing, or data deletion was performed. Videos and PNG/JPG assets are generated under reports for presentation use and should not be pushed as Git data.
