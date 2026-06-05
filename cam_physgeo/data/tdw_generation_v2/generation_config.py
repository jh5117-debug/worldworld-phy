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
    camera_set: str | None
    camera_variants: list[dict[str, Any]]
    template_camera_variants: dict[str, list[str]]
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
        camera_set=raw.get("camera_set"),
        camera_variants=list(raw.get("camera_variants", [])),
        template_camera_variants={str(k): [str(x) for x in v] for k, v in dict(raw.get("template_camera_variants", {})).items()},
        filters=dict(raw.get("filters", {})),
        templates=list(raw.get("templates", config.get("default_templates", []))),
        output=dict(raw.get("output", config.get("output", {}))),
    )


def camera_set_config(config: dict[str, Any], camera_set: str | None) -> dict[str, Any]:
    if not camera_set:
        return {}
    sets = config.get("camera_sets", {})
    if camera_set not in sets:
        raise KeyError(f"Unknown camera_set {camera_set!r}; available={sorted(sets)}")
    raw = sets[camera_set]
    if not isinstance(raw, dict):
        raise ValueError(f"camera_set {camera_set!r} must be a mapping")
    return raw


def variant_name(variant: dict[str, Any]) -> str:
    return str(variant.get("name", ""))


def profile_camera_variant_names(profile: GenerationProfile) -> list[str]:
    names: list[str] = []
    for variant in profile.camera_variants:
        name = variant_name(variant)
        if name and name not in names:
            names.append(name)
    for template_variants in profile.template_camera_variants.values():
        for name in template_variants:
            if name and name not in names:
                names.append(name)
    return names


def validate_profile_camera_set(config: dict[str, Any], profile: GenerationProfile) -> None:
    """Ensure profile variants are explicitly allowed and contain no stress keywords."""
    if not profile.camera_set:
        return
    cset = camera_set_config(config, profile.camera_set)
    allowed = {str(v) for v in cset.get("allowed_variants", [])}
    banned = [str(v).lower() for v in cset.get("banned_keywords", [])]
    variant_motion = {variant_name(v): str(v.get("motion", "")) for v in profile.camera_variants}
    mapping = cset.get("upstream_mapping", {}) if cset else {}
    for name in profile_camera_variant_names(profile):
        text = f"{name} {variant_motion.get(name, mapping.get(name, {}).get('motion', ''))}".lower()
        if allowed and name not in allowed:
            raise ValueError(
                f"Profile {profile.name!r} camera_set {profile.camera_set!r} "
                f"does not allow variant {name!r}"
            )
        hit = [word for word in banned if word and word in text]
        if hit:
            raise ValueError(
                f"Profile {profile.name!r} variant {name!r} contains banned "
                f"warmup keyword(s): {hit}"
            )


def upstream_camera_mapping(config: dict[str, Any], profile: GenerationProfile) -> list[dict[str, Any]]:
    """Map profile camera variants to the upstream batch runner CAMERA_VARIANTS format."""
    validate_profile_camera_set(config, profile)
    cset = camera_set_config(config, profile.camera_set)
    mapping = cset.get("upstream_mapping", {}) if cset else {}
    variant_by_name = {variant_name(variant): variant for variant in profile.camera_variants}
    out: list[dict[str, Any]] = []
    for name in profile_camera_variant_names(profile):
        variant = variant_by_name.get(name, {"name": name})
        raw = dict(mapping.get(name, {}))
        if not raw:
            raw = {
                "motion": variant.get("motion", "orbit"),
                "orbit": float(variant.get("yaw_degrees", 0.0)),
                "height": float(variant.get("height_delta", 0.0)),
                "radius": float(variant.get("radius_delta", 0.0)),
                "strafe": float(variant.get("translation", 0.0)) if variant.get("motion") == "strafe" else 0.0,
                "require_reobserve": False,
            }
        raw["name"] = name
        raw.setdefault("motion", variant.get("motion", "orbit"))
        raw.setdefault("orbit", 0.0)
        raw.setdefault("height", 0.0)
        raw.setdefault("radius", 0.0)
        raw.setdefault("strafe", 0.0)
        raw.setdefault("require_reobserve", False)
        out.append(raw)
    return out


def tdw_display_gpu_index(config: dict[str, Any]) -> int | None:
    raw = config.get("tdw_display", {})
    if isinstance(raw, dict) and raw.get("gpu_index") is not None:
        return int(raw["gpu_index"])
    return None


def allowed_gpu_indices(config: dict[str, Any]) -> list[int]:
    return [int(x) for x in config.get("allowed_gpu_indices", [6, 7])]


def output_root(config: dict[str, Any], override: str | None = None) -> Path:
    if override:
        return Path(override)
    return Path(config.get("output_root", "local_assets/data/physion/generated_v2"))


def existing_workspace(config: dict[str, Any]) -> Path:
    return Path(config.get("existing_moving_camera_workspace", "/home/nvme03/workspace/physion_moving_camera_mainline_20260505"))
