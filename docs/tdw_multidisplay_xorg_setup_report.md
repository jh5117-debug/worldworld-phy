# TDW Multidisplay Xorg Setup Report

## Result

Automatic root-side Xorg setup was not performed because root batch-mode SSH was unavailable from the ubuntu session. No root password was recorded, echoed, scripted, or committed.

## Current Display Audit

- `DISPLAY=:8`: usable, NVIDIA OpenGL renderer, existing GPU0 Xorg preserved.
- `DISPLAY=:9`: `xdpyinfo` works, but OpenGL renderer is Mesa llvmpipe, not NVIDIA.
- `DISPLAY=:10`: `xdpyinfo` works, but OpenGL renderer is Mesa llvmpipe, not NVIDIA.
- `DISPLAY=:11`: `xdpyinfo` works, but OpenGL renderer is Mesa llvmpipe, not NVIDIA.
- `DISPLAY=:12`: `xdpyinfo` works, but OpenGL renderer is Mesa llvmpipe, not NVIDIA.
- `DISPLAY=:13`: `xdpyinfo` works, but OpenGL renderer is Mesa llvmpipe, not NVIDIA.
- `DISPLAY=:14`: unavailable.
- `DISPLAY=:15`: unavailable.

`xdpyinfo` alone is not sufficient. TDW/Unity requires NVIDIA OpenGL, so `:9` to `:13` cannot be used for GPU TDW generation in their current state.

## Required Mapping

- `:8`  -> GPU0, BusID `PCI:82:0:0`, already present.
- `:9`  -> GPU1, BusID `PCI:88:0:0`.
- `:10` -> GPU2, BusID `PCI:96:0:0`.
- `:11` -> GPU3, BusID `PCI:102:0:0`.
- `:12` -> GPU4, BusID `PCI:170:0:0`.
- `:13` -> GPU5, BusID `PCI:186:0:0`.
- `:14` -> GPU6, BusID `PCI:202:0:0`.
- `:15` -> GPU7, BusID `PCI:218:0:0`.

## Admin Action Needed

As root, create `/etc/X11/tdw-xorg-gpu1.conf` through `/etc/X11/tdw-xorg-gpu7.conf` with the matching BusID values, then start Xorg servers for `:9` through `:15`. Do not overwrite `/etc/X11/tdw-xorg-gpu0.conf` and do not kill `:8`.

After setup, verify each display with both:

```bash
DISPLAY=:9 xdpyinfo
DISPLAY=:9 glxinfo -B
```

Every display must report `OpenGL vendor string: NVIDIA Corporation` and an NVIDIA H20 renderer before TDW generation is allowed.
