"""Deprecated alias for Physion moving-camera scanner."""

from __future__ import annotations

from cam_physgeo.data.scan_physion_movingcam import iter_physion_movingcam_samples


def iter_movingcam_samples(root, limit=None):
    print("WARNING: scan_movingcam_synthetic is deprecated; emitting Physion moving-camera samples.")
    return iter_physion_movingcam_samples(root, limit=limit)
