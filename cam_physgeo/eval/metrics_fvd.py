from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FVDStatus:
    status: str
    reason: str
    attempted_fix: str
    backend: str = "none"


def fvd_backend_status() -> FVDStatus:
    """Return whether a real video FVD backend is available.

    This intentionally does not treat image FID as FVD. FVD needs a video
    feature backbone such as I3D plus the correct temporal feature pooling.
    """
    attempts: list[str] = []
    try:
        from torchmetrics.video import FrechetVideoDistance  # type: ignore  # noqa: F401
        return FVDStatus(
            status="AVAILABLE",
            reason="torchmetrics.video.FrechetVideoDistance imports",
            attempted_fix="torchmetrics video FVD backend found locally",
            backend="torchmetrics.video.FrechetVideoDistance",
        )
    except Exception as exc:
        attempts.append(f"torchmetrics.video.FrechetVideoDistance unavailable: {exc}")

    try:
        import pytorchvideo  # noqa: F401
        import pytorchvideo.models.hub as hub  # noqa: F401
        attempts.append("pytorchvideo imports after lightweight install, but it does not provide an FVD metric or local I3D/FVD weights")
    except Exception as exc:
        attempts.append(f"pytorchvideo unavailable or incompatible: {exc}")

    try:
        import pytorch_fid  # noqa: F401
        attempts.append("pytorch-fid is installed, but image FID is not reported as video FVD")
    except Exception as exc:
        attempts.append(f"pytorch-fid unavailable: {exc}")

    return FVDStatus(
        status="BLOCKED_BY_ENV",
        reason="No real video FVD backend with local temporal feature weights is available. " + " | ".join(attempts),
        attempted_fix="Installed/checked pytorchvideo and torchmetrics; refused to substitute image FID for FVD; no uncontrolled I3D weight download was started.",
        backend="none",
    )


def compute_fvd_if_available(*_: Any, **__: Any) -> dict[str, Any]:
    status = fvd_backend_status()
    return {
        "fvd_status": status.status,
        "fvd_reason": status.reason,
        "fvd_attempted_fix": status.attempted_fix,
        "fvd_backend": status.backend,
    }
