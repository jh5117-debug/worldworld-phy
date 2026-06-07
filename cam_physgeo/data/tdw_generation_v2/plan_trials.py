from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generation_config import get_profile, load_config, upstream_camera_mapping, validate_profile_camera_set, variant_name


def _bool_arg(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def parse_template_counts(raw: str | None) -> dict[str, int]:
    if not raw:
        return {}
    out: dict[str, int] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(f"template_counts item must be name:count, got {item!r}")
        name, value = item.split(":", 1)
        count = int(value)
        if count < 0:
            raise ValueError(f"template count must be non-negative for {name!r}")
        out[name.strip()] = count
    return out


def build_template_sequence(templates: list[str], num_trials: int, template_counts: dict[str, int] | None = None) -> list[str]:
    templates = list(templates)
    if not templates:
        raise ValueError("At least one template is required")
    if template_counts:
        unknown = sorted(set(template_counts) - set(templates))
        if unknown:
            raise ValueError(f"template_counts references template(s) not in --templates/profile: {unknown}")
        seq: list[str] = []
        for template in templates:
            seq.extend([template] * int(template_counts.get(template, 0)))
        if len(seq) != num_trials:
            raise ValueError(f"template_counts sum {len(seq)} must equal --num_trials {num_trials}")
        return seq
    return [templates[idx % len(templates)] for idx in range(num_trials)]


def build_trials(
    config_path: Path,
    profile_name: str,
    templates: list[str],
    num_trials: int,
    template_counts: dict[str, int] | None = None,
    *,
    diverse_scene_seeds: bool = False,
    unique_source_configs: bool = False,
) -> list[dict]:
    config = load_config(config_path)
    profile = get_profile(config, profile_name)
    validate_profile_camera_set(config, profile)
    templates = templates or profile.templates
    variants = profile.camera_variants
    variant_by_name = {variant_name(variant): variant for variant in variants}
    upstream_variants = {row["name"]: row for row in upstream_camera_mapping(config, profile)}
    if not upstream_variants:
        raise ValueError(f"Profile {profile_name} has no camera_variants")
    seed_start = int(config.get("seed_start", 20000))
    trials = []
    template_sequence = build_template_sequence(templates, num_trials, template_counts)
    template_seen: dict[str, int] = {template: 0 for template in templates}
    for idx in range(num_trials):
        template = template_sequence[idx]
        template_variant_names = profile.template_camera_variants.get(template, [])
        if template_variant_names:
            local_idx = template_seen.get(template, 0)
            camera_variant_name = template_variant_names[local_idx % len(template_variant_names)]
            template_seen[template] = local_idx + 1
        else:
            variant = variants[idx % len(variants)]
            camera_variant_name = str(variant["name"])
        variant = variant_by_name.get(camera_variant_name, {"name": camera_variant_name})
        seed = seed_start + idx
        trial_id = f"tdw_v2_{profile_name}_{template}_{camera_variant_name}_seed{seed}"
        upstream_variant = dict(upstream_variants[camera_variant_name])
        filters = dict(profile.filters)
        scene_seed = seed if diverse_scene_seeds else seed_start + template_seen.get(template, 0)
        motion_start = filters.get("camera_motion_start", filters.get("motion_start"))
        motion_end = filters.get("camera_motion_end", filters.get("motion_end"))
        trials.append({
            "trial_id": trial_id,
            "profile": profile_name,
            "purpose": profile.purpose,
            "template": template,
            "seed": seed,
            "camera_set": profile.camera_set,
            "camera_variant": camera_variant_name,
            "camera_motion": str(variant.get("motion", upstream_variant.get("motion", ""))),
            "camera_args": {
                "yaw_degrees": variant.get("yaw_degrees"),
                "translation": variant.get("translation"),
                "height_delta": variant.get("height_delta"),
                "stress": bool(variant.get("stress", False)),
            },
            "camera_motion_start": motion_start,
            "camera_motion_end": motion_end,
            "upstream_camera_variant": upstream_variant,
            "filters": filters,
            "trial_seed": seed,
            "scene_seed": scene_seed,
            "source_config_path": None,
            "source_config_id": f"{template}_scene_seed{scene_seed}",
            "scene_diversity": {
                "diverse_scene_seeds": bool(diverse_scene_seeds),
                "unique_source_configs": bool(unique_source_configs),
                "method": "seed-diverse Physion upstream template generation; source_config_path unavailable in current runner",
            },
            "status": "planned",
            "notes": "Physion-style TDW simulated moving-camera plan; not real-world data.",
        })
    return trials


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan staged TDW/Physion-style moving-camera v2 trials.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--templates", nargs="*", default=[])
    parser.add_argument("--template_counts", default=None)
    parser.add_argument("--num_trials", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--diverse_scene_seeds", type=_bool_arg, default=False)
    parser.add_argument("--unique_source_configs", type=_bool_arg, default=False)
    args = parser.parse_args()

    template_counts = parse_template_counts(args.template_counts)
    trials = build_trials(
        args.config,
        args.profile,
        args.templates,
        args.num_trials,
        template_counts,
        diverse_scene_seeds=bool(args.diverse_scene_seeds),
        unique_source_configs=bool(args.unique_source_configs),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in trials:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {
        "config": str(args.config),
        "profile": args.profile,
        "num_trials": len(trials),
        "templates": sorted(set(t["template"] for t in trials)),
        "template_distribution": {name: sum(1 for t in trials if t["template"] == name) for name in sorted(set(t["template"] for t in trials))},
        "camera_set": trials[0].get("camera_set") if trials else None,
        "camera_variants": sorted(set(str(t["camera_variant"]) for t in trials)),
        "diverse_scene_seeds": bool(args.diverse_scene_seeds),
        "unique_source_configs": bool(args.unique_source_configs),
        "out": str(args.out),
        "dry_run": bool(args.dry_run),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
