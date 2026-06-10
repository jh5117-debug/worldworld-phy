# Current State Before 4-Condition Reward Scoring

Date: 2026-06-10

Input rollout root:

`local_assets/experiments/exp_tdw_v5_scaleup_warmup_reward_pairs/rollout/4condition_base_vs_stageA_adapter/`

Human review pack:

`local_assets/reports/human_review/tdw_v5_stageA_4condition_base_vs_adapter/video_gallery.html`

Input status:

- GT videos: 4/4.
- Base rollout videos: 4/4.
- Stage A adapter rollout videos: 4/4.
- Video probe: 12/12.
- Adapter checkpoint loaded: yes.
- `use_action=false`: preserved.

Conditions:

| Template | Condition | Camera |
|---|---|---|
| drop | `tdw_v3_00000_drop_orbit_left_72_seed22000_0000` | `orbit_left_72` |
| collision | `tdw_v3_00093_collision_strafe_left_180_seed22093_0000` | `strafe_left_180` |
| roll | `tdw_v3_00145_roll_orbit_right_60_seed22145_0000` | `orbit_right_60` |
| containment | `tdw_v3_00161_containment_orbit_left_44_seed22161_0000` | `orbit_left_44` |

Reward can run on the existing videos. This round does not approve DPO, training, VideoGPA `03_train`, Stage1, new TDW generation, new LingBot rollout, reward calibration, or reward-weight changes.
