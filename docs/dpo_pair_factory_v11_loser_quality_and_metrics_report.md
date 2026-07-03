Current Status: MIXED

# DPO Pair Factory v11 Ready500 Loser Quality and Metrics Backend Report

Updated: 2026-07-04 04:10:15

## 1. One-by-One LOSE Quality Audit

All 500 rows from `manifests/dpo_pair_factory_v11_ready_500.jsonl` were re-audited against their contact sheet, existing Codex visual audit fields, score CSV, reward margin, loser video existence/readability, and quality gates.

Outputs:

- `reports/dpo_pair_factory_v11/loser_quality/ready500_loser_quality_audit.csv`
- `reports/dpo_pair_factory_v11/loser_quality/ready500_loser_quality_audit.jsonl`
- `reports/dpo_pair_factory_v11/loser_quality/ready500_loser_quality_summary.md`
- `reports/dpo_pair_factory_v11/loser_quality/ready500_loser_quality_rejected.jsonl`
- `manifests/dpo_pair_factory_v11_ready500_trainable_after_loser_audit.jsonl`

Result:

- Audited: 500
- Trainable after loser audit: 497
- Reject / review: 3
- Main reject reason: `too_subtle_metric`

Rejected pair IDs:

- `protocol_v4_TypeAplus_022_s4_strong_pass_object_identity_change_local`
- `protocol_v4_TypeAplus_024_s4_strong_pass_partial_freeze`
- `protocol_v4_TypeAplus_028_s4_strong_pass_partial_freeze`

Interpretation: the v11 ready500 dataset is mostly usable, but the exact training-safe set is 497 unless the three subtle TypeA_plus pairs are replaced or manually accepted after human review. The original 500 should not be treated as automatically training-clean.

## 2. Metrics Backend Repair

Installed user-level packages without sudo:

- `lpips`
- `torchmetrics`
- `pytorch-fid`
- `piq`
- `vbench`
- `pytorchvideo`

Backend status:

- LPIPS: `AVAILABLE`; import passed and real `LPIPS(net=alex)` smoke passed.
- Image FID: import passed via `pytorch-fid`, but this is diagnostic only and not FVD.
- FVD: `BLOCKED_BY_ENV_TEMPORAL_BACKBONE`; no real Frechet Video Distance backend with local temporal feature weights is available.
- VBench: `PACKAGE_CLI_AVAILABLE_CONFIG_BLOCKED`; package and CLI work, but project-local dimensions, input convention, and checkpoint/cache policy are not configured for actual scoring.

Artifacts:

- `reports/dpo_pair_factory_v11/metrics_backend_repair/backend_probe_initial.txt`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/pip_install_lpips_fvd_vbench.log`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/pip_install_pytorchvideo.log`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/backend_probe_after_install.txt`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/lpips_real_smoke.txt`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/vbench_evaluate_help.txt`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/metrics_backend_status.csv`
- `reports/dpo_pair_factory_v11/metrics_backend_repair/metrics_backend_status.md`

## 3. Decision

- Use `manifests/dpo_pair_factory_v11_ready500_trainable_after_loser_audit.jsonl` for training candidate data, not the original ready500 manifest.
- LPIPS can now be recomputed in the next metrics pass.
- Do not report FVD until a real video FVD temporal backbone and local weights are configured.
- Do not report VBench until explicit VBench dimensions, video folder convention, and checkpoint/cache policy are configured.

## 4. Verification

- `python3 -m compileall cam_physgeo src tests`: PASS
- `python3 -m pytest ...`: NOT_RUN / unavailable because current Python still reports `No module named pytest`.
- Direct backend smoke: LPIPS PASS, VBench import/CLI PASS, FVD structured BLOCKED status PASS.
