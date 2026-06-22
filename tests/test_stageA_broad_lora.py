from __future__ import annotations

from types import SimpleNamespace
import pytest
import torch

from physical_consistency.stages.stage1_physinone_cam.trainer import Stage1BranchTrainer, fixed_validation_noise_seed
from physical_consistency.trainers.stage1_components import (
    LoRALinear,
    apply_lora_to_wan_model,
    classify_lora_linear_group,
)


class _Attention(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.q = torch.nn.Linear(4, 4)
        self.k = torch.nn.Linear(4, 4)
        self.v = torch.nn.Linear(4, 4)
        self.o = torch.nn.Linear(4, 4)


class _Block(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.self_attn = _Attention()
        self.cross_attn = _Attention()
        self.ffn = torch.nn.Sequential(torch.nn.Linear(4, 8), torch.nn.SiLU(), torch.nn.Linear(8, 4))
        self.cam_injector_layer1 = torch.nn.Linear(6, 6)
        self.cam_injector_layer2 = torch.nn.Linear(6, 6)
        self.cam_scale_layer = torch.nn.Linear(6, 4)
        self.cam_shift_layer = torch.nn.Linear(6, 4)
        self.norm = torch.nn.LayerNorm(4)


class _WanLike(torch.nn.Module):
    def __init__(self, blocks: int = 2) -> None:
        super().__init__()
        self.blocks = torch.nn.ModuleList(_Block() for _ in range(blocks))
        self.head = torch.nn.Linear(4, 4)


def test_classify_lora_linear_group() -> None:
    assert classify_lora_linear_group("blocks.0.self_attn.q") == "self_attention"
    assert classify_lora_linear_group("blocks.0.cross_attn.v") == "cross_attention"
    assert classify_lora_linear_group("blocks.0.ffn.0") == "ffn"
    assert classify_lora_linear_group("blocks.0.cam_shift_layer") == "camera_conditioning"
    assert classify_lora_linear_group("blocks.0.norm") is None


def test_apply_broad_lora_requires_all_groups_and_freezes_base() -> None:
    model = _WanLike(blocks=2)
    report = apply_lora_to_wan_model(
        model,
        rank=2,
        alpha=2,
        dropout=0.0,
        target_groups=("camera_conditioning", "self_attention", "cross_attention", "ffn"),
        required_groups=("camera_conditioning", "self_attention", "cross_attention", "ffn"),
        block_start=0,
        block_end=0,
        merge_mode="out_of_place",
    )
    counts = {group: len(names) for group, names in report.selected_by_group.items()}
    assert counts["self_attention"] == 4
    assert counts["cross_attention"] == 4
    assert counts["ffn"] == 2
    assert counts["camera_conditioning"] == 4
    assert isinstance(model.blocks[0].self_attn.q, LoRALinear)
    assert not isinstance(model.blocks[1].self_attn.q, LoRALinear)
    assert not model.blocks[0].self_attn.q.base.weight.requires_grad
    assert model.blocks[0].self_attn.q.lora_A.weight.requires_grad
    assert model.blocks[0].self_attn.q.lora_B.weight.requires_grad
    assert torch.count_nonzero(model.blocks[0].self_attn.q.lora_B.weight).item() == 0
    assert not model.head.weight.requires_grad


def test_apply_broad_lora_fails_when_required_group_missing() -> None:
    model = _WanLike(blocks=1)
    with pytest.raises(RuntimeError, match="Required LoRA target groups missing"):
        apply_lora_to_wan_model(
            model,
            rank=2,
            alpha=2,
            dropout=0.0,
            target_groups=("self_attention",),
            required_groups=("self_attention", "cross_attention"),
        )

def test_fixed_validation_noise_seed_is_checkpoint_invariant() -> None:
    seed_a = fixed_validation_noise_seed(
        base_seed=42,
        branch="high_only",
        validation_index=7,
        sample_id="01000_drop_orbit_left_72_seed40000",
    )
    seed_b = fixed_validation_noise_seed(
        base_seed=42,
        branch="high_only",
        validation_index=7,
        sample_id="01000_drop_orbit_left_72_seed40000",
    )
    assert seed_a == seed_b
    assert seed_a == fixed_validation_noise_seed(
        base_seed=42,
        branch="high",
        validation_index=7,
        sample_id="01000_drop_orbit_left_72_seed40000",
    )
    assert seed_a != fixed_validation_noise_seed(
        base_seed=42,
        branch="low",
        validation_index=7,
        sample_id="01000_drop_orbit_left_72_seed40000",
    )
    assert seed_a != fixed_validation_noise_seed(
        base_seed=42,
        branch="high_only",
        validation_index=8,
        sample_id="01000_drop_orbit_left_72_seed40000",
    )

def test_fixed_timestep_sample_high_only_uses_high_noise_band() -> None:
    trainer = object.__new__(Stage1BranchTrainer)
    trainer.branch = "high_only"
    trainer.cfg = SimpleNamespace(fixed_val_sample_count=4)
    trainer.accelerator = SimpleNamespace(device=torch.device("cpu"))
    trainer.helper = SimpleNamespace(
        high_noise_indices=torch.tensor([8, 9]),
        high_noise_weights=torch.tensor([1.0, 2.0]),
        low_noise_indices=torch.tensor([1, 2]),
        low_noise_weights=torch.tensor([3.0, 4.0]),
        sigmas=torch.arange(10, dtype=torch.float32),
        timesteps_schedule=torch.arange(10, dtype=torch.float32),
        branch_for_timestep_index=lambda idx: "high" if idx >= 8 else "low",
    )

    sample = Stage1BranchTrainer._fixed_timestep_sample(trainer, validation_index=0)

    assert sample.index in {8, 9}
    assert sample.branch == "high"
    assert sample.timestep.item() >= 8

