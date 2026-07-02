from pathlib import Path

import pytest

from cam_physgeo.dpo.safe_wan_policy_loader import _dtype_from_name, _resolve_model_paths


def test_resolve_model_paths_from_root(tmp_path: Path):
    (tmp_path / "lingbot_world_fast").mkdir()
    root, subfolder = _resolve_model_paths(tmp_path)
    assert root == tmp_path.resolve()
    assert subfolder == "lingbot_world_fast"


def test_resolve_model_paths_from_fast_dir(tmp_path: Path):
    fast = tmp_path / "lingbot_world_fast"
    fast.mkdir()
    root, subfolder = _resolve_model_paths(fast)
    assert root == tmp_path.resolve()
    assert subfolder == "lingbot_world_fast"


def test_dtype_from_name_bf16():
    torch = pytest.importorskip("torch")
    assert _dtype_from_name("bf16") == torch.bfloat16


def test_resolve_model_paths_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        _resolve_model_paths(tmp_path)
