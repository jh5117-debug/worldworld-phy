# Camera Embedding Probe Report

Command run on H20 helper worktree:

```bash
TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 \
/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python \
  -m cam_physgeo.eval.probe_camera_embedding \
  --samples local_assets/data/physion/processed/lingbot_cam_inputs/smoke \
  --out local_assets/reports/smoke/camera_embedding_probe \
  --limit 1 \
  --variants correct frozen reversed exaggerated_yaw zero_motion \
  --local-files-only \
  --save_summary \
  --save_npz false \
  --device cpu
```

No video generation was run for this probe.

## Sample

- Sample: `physion_movingcam_07abddf5748b`
- Poses shape: `(81, 4, 4)`
- Raw intrinsics shape: `(81, 4, 4)`
- Converted intrinsics shape: `(81, 4)`
- Dummy action shape: `(81, 4)`
- Dummy action norm: `0.0`
- LingBot code root: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/third_party/lingbot_world`

Probe grid was intentionally small to avoid full generation:

- raw Plucker grid: `(2, 64, 112, 3)`
- rearranged Plucker tensor: `(1, 192, 2, 8, 14)`
- action tensor: `(1, 256, 2, 8, 14)`, all zeros
- final control tensor: `(1, 448, 2, 8, 14)`

## Pairwise Distances

Output files:

- `local_assets/reports/smoke/camera_embedding_probe/summary.json`
- `local_assets/reports/smoke/camera_embedding_probe/pairwise_distances.csv`

Key distances:

- correct vs frozen: L2 `12.8458`, cosine `0.994244`
- correct vs reversed: L2 `25.6122`, cosine `0.977121`
- correct vs exaggerated_yaw: L2 `83.0763`, cosine `0.759289`
- correct vs zero_motion: L2 `12.8458`, cosine `0.994244`
- frozen vs zero_motion: L2 `0.0`, cosine approximately `1.0`

## Conclusion

Camera variants do change the actual LingBot Plucker/control tensor. Therefore the bug is not that poses/intrinsics are ignored before the embedding function. Gate C is still not fully passed because video-level output differences were not proven above stochastic baseline, but camera condition is confirmed to enter the model-side control tensor.
