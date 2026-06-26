from __future__ import annotations


def test_strict_future_latent_indices_excludes_prefix_touched_latents():
    from cam_physgeo.dpo.lingbot_fast_energy import strict_future_latent_indices

    assert strict_future_latent_indices(total_frames=81, prefix_len=5, latent_frames=21) == list(range(2, 21))


def test_stage1_args_defaults_to_fast_camera_lora():
    from cam_physgeo.dpo.lingbot_fast_energy import build_stage1_args

    args = build_stage1_args({"student_lora_rank": 4, "student_lora_target_groups": ["camera_conditioning"]})
    assert args.model_family == "lingbot_world_fast"
    assert args.control_type == "cam"
    assert args.student_lora_rank == 4
    assert args.student_lora_target_groups == ("camera_conditioning",)
