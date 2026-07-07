# Latent Relation Monitor Backend Audit

Decision: `LATENT_MONITOR_BLOCKED`

Search meta: `{'visited_dirs': 5000, 'elapsed_seconds': 5.439, 'stop_reason': 'max_dirs', 'max_dirs': 5000, 'max_seconds': 20.0}`

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
- `/home/nvme03/workspace/world_model_phys/scripts/test_vjepa_load.py`

No V-JEPA / VideoREPA / TRD values are produced by this audit. If no backend is available, v14 must report `LATENT_MONITOR_BLOCKED`; fake latent scores are forbidden.

## v14 Requirement Audit Update

No TRD/VJEPA winner-vs-loser margin was produced. Local files/import candidates are not sufficient evidence for monitor validity. v14 therefore records `LATENT_MONITOR_BLOCKED`; no latent auxiliary loss is enabled.
