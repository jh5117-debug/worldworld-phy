from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.utils.io import read_json, write_json, write_jsonl


def _bool_arg(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in {"1", "true", "yes", "y", "on"}


def _safe_json(path: Path) -> dict[str, Any]:
    return read_json(path, default={}) or {}


def _sample_from_condition(condition_dir: Path, *, candidate_video: Path, label: str, row: dict[str, Any] | None = None) -> dict[str, Any]:
    row = row or {}
    metadata = _safe_json(condition_dir / "metadata.json")
    sample: dict[str, Any] = {
        "sample_id": condition_dir.name,
        "condition_id": condition_dir.name,
        "eval_label": label,
        "source": "tdw_v5_lingbot_rollout",
        "template": metadata.get("template") or row.get("template"),
        "camera_variant": metadata.get("camera_variant") or metadata.get("camera_motion") or row.get("camera_variant"),
        "camera_motion": metadata.get("camera_motion") or row.get("camera_motion"),
        "image_path": str(condition_dir / "image.jpg"),
        "prompt_path": str(condition_dir / "prompt.txt"),
        "poses_path": str(condition_dir / "poses.npy"),
        "intrinsics_path": str(condition_dir / "intrinsics.npy"),
        "metadata_path": str(condition_dir / "metadata.json"),
        "action_path": str(condition_dir / "action.npy"),
        "use_action": False,
        "has_camera_pose": (condition_dir / "poses.npy").exists(),
        "has_intrinsics": (condition_dir / "intrinsics.npy").exists(),
        "candidate_video_path": str(candidate_video),
        "video_path": str(candidate_video),
    }
    if (condition_dir / "depth.npy").exists():
        sample["depth_path"] = str(condition_dir / "depth.npy")
        sample["has_depth"] = True
    if (condition_dir / "id_mask.npy").exists():
        sample["id_path"] = str(condition_dir / "id_mask.npy")
        sample["has_id_mask"] = True
    return sample


def _iter_score_inputs(rollout_root: Path) -> list[dict[str, Any]]:
    summary = _safe_json(rollout_root / "rollout_summary.json")
    conditions = {Path(path).name: Path(path) for path in summary.get("condition_dirs", [])}
    selected_rows = {str(row.get("sample_id") or ""): row for row in (summary.get("selected", {}).get("rows") or []) if isinstance(row, dict)}
    rows: list[dict[str, Any]] = []
    for condition_id, condition_dir in sorted(conditions.items()):
        if not condition_dir.exists():
            continue
        selected = selected_rows.get(condition_id, {})
        gt = condition_dir / "target.mp4"
        if gt.exists():
            rows.append(_sample_from_condition(condition_dir, candidate_video=gt, label="clean_gt", row=selected))
        for label in ["base", "stageA_adapter"]:
            generated = rollout_root / label / condition_id / "generated.mp4"
            if generated.exists():
                rows.append(_sample_from_condition(condition_dir, candidate_video=generated, label=label, row=selected))
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollout_root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reward_version", default="v5")
    ap.add_argument("--use_raft", default="true")
    ap.add_argument("--use_dino", default="true")
    ap.add_argument("--confidence_weighted", default="true")
    ap.add_argument("--make_tables", default="true")
    ap.add_argument("--make_contact_sheets", default="false")
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    score_inputs = _iter_score_inputs(Path(args.rollout_root))
    scores = [score_sample(row) for row in score_inputs]
    for row, scored in zip(score_inputs, scores):
        scored["condition_id"] = row.get("condition_id")
        scored["eval_label"] = row.get("eval_label")
        scored["camera_variant"] = row.get("camera_variant")
        scored["candidate_video_path"] = row.get("candidate_video_path")
        scored["image_path"] = row.get("image_path")
        scored["poses_path"] = row.get("poses_path")
        scored["intrinsics_path"] = row.get("intrinsics_path")
        scored["metadata_path"] = row.get("metadata_path")
        scored["use_action"] = False

    write_jsonl(scores, out_dir / "scores.jsonl")

    by_label = defaultdict(list)
    for row in scores:
        by_label[str(row.get("eval_label"))].append(row)

    def mean(label: str, key: str) -> float | None:
        values = [float(row.get(key) or 0.0) for row in by_label.get(label, [])]
        return sum(values) / len(values) if values else None

    adapter_wins = 0
    comparable = 0
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in scores:
        grouped[str(row.get("condition_id"))][str(row.get("eval_label"))] = row
    for group in grouped.values():
        base = group.get("base")
        adapter = group.get("stageA_adapter")
        if not base or not adapter:
            continue
        comparable += 1
        if float(adapter.get("reward_total_confidence_weighted") or 0.0) > float(base.get("reward_total_confidence_weighted") or 0.0):
            adapter_wins += 1

    confidence_values = [float(row.get("reward_confidence_overall") or 0.0) for row in scores if row.get("eval_label") != "clean_gt"]
    real_backend_values = [float(row.get("reward_total_real_backend_confidence") or 0.0) for row in scores if row.get("eval_label") != "clean_gt"]
    summary = {
        "status": "scored",
        "rollout_root": args.rollout_root,
        "reward_version": args.reward_version,
        "score_count": len(scores),
        "label_distribution": dict(Counter(str(row.get("eval_label")) for row in scores)),
        "base_avg_reward_confidence_weighted": mean("base", "reward_total_confidence_weighted"),
        "adapter_avg_reward_confidence_weighted": mean("stageA_adapter", "reward_total_confidence_weighted"),
        "gt_avg_reward_confidence_weighted": mean("clean_gt", "reward_total_confidence_weighted"),
        "adapter_greater_than_base_count": adapter_wins,
        "adapter_base_comparable_count": comparable,
        "generated_reward_confidence_avg": sum(confidence_values) / len(confidence_values) if confidence_values else 0.0,
        "generated_real_backend_confidence_avg": sum(real_backend_values) / len(real_backend_values) if real_backend_values else 0.0,
        "trustworthy_for_pairs": bool(confidence_values and (sum(confidence_values) / len(confidence_values)) >= 0.5 and (sum(real_backend_values) / len(real_backend_values)) >= 0.5),
        "notes": [
            "This wrapper does not recalibrate reward weights.",
            "If generated-video backends are fallback-heavy, pair construction must stay blocked.",
        ],
    }
    write_json(summary, out_dir / "summary.json")

    if _bool_arg(args.make_tables):
        with (out_dir / "summary_table.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "condition_id",
                    "eval_label",
                    "template",
                    "camera_motion",
                    "reward_total_confidence_weighted",
                    "reward_confidence_overall",
                    "reward_total_real_backend_confidence",
                    "reward_provisional",
                    "candidate_video_path",
                ],
            )
            writer.writeheader()
            for row in scores:
                writer.writerow({key: row.get(key) for key in writer.fieldnames})
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
