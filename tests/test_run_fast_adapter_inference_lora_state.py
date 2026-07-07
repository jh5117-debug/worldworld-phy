from cam_physgeo.eval.run_fast_adapter_inference import parse_args


def test_parse_lora_state_args():
    args = parse_args([
        "--manifest", "manifest.jsonl",
        "--out", "out",
        "--model_label", "step007",
        "--lora_state", "state.pt",
        "--lora_rank", "4",
        "--lora_alpha", "4",
        "--lora_target_groups", "camera_conditioning",
    ])
    assert args.lora_state == "state.pt"
    assert args.lora_rank == 4
    assert args.lora_alpha == 4
    assert args.lora_target_groups == "camera_conditioning"
