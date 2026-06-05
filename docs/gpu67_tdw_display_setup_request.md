# GPU6/7 TDW Display Setup Request

Date: 2026-06-05

## Blocker

`warmup_visible_motion` actual TDW generation requires a TDW / Unity display bound to GPU6 or GPU7.

Current available TDW display:

```text
DISPLAY=:8
```

But this display is bound to GPU0:

```text
/etc/X11/tdw-xorg-gpu0.conf
```

The current user instruction forbids GPU0-5 for this task, so actual generation cannot run.

Additional audit result:

```text
sudo: a password is required
sudo_not_available
```

So Codex cannot create `/etc/X11/tdw-xorg-gpu6.conf` or start `Xorg :16` in this run.

GPU6 PCI bus id:

```text
00000000:CA:00.0
```

Xorg BusID form:

```text
PCI:202:0:0
```

## Needed Setup

An administrator or user with sufficient permissions should create a TDW Xorg display on GPU6 or GPU7.

Suggested display names:

- `DISPLAY=:16` for GPU6
- `DISPLAY=:17` for GPU7

Draft setup pattern:

```bash
sudo nvidia-xconfig \
  --allow-empty-initial-configuration \
  --use-display-device=None \
  --virtual=1280x720 \
  --busid PCI:202:0:0 \
  --output-xconfig=/etc/X11/tdw-xorg-gpu6.conf

sudo Xorg :16 \
  -config /etc/X11/tdw-xorg-gpu6.conf \
  -noreset +extension GLX +extension RANDR +extension RENDER \
  -logfile /tmp/xorg-gpu-16.log
```

The exact `BusID` must be taken from `nvidia-smi -q` or `nvidia-xconfig --query-gpu-info`.

Minimal manual config content, matching the existing GPU0 pattern:

```text
Section "ServerFlags"
    Option "AutoAddGPU" "False"
    Option "AutoBindGPU" "False"
EndSection

Section "ServerLayout"
    Identifier "TDWHeadlessGPU6"
    Screen 0 "Screen0" 0 0
EndSection

Section "Device"
    Identifier "GPU6"
    Driver "nvidia"
    VendorName "NVIDIA Corporation"
    BusID "PCI:202:0:0"
    Option "AllowEmptyInitialConfiguration" "True"
EndSection

Section "Screen"
    Identifier "Screen0"
    Device "GPU6"
    DefaultDepth 24
    Option "AllowEmptyInitialConfiguration" "True"
    SubSection "Display"
        Depth 24
        Virtual 1280 720
    EndSubSection
EndSection
```

Validation after setup:

```bash
DISPLAY=:16 xdpyinfo >/tmp/tdw_xdpyinfo_16.txt 2>&1
ps -ef | grep "Xorg :16" | grep -v grep
nvidia-smi --query-gpu=index,pci.bus_id,memory.used,memory.total,utilization.gpu --format=csv
```

## Command To Run After Setup

After a GPU6/7 display exists, run:

```bash
bash scripts/31_run_tdw_generation_v2_smoke.sh \
  --profile warmup_visible_motion \
  --plan local_assets/data/physion/generated_v2/manifests/plan_warmup_visible_motion_10.jsonl \
  --out_root local_assets/data/physion/generated_v2 \
  --display <GPU6_OR_GPU7_DISPLAY> \
  --allowed_gpu_ids 6,7 \
  --require_allowed_gpu_display \
  --no_overwrite
```

## Current Decision

Do not use GPU0. Do not generate visible-motion data until a GPU6/7 TDW display is available.
