from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cam_physgeo.utils.io import read_jsonl


def convert_pair(pair: dict[str, Any]) -> dict[str, Any]:
    cond = pair.get("condition") or {}
    winner = pair.get("winner") or {}
    loser = pair.get("loser") or {}
    prompt = resolve_prompt_text(cond.get("prompt"))
    chosen_reward = float((winner.get("reward") or {}).get("reward_total") or 0.0)
    rejected_reward = float((loser.get("reward") or {}).get("reward_total") or 0.0)
    extra_condition = {
        "image": cond.get("image"),
        "prefix": cond.get("prefix"),
        "poses": cond.get("poses"),
        "intrinsics": cond.get("intrinsics"),
        "metadata": cond.get("metadata"),
        "use_action": False,
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
                "source": winner.get("source"),
            },
            {
                "video_path": loser.get("video"),
                "generation_id": f"corrupted_{loser.get('corruption_type') or pair.get('corruption')}",
                "consistency_score": 1.0 - rejected_reward,
                "motion_norm": 1.0,
                "physgeo_reward": rejected_reward,
                "source": loser.get("source"),
                "corruption_type": loser.get("corruption_type") or pair.get("corruption"),
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
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    rows = [convert_pair(row) for row in read_jsonl(args.pairs)]
    missing = [row["group_id"] for row in rows if len(row.get("videos") or []) < 2 or not row.get("prompt")]
    payload = {"groups": rows, "format": "videogpa_meta_data", "metric_name": "consistency_score", "metric_mode": "min"}
    summary = {"pairs": len(rows), "groups": len(rows), "missing_required": len(missing), "out": args.out, "dry_run": args.dry_run}
    print(summary)
    if not args.dry_run:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
