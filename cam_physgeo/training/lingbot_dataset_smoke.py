from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_video(path: str | Path, *, max_frames: int, resolution: str, probe_decode: bool) -> tuple[np.ndarray | None, dict[str, Any]]:
    if not probe_decode:
        return None, {"decoded": False}
    h, w = [int(x) for x in resolution.lower().split("x", 1)]
    start = time.time()
    frames: list[np.ndarray] = []
    error = None
    try:
        import cv2  # type: ignore

        cap = cv2.VideoCapture(str(path))
        while len(frames) < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)
            frames.append(frame)
        cap.release()
    except Exception as exc:
        error = repr(exc)
    if not frames:
        return None, {"decoded": False, "error": error or "no frames", "seconds": time.time() - start}
    while len(frames) < max_frames:
        frames.append(frames[-1].copy())
    arr = np.stack(frames[:max_frames]).astype("float32") / 255.0
    return arr, {"decoded": True, "frames": int(arr.shape[0]), "shape": list(arr.shape), "seconds": time.time() - start}


def _load_item(row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    image = np.asarray(Image.open(row["image_path"]).convert("RGB"))
    poses = np.load(row["poses_path"])
    intrinsics = np.load(row["intrinsics_path"])
    action = np.load(row["action_path"])
    metadata = _read_json(row["metadata_path"])
    prompt = Path(row["prompt_path"]).read_text(encoding="utf-8", errors="ignore").strip()
    video, video_probe = _read_video(
        row["target_video_path"],
        max_frames=args.num_frames,
        resolution=args.resolution,
        probe_decode=args.probe_video_decode,
    )
    return {
        "sample_id": row["sample_id"],
        "template": row.get("template"),
        "camera_variant": row.get("camera_variant"),
        "image": image,
        "video": video,
        "poses": poses,
        "intrinsics": intrinsics,
        "action": action,
        "prompt": prompt,
        "metadata_use_action": metadata.get("use_action"),
        "video_probe": video_probe,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_manifest", required=True)
    parser.add_argument("--val_manifest", required=True)
    parser.add_argument("--test_manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--num_workers", type=int, default=0)
    parser.add_argument("--num_frames", type=int, default=81)
    parser.add_argument("--resolution", default="480x832")
    parser.add_argument("--use_action", default="false")
    parser.add_argument("--max_batches", type=int, default=3)
    parser.add_argument("--probe_video_decode", action="store_true")
    parser.add_argument("--probe_camera_shapes", action="store_true")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifests = {
        "train": _load_jsonl(Path(args.train_manifest)),
        "val": _load_jsonl(Path(args.val_manifest)),
        "test": _load_jsonl(Path(args.test_manifest)),
    }
    batches: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for split, rows in manifests.items():
        split_rows = rows[: args.batch_size * args.max_batches]
        for batch_idx in range(0, len(split_rows), args.batch_size):
            raw_batch = split_rows[batch_idx : batch_idx + args.batch_size]
            items = []
            for row in raw_batch:
                try:
                    items.append(_load_item(row, args))
                except Exception as exc:
                    failures.append({"split": split, "sample_id": row.get("sample_id"), "error": repr(exc)})
            if not items:
                continue
            batch = {
                "split": split,
                "batch_index": len(batches),
                "batch_size": len(items),
                "keys": sorted(k for k in items[0].keys() if k not in {"image", "video", "poses", "intrinsics", "action"}),
                "image_shape": [len(items)] + list(items[0]["image"].shape),
                "video_shape": [len(items)] + list(items[0]["video"].shape) if items[0]["video"] is not None else None,
                "poses_shape": [len(items)] + list(items[0]["poses"].shape),
                "intrinsics_shape": [len(items)] + list(items[0]["intrinsics"].shape),
                "action_shape": [len(items)] + list(items[0]["action"].shape),
                "action_norms": [float(np.linalg.norm(item["action"])) for item in items],
                "metadata_use_action": [item["metadata_use_action"] for item in items],
                "prompt_examples": [item["prompt"][:160] for item in items[:2]],
                "template_distribution": dict(Counter(item["template"] for item in items)),
                "camera_distribution": dict(Counter(item["camera_variant"] for item in items)),
                "video_decode": [item["video_probe"] for item in items],
            }
            batches.append(batch)
    result = {
        "manifests": {split: len(rows) for split, rows in manifests.items()},
        "batch_size": args.batch_size,
        "max_batches": args.max_batches,
        "num_workers": args.num_workers,
        "use_action_requested": args.use_action,
        "batches": batches,
        "failures": failures,
        "passed": not failures and bool(batches),
    }
    (out / "dataloader_smoke_report.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    (out / "README.md").write_text(
        "# LingBot dataset smoke\n\n"
        f"Passed: {result['passed']}\n\n"
        f"Batches checked: {len(batches)}\n\n"
        f"Failures: {len(failures)}\n"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
