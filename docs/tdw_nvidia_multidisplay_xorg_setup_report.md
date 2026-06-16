# TDW NVIDIA Multidisplay Xorg Setup Report

## Root setup result

Root batch-mode SSH was unavailable from this Codex session. No root password was recorded, echoed, scripted, or committed. No `/etc/X11` files were created or modified in this round.

## Current display map

- `:8` -> NVIDIA renderer, existing GPU0 display, preserved.
- `:9` -> llvmpipe, not allowed for TDW GPU generation.
- `:10` -> llvmpipe, not allowed for TDW GPU generation.
- `:11` -> llvmpipe, not allowed for TDW GPU generation.
- `:12` -> llvmpipe, not allowed for TDW GPU generation.
- `:13` -> llvmpipe, not allowed for TDW GPU generation.
- `:14` / `:15` -> unavailable.
- `:20` to `:26` -> unavailable before root setup.

## Required target map

- `:20` -> GPU1, PCI bus `00000000:58:00.0`, Xorg BusID `PCI:88:0:0`.
- `:21` -> GPU2, PCI bus `00000000:60:00.0`, Xorg BusID `PCI:96:0:0`.
- `:22` -> GPU3, PCI bus `00000000:66:00.0`, Xorg BusID `PCI:102:0:0`.
- `:23` -> GPU4, PCI bus `00000000:AA:00.0`, Xorg BusID `PCI:170:0:0`.
- `:24` -> GPU5, PCI bus `00000000:BA:00.0`, Xorg BusID `PCI:186:0:0`.
- `:25` -> GPU6, PCI bus `00000000:CA:00.0`, Xorg BusID `PCI:202:0:0`.
- `:26` -> GPU7, PCI bus `00000000:DA:00.0`, Xorg BusID `PCI:218:0:0`.

## Verification requirement

Before any TDW multi-display smoke, every candidate display must pass:

```bash
DISPLAY=:20 xdpyinfo
DISPLAY=:20 glxinfo -B
```

The renderer must contain `NVIDIA Corporation` / `NVIDIA H20`; llvmpipe is a hard fail.

## Ready for smoke

No. Only one NVIDIA display is currently available.
