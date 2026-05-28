# Current State Before LingBot-Fast / VideoGPA Adapter

1. Current branch: `physion-videogpa-lingbotfast-minimal-adapter` in the clean auxiliary worktree; the original project root remains dirty and was not overwritten.
2. Git cleanliness: auxiliary worktree has only this turn's intended code/docs changes; original project root still contains pre-existing untracked/modified files.
3. Active root: `local_assets` remains the runtime root through `configs/cam_physgeo/paths.yaml`.
4. `local_assets/data/physion`: exists through the project-root symlink in this worktree.
5. `local_assets/weights/lingbot_fast`: exists, about 69.1 GiB, 16 safetensors shards.
6. `local_assets/third_party/VideoGPA/official_repo`: exists, commit `551e63a5c2c493962f1e1d090bfa8324bf18b694`.
7. VideoGPA pair export: exists at `local_assets/data/physion/processed/dpo_pairs/smoke/videogpa_pairs.json`, 51 groups.
8. Reward calibration smoke-20: exists from the previous pass; this turn expanded to 50 samples.
9. LingBot-Fast loader dry-run: path/config/shard/runtime-bundle checks pass. The Fast root itself lacks VAE/T5/tokenizer, so a symlink runtime bundle is prepared under `local_assets/cache/lingbot_fast_cam_runtime` using Base VAE/T5/tokenizer plus Fast shards.
10. Actual Fast inference result: attempted, but did not complete within the 180 second smoke timeout; no generated video exists.
11. Formal training: no formal Stage1, DPO, or long inference/training was launched.
12. Active `/home/nvme03` path: only the LingBot conda environment path is configured as `LINGBOT_ENV`; active data/weights/third-party outputs remain under `local_assets`.
13. GPU 6/7: were idle before and after the timed Fast smoke; no lingering LingBot smoke process remained.

