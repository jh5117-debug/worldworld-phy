from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cam_physgeo.utils.io import read_jsonl
from cam_physgeo.dpo.preference_schema import pair_reward_breakdown, validate_pair


def _truthy(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in {"1", "true", "yes", "y", "on"}


def convert_pair(pair: dict[str, Any], *, include_camera_metadata: bool = False) -> dict[str, Any]:
    cond = pair.get("condition") or {}
    winner = pair.get("winner") or {}
    loser = pair.get("loser") or {}
    prompt = resolve_prompt_text(cond.get("prompt"))
    chosen_reward = float((winner.get("reward") or {}).get("reward_total") or 0.0)
    rejected_reward = float((loser.get("reward") or {}).get("reward_total") or 0.0)
    loser_source = loser.get("source") or "loser"
    if pair.get("pair_type") == "gt_vs_fast_rollout":
        loser_generation_id = "lingbot_fast_zero_shot"
    else:
        loser_generation_id = f"corrupted_{loser.get('corruption_type') or pair.get('corruption')}"
    extra_condition = {
        "image": cond.get("image"),
        "prefix": cond.get("prefix"),
        "poses": cond.get("poses"),
        "intrinsics": cond.get("intrinsics"),
        "metadata": cond.get("metadata"),
        "use_action": False,
        "dummy_action": cond.get("action") or cond.get("dummy_action"),
    }
    if include_camera_metadata:
        extra_condition["camera_condition"] = {
            "poses_path": cond.get("poses"),
            "intrinsics_path": cond.get("intrinsics"),
            "metadata_path": cond.get("metadata"),
            "image_path": cond.get("image"),
            "prompt_path": cond.get("prompt"),
            "use_action": False,
            "note": "Camera condition is preserved as sidecar metadata; native VideoGPA encode does not consume LingBot poses/intrinsics.",
        }
    return {
        "group_id": pair.get("pair_id"),
        "prompt": prompt,
        "text_prompt": prompt,
        "input_image_path": cond.get("image"),
        "original_video_path": winner.get("video"),
        "extra_condition": extra_condition,
        "videos": [
            {
                "video_path": winner.get("video"),
                "generation_id": "clean_physion_gt",
                "consistency_score": 1.0 - chosen_reward,
                "motion_norm": 1.0,
                "physgeo_reward": chosen_reward,
                "reward": winner.get("reward") or winner.get("reward_v5"),
                "source": winner.get("source"),
                "role": "winner",
            },
            {
                "video_path": loser.get("video"),
                "generation_id": loser_generation_id,
                "consistency_score": 1.0 - rejected_reward,
                "motion_norm": 1.0,
                "physgeo_reward": rejected_reward,
                "reward": loser.get("reward") or loser.get("reward_v5"),
                "source": loser_source,
                "corruption_type": loser.get("corruption_type") or pair.get("corruption"),
                "role": "loser",
            },
        ],
        "metadata": {
            "pair_id": pair.get("pair_id"),
            "pair_type": pair.get("pair_type"),
            "margin": pair.get("margin"),
            "winner_source": winner.get("source"),
            "loser_source": loser.get("source"),
            "corruption_type": loser.get("corruption_type") or pair.get("corruption"),
            "quality_flags": pair.get("quality_flags") or [],
            "winner_reward": winner.get("reward"),
            "loser_reward": loser.get("reward"),
            "reward_breakdown": pair.get("reward_v5_breakdown") or pair_reward_breakdown(pair),
            "use_action": False,
            "camera_condition_sidecar": extra_condition,
        },
    }


def resolve_prompt_text(value: str | None) -> str:
    if not value:
        return "A synthetic physical scene."
    if str(value).startswith("generated://"):
        return "A synthetic indoor physical scene. The static background should remain geometrically stable. Foreground objects move under physical dynamics. The camera follows the provided camera trajectory."
    path = Path(str(value))
    if path.exists() and path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            return text
    return str(value)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--format", default="videogpa", choices=["videogpa"])
    ap.add_argument("--include_camera_metadata", default="false")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    include_camera_metadata = _truthy(args.include_camera_metadata)
    source_rows = list(read_jsonl(args.pairs))
    validation = [{"pair_id": row.get("pair_id"), "errors": validate_pair(row, check_paths=True)} for row in source_rows]
    rows = [convert_pair(row, include_camera_metadata=include_camera_metadata) for row in source_rows]
    missing = [row["group_id"] for row in rows if len(row.get("videos") or []) < 2 or not row.get("prompt")]
    missing.extend(v["pair_id"] for v in validation if v["errors"])
    payload = {"groups": rows, "format": "videogpa_meta_data", "metric_name": "consistency_score", "metric_mode": "min"}
    summary = {
        "pairs": len(rows),
        "groups": len(rows),
        "missing_required": len(missing),
        "validation_errors": validation,
        "camera_metadata_included": include_camera_metadata,
        "out": args.out,
        "dry_run": args.dry_run,
    }
    print(summary)
    if not args.dry_run:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
