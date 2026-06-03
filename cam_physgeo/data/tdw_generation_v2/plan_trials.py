from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generation_config import get_profile, load_config


def build_trials(config_path: Path, profile_name: str, templates: list[str], num_trials: int) -> list[dict]:
    config = load_config(config_path)
    profile = get_profile(config, profile_name)
    templates = templates or profile.templates
    variants = profile.camera_variants
    if not variants:
        raise ValueError(f"Profile {profile_name} has no camera_variants")
    seed_start = int(config.get("seed_start", 20000))
    trials = []
    for idx in range(num_trials):
        template = templates[idx % len(templates)]
        variant = variants[idx % len(variants)]
        seed = seed_start + idx
        trial_id = f"tdw_v2_{profile_name}_{template}_{variant['name']}_seed{seed}"
        trials.append({
            "trial_id": trial_id,
            "profile": profile_name,
            "purpose": profile.purpose,
            "template": template,
            "seed": seed,
            "camera_variant": variant,
            "filters": profile.filters,
            "status": "planned",
            "notes": "Physion-style TDW simulated moving-camera plan; not real-world data.",
        })
    return trials


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan staged TDW/Physion-style moving-camera v2 trials.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--templates", nargs="*", default=[])
    parser.add_argument("--num_trials", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    trials = build_trials(args.config, args.profile, args.templates, args.num_trials)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in trials:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {
        "config": str(args.config),
        "profile": args.profile,
        "num_trials": len(trials),
        "templates": sorted(set(t["template"] for t in trials)),
        "camera_variants": sorted(set(t["camera_variant"]["name"] for t in trials)),
        "out": str(args.out),
        "dry_run": bool(args.dry_run),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
