# v14 Real-Energy Calibration8 Summary

Decision: `REAL_ENERGY_CALIBRATION8_PASS`

- Rows: `8`
- OK rows: `8`
- GPU: `physical GPU5 via CUDA_VISIBLE_DEVICES=5`
- CSV: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration12_cuda_runtime_limit8/shard_00_of_01.csv`
- JSONL: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration12_cuda_runtime_limit8/shard_00_of_01.jsonl`
- Source manifest: `manifests/dpo_v14_subsets/asset_complete_prefix5_calibration12.jsonl`
- Delta_ref min / median / mean / max: `-0.0018915832` / `0.00748670846` / `0.0080279191` / `0.0188321397`
- Delta_ref positive / negative rows: `7` / `1`
- Energy seconds min / mean / max: `169.76` / `184.01` / `213.95`

This extends the previous bounded real-energy proof from 4 rows to 8 rows on an asset-complete v11 synthetic controlled subset. It still does not prove all500/S_pass/rollout real-energy coverage, and it does not change the DPO recipe decision.
