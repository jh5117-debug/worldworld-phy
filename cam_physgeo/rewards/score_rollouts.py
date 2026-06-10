from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.utils.io import read_json, write_json, write_jsonl
from cam_physgeo.rewards.feature_backend import estimate_dino_video_features
from cam_physgeo.rewards.flow_backend import estimate_flow


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


def _runtime_device() -> str:
    try:
        import torch  # type: ignore

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _attach_backends(row: dict[str, Any], *, use_raft: bool, use_dino: bool, device: str) -> dict[str, Any]:
    enriched = dict(row)
    video = row.get("candidate_video_path") or row.get("video_path")
    if use_raft and video:
        enriched["flow_backend_result"] = estimate_flow(
            video,
            resolution=(256, 448),
            max_frames=4,
            backend="auto",
            weights_root="local_assets/weights/optical_flow",
            device=device,
        )
    if use_dino and video:
        enriched["dino_feature_result"] = estimate_dino_video_features(
            video,
            weights_root="local_assets/weights",
            device=device,
            allow_download_small=False,
            max_frames=4,
        )
    return enriched


def _coverage(scores: list[dict[str, Any]]) -> dict[str, Any]:
    by_label: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "components": Counter(), "real": Counter(), "fallback": Counter(), "missing": Counter()})
    for row in scores:
        label = str(row.get("eval_label") or "unknown")
        by_label[label]["count"] += 1
        for name, part in (row.get("components") or {}).items():
            backend_conf = str(part.get("backend_confidence") or "unknown")
            by_label[label]["components"][name] += 1
            if backend_conf in {"real", "fallback", "missing"}:
                by_label[label][backend_conf][name] += 1
    return {
        label: {
            "count": data["count"],
            "components": dict(data["components"]),
            "real_components": dict(data["real"]),
            "fallback_components": dict(data["fallback"]),
            "missing_components": dict(data["missing"]),
        }
        for label, data in by_label.items()
    }


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
    ap.add_argument("--score_gt", default="true")
    ap.add_argument("--score_base", default="true")
    ap.add_argument("--score_adapter", default="true")
    ap.add_argument("--use_action", default="false")
    ap.add_argument("--local_files_only", default="true")
    ap.add_argument("--device", default="auto")
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    score_inputs = _iter_score_inputs(Path(args.rollout_root))
    allowed_labels = set()
    if _bool_arg(args.score_gt):
        allowed_labels.add("clean_gt")
    if _bool_arg(args.score_base):
        allowed_labels.add("base")
    if _bool_arg(args.score_adapter):
        allowed_labels.add("stageA_adapter")
    score_inputs = [row for row in score_inputs if str(row.get("eval_label")) in allowed_labels]
    device = _runtime_device() if str(args.device).lower() == "auto" else str(args.device)
    enriched_inputs = [
        _attach_backends(row, use_raft=_bool_arg(args.use_raft), use_dino=_bool_arg(args.use_dino), device=device)
        for row in score_inputs
    ]
    scores = [score_sample(row) for row in enriched_inputs]
    for row, scored in zip(enriched_inputs, scores):
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
        "device": device,
        "use_raft": _bool_arg(args.use_raft),
        "use_dino": _bool_arg(args.use_dino),
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
        "backend_coverage": _coverage(scores),
        "notes": [
            "This wrapper does not recalibrate reward weights.",
            "If generated-video backends are fallback-heavy, pair construction must stay blocked.",
        ],
    }
    write_json(summary, out_dir / "summary.json")
    write_json(summary.get("backend_coverage") or {}, out_dir / "reward_backend_coverage.json")

    if _bool_arg(args.make_tables):
        fieldnames=[
            "condition_id",
            "eval_label",
            "template",
            "camera_motion",
            "camera_variant",
            "reward_total_confidence_weighted",
            "reward_total_real_backend_only",
            "reward_total_real_backend_confidence",
            "R_flow_dino_only",
            "R_flow_dino_confidence",
            "reward_confidence_overall",
            "reward_provisional",
            "P_freeze",
            "candidate_video_path",
        ]
        for table_name in ["summary_table.csv", "reward_summary.csv"]:
            with (out_dir / table_name).open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for row in scores:
                    writer.writerow({key: row.get(key) for key in fieldnames})
        with (out_dir / "reward_breakdown_by_condition.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "condition_id",
                    "eval_label",
                    "R_bg",
                    "R_cam",
                    "R_fg",
                    "R_phys",
                    "R_reobs",
                    "R_quality",
                    "P_freeze",
                    "reward_total_confidence_weighted",
                    "reward_total_real_backend_only",
                    "R_flow_dino_only",
                ],
            )
            writer.writeheader()
            for row in scores:
                comps = row.get("components") or {}
                writer.writerow(
                    {
                        "condition_id": row.get("condition_id"),
                        "eval_label": row.get("eval_label"),
                        "R_bg": (comps.get("bg") or {}).get("score"),
                        "R_cam": (comps.get("cam") or {}).get("score"),
                        "R_fg": (comps.get("fg") or {}).get("score"),
                        "R_phys": (comps.get("phys") or {}).get("score"),
                        "R_reobs": (comps.get("reobs") or {}).get("score"),
                        "R_quality": (comps.get("quality") or {}).get("score"),
                        "P_freeze": row.get("P_freeze"),
                        "reward_total_confidence_weighted": row.get("reward_total_confidence_weighted"),
                        "reward_total_real_backend_only": row.get("reward_total_real_backend_only"),
                        "R_flow_dino_only": row.get("R_flow_dino_only"),
                    }
                )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
