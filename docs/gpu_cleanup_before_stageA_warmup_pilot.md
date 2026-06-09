# GPU Cleanup Before Stage A Warmup Pilot

Date: 2026-06-09

Scope: TDW v5 200 Stage A LingBot-Fast warmup pilot. GPU0 was not used. GPU4-7 were allowed; GPU7 was selected first.

## Preflight

Remote host: `instance-afs92r3e`

Run worktree:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_visible_motion_v2_run_work`

The helper worktree was used because it contains the local TDW v5 data and the LingBot/Fast adapter runtime needed for this smoke.

## GPU Snapshot

At preflight, GPUs 4-7 were idle:

| GPU | PCI bus | Memory used | Total memory | Utilization |
|---|---:|---:|---:|---:|
| 4 | 00000000:AA:00.0 | 1 MiB | 97871 MiB | 0% |
| 5 | 00000000:BA:00.0 | 1 MiB | 97871 MiB | 0% |
| 6 | 00000000:CA:00.0 | 1 MiB | 97871 MiB | 0% |
| 7 | 00000000:DA:00.0 | 1 MiB | 97871 MiB | 0% |

GPUs 0-3 were occupied by unrelated work and were not touched.

## Cleanup Actions

No GPU4-7 cleanup was needed.

| PID | User | Command | GPU | Memory | Action | Reason |
|---:|---|---|---:|---:|---|---|
| none | n/a | n/a | 4-7 | n/a | no kill | GPUs 4-7 were already free |

## Safety

- Did not kill Xorg, ssh, systemd, docker, root-owned system processes, or unrelated services.
- Did not touch GPU0-3 jobs.
- Stage A pilot used GPU7 only.
