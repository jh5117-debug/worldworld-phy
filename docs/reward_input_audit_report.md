# Reward Input Audit Report

Command run:

```bash
/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python \
  -m cam_physgeo.eval.audit_reward_inputs \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --rollouts local_assets/data/physion/processed/rollouts/fast_zero_shot_smoke \
  --out local_assets/reports/smoke/reward_input_audit \
  --limit 3
```

Outputs:

- `local_assets/reports/smoke/reward_input_audit/summary.json`
- `local_assets/reports/smoke/reward_input_audit/reward_input_audit.jsonl`
- `local_assets/reports/smoke/reward_input_audit/backend_table.csv`

## Findings

All three checked samples have clean GT metadata available, but the current reward scorer still marks every component as fallback:

- `physion_movingcam_07abddf5748b`: clean real metadata available; Fast generated depth/id missing.
- `physion_movingcam_13db379640ce`: clean real metadata available; Fast generated depth/id missing.
- `physion_movingcam_1a0d32560b71`: clean real metadata available; Fast generated depth/id missing.

Component backend confidence for clean GT:

- `bg`: fallback
- `cam`: fallback
- `fg`: fallback
- `phys`: fallback
- `reobs`: fallback
- `quality`: fallback
- `freeze`: fallback

Component backend confidence for Fast rollout:

- same as clean: all fallback

## Conclusion

The clean GT side has Physion metadata available, but the reward implementations are not yet consuming it as real backends in `eval_fast_rollouts`. This explains why clean GT can score lower than Fast: the scorer is comparing proxy frame-diff/motion/quality terms rather than simulator-grounded depth, ID mask, camera, and object-state terms.
