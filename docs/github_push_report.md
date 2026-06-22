# GitHub Push Report

Date: 2026-06-22

Branch: research/stageA-v5-datafix-train-20260620

Latest local commit before push: 9da28cdb74326f0216ab4f31a8687b46e8c3a974

Summary:
- Fixed StageA high-branch OOM by enabling LoRA token chunking, bf16 LoRA activations, and expandable CUDA allocator segments.
- Fixed low-branch gate handling by separating blocking reasons from advisory spike-ratio warnings.
- Added StageA OOM / low-gate report and updated PRD/runbook/status docs.
- No local_assets, HDF5, MP4, NPY, checkpoint, LoRA weight, or large log files are included in this commit.

Push status: pending at report creation; updated by final assistant report after git push.
