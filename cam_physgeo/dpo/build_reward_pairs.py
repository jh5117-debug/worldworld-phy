from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from cam_physgeo.utils.io import read_jsonl, write_json, write_jsonl


def _bool_arg(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in {"1", "true", "yes", "y", "on"}


def _score(row: dict[str, Any]) -> float:
    for key in ["reward_total_confidence_weighted", "R_total_confidence_weighted", "reward_total", "R_total"]:
        if row.get(key) is not None:
            return float(row.get(key) or 0.0)
    return 0.0


def _confidence(row: dict[str, Any]) -> float:
    return float(row.get("reward_confidence_overall") or row.get("reward_total_real_backend_confidence") or 0.0)


def _condition(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "image": row.get("image_path"),
        "prompt": row.get("prompt_path"),
        "poses": row.get("poses_path"),
        "intrinsics": row.get("intrinsics_path"),
        "metadata": row.get("metadata_path"),
        "use_action": False,
        "template": row.get("template"),
        "camera_motion": row.get("camera_motion"),
        "condition_id": row.get("condition_id"),
    }


def _make_pair(
    *,
    condition_id: str,
    winner: dict[str, Any],
    loser: dict[str, Any],
    pair_type: str,
    margin: float,
) -> dict[str, Any]:
    raw = f"{condition_id}:{pair_type}:{winner.get('eval_label')}:{loser.get('eval_label')}:{winner.get('candidate_video_path')}:{loser.get('candidate_video_path')}"
    return {
        "pair_id": "pair_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12],
        "condition_id": condition_id,
        "pair_type": pair_type,
        "condition": _condition(winner),
        "winner": {
            "video": winner.get("candidate_video_path"),
            "source": winner.get("eval_label"),
            "reward": winner,
        },
        "loser": {
            "video": loser.get("candidate_video_path"),
            "source": loser.get("eval_label"),
            "reward": loser,
        },
        "winner_type": winner.get("eval_label"),
        "loser_type": loser.get("eval_label"),
        "reward_winner": _score(winner),
        "reward_loser": _score(loser),
        "reward_margin": margin,
        "backend_confidence": min(_confidence(winner), _confidence(loser)),
        "template": winner.get("template"),
        "camera_variant": winner.get("camera_variant") or winner.get("camera_motion"),
        "use_action": False,
        "reward_breakdown": {
            "winner": winner,
            "loser": loser,
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reward_scores", required=True)
    ap.add_argument("--rollout_root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min_margin", type=float, default=0.05)
    ap.add_argument("--min_confidence", type=float, default=0.5)
    ap.add_argument("--max_pairs", type=int, default=50)
    ap.add_argument("--include_gt_vs_generated", default="true")
    ap.add_argument("--include_adapter_vs_base", default="true")
    ap.add_argument("--use_action", default="false")
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = list(read_jsonl(args.reward_scores))
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[str(row.get("condition_id") or row.get("sample_id"))][str(row.get("eval_label"))] = row

    pairs: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for condition_id, group in sorted(grouped.items()):
        if len(pairs) >= int(args.max_pairs):
            break
        gt = group.get("clean_gt")
        base = group.get("base")
        adapter = group.get("stageA_adapter")
        generated = [row for row in [base, adapter] if row]
        if _bool_arg(args.include_gt_vs_generated) and gt:
            for candidate in generated:
                margin = _score(gt) - _score(candidate)
                conf = min(_confidence(gt), _confidence(candidate))
                if margin >= float(args.min_margin) and conf >= float(args.min_confidence):
                    pairs.append(_make_pair(condition_id=condition_id, winner=gt, loser=candidate, pair_type="gt_vs_generated", margin=margin))
                else:
                    rejected.append(
                        {
                            "condition_id": condition_id,
                            "pair_type": "gt_vs_generated",
                            "candidate": candidate.get("eval_label"),
                            "reason": "margin_or_confidence_below_threshold",
                            "margin": margin,
                            "confidence": conf,
                        }
                    )
        if _bool_arg(args.include_adapter_vs_base) and base and adapter:
            base_score = _score(base)
            adapter_score = _score(adapter)
            margin = abs(adapter_score - base_score)
            conf = min(_confidence(base), _confidence(adapter))
            if margin >= float(args.min_margin) and conf >= float(args.min_confidence):
                winner, loser = (adapter, base) if adapter_score > base_score else (base, adapter)
                pairs.append(_make_pair(condition_id=condition_id, winner=winner, loser=loser, pair_type="adapter_vs_base", margin=margin))
            else:
                rejected.append(
                    {
                        "condition_id": condition_id,
                        "pair_type": "adapter_vs_base",
                        "reason": "margin_or_confidence_below_threshold",
                        "margin": margin,
                        "confidence": conf,
                    }
                )

    pairs = pairs[: int(args.max_pairs)]
    write_jsonl(pairs, out_dir / "dpo_pairs.jsonl")
    write_jsonl(rejected, out_dir / "rejected_pairs.jsonl")

    with (out_dir / "pair_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["pair_id", "condition_id", "pair_type", "winner_type", "loser_type", "reward_margin", "backend_confidence", "template", "camera_variant"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in pairs:
            writer.writerow({key: row.get(key) for key in fieldnames})

    summary = {
        "status": "pairs_ready" if pairs else "no_pairs_ready",
        "reward_scores": args.reward_scores,
        "rollout_root": args.rollout_root,
        "pair_count": len(pairs),
        "rejected_count": len(rejected),
        "min_margin": float(args.min_margin),
        "min_confidence": float(args.min_confidence),
        "pair_type_distribution": dict(Counter(row.get("pair_type") for row in pairs)),
        "template_distribution": dict(Counter(row.get("template") for row in pairs)),
        "ready_for_dpo_pilot": bool(pairs),
        "notes": [
            "This builder constructs pair manifests only; it does not run DPO.",
            "If pair_count is zero, reward confidence or margins are insufficient and DPO must remain blocked.",
        ],
    }
    write_json(summary, out_dir / "summary.json")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
