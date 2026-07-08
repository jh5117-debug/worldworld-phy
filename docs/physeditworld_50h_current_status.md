# PhysEditWorld 50h Current Status

Updated: 2026-07-08T17:29:56 CST

## Runtime State

- Host repo: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys`.
- Branch: `physion-only-local-assets-videogpa-smoke`.
- Commit: `681b34f (HEAD -> physion-only-local-assets-videogpa-smoke, physion-only-cam-physgeo-dpo, main, cam-physgeo-dpo-refactor) Quiet TRD diagnostics and default empty paths`.
- H20 is expected to be reclaimed, so the first priority is migration preparation to PAI/NAS.
- Target NAS path: `/mnt/workspace/hj/nas_hj`.
- GPU policy for this line: physical GPU4, GPU5, GPU6, GPU7 only.
- Forbidden GPUs: physical GPU0, GPU1, GPU2, GPU3.
- Current observation: GPU4-7 are occupied by existing FastWAM/libero evaluation processes, so this update does not start training, rollout, or metrics jobs.

## Refocus

The project line is refocused away from old CSGO, old PhyInOne mixing, and direct large DPO. The current research line is PhysEditWorld-style LingBot-Fast physics-editable world model training.

PhysEditWorld must be treated as action + camera + gravity matched replay data, not as passive camera-only physics data. The first training stage uses PhysEditWorld 50h only. Our older passive physics data should be reserved for a later ablation after the PhysEditWorld-only baseline is understood.

## Gravity Conditioning

- First version: prompt-only gravity conditioning, matching the PhysEditWorld paper-style baseline.
- Prompt should include explicit text such as `The scene is rendered under gravity: 0.25g.`
- No gravity MLP is introduced in this version.
- No gravity embedding is introduced in this version.
- LingBot-Fast architecture is not changed for gravity in this version.

## Condition And Target

Condition:

- image or prefix video;
- prompt with gravity token;
- action trace;
- camera trajectory;
- intrinsics.

Target:

- future video under the same replay condition and gravity.

## This Round

This round is migration + data schema + baseline + gated warm-up preparation. It is not large DPO.

Allowed next phases:

1. H20 to PAI/NAS migration manifest and environment export.
2. PhysEditWorld 50h data audit and replay-group-safe splits.
3. LingBot-Fast input conversion with prompt-only gravity.
4. Original LingBot-Fast / base baseline rollout if GPU4-7 are free.
5. Rank32 support warm-up only after preflight and gates.
6. Anchored DPO pair construction only after warm-up video and metric gates.
7. Tiny anchored DPO probe only after pair gate.

## Explicit Non-Goals

- No large DPO.
- No train400.
- No StageB.
- No GRPO.
- No broad-LoRA.
- No full-data long StageA.
- No checkpoint, data, or weight deletion.
- No `local_assets`, videos, checkpoints, weights, or large logs pushed to Git.
- No GPU0-3 usage by this line.

## Source Context Files

Existing context files read/available:

- `README_cam_physgeo_dpo.md`
- `docs/project_refocus.md`
- `docs/experiment_plan.md`
- `docs/implementation_status.md`
- `docs/framework_completeness_audit.md`
- `docs/metrics.md`
- `docs/research_notes.md`
- `docs/data_locations.md`
- `docs/github_push_report.md`

Missing context files noted but not blocking:

- `docs/dpo_failure_root_cause_report.md`
- `docs/dpo_utility_calibration_v14_report.md`
- `docs/vjepa_videorepa_winner_anchor_plan.md`
- `docs/fulldata_lingbotfast_warmup_loser_eval_status.md`

## Initial Git Status Excerpt

```text
M .gitignore
 M configs/train_stage2_phycsgo_act.yaml
 D data/audit/csgo_human_eval_template.csv
 D data/audit/csgo_physics_taxonomy_v1.md
 D logs/.gitkeep
?? README_cam_physgeo_dpo.md
?? cam_physgeo/
?? configs/cam_physgeo/
?? configs/generated/
?? configs/train_stage1_physinone_cam.yaml.localbackup.20260428_063010
?? configs/train_stage2_phycsgo_act.runtime_act4.yaml
?? configs/train_stage2_phycsgo_act.yaml.bak_20260510_113145
?? docs/
?? eval_assets/
?? h20_probe_all_in_one.txt
?? h20_train_accel_probe_20260416_115015.txt
?? links/base_model
?? links/lingbot_code
?? links/stage1_epoch2
?? links/stage1_final
?? links/teacher_ckpt
?? links/videophy2_checkpoint
?? scripts/00_plan_local_assets.sh
?? scripts/00_readonly_audit.sh
?? scripts/01_build_data_manifest.sh
?? scripts/01_migrate_assets_to_project.sh
?? scripts/01_physion_download_or_check.sh
?? scripts/02_physion_hdf5_audit.sh
?? scripts/02_validate_data.sh
?? scripts/03_build_physion_manifest.sh
?? scripts/03_convert_cam_inputs.sh
?? scripts/04_convert_physion_cam_inputs.sh
?? scripts/04_reward_calibration.sh
?? scripts/05_reward_calibration.sh
?? scripts/05_stage1_warmup.sh
?? scripts/06_generate_rollouts.sh
?? scripts/06_stage1_physion_warmup.sh
?? scripts/07_build_dpo_pairs.sh
?? scripts/08_build_dpo_pairs.sh
?? scripts/08_export_videogpa_pairs.sh
?? scripts/08_stage2_anchored_dpo.sh
?? scripts/09_stage2_anchored_dpo.sh
?? scripts/09_stage3_self_dpo.sh
?? scripts/10_eval_all.sh
?? scripts/10_stage3_self_dpo.sh
?? scripts/11_eval_all.sh
?? scripts/12_generate_physion_movingcam_subset.sh
?? scripts/download_flux2_dev_devturbo_hf.sh
?? scripts/generate_videophy2_first_frames_flux2.py
?? scripts/safe_delete_from_manifest.sh
?? smoke_after_release_fix.txt
?? src/physical_consistency/stages/stage1_physinone_cam/trainer.py.bak_ddp_bundle_20260515_154317
?? tests/test_cam_physgeo_smoke.py
?? tests/test_physion_smoke.py
?? third_party/vjepa2_official/
```
