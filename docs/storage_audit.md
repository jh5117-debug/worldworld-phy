# Storage Audit

First-stage audit only. No delete, unlink, clean, checkpoint removal, dataset removal, log removal, sudo, or process kill was executed.

## Filesystems

- `/home/nvme03`: 3.4T total, 2.5T used, 951G available, 73% used.
- `/home/nvme04`: 3.4T total, 3.2T used, 208G available, 95% used.

## Large Roots

- Project code root: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys`, 591G.
- Dataset root: `/home/nvme04/workspace/world_model_phys/PHYS/Dataset`, 878G.
- Weight root: `/home/nvme04/workspace/world_model_phys/PHYS/weight`, 383G, protected.
- PhyInOne family under `Phy_Dataset`, protected by default.
- moving-camera synthetic extension data output root: `/home/nvme03/workspace/physion_moving_camera_mainline_20260505/outputs`, 43G, protected.

## Project Hot Spots

- `checkpoints`: 590G, mostly deprecated action/mixed-objective checkpoints. High risk.
- `eval_outputs`: about 1.0G, old full validation and comparison outputs. Medium risk.
- `runs/wandb`: 101M, old run metadata. Medium risk.
- `logs`: 23M, old logs. Medium risk.
- Python caches and pytest caches: low risk.

Detailed candidates are in `cleanup/candidate_delete_manifest.tsv`. Protected paths are in `cleanup/protected_manifest.tsv`.
