from __future__ import annotations

import torch

from cam_physgeo.dpo.failure_diagnostics import _flat_grad


def test_flat_grad_preserves_zero_for_missing_grad() -> None:
    p1 = torch.nn.Parameter(torch.tensor([1.0, 2.0]))
    p2 = torch.nn.Parameter(torch.tensor([3.0]))
    (p1.sum() * 2.0).backward()
    vec = _flat_grad([p1, p2])
    assert vec.shape[0] == 3
    assert torch.allclose(vec[:2], torch.tensor([2.0, 2.0]))
    assert vec[2].item() == 0.0
