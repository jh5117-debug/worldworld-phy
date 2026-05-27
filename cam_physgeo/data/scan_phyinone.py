"""Deprecated compatibility module.

The active Cam-PhysGeo-DPO pipeline is Physion-only. This file is kept so old
imports fail gently instead of reviving the previous data direction.
"""

from __future__ import annotations

from typing import Iterator


def iter_phyinone_samples(*args, **kwargs) -> Iterator[dict]:
    print("WARNING: scan_phyinone is deprecated and returns no samples in the Physion-only pipeline.")
    return iter(())
