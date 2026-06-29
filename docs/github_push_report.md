# GitHub Push Report

## Current Push Status (2026-06-30 05:14:29)

- Branch: research/quant-small-lora-dpo-probe-20260624
- Scope prepared for push: candidate generator v2 audit, TypeA-only Protocol v3 refresh, DPO smoke v3 training/video-smoke reports.
- DPO smoke v3 status: ENGINEERING_PASS_OBJECTIVE_SIGNAL_FAIL, not scalable.
- Large artifacts excluded from intended commit: local_assets, MP4/JPG/PNG, NPY/NPZ, PT/PTH/safetensors/checkpoints, and large logs.


## Current Push Status (2026-06-29 15:45:34)

- Branch: research/quant-small-lora-dpo-probe-20260624
- Latest pushed commit before this report update: efbea19 Build DPO preference protocol v3 with local masks
- Protocol v3 PRD commit: 93af736
- Metrics backend v2 commit: 8d5711a
- Final tests: compileall PASS; pytest related set 17 passed.
- Candidate generator v2 and DPO smoke v3 blocked by GPU capacity; not launched.
- Large artifacts excluded: MP4/JPG/PNG/HDF5/NPY/PT/PTH/checkpoints/local_assets.


## Current Pending Protocol v3 Work (2026-06-29 15:39:49)

- Metrics v2 commit: `8d5711a` pushed.
- LocalDPO mask v2 and Protocol v3 are being prepared for commit.
- Candidate generator and DPO smoke are blocked by GPU capacity, not launched.


## Current Push Status (2026-06-29 14:24:45)

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Latest pushed commit: `d52a9c5 Build DPO protocol v2 metrics and engineering runthrough`
- Previous PRD checkpoint commit: `980acaa Prepare DPO protocol v2 metrics and runthrough PRDs`
- Push status: success
- Large artifacts excluded: MP4/JPG/PNG/HDF5/NPY/PT/PTH/checkpoints/local_assets.



## Current DPO Protocol v2 Status (2026-06-29 14:18:28)

- Protocol v2 manifest: `manifests/dpo_preference_protocol_v2_pairs.jsonl`
- Valid v2 pairs: 34 total, 34 Type A, 0 Type B, 0 Type C.
- Type B rollout losers are currently blocked by blur/sharpness gates; do not use them for DPO.
- Metrics backend: PSNR/SSIM/LPIPS pass; FVD and VBench are BLOCKED_BY_ENV.
- DPO engineering run-through: PASS_ENGINEERING_ONLY on 8 Type A pairs for 10 steps with checkpoint video eval. Learning signal remains loser-dominant, so do not scale DPO.
- Explicitly not run: StageB, GRPO, full-data long StageA, large-scale DPO.


<!-- DPO_FAILURE_DIAG_PUSH_20260629_START -->
## DPO Failure Root-Cause Diagnosis Push Update (2026-06-29)

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Scope: DPO failure root-cause diagnostics after S0 objective ablation failed.
- Commit pushed: `824005a` (`Diagnose DPO winner-preserving signal failure`).
- Included: diagnostic code, tests, Markdown reports, and small CSV/JSON summaries under `reports/dpo_failure_diagnostics/`.
- Excluded: `local_assets/`, MP4/JPG/PNG videos/contact sheets, HDF5/H5, NPY/NPZ, PT/PTH/safetensors, checkpoints, model weights, and large logs.
- Push status: success to `origin/research/quant-small-lora-dpo-probe-20260624`.
- Safety: no large DPO, StageB, GRPO, full-data StageA, checkpoint deletion, or data/weight/video push was performed.

<!-- DPO_FAILURE_DIAG_PUSH_20260629_END -->


<!-- ENERGY_AUDIT_PUSH_20260628_START -->
## Full Real-Energy Audit Push Update (2026-06-28)

- Branch: `research/quant-small-lora-dpo-probe-20260624`
- Scope: full real LingBot-Fast energy audit for 66 V2V-5 DPO preference protocol v1 pairs.
- Submitted files are lightweight code, Markdown, CSV, and JSONL summaries only.
- Not submitted: MP4/JPG contact sheets, HDF5, NPY/NPZ, PT/PTH/safetensors, checkpoints, weights, large logs, and local_assets.
- Commit pushed: `1f61a2b` (`Audit real LingBot energy margins for V2V5 DPO preference pairs`).
- Push status: success to `origin/research/quant-small-lora-dpo-probe-20260624`.

<!-- ENERGY_AUDIT_PUSH_20260628_END -->


Updated: 2026-06-28T00:25:45

Branch: `research/quant-small-lora-dpo-probe-20260624`

## Latest Successful Push

Pushed to `origin/research/quant-small-lora-dpo-probe-20260624`.

Latest protocol commit pushed:

- `fb467c6` Implement V2V5 DPO preference pair protocol with medium-hard negatives

Previous result commits on this branch include:

- `ac66be9` Update V2V5 DPO push report
- `eeff57a` Document V2V5 StageA and DPO probe results

## Included In Latest Push

- `cam_physgeo/dpo/preference_protocol_v1.py`
- V2V-5 preference protocol tests
- `manifests/dpo_preference_protocol_v1_pairs.jsonl`
- lightweight CSV/JSON/Markdown summaries under `reports/dpo_preference_protocol_v1/`
- literature integration and protocol PRD docs

## Excluded From Git

- `local_assets/`
- MP4/JPG/PNG contact sheets and videos
- HDF5/H5
- NPY/NPZ
- PT/PTH/safetensors/checkpoints
- model weights and large logs

## Safety

No DPO training, StageB, GRPO, full-data long StageA, checkpoint deletion, or data/weight/video push was performed.

## 2026-06-28 DPO Objective Ablation

Pending commit/push after S0 report generation. No data, videos, checkpoints, or large logs staged.