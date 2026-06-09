# GPU Cleanup Before Stage A Balanced Warmup

Date: 2026-06-09

Scope: TDW v5 200 balanced Stage A high-noise LingBot-Fast warmup pilot.

Allowed GPUs: 4, 5, 6, 7. GPU7 was selected. GPU0 was not used.

## Preflight Snapshot

At preflight, GPUs 4-7 were idle:

| GPU | PCI bus | Memory used | Total memory | Utilization |
|---:|---|---:|---:|---:|
| 4 | 00000000:AA:00.0 | 1 MiB | 97871 MiB | 0% |
| 5 | 00000000:BA:00.0 | 1 MiB | 97871 MiB | 0% |
| 6 | 00000000:CA:00.0 | 1 MiB | 97871 MiB | 0% |
| 7 | 00000000:DA:00.0 | 1 MiB | 97871 MiB | 0% |

Only Xorg was visible on GPU0. No GPU4-7 training/Python process needed cleanup.

## Cleanup Actions

| PID | User | Command | GPU | Memory | Action | Reason |
|---:|---|---|---:|---:|---|---|
| none | n/a | n/a | 4-7 | n/a | no kill | GPUs 4-7 were already free |

## Safety

- Did not kill Xorg, ssh, systemd, docker, root-owned system processes, or unrelated services.
- Did not use GPU0.
- Did not touch TDW/Unity generation.
