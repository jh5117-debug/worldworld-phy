# Migration Approval Review Packet

Decision: `MIGRATION_APPROVAL_REVIEW_PACKET_READY`

## Purpose

This packet ranks the no-default-approval copy-plan rows so a reviewer can decide which assets should become approved later. It does not approve, copy, delete, or recursively size any payload.

## Counts

- Rows: `800`
- High-priority rows: `11`
- Top rows shown in JSON: `50`

### By Priority

- `blocked`: 246
- `high`: 11
- `low`: 249
- `medium`: 294

### By Action

- `DO_NOT_APPROVE`: 244
- `DO_NOT_APPROVE_UNTIL_SOURCE_EXISTS`: 2
- `KEEP_UNAPPROVED_UNLESS_NEEDED`: 249
- `REVIEW_FOR_APPROVAL`: 11
- `REVIEW_IF_NEEDED`: 294

## Reviewer Rule

Only after NAS/root are visible should a reviewer edit `reports/migration/approved_copy_manifest_template.tsv` and set `approved=true` for a minimal restore payload. Do not approve old outputs, contact sheets, broad `local_assets/`, failed checkpoints, or logs.

## Top Review Sources

- `high` score=72 `weights` `/home/nvme03/workspace/world_model_phys/checkpoints/CogVideoX-5B-I2V/tokenizer/tokenizer_config.json`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; model payload marker `/checkpoints/`; weight keywords: tokenizer,checkpoint,model; file can be byte-counted/hash-reviewed; sha256 available; category=weight_or_model_candidate
- `high` score=67 `weights` `/home/nvme03/workspace/world_model_phys/checkpoints/CogVideoX-5B-I2V/vae/diffusion_pytorch_model.safetensors`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; model payload marker `/checkpoints/`; weight keywords: vae,checkpoint,model; file can be byte-counted/hash-reviewed; category=weight_or_model_candidate
- `high` score=67 `weights` `/home/nvme03/workspace/world_model_phys/checkpoints/MAGI-1/ckpt/vae/diffusion_pytorch_model.safetensors`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; model payload marker `/checkpoints/`; weight keywords: vae,checkpoint,model; file can be byte-counted/hash-reviewed; category=weight_or_model_candidate
- `high` score=64 `weights` `/home/nvme03/workspace/world_model_phys/checkpoints/CogVideoX-5B-I2V/tokenizer`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; model payload marker `/checkpoints/`; weight keywords: tokenizer,checkpoint,model; directory requires recursive human review before approval; hash pending because directory/large asset; category=weight_or_model_candidate
- `high` score=64 `weights` `/home/nvme03/workspace/world_model_phys/checkpoints/CogVideoX-5B-I2V/vae`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; model payload marker `/checkpoints/`; weight keywords: vae,checkpoint,model; directory requires recursive human review before approval; hash pending because directory/large asset; category=weight_or_model_candidate
- `high` score=64 `weights` `/home/nvme03/workspace/world_model_phys/checkpoints/MAGI-1/ckpt/t5`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; model payload marker `/checkpoints/`; weight keywords: t5,checkpoint,model; directory requires recursive human review before approval; hash pending because directory/large asset; category=weight_or_model_candidate
- `high` score=64 `weights` `/home/nvme03/workspace/world_model_phys/checkpoints/MAGI-1/ckpt/t5/t5-v1_1-xxl`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; model payload marker `/checkpoints/`; weight keywords: t5,checkpoint,model; directory requires recursive human review before approval; hash pending because directory/large asset; category=weight_or_model_candidate
- `high` score=64 `weights` `/home/nvme03/workspace/world_model_phys/checkpoints/MAGI-1/ckpt/vae`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; model payload marker `/checkpoints/`; weight keywords: vae,checkpoint,model; directory requires recursive human review before approval; hash pending because directory/large asset; category=weight_or_model_candidate
- `high` score=64 `weights` `/home/nvme04/workspace/world_model_phys/PHYS/weight/Lingbot-base-cam`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; model payload marker `/weight/`; weight keywords: lingbot,model,weight; directory requires recursive human review before approval; hash pending because directory/large asset; category=weight_or_model_candidate
- `high` score=60 `weights` `/home/nvme04/workspace/world_model_phys/PHYS/weight/videophy_2_auto`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; model payload marker `/weight/`; weight keywords: model,weight; directory requires recursive human review before approval; hash pending because directory/large asset; category=weight_or_model_candidate
- `high` score=36 `weights` `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/third_party/VideoREPA/ckpt/VideoMAEv2`
  - action: `REVIEW_FOR_APPROVAL`; reason: weight/model candidate; weight keywords: model; directory requires recursive human review before approval; hash pending because directory/large asset; category=weight_or_model_candidate
