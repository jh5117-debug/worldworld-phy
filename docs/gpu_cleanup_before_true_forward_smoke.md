# GPU Cleanup Before True Forward Smoke

Date: 2026-06-09

Scope: inspect GPU4-7 before LingBot-Fast component load and forward-loss smoke.

## Result

No GPU4-7 process was killed.

`nvidia-smi` before the smoke showed:

| GPU | Memory | Utilization | Action |
|---|---:|---:|---|
| 4 | 1 MiB / 97871 MiB | 0% | none |
| 5 | 1 MiB / 97871 MiB | 0% | none |
| 6 | 1 MiB / 97871 MiB | 0% | none |
| 7 | 1 MiB / 97871 MiB | 0% | used for this smoke |

GPU0-3 were occupied by an unrelated GR00T job and were not touched.

No Xorg, ssh, systemd, docker, root-owned system service, or unknown system process was killed.

## Process Cleanup Log

| PID | User | GPU | Memory | Command | Kill Reason |
|---|---|---:|---:|---|---|
| none | n/a | 4-7 | n/a | n/a | GPU4-7 were free |

Raw audit path on H20:

`local_assets/experiments/exp_tdw_v5_200_true_forward_loss_gate/logs/gpu_cleanup_audit.txt`
