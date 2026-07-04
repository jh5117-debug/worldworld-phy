Current Status: PASS

# VBench Real Smoke Summary

- Command: `vbench evaluate --dimension temporal_flickering --mode custom_input`
- Input videos: 3 symlinked repaired ready500 loser videos
- Offline/local mode: requested with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 --load_ckpt_from_local True`
- Python shim: temporary `python -> /usr/bin/python3` under `reports/dpo_pair_factory_v11/metrics_backend_repair/vbench_bin/`
- Result JSON: `reports/dpo_pair_factory_v11/metrics_backend_repair/vbench_real_smoke_out/results_2026-07-04-12:26:30_eval_results.json`
- CSV: `reports/dpo_pair_factory_v11/metrics_backend_repair/vbench_real_smoke.csv`
- Status: `PASS`

Notes:
- This verifies real VBench execution for `temporal_flickering`, not the full VBench suite.
- Runtime emitted a NCCL process-group warning but completed with exit code 0.
- Other dimensions may require local model weights/cache and should be audited dimension-by-dimension before reporting full VBench.
