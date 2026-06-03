# TDW Display / GPU Routing Audit

## Summary

Actual TDW / Unity generation remains blocked. The existing TDW display `:8` is bound to GPU0, while this task only permits GPU6/7 for smoke/gate jobs. No GPU6/7-backed Xorg display was found.

## Initial Environment

- Host: `instance-afs92r3e`
- Main project path: `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys`
- Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Main worktree branch was dirty, so implementation continued from the clean local/aux branch workflow.

## Running Xorg / Displays

Running display process found:

```text
/usr/lib/xorg/Xorg :8 -config /etc/X11/tdw-xorg-gpu0.conf -noreset +extension GLX +extension RANDR +extension RENDER -logfile /tmp/xorg-gpu-8.log
```

Config file:

```text
/etc/X11/tdw-xorg-gpu0.conf
```

The config contains:

```text
Section "Device"
    Identifier "GPU0"
    Driver "nvidia"
    BusID "PCI:82:0:0"
EndSection
```

Conclusion: `DISPLAY=:8` is bound to GPU0.

## Existing Display Sockets

The server has X sockets:

- `X8`
- `X9`
- `X10`
- `X11`
- `X12`
- `X13`

Connectivity check found these displays respond to `xdpyinfo`, but only `:8` is an NVIDIA Xorg display. Displays `:9` to `:13` are Xvfb:

```text
Xvfb :9  -screen 0 1280x720x24
Xvfb :10 -screen 0 1280x720x24
Xvfb :11 -screen 0 1280x720x24
Xvfb :12 -screen 0 1280x720x24
Xvfb :13 -screen 0 1280x720x24
```

`DISPLAY=:9 glxinfo -B` reports Mesa llvmpipe:

```text
OpenGL vendor string: Mesa
OpenGL renderer string: llvmpipe (LLVM 15.0.7, 256 bits)
```

This means `:9` is CPU/software OpenGL, not GPU6/7. It does not prove TDW/Unity can run correctly in the current headless mode.

## GPU6/7 Display Availability

No Xorg display bound to GPU6 or GPU7 was found. GPU6 and GPU7 were idle, but there was no corresponding TDW Xorg config or running Xorg display.

## TDW Runner DISPLAY Behavior

The upstream batch runner accepts `--display` and sets `env["DISPLAY"] = args.display` for the child process. The child TDW script also has its own `--gpu` path:

```python
if args.gpu is not None:
    os.environ["DISPLAY"] = ":0." + str(args.gpu)
elif "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":0"
```

The batch script currently passes `--gpu None` to the child command. Further testing is required before using Xvfb/CPU mode, because the child parser may interpret `"None"` as a non-`None` value and override `DISPLAY`.

## Sudo / Admin Requirement

Creating a new NVIDIA Xorg display bound to GPU6/7 likely requires root or system-level Xorg configuration. This task explicitly disallows using sudo/admin escalation. Therefore no new GPU6/7 Xorg display was started.

## Can We Use GPU6/7 Without Affecting Others?

Not yet. GPUs 6/7 are free, but there is no confirmed GPU6/7 display. We can safely use them only after a GPU6/7 Xorg display is created or an approved TDW headless path is validated.

## Decision

Do not run TDW generation in this round. The safe next step is user choice:

- configure/approve a GPU6/7 display;
- approve exactly one GPU0-bound `:8` TDW smoke;
- pause generation and keep only wrapper/plan validation.

