Current Status: PASS

# DPO Pair Factory v10b PPT Slide Notes

Existing video: `reports/ppt_winlose_showcase_latest/dpo_pair_factory_v10_ready_showcase.mp4`

## What This Video Shows

The video shows five WIN/LOSE examples from the frozen v10 pair factory. It is meant to explain the preference-pair protocol and the reward/visual gate, not to claim that DPO training has succeeded.

## Segment Guide

1. `v6b_GT_C_008_01029_drop_orbit_left_72_seed40029`: real rollout-derived GT>C pair. WIN is clean GT future, LOSE is C camera+self-temporal rank4 rollout with foreground/extra-object failure.
2. `v10_TypeM_074_01060_drop_orbit_left_72_seed40060_local_patch_drift`: controlled synthetic visible TypeM-v10 negative with local patch drift.
3. `v10_TypeM_071_01038_drop_orbit_left_72_seed40038_foreground_identity_color_shift`: controlled synthetic visible TypeM-v10 negative with foreground identity/color shift.
4. `v10_TypeM_080_v6b_GT_C_001_01014_drop_orbit_left_72_seed40014_local_temporal_jump`: controlled synthetic visible TypeM-v10 negative with temporal jump.
5. `v10_TypeM_053_04351_containment_orbit_left_44_seed43351_local_patch_freeze`: controlled synthetic visible TypeM-v10 negative with local freeze.

## How To Explain It

- We now have 81 strict-ready DPO pairs.
- 15 are real rollout-derived GT>C pairs.
- 63 are controlled synthetic TypeM-v10 visible negatives.
- The synthetic pairs are intentionally controlled and visually readable; they are useful for anchored/LocalDPO-style objectives.
- They are not real model rollout losers, so the honest caveat is that real rollout expansion still needs WanI2VFast initialization fixed.

## Likely Questions

Q: Are all 81 model-generated losers?
A: No. 15 are real rollout-derived GT>C; 63 are controlled synthetic TypeM-v10; 3 are TypeA_plus controlled pairs.

Q: Can we train DPO now?
A: The pair-data gate for a tiny anchored DPO is ready, but large-scale DPO should wait until winner-side objective validation and more real rollout pairs.

Q: Why use synthetic pairs?
A: They give clear, medium-hard, localized physical/geometric failures while the real rollout generator still has an initialization bottleneck.
