# TDW GPU6/7 Display Audit v2

Date: 2026-06-05

## Worktree

Remote execution worktree:

`/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_gpu67_visible_motion_work`

Base branch:

`physion-tdw-visible-motion-profile`

## GPU Status

`nvidia-smi --query-gpu=index,pci.bus_id,memory.used,memory.total,utilization.gpu --format=csv`

| GPU | PCI bus id | Memory used | Utilization |
|---:|---|---:|---:|
| 0 | `00000000:52:00.0` | 5687 MiB | 0% |
| 1 | `00000000:58:00.0` | 4974 MiB | 1% |
| 2 | `00000000:60:00.0` | 5544 MiB | 1% |
| 3 | `00000000:66:00.0` | 2432 MiB | 0% |
| 4 | `00000000:AA:00.0` | 4928 MiB | 0% |
| 5 | `00000000:BA:00.0` | 4380 MiB | 1% |
| 6 | `00000000:CA:00.0` | 1 MiB | 0% |
| 7 | `00000000:DA:00.0` | 1 MiB | 0% |

GPU6 and GPU7 are idle, but that is not enough for TDW / Unity. TDW needs an Xorg display bound to the chosen GPU.

## Display Audit

Observed X sockets:

```text
X8
X9
X10
X11
X12
X13
```

Observed Xorg process:

```text
/usr/lib/xorg/Xorg :8 -config /etc/X11/tdw-xorg-gpu0.conf -noreset +extension GLX +extension RANDR +extension RENDER -logfile /tmp/xorg-gpu-8.log
```

`DISPLAY=:8` remains bound to GPU0.

No GPU6/GPU7 Xorg config was found:

```bash
ls -l /etc/X11/*gpu6* /etc/X11/*gpu7*
```

Result:

No matching files.

## Sudo Check

Command:

```bash
sudo -n true && echo sudo_available || echo sudo_not_available
```

Result:

```text
sudo: a password is required
sudo_not_available
```

## Decision

No actual TDW generation was run.

Reasons:

- GPU0 is explicitly forbidden for this turn.
- `DISPLAY=:8` is GPU0-bound.
- No GPU6/7 TDW display exists.
- Creating `/etc/X11/tdw-xorg-gpu6.conf` and starting `Xorg :16` require sudo/admin access.
- Passwordless sudo is not available.

## GPU0 Avoidance

Confirmed:

- GPU0-bound `DISPLAY=:8` was not used.
- No new visible-motion HDF5/MP4/NPY was generated.
