from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from cam_physgeo.utils.video import probe_video

INSPECT_FILES = [
    "README.md",
    "train/01_preference_pair.py",
    "train/dataset.py",
]


def _glob_existing(root: Path, patterns: list[str]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        found.extend(str(p.relative_to(root)) for p in sorted(root.glob(pattern)) if p.is_file())
    return found


def inspect_videogpa(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    result: dict[str, Any] = {
        "root": str(root),
        "exists": root.exists(),
        "remote": None,
        "commit": None,
        "files": {},
        "missing_files": [],
        "encode_scripts": [],
        "train_scripts": [],
        "config_files": [],
        "format_summary": {
            "preference_pair": "VideoGPA metadata is {'groups': [...]}; each group has group_id, prompt/text_prompt, input_image_path, original_video_path, and a videos list.",
            "encode": "Encode stage adds latent_path and condition_path to each video entry, using model-specific VAE/text/image encoders.",
            "train": "DPODataset reads groups, ranks videos by consistency_score (lower is better by default), loads latent_path/condition_path, then trains with DPO loss.",
            "camera_condition": "Camera poses/intrinsics are stored as extra_condition metadata and require a LingBot-specific adapter before training.",
        },
        "compatibility": {
            "lingbot_fast": "not directly compatible until Wan/LingBot condition adapter maps image/prefix/camera tensors into VideoGPA batch.",
            "current_scope": "inspect, data-format export, and encode-readiness smoke only; no training",
        },
    }
    if not root.exists():
        return result
    try:
        result["commit"] = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        pass
    try:
        result["remote"] = subprocess.check_output(["git", "-C", str(root), "remote", "-v"], text=True).strip()
    except Exception:
        pass
    result["encode_scripts"] = _glob_existing(root, ["train/*/02_encode.py", "train/**/02_encode.py", "scripts/*encode*.py"])
    result["train_scripts"] = _glob_existing(root, ["train/*/03_train.py", "train/**/03_train.py"])
    result["config_files"] = _glob_existing(root, ["configs/**/*.yaml", "configs/**/*.yml", "configs/**/*.json"])
    for rel in sorted(set(INSPECT_FILES + result["encode_scripts"][:4] + result["train_scripts"][:4])):
        path = root / rel
        if not path.exists():
            result["missing_files"].append(rel)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        result["files"][rel] = {
            "line_count": len(text.splitlines()),
            "mentions": {
                "prompt": "prompt" in text,
                "chosen": "chosen" in text or "winner" in text or "positive" in text,
                "rejected": "rejected" in text or "loser" in text or "negative" in text,
                "latent": "latent" in text.lower(),
                "wan": "wan" in text.lower(),
                "cogvideox": "cogvideox" in text.lower(),
                "camera": "camera" in text.lower() or "pose" in text.lower() or "intrinsic" in text.lower(),
            },
        }
    return result


def validate_videogpa_pairs(pairs_path: str | Path, limit_pairs: int = 0) -> dict[str, Any]:
    path = Path(pairs_path)
    result: dict[str, Any] = {"pairs": str(path), "exists": path.exists(), "groups": 0, "checked_groups": 0, "missing": [], "video_meta": [], "camera_condition_preserved": False, "can_read_pair_json": False}
    if not path.exists():
        return result
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups = payload.get("groups") or []
    result["can_read_pair_json"] = True
    result["groups"] = len(groups)
    for group in groups[: limit_pairs or len(groups)]:
        result["checked_groups"] += 1
        extra = group.get("extra_condition") or {}
        if extra.get("poses") and extra.get("intrinsics"):
            result["camera_condition_preserved"] = True
        if not group.get("prompt"):
            result["missing"].append({"group_id": group.get("group_id"), "field": "prompt"})
        videos = group.get("videos") or []
        if len(videos) < 2:
            result["missing"].append({"group_id": group.get("group_id"), "field": "videos<2"})
        for video in videos[:2]:
            vp = Path(str(video.get("video_path") or ""))
            meta = {"group_id": group.get("group_id"), "video_path": str(vp), "exists": vp.exists(), "generation_id": video.get("generation_id")}
            if vp.exists():
                meta.update(probe_video(vp))
            result["video_meta"].append(meta)
    return result


def encode_smoke(root: str | Path, pairs: str | Path, out: str | Path, limit_pairs: int = 2, gpu_ids: str = "") -> dict[str, Any]:
    inspect = inspect_videogpa(root)
    pair_check = validate_videogpa_pairs(pairs, limit_pairs=limit_pairs)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "videogpa_root": str(root),
        "gpu_ids": gpu_ids,
        "inspect": inspect,
        "pair_check": pair_check,
        "encode_attempted": False,
        "encoded": False,
        "latent_output": None,
        "camera_condition_preserved": pair_check.get("camera_condition_preserved", False),
        "blocking_reason": "Native VideoGPA encode scripts are model-specific and expect their own VAE/model condition format. LingBot-Fast camera-conditioned VAE/condition adapter is not implemented yet.",
        "next_adapter": "Implement LingBotFastVideoGPAAdapter.encode_video_to_latent and encode_condition, then call VideoGPA training code through a wrapper.",
    }
    (out / "encode_smoke_report.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# VideoGPA Encode Smoke Report",
        "",
        f"- Can read pair JSON: {pair_check.get('can_read_pair_json')}",
        f"- Groups: {pair_check.get('groups')}",
        f"- Checked groups: {pair_check.get('checked_groups')}",
        f"- Winner/loser videos inspected: {len(pair_check.get('video_meta') or [])}",
        f"- Camera condition preserved: {pair_check.get('camera_condition_preserved')}",
        f"- Encode attempted: {result['encode_attempted']}",
        f"- Encoded: {result['encoded']}",
        f"- Blocking reason: {result['blocking_reason']}",
        "",
        "No VideoGPA `03_train.py` command was launched.",
    ]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def write_plan(result: dict[str, Any], out: str | Path) -> None:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# VideoGPA Integration Plan",
        "",
        f"- repo path: `{result['root']}`",
        f"- exists: {result['exists']}",
        f"- commit: `{result.get('commit')}`",
        "",
        "## Answers",
        "1. Preference data is a `groups` JSON. Each group has `group_id`, `prompt`/`text_prompt`, optional `input_image_path`, `original_video_path`, `extra_condition`, and `videos`.",
        "2. Our `videogpa_pairs.json` is format-compatible for metadata reading; actual encode/train compatibility still needs a LingBot-specific latent/condition adapter.",
        "3. Encode input is a preference JSON plus video paths, prompts, model/VAE config, and output latent root.",
        "4. Encode output is metadata with `latent_path`/`condition_path` per video in VideoGPA's native backends.",
        "5. VideoGPA has image/video model paths for its supported backends, but not this LingBot-Fast camera-condition path out of the box.",
        "6. VideoGPA does not natively consume camera poses/intrinsics; we preserve them in `extra_condition`.",
        "7. The minimum adapter keeps VideoGPA pair ranking/loss semantics and adds LingBot condition collation outside the official repo.",
        "8. VideoGPA Wan/CogVideoX loaders cannot be assumed to load LingBot-Fast; LingBot-Fast uses project-local WanI2VFast and camera Plucker conditioning.",
        "9. A LingBotFastAdapter needs `load_model`, `encode_video_to_latent`, `encode_condition`, `prepare_winner_loser_batch`, and real `compute_dpo_energy_or_logprob`.",
        "10. Encode smoke currently validates pair JSON and video readability; it stops before native latent encoding because the LingBot VAE/condition adapter is missing.",
        "11. Do not modify official VideoGPA training scripts yet; use wrapper/adapter files under `cam_physgeo/dpo`.",
        "12. Formal training still needs Fast inference, rollout reward validation, encode smoke with real LingBot latents, and a non-fake energy/logprob adapter.",
        "",
        "## Discovered Scripts",
        f"- encode scripts: {result.get('encode_scripts')}",
        f"- train scripts: {result.get('train_scripts')}",
        "",
        "## Inspected Files",
    ]
    for rel, meta in sorted((result.get("files") or {}).items()):
        lines.append(f"- `{rel}`: {meta}")
    if result.get("missing_files"):
        lines.extend(["", "## Missing Files"])
        for rel in result["missing_files"]:
            lines.append(f"- `{rel}`")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--videogpa_root", required=True)
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--out", default="docs/videogpa_integration_plan.md")
    ap.add_argument("--pairs", default="")
    ap.add_argument("--encode-smoke", action="store_true")
    ap.add_argument("--limit_pairs", type=int, default=2)
    ap.add_argument("--gpu_ids", default="")
    args = ap.parse_args(argv)
    if args.encode_smoke:
        result = encode_smoke(args.videogpa_root, args.pairs, args.out, limit_pairs=args.limit_pairs, gpu_ids=args.gpu_ids)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    result = inspect_videogpa(args.videogpa_root)
    if args.inspect:
        write_plan(result, args.out)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
