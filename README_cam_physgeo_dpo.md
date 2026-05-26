# Cam-PhysGeo-DPO

Camera-Conditioned Physical-Geometric Preference Alignment for LingBot-Fast / LingBot-Base.

Build a dry-run manifest:

```bash
python -m cam_physgeo.data.build_manifest   --phyinone_root /home/nvme04/workspace/world_model_phys/PHYS/Dataset/Phy_Dataset/PhysInOne_cam   --movingcam_root /home/nvme03/workspace/physion_moving_camera_mainline_20260505/synthetic_data_assets   --out manifests/cam_physgeo_all.jsonl   --dry-run --limit 50
```

Convert cam-only inputs:

```bash
python -m cam_physgeo.data.convert_to_lingbot_cam_inputs   --manifest manifests/cam_physgeo_train.jsonl   --out data/cam_physgeo_lingbot_inputs/train   --num_frames 81 --fps 16 --size 480x832   --use_action false --make_dummy_action true --dry-run
```

Run reward calibration skeleton:

```bash
bash scripts/04_reward_calibration.sh --dry-run --limit 20
```

No deletion, long training, model download, or checkpoint mutation is part of this first stage.
