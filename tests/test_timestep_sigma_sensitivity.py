from __future__ import annotations

import torch

from cam_physgeo.dpo.failure_diagnostics import _make_timestep_sample


class _Helper:
    def __init__(self) -> None:
        self.sigmas = torch.tensor([0.1, 0.4, 0.7, 0.9])
        self.timesteps_schedule = torch.arange(4, dtype=torch.float32)

    def branch_for_timestep_index(self, idx: int) -> str:
        return "high" if idx >= 2 else "low"


class _Backend:
    def __init__(self) -> None:
        self.helper = _Helper()
        self.device = torch.device("cpu")


def test_make_timestep_sample_uses_full_schedule_not_high_only() -> None:
    backend = _Backend()
    low = _make_timestep_sample(backend, 0.12)
    high = _make_timestep_sample(backend, 0.88)
    assert low.index == 0
    assert high.index == 3
    assert low.sigma != high.sigma
