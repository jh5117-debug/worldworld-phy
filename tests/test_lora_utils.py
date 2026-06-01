from __future__ import annotations

import torch
from torch import nn

from cam_physgeo.dpo.lora_utils import (
    LoRALinear,
    count_lora_parameters,
    freeze_non_lora_parameters,
    inject_lora_into_modules,
    list_lora_parameters,
    remove_lora_from_model,
)


def test_lora_linear_shape_and_freeze() -> None:
    base = nn.Linear(8, 4)
    wrapped = LoRALinear(base, rank=2, alpha=4)
    x = torch.randn(3, 8)
    y = wrapped(x)
    assert list(y.shape) == [3, 4]
    assert not wrapped.base.weight.requires_grad
    assert wrapped.lora_A.requires_grad
    assert wrapped.lora_B.requires_grad


def test_inject_lora_backward_and_count() -> None:
    model = nn.Sequential(nn.Linear(8, 4), nn.ReLU(), nn.Linear(4, 2))
    injections = inject_lora_into_modules(model, ["0"], rank=2, alpha=4)
    assert injections[0].lora_param_count == 2 * (8 + 4)
    freeze_non_lora_parameters(model)
    assert count_lora_parameters(model) == 24
    rows = list_lora_parameters(model)
    assert len(rows) == 2
    assert all(row["requires_grad"] for row in rows)

    x = torch.randn(5, 8)
    loss = model(x).float().pow(2).mean()
    loss.backward()
    grads = [param.grad for name, param in model.named_parameters() if "lora_" in name]
    assert grads and all(grad is not None for grad in grads)
    assert all(torch.isfinite(grad).all() for grad in grads if grad is not None)
    assert all(param.grad is None for name, param in model.named_parameters() if "lora_" not in name)


def test_remove_lora_restores_linear() -> None:
    model = nn.Sequential(nn.Linear(8, 4), nn.ReLU(), nn.Linear(4, 2))
    inject_lora_into_modules(model, ["0"], rank=2, alpha=4)
    assert isinstance(model[0], LoRALinear)
    removed = remove_lora_from_model(model)
    assert removed == ["0"]
    assert isinstance(model[0], nn.Linear)
