# Git Artifact Policy Audit

Decision: `GIT_ARTIFACT_POLICY_PASS_WITH_SIZE_WARNINGS`

- Treeish: `HEAD`
- Forbidden tracked artifacts: `0`
- Large tracked file warnings: `2`

This audit checks tracked Git artifacts only. It does not delete files, copy files, use GPUs, train, rollout, or run DPO.

## Large Tracked File Warnings
- `third_party/VideoREPA/finetune/openvid/openvid_3w2.csv` (19931321 bytes): tracked file exceeds 10485760 bytes
- `third_party/VideoREPA/finetune/openvid/openvid_6w4.csv` (39916145 bytes): tracked file exceeds 10485760 bytes
