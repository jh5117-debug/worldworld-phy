# TDW GPU6/7 Display Setup Report

Date: 2026-06-05

## Setup Attempt

The setup path was audited but not executed because sudo is required and passwordless sudo is not available.

## Sudo

Result:

```text
sudo_not_available
```

The shell reported:

```text
sudo: a password is required
```

## Config Creation

Not created.

Intended config:

`/etc/X11/tdw-xorg-gpu6.conf`

Reason:

Writing to `/etc/X11` requires sudo/admin privileges.

## Display Startup

Not started.

Intended display:

`DISPLAY=:16`

Reason:

Starting a GPU-bound Xorg process requires sudo/admin privileges.

## GPU Binding

GPU6 PCI bus id:

`00000000:CA:00.0`

Xorg-style BusID:

`PCI:202:0:0`

This was not activated because the config could not be written and Xorg could not be started.

## TDW Generation Permission

Actual TDW generation is not allowed yet.

Required before generation:

- a running `Xorg :16` or equivalent display;
- config or process inspection showing it is bound to GPU6 or GPU7;
- `xdpyinfo` success on that display;
- `run_tdw_trial.py` display guard detecting GPU6/7.
