# GPU6/7 TDW Display Requirement Report

Date: 2026-06-05

## Requirement

This run is only allowed to use GPU6 or GPU7 for TDW / Unity generation. GPU0-5 are forbidden for this turn.

## Current Display Audit

Observed X/TDW process:

```text
/usr/lib/xorg/Xorg :8 -config /etc/X11/tdw-xorg-gpu0.conf ...
```

Observed X sockets:

```text
X8
X9
X10
X11
X12
X13
```

Only `:8` has an observed Xorg process, and it uses:

```text
/etc/X11/tdw-xorg-gpu0.conf
```

That config defines:

```text
Identifier "GPU0"
BusID "PCI:82:0:0"
```

GPU6/7 config lookup:

```text
ls /etc/X11/*gpu6* /etc/X11/*gpu7*
```

Result:

No GPU6/GPU7 TDW Xorg config was found.

GPU status at audit time:

- GPU6: 1 MiB used, 0% utilization.
- GPU7: 1 MiB used, 0% utilization.

The GPUs are idle, but there is no verified TDW display bound to GPU6 or GPU7.

## Decision

Actual TDW generation is blocked.

The existing GPU0-bound `DISPLAY=:8` was not used.

## Confirmation

- GPU0 was not used for generation.
- No visible-motion HDF5/MP4/NPY data was generated.
- Only plan dry-run and display audit were performed.
