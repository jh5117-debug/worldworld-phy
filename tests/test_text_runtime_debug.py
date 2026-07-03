from pathlib import Path


def test_text_runtime_debug_module_exists():
    path = Path("cam_physgeo/dpo/text_runtime_debug.py")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "10_construct_umt5_xxl_encoder_cpu" in text
    assert "11_torch_load_t5_checkpoint_cpu" in text
    assert "12_load_state_dict_into_t5" in text
