from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


@dataclass(frozen=True)
class GenerationProfile:
    name: str
    purpose: str
    camera_variants: list[dict[str, Any]]
    filters: dict[str, Any]
    templates: list[str]
    output: dict[str, Any]


def _minimal_yaml_load(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required to read tdw_generation_v2.yaml. "
            "Install/use the project env with yaml available, or pass a JSON config."
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return _minimal_yaml_load(path)


def get_profile(config: dict[str, Any], profile: str) -> GenerationProfile:
    profiles = config.get("profiles", {})
    if profile not in profiles:
        raise KeyError(f"Unknown profile {profile!r}; available={sorted(profiles)}")
    raw = profiles[profile]
    return GenerationProfile(
        name=profile,
        purpose=str(raw.get("purpose", "")),
        camera_variants=list(raw.get("camera_variants", [])),
        filters=dict(raw.get("filters", {})),
        templates=list(raw.get("templates", config.get("default_templates", []))),
        output=dict(raw.get("output", config.get("output", {}))),
    )


def output_root(config: dict[str, Any], override: str | None = None) -> Path:
    if override:
        return Path(override)
    return Path(config.get("output_root", "local_assets/data/physion/generated_v2"))


def existing_workspace(config: dict[str, Any]) -> Path:
    return Path(config.get("existing_moving_camera_workspace", "/home/nvme03/workspace/physion_moving_camera_mainline_20260505"))
