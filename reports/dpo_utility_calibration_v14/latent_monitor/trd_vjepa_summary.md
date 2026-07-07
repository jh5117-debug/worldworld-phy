# TRD / V-JEPA Latent Monitor Summary

Decision: `LATENT_MONITOR_PASS_VJEPA2_SMOKE`

This is a bounded V-JEPA2 token-relation monitor smoke, not an auxiliary-loss training integration.

Rows: 4; ok: 4
Positive V-JEPA margin rows: 4/4
Positive token-relation margin rows: 4/4
Device: `cuda:0` via `CUDA_VISIBLE_DEVICES=4`
Weight: `/home/nvme04/workspace/world_model_phys/PHYS/weight/vjepa2_1/vjepa2_1_vitb_dist_vitG_384.pt`

## Per-Pair Margins
- `v11_SYN_0017_02215_collision_strafe_left_180_seed41215_background_drift_visible`: vjepa_margin=0.000923, token_relation_margin=0.038835
- `v11_SYN_0035_02228_collision_orbit_right_64_seed41228_background_drift_visible`: vjepa_margin=0.001192, token_relation_margin=0.038212
- `v11_SYN_0041_02239_collision_strafe_left_180_seed41239_background_drift_visible`: vjepa_margin=0.001227, token_relation_margin=0.040755
- `v11_SYN_0047_02259_collision_strafe_left_180_seed41259_background_drift_visible`: vjepa_margin=0.000886, token_relation_margin=0.042215

## Interpretation

The local V-JEPA2.1 ViT-B EMA encoder distinguishes the controlled loser from the clean winner on all four asset-complete calibration pairs. This supports using a V-JEPA2/DINO latent visual monitor in v15 to catch artifact amplification before scaling DPO. It does not change the v14 DPO decision because the existing DPO checkpoint videos still degraded.
