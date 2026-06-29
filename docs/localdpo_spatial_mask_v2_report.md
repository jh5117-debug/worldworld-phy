# LocalDPO Spatial Mask v2 Report

Current Status: PASS
Updated: 2026-06-29 15:38:49

## Result

- Input: `reports/dpo_preference_protocol_v2/localdpo_ready_pairs_v2.jsonl`
- Total Type A pairs audited: 34
- Usable spatial+time masks: 34
- Time-only fallback: 0
- Invalid masks: 0
- Mean local mask ratio: 0.199618
- Min local mask ratio: 0.079791
- Max local mask ratio: 0.365385

The mask builder maps affected raw frame spans to latent temporal slots with stride 4 and excludes prefix frames. Spatial masks come from affected mask files or affected region boxes and are resized to the latent spatial grid.

Outputs:

- `reports/localdpo_mask_v2/mask_audit.csv`
- `reports/localdpo_mask_v2/mask_summary.md`
- `reports/localdpo_mask_v2/localdpo_ready_pairs_spatial_v2.jsonl`
