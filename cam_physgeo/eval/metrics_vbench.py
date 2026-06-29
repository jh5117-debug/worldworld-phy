from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VBenchStatus:
    status: str
    reason: str
    attempted_fix: str


def vbench_backend_status() -> VBenchStatus:
    try:
        import vbench  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment dependent
        return VBenchStatus(
            status="BLOCKED_BY_ENV",
            reason=f"VBench import failed: {exc}",
            attempted_fix="Checked local Python environment. VBench was not installed; large model downloads were not started automatically.",
        )
    return VBenchStatus(status="AVAILABLE", reason="vbench package imports", attempted_fix="local import check")


def compute_vbench_if_available(*_: Any, **__: Any) -> dict[str, Any]:
    status = vbench_backend_status()
    if status.status != "AVAILABLE":
        return {
            "vbench_status": status.status,
            "vbench_reason": status.reason,
            "vbench_attempted_fix": status.attempted_fix,
        }
    return {
        "vbench_status": "BLOCKED_BY_ENV",
        "vbench_reason": "VBench package imports, but project-local model/config/runtime paths are not configured in this wrapper yet.",
        "vbench_attempted_fix": "Import check passed; explicit VBench assets/config are still required before scoring.",
    }
