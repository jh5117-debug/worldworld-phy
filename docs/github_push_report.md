# GitHub Push Report

Date: 2026-06-22

Branch: research/stageA-v5-datafix-train-20260620

Pushed commit: 0d90086cdef6d6f8223c76b863a9cd1ca08cf3e0

Push status: success.

Remote:
- origin research/stageA-v5-datafix-train-20260620

Summary:
- Fixed StageA high-branch OOM by enabling LoRA token chunking, bf16 LoRA activations, and expandable CUDA allocator segments.
- Fixed low-branch gate handling by separating blocking reasons from advisory spike-ratio warnings.
- Added StageA OOM / low-gate report and updated PRD/runbook/status docs.
- No local_assets, HDF5, MP4, NPY, checkpoint, LoRA weight, or large log files are included in the pushed commit.

---

Date: 2026-06-22

Branch: research/lingbot-fast-stageA-high-only-20260622

Pushed commit: 5526677

Push status: success.

Remote:
- origin research/lingbot-fast-stageA-high-only-20260622

Summary:
- Stopped the invalid Base low/high StageA path and documented the cleanup.
- Added the LingBot-World-Fast high-only StageA configuration, launcher and guards.
- Fixed Fast loader routing so the policy loads from `lingbot_world_fast` and rejects Base low/high branches.
- Added fixed-validation CLI overrides and preserved `branch_mode=high_only` in final logs.
- Verified single-GPU, 2-GPU DDP and 7-GPU DDP high-only Fast preflights.
- Updated PRD, runbook, training report, data locations and status docs.
- No local_assets, HDF5, MP4, NPY, checkpoint, LoRA weight, or large log files are included in the pushed commit.

## 2026-06-23 Fast High-Only StageA Completion Push

Status: pushed.

- Branch: `research/lingbot-fast-stageA-high-only-20260622`
- Remote: `git@github-worldworld-phy-deploy:jh5117-debug/worldworld-phy.git`
- Commit: `a7f755a Document Fast high-only StageA completion`
- Files pushed:
  - `docs/stageA_v5_training_report.md`
  - `docs/stageA_v5_final_report.md`
  - `docs/fast_bf16_sigfpe_investigation.md`
- Excluded from Git:
  - `local_assets/`
  - training checkpoints and adapter weights
  - generated HDF5/MP4/NPY/NPZ data
  - large logs and experiment outputs

The push records the completed LingBot-World-Fast high-only StageA PASS result and the post-run true-model BF16 LoRA preflight PASS result. StageB, DPO, reward scoring, rollout, and pair mining were not run.
