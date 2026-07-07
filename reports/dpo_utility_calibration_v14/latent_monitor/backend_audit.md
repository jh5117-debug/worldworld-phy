# Latent Relation Monitor Backend Audit

Decision: `LATENT_MONITOR_BACKEND_FOUND_NEEDS_SCORING`

Search meta: `{'visited_dirs': 20000, 'elapsed_seconds': 19.203, 'stop_reason': 'max_dirs', 'max_dirs': 20000, 'max_seconds': 30.0}`

## Imports
- vjepa: False
- vijepa: False
- dinov2: False
- transformers: True
- torchvision: True
- clip: True
- open_clip: False
- pytorchvideo: True

## Candidate Local Files

- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/lib/python3.10/site-packages/transformers/models/dinov2/configuration_dinov2.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/lib/python3.10/site-packages/transformers/models/dinov2/modeling_dinov2.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/lib/python3.10/site-packages/transformers/models/dinov2/modeling_flax_dinov2.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/lib/python3.10/site-packages/transformers/models/dinov2_with_registers/configuration_dinov2_with_registers.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/lib/python3.10/site-packages/transformers/models/dinov2_with_registers/modeling_dinov2_with_registers.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/lib/python3.10/site-packages/transformers/models/dinov2_with_registers/modular_dinov2_with_registers.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/lib/python3.10/site-packages/transformers/models/videomae/configuration_videomae.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/lib/python3.10/site-packages/transformers/models/videomae/feature_extraction_videomae.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/lib/python3.10/site-packages/transformers/models/videomae/image_processing_videomae.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/lib/python3.10/site-packages/transformers/models/videomae/modeling_videomae.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world/lib/python3.10/site-packages/transformers/models/dinov2/configuration_dinov2.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world/lib/python3.10/site-packages/transformers/models/dinov2/modeling_dinov2.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world/lib/python3.10/site-packages/transformers/models/dinov2/modeling_flax_dinov2.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world/lib/python3.10/site-packages/transformers/models/dinov2_with_registers/configuration_dinov2_with_registers.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world/lib/python3.10/site-packages/transformers/models/dinov2_with_registers/modeling_dinov2_with_registers.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world/lib/python3.10/site-packages/transformers/models/dinov2_with_registers/modular_dinov2_with_registers.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world/lib/python3.10/site-packages/transformers/models/videomae/configuration_videomae.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world/lib/python3.10/site-packages/transformers/models/videomae/feature_extraction_videomae.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world/lib/python3.10/site-packages/transformers/models/videomae/image_processing_videomae.py`
- `/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world/lib/python3.10/site-packages/transformers/models/videomae/modeling_videomae.py`
- `/home/nvme03/workspace/lingbot-world/reference/PhysVideoGenerator/src/encoders/vjepa2_encoder.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/bin/pc-train-trd-v1`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/dinov2/configuration_dinov2.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/dinov2/modeling_dinov2.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/dinov2_with_registers/configuration_dinov2_with_registers.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/dinov2_with_registers/modeling_dinov2_with_registers.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/dinov2_with_registers/modular_dinov2_with_registers.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/videomae/configuration_videomae.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/videomae/image_processing_pil_videomae.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/videomae/image_processing_videomae.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/videomae/modeling_videomae.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/videomae/video_processing_videomae.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/vjepa2/configuration_vjepa2.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/vjepa2/modeling_vjepa2.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-main/lib/python3.10/site-packages/transformers/models/vjepa2/video_processing_vjepa2.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-videophy/bin/pc-train-trd-v1`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-videophy/lib/python3.10/site-packages/transformers/models/videomae/configuration_videomae.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-videophy/lib/python3.10/site-packages/transformers/models/videomae/convert_videomae_to_pytorch.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-videophy/lib/python3.10/site-packages/transformers/models/videomae/feature_extraction_videomae.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-videophy/lib/python3.10/site-packages/transformers/models/videomae/image_processing_videomae.py`
- `/home/nvme03/workspace/world_model_phys/.conda_envs/phys-videophy/lib/python3.10/site-packages/transformers/models/videomae/modeling_videomae.py`
- `/home/nvme03/workspace/world_model_phys/code/finetune_v3/lingbot-csgo-finetune/i3d_torchscript.pt`
- `/home/nvme03/workspace/world_model_phys/external/Depth-Anything-V2/depth_anything_v2/dinov2.py`
- `/home/nvme03/workspace/world_model_phys/external/Depth-Anything-V2/metric_depth/depth_anything_v2/dinov2.py`
- `/home/nvme03/workspace/world_model_phys/external/WMReward/vjepa2/assets/vjepa2-abstract-new.png`
- `/home/nvme03/workspace/world_model_phys/external/WMReward/vjepa2/assets/vjepa2-ac-abstract-new.png`
- `/home/nvme03/workspace/world_model_phys/external/WMReward/vjepa2/notebooks/vjepa2_demo.ipynb`
- `/home/nvme03/workspace/world_model_phys/external/WMReward/vjepa2/notebooks/vjepa2_demo.py`
- `/home/nvme03/workspace/world_model_phys/external/WMReward/vjepa2/tests/datasets/test_vjepa_transforms.py`
- `/home/nvme03/workspace/world_model_phys/logs/downloads/vjepa2_download.log`

## Candidate Local Weight Files

- `/home/nvme03/workspace/world_model_phys/code/finetune_v3/lingbot-csgo-finetune/i3d_torchscript.pt`
- `/home/nvme04/workspace/world_model_phys/PHYS/weight/vjepa2_1/vjepa2_1_vitb_dist_vitG_384.pt`
- `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/weights/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth`
- `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/weights/vjepa2/vjepa2_1_vitb_dist_vitG_384.pt`

No V-JEPA / VideoREPA / TRD values are produced by this audit. `LATENT_MONITOR_BACKEND_FOUND_NEEDS_SCORING` only means local code and weight candidates exist; scoring still must run before any latent-monitor PASS. Fake latent scores are forbidden.
