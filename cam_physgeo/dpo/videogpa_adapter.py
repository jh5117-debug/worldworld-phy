from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


INSPECT_FILES = [
    "README.md",
    "train/01_preference_pair.py",
    "train/dataset.py",
]


def inspect_videogpa(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    result: dict[str, Any] = {
        "root": str(root),
        "exists": root.exists(),
        "remote": None,
        "commit": None,
        "files": {},
        "missing_files": [],
        "format_summary": {
            "preference_pair": "VideoGPA metadata is {'groups': [...]}; each group has group_id, prompt/text_prompt, input_image_path, original_video_path, and a videos list.",
            "encode": "Encode stage adds latent_path and condition_path to each video entry, using model-specific VAE/text/image encoders.",
            "train": "DPODataset reads groups, ranks videos by consistency_score (lower is better by default), loads latent_path/condition_path, then trains with DPO loss.",
            "camera_condition": "Camera poses/intrinsics are stored as extra_condition metadata and require a LingBot-specific adapter before training.",
        },
        "compatibility": {
            "lingbot_fast": "not directly compatible until Wan/LingBot condition adapter maps image/prefix/camera tensors into VideoGPA batch.",
            "current_scope": "data-format export and dry-run only",
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
    for rel in INSPECT_FILES:
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
            },
        }
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
        "1. Preference data is a `groups` JSON. Each group has `group_id`, `prompt`/`text_prompt`, optional `input_image_path`, `original_video_path`, and `videos`; each video stores `video_path`, `generation_id`, `consistency_score`, `motion_norm`, and later `latent_path`/`condition_path`.",
        "2. The encode stage needs video paths, prompts, image prompts for I2V/TI2V, model path, output JSON, latent root, GPU list, and frame count.",
        "3. The DPO train stage needs encoded latents and conditions, `metric_name`, `metric_mode`, `min_gap`, beta, LoRA config, and a compatible model backend.",
        "4. VideoGPA includes backend-specific train scripts; the inspected files indicate whether Wan/CogVideoX strings are present.",
        "5. LingBot-Fast is not assumed binary-compatible with VideoGPA Wan entrypoints until a LingBot camera-condition batch adapter is written.",
        "6. Required adapters: Physion pair exporter, LingBot cam-condition dataset adapter, latent encoder adapter, and frozen reference/policy loader adapter.",
        "7. Clean/corrupt Physion pairs export into one VideoGPA group per pair: clean GT has lower `consistency_score = 1 - R_total`, corrupted has higher score.",
        "8. Camera poses/intrinsics are preserved in group-level `extra_condition` and `metadata`; training support is a separate adapter step.",
        "9. If VideoGPA only supports text conditioning, extend the dataset batch with image/prefix/camera tensors while keeping the DPO loss path intact.",
        "10. Current dry-run checks repository shape and exported JSON readability; no `03_train.py` long training is launched.",
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
    args = ap.parse_args(argv)
    result = inspect_videogpa(args.videogpa_root)
    if args.inspect:
        write_plan(result, args.out)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
