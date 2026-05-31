# Reward On Fast Rollout Debug V2 Report

Command run:

```bash
CUDA_VISIBLE_DEVICES=6,7 \
/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python \
  -m cam_physgeo.eval.eval_fast_rollouts \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --rollouts local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke \
  --out local_assets/reports/reward_calibration/fast_zero_shot_reward_debug_v2 \
  --limit 3 \
  --save_debug \
  --gpu_ids 6,7 \
  --debug_reward_breakdown \
  --confidence_weighted \
  --report_all_variants
```

Outputs:

- `local_assets/reports/reward_calibration/fast_zero_shot_reward_debug_v2/summary.md`
- `local_assets/reports/reward_calibration/fast_zero_shot_reward_debug_v2/scores.jsonl`
- `local_assets/reports/reward_calibration/fast_zero_shot_reward_debug_v2/per_metric_table.csv`

## Aggregate Scores

- Raw clean avg: `0.5949391852320083`
- Raw Fast avg: `0.8796054208438063`
- Raw clean > Fast win rate: `0.0`
- Confidence-weighted clean avg: `0.19335628899522198`
- Confidence-weighted Fast avg: `0.2175242075449916`
- Confidence-weighted clean > Fast win rate: `0.0`
- Real-backend-only clean avg: `0.0`
- Real-backend-only Fast avg: `0.0`
- Proxy-only clean avg: `0.7810828307925798`
- Proxy-only Fast avg: `0.8787116502807581`

## Why Fast Still Scores Higher

The reward is still proxy dominated:

- All clean and Fast components are marked fallback.
- `R_phys` motion proxy consistently favors Fast.
- Clean GT receives freeze penalties on two samples: `0.5` and `0.25`; Fast receives `0.0`.
- `R_quality` no longer dominates the confidence-weighted total because its confidence is capped and its confidence-weighted weight is limited, but quality remains a proxy term.

Per-sample key deltas:

- `07abddf5748b`: clean loses mostly because `R_phys` delta is `-0.3522` and clean freeze penalty is `0.5`.
- `13db379640ce`: clean has better geometry/identity but loses on `R_phys` by `-0.3373`.
- `1a0d32560b71`: clean loses on `R_phys` by `-0.1764` and has freeze penalty `0.25`.

## Conclusion

The v2 aggregation prevents fallback from being misrepresented as high-confidence. It does not make the reward DPO-ready. The correct interpretation is:

- Raw/proxy totals still rank Fast above clean.
- Real backend score is absent for both sides.
- Reward-on-rollout remains unreliable for DPO pair selection.

Next repair must wire real clean GT metadata into `R_bg`, `R_cam`, `R_fg`, `R_phys`, and `P_freeze`, and add real DINO/flow/video-feature backends for generated rollouts.
