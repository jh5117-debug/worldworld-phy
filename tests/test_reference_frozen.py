from __future__ import annotations

import torch


class _FakeLora(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.scaling = 3.0
        self.lora_A = torch.nn.Linear(2, 1, bias=False)
        self.lora_B = torch.nn.Linear(1, 2, bias=False)


def test_reference_mode_restores_lora_scaling_without_grad():
    from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy

    fake = torch.nn.Sequential(_FakeLora())
    obj = object.__new__(LingBotFastDpoEnergy)
    obj.model = fake
    assert fake[0].scaling == 3.0
    with obj.reference_mode():
        assert fake[0].scaling == 0.0
        assert not fake.training
    assert fake[0].scaling == 3.0
