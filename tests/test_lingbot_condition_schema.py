from pathlib import Path
from cam_physgeo.data.lingbot_condition_schema import validate_condition_dir, write_json


def test_condition_schema_requires_prompt_only(tmp_path: Path):
    for name in ["target.mp4", "action.npy", "poses.npy", "intrinsics.npy", "prompt.txt", "prefix.mp4"]:
        (tmp_path / name).write_bytes(b"x")
    write_json(tmp_path / "gravity.json", {"gravity_value": 1.0, "gravity_condition_type": "prompt_only"})
    write_json(tmp_path / "metadata.json", {"use_action": True, "use_camera": True, "use_intrinsics": True, "gravity_condition_type": "prompt_only", "gravity_value": 1.0})
    assert validate_condition_dir(tmp_path) == []
