from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import nn


@dataclass
class LoraInjection:
    module_name: str
    rank: int
    alpha: float
    lora_param_count: int
    base_param_count: int


class LoRALinear(nn.Module):
    """Tiny runtime LoRA wrapper for a frozen ``nn.Linear``.

    This module is intentionally small: it only supports inference/training
    plumbing smoke tests and does not implement persistence.
    """

    def __init__(self, base: nn.Linear, *, rank: int = 2, alpha: float = 4.0, dropout: float = 0.0) -> None:
        super().__init__()
        if rank <= 0:
            raise ValueError(f"rank must be positive, got {rank}")
        self.base = base
        self.rank = int(rank)
        self.alpha = float(alpha)
        self.scaling = self.alpha / float(self.rank)
        self.dropout = nn.Dropout(float(dropout)) if dropout and dropout > 0 else nn.Identity()

        for param in self.base.parameters():
            param.requires_grad_(False)

        device = self.base.weight.device
        # Keep trainable LoRA factors in fp32 so a tiny AdamW step at lr=1e-5
        # is observable even when the frozen LingBot base runs in bf16.
        dtype = torch.float32
        self.lora_A = nn.Parameter(torch.empty(self.rank, self.base.in_features, device=device, dtype=dtype))
        self.lora_B = nn.Parameter(torch.empty(self.base.out_features, self.rank, device=device, dtype=dtype))
        self.reset_lora_parameters()

    def reset_lora_parameters(self) -> None:
        # Nonzero B lets the backward-only smoke observe gradients on both low
        # rank factors without requiring an optimizer warm-up step.
        nn.init.kaiming_uniform_(self.lora_A, a=5**0.5)
        nn.init.normal_(self.lora_B, mean=0.0, std=1e-4)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base_out = self.base(x)
        lora_input = self.dropout(x).to(dtype=self.lora_A.dtype)
        lora_hidden = torch.nn.functional.linear(lora_input, self.lora_A)
        lora_out = torch.nn.functional.linear(lora_hidden, self.lora_B)
        return base_out + (lora_out * self.scaling).to(dtype=base_out.dtype)

    @property
    def lora_param_count(self) -> int:
        return int(self.lora_A.numel() + self.lora_B.numel())

    @property
    def base_param_count(self) -> int:
        return int(sum(param.numel() for param in self.base.parameters()))


def _get_parent_module(model: nn.Module, module_name: str) -> tuple[nn.Module, str]:
    if not module_name:
        raise ValueError("cannot replace the root module with LoRA")
    parent_name, child_name = module_name.rsplit(".", 1) if "." in module_name else ("", module_name)
    parent: nn.Module = model
    if parent_name:
        for part in parent_name.split("."):
            parent = getattr(parent, part)
    return parent, child_name


def inject_lora_into_modules(
    model: nn.Module,
    target_module_names: list[str],
    *,
    rank: int = 2,
    alpha: float = 4.0,
    dropout: float = 0.0,
) -> list[LoraInjection]:
    injections: list[LoraInjection] = []
    module_map = dict(model.named_modules())
    for name in target_module_names:
        module = module_map.get(name)
        if module is None:
            raise KeyError(f"target module not found: {name}")
        if isinstance(module, LoRALinear):
            injections.append(
                LoraInjection(
                    module_name=name,
                    rank=module.rank,
                    alpha=module.alpha,
                    lora_param_count=module.lora_param_count,
                    base_param_count=module.base_param_count,
                )
            )
            continue
        if not isinstance(module, nn.Linear):
            raise TypeError(f"target module is not nn.Linear: {name} ({type(module).__name__})")
        parent, child_name = _get_parent_module(model, name)
        wrapped = LoRALinear(module, rank=rank, alpha=alpha, dropout=dropout)
        setattr(parent, child_name, wrapped)
        injections.append(
            LoraInjection(
                module_name=name,
                rank=int(rank),
                alpha=float(alpha),
                lora_param_count=wrapped.lora_param_count,
                base_param_count=wrapped.base_param_count,
            )
        )
    return injections


def freeze_non_lora_parameters(model: nn.Module) -> None:
    for name, param in model.named_parameters():
        param.requires_grad_("lora_" in name)


def list_lora_parameters(model: nn.Module) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, param in model.named_parameters():
        if "lora_" not in name:
            continue
        rows.append(
            {
                "name": name,
                "shape": list(param.shape),
                "numel": int(param.numel()),
                "requires_grad": bool(param.requires_grad),
                "dtype": str(param.dtype).replace("torch.", ""),
                "device": str(param.device),
            }
        )
    return rows


def count_lora_parameters(model: nn.Module) -> int:
    return int(sum(row["numel"] for row in list_lora_parameters(model)))


def remove_lora_from_model(model: nn.Module) -> list[str]:
    removed: list[str] = []
    for name, module in list(model.named_modules()):
        if not isinstance(module, LoRALinear):
            continue
        parent, child_name = _get_parent_module(model, name)
        setattr(parent, child_name, module.base)
        removed.append(name)
    return removed
