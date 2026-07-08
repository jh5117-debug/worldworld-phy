# v14 Real-Energy Calibration12 Summary

Decision: `REAL_ENERGY_CALIBRATION12_PASS`

- Rows: `12`
- OK rows: `12`
- GPU: `physical GPU5 via CUDA_VISIBLE_DEVICES=5`
- CSV: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration12_cuda_runtime_limit8/shard_00_of_01.csv`
- JSONL: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work/reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration12_cuda_runtime_limit8/shard_00_of_01.jsonl`
- Source manifest: `manifests/dpo_v14_subsets/asset_complete_prefix5_calibration12.jsonl`
- Delta_ref min / median / mean / max: `-0.0018915832` / `0.00718332082` / `0.00877968874` / `0.0206041709`
- Delta_ref positive / negative rows: `11` / `1`
- Energy seconds min / mean / max: `169.76` / `186.19` / `241.61`

This extends the bounded real-energy proof from 8 to 12 rows on an asset-complete v11 synthetic controlled subset. It still does not prove all500/S_pass/rollout real-energy coverage, and it does not change the DPO recipe decision.
