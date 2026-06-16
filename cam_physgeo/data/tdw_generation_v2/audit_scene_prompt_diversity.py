"""Audit prompt and lightweight scene diversity for LingBot-format TDW manifests."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _sha(text: Any, n: int = 16) -> str:
    return hashlib.sha1(str(text).encode("utf-8", errors="ignore")).hexdigest()[:n]


def _read_prompt(row: dict[str, Any]) -> str:
    path = row.get("prompt_path")
    if path and Path(path).exists():
        try:
            return Path(path).read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            return ""
    return str(row.get("prompt") or row.get("caption") or "").strip()


def _first_frame_ahash(path: str | None) -> str | None:
    if not path or not Path(path).exists():
        return None
    cap = cv2.VideoCapture(str(path))
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (16, 16), interpolation=cv2.INTER_AREA)
    med = float(np.median(small))
    bits = (small > med).astype(np.uint8).reshape(-1)
    val = 0
    for bit in bits:
        val = (val << 1) | int(bit)
    return f"{val:064x}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--compute_first_frame_phash", default="true")
    ap.add_argument("--compute_prompt_hash", default="true")
    ap.add_argument("--compute_scene_hash", default="true")
    ap.add_argument("--check_template_distribution", default="true")
    ap.add_argument("--check_camera_distribution", default="true")
    args = ap.parse_args()

    rows = _read_jsonl(args.manifest)
    do_phash = str(args.compute_first_frame_phash).lower() in {"1", "true", "yes"}
    prompts: collections.Counter[str] = collections.Counter()
    prompt_hashes: collections.Counter[str] = collections.Counter()
    phashes: collections.Counter[str] = collections.Counter()
    scenes: collections.Counter[str] = collections.Counter()
    templates: collections.Counter[str] = collections.Counter()
    cameras: collections.Counter[str] = collections.Counter()
    samples: list[dict[str, Any]] = []
    missing_video = 0
    missing_prompt = 0

    for idx, row in enumerate(rows):
        template = row.get("template")
        camera = row.get("camera_variant")
        templates[str(template)] += 1
        cameras[str(camera)] += 1
        prompt = _read_prompt(row)
        if not prompt:
            missing_prompt += 1
        ph = _sha(prompt)
        prompts[prompt] += 1
        prompt_hashes[ph] += 1
        first = _first_frame_ahash(row.get("target_video_path")) if do_phash else None
        if first:
            phashes[first] += 1
        elif do_phash:
            missing_video += 1
        source = row.get("source_hdf5_path") or row.get("source_path") or row.get("hdf5_path") or ""
        seed = row.get("seed", "")
        sid = row.get("sample_id", "")
        scene_hash = _sha("|".join(map(str, [template, source, seed, first, sid])))
        scenes[scene_hash] += 1
        if idx < 10:
            samples.append({
                "sample_id": sid,
                "template": template,
                "camera_variant": camera,
                "seed": seed,
                "prompt_hash": ph,
                "first_frame_phash": first,
                "scene_hash": scene_hash,
                "prompt": prompt[:240],
            })

    top_prompt_count = prompts.most_common(1)[0][1] if prompts else 0
    summary = {
        "manifest": str(args.manifest),
        "count": len(rows),
        "missing_video": missing_video,
        "missing_prompt": missing_prompt,
        "template_distribution": dict(templates),
        "camera_distribution": dict(cameras),
        "unique_prompt_count": len(prompts),
        "prompt_hash_unique_count": len(prompt_hashes),
        "generic_prompt_ratio": top_prompt_count / len(rows) if rows else 0.0,
        "top_prompts": [{"count": count, "prompt": prompt[:400]} for prompt, count in prompts.most_common(5)],
        "first_frame_phash_unique_count": len(phashes),
        "first_frame_phash_duplicate_count": sum(count - 1 for count in phashes.values() if count > 1),
        "top_first_frame_phash_duplicates": phashes.most_common(10),
        "scene_hash_unique_count": len(scenes),
        "duplicate_scene_hash_count": sum(count - 1 for count in scenes.values() if count > 1),
        "top_scene_hash_duplicates": scenes.most_common(10),
        "sample_records": samples,
        "ready_for_warmup_data_integrity": missing_video == 0,
        "ready_for_warmup_prompt_quality": len(prompts) > 4,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2)[:5000])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
