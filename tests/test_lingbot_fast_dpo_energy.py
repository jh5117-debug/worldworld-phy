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


def test_prefix5_dataset_reads_new_schema_without_legacy_filter(tmp_path):
    import json
    from pathlib import Path

    from cam_physgeo.dpo.prefix5_dpo_dataset import Prefix5DpoDataset

    pair = {
        "pair_id": "p0",
        "margin": 0.12,
        "condition": {"prefix_len": 5, "prediction_start_frame": 5},
        "loss_frame_indices": list(range(5, 81)),
        "reward_frame_indices": list(range(5, 81)),
        "same_prefix": True,
        "same_prompt": True,
        "same_poses": True,
        "same_intrinsics": True,
        "winner": {"future_frame_indices": list(range(5, 81))},
        "loser": {"future_frame_indices": list(range(5, 81))},
    }
    manifest = tmp_path / "pairs.jsonl"
    manifest.write_text(json.dumps(pair) + "\n", encoding="utf-8")
    ds = Prefix5DpoDataset(manifest, limit_pairs=1, min_margin=0.0)
    assert len(ds) == 1
