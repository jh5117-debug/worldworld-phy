from __future__ import annotations

import argparse
from pathlib import Path

from cam_physgeo.rewards.feature_backend import estimate_dino_video_features, find_dinov2_checkpoint
from cam_physgeo.rewards.total_reward import score_sample
from cam_physgeo.trd.feature_extractors import inspect_backend
from cam_physgeo.utils.io import load_yaml, read_jsonl, write_jsonl


def feature_backend_status(weights_root: str = "local_assets/weights", device: str = "cpu") -> dict:
    dino = inspect_backend("dinov2", weights_root, device)
    video = inspect_backend("vjepa2_or_videomae2", weights_root, device)
    return {
        "dinov2": dino,
        "vjepa2_or_videomae2": video,
        "actual_forward_available": find_dinov2_checkpoint(weights_root) is not None,
        "status": "dinov2_checkpoint_present" if find_dinov2_checkpoint(weights_root) is not None else "proxy_feature_fallback_active",
        "notes": [
            "DINO/V-JEPA hooks are present, but this smoke path does not run real frozen-feature forward unless a concrete loader is added.",
            "Reward scores record this status so rollout sensitivity is not overstated.",
        ],
    }


def _resolve_video_for_manifest_row(row: dict) -> str | None:
    video = row.get("candidate_video_path") or row.get("video_path")
    if video:
        return str(video)
    sample_id = row.get("sample_id")
    if sample_id:
        candidate = Path("local_assets/data/physion/processed/lingbot_cam_inputs/smoke") / str(sample_id) / "target.mp4"
        if candidate.exists():
            return str(candidate)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--config", default="")
    ap.add_argument("--out", default="local_assets/reports/smoke/reward_scores.jsonl")
    ap.add_argument("--source", default="", choices=["", "physion_official", "physion_movingcam"])
    ap.add_argument("--candidate_video_column", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--save_debug_vis", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--require_feature_backend", default="false")
    ap.add_argument("--weights_root", default="local_assets/weights")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--feature_backend", default="", choices=["", "dinov2"])
    a = ap.parse_args(argv)
    cfg = load_yaml(a.config) if a.config else {}
    weights = (cfg.get("weights") or cfg.get("reward_weights") or {}) if isinstance(cfg, dict) else {}
    require_backend = str(a.require_feature_backend).lower() in {"1", "true", "yes", "y"}
    backend = feature_backend_status(a.weights_root, a.device) if require_backend else None
    rows = []
    seen = 0
    for s in read_jsonl(a.manifest):
        if a.source and s.get("source") != a.source:
            continue
        if a.limit and seen >= a.limit:
            break
        if a.candidate_video_column and s.get(a.candidate_video_column):
            s = dict(s)
            s["candidate_video_path"] = s.get(a.candidate_video_column)
        if a.feature_backend == "dinov2":
            video = _resolve_video_for_manifest_row(s)
            s = dict(s)
            if video and not s.get("candidate_video_path") and not s.get("video_path"):
                s["candidate_video_path"] = video
            s["dino_feature_result"] = estimate_dino_video_features(
                video,
                weights_root=a.weights_root,
                device=a.device,
                allow_download_small=False,
                max_frames=4,
            )
        scored = score_sample(s, weights=weights)
        if backend is not None:
            scored["feature_backend_requirement"] = {
                "required": True,
                "met": bool(backend.get("actual_forward_available")),
                "status": backend,
            }
        rows.append(scored)
        seen += 1
    print({"scored": len(rows), "out": a.out, "source": a.source, "save_debug_vis": a.save_debug_vis, "dry_run": a.dry_run, "feature_backend_required": require_backend, "feature_backend_met": bool(backend and backend.get("actual_forward_available")) if backend else None})
    if not a.dry_run:
        write_jsonl(rows, a.out)
        if a.save_debug_vis:
            Path(a.out).with_suffix(".debug.md").write_text(
                "# Reward Debug Smoke\n\nDebug visualization hooks are enabled. Current feature status is recorded per row; real DINO/V-JEPA forward remains a TODO when `actual_forward_available=false`.\n",
                encoding="utf-8",
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