- `medium` score=30 `data` `/home/nvme03/ubuntu_home_redirect/.vscode-server/extensions/ms-python.vscode-pylance-2026.2.1/typings/vscode.proposed.codeActionAI.d.ts`
  - action: `REVIEW_IF_NEEDED`; reason: data candidate; PhysEditWorld schema keywords: action,pose; file can be byte-counted/hash-reviewed; sha256 available; category=physeditworld_or_gravity_candidate
- `medium` score=30 `data` `/home/nvme03/workspace/lingbot-world/physinone_sft_conditions_81f_pull50_20260513/MovingHitsFixed_WindGravityBalance__bg156__vbGA3S/action.npy`
  - action: `REVIEW_IF_NEEDED`; reason: data candidate; PhysEditWorld schema keywords: gravity,action; file can be byte-counted/hash-reviewed; sha256 available; category=physeditworld_or_gravity_candidate
- `medium` score=30 `data` `/home/nvme03/workspace/lingbot-world/physion_lingbot_inputs_camera_support_probe_20260515/collision_00012_collision_lookaway_up_reobserve_seed19000/action.npy`
  - action: `REVIEW_IF_NEEDED`; reason: data candidate; PhysEditWorld schema keywords: action,camera; file can be byte-counted/hash-reviewed; sha256 available; category=physeditworld_or_gravity_candidate
- `medium` score=30 `data` `/home/nvme03/workspace/lingbot-world/physion_lingbot_inputs_camera_support_probe_20260515/collision_00014_collision_offscreen_z_reobserve_seed19000/action.npy`
  - action: `REVIEW_IF_NEEDED`; reason: data candidate; PhysEditWorld schema keywords: action,camera; file can be byte-counted/hash-reviewed; sha256 available; category=physeditworld_or_gravity_candidate
- `medium` score=30 `data` `/home/nvme03/workspace/lingbot-world/physion_lingbot_inputs_camera_support_probe_20260515/drop_00003_drop_lookaway_up_reobserve_seed19001/action.npy`
  - action: `REVIEW_IF_NEEDED`; reason: data candidate; PhysEditWorld schema keywords: action,camera; file can be byte-counted/hash-reviewed; sha256 available; category=physeditworld_or_gravity_candidate
- `medium` score=30 `data` `/home/nvme03/workspace/lingbot-world/physion_lingbot_inputs_camera_support_probe_20260515/drop_00004_drop_offscreen_z_reobserve_seed19001/action.npy`
  - action: `REVIEW_IF_NEEDED`; reason: data candidate; PhysEditWorld schema keywords: action,camera; file can be byte-counted/hash-reviewed; sha256 available; category=physeditworld_or_gravity_candidate
- `medium` score=30 `data` `/home/nvme03/workspace/lingbot-world/physion_lingbot_inputs_native832_object_anchor_prompt_20260512/native832_drop_pose1_object_anchor_prompt/action.npy`
  - action: `REVIEW_IF_NEEDED`; reason: data candidate; PhysEditWorld schema keywords: action,pose; file can be byte-counted/hash-reviewed; sha256 available; category=physeditworld_or_gravity_candidate
- `medium` score=30 `data` `/home/nvme03/workspace/lingbot-world/physion_lingbot_inputs_native832_physics_k4_20260512/native832_drop_pose1_physics_prompt/action.npy`
  - action: `REVIEW_IF_NEEDED`; reason: data candidate; PhysEditWorld schema keywords: action,pose; file can be byte-counted/hash-reviewed; sha256 available; category=physeditworld_or_gravity_candidate
- `medium` score=30 `data` `/home/nvme03/workspace/lingbot-world/physion_lingbot_inputs_native832_scene_prompt_20260512/native832_drop_pose1_scene_prompt/action.npy`
  - action: `REVIEW_IF_NEEDED`; reason: data candidate; PhysEditWorld schema keywords: action,pose; file can be byte-counted/hash-reviewed; sha256 available; category=physeditworld_or_gravity_candidate

## Safety

- Copied files: `False`
- Deleted files: `False`
- Approved rows modified: `False`
- Default approved: `False`
