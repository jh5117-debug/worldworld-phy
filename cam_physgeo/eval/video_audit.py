from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from cam_physgeo.utils.io import ensure_dir, read_jsonl

VIDEO_KEYS = ("candidate_video", "generated_video", "video_path", "target_video", "target_video_path", "video", "mp4")
SCORE_FIELDS = (
    "background_stability", "camera_following", "foreground_identity", "object_deformation",
    "physical_event", "reobserve", "freeze", "visual_quality",
)
FAILURE_TAGS = (
    "background_drift", "wrong_camera", "object_disappear", "object_duplicate", "object_deform",
    "color_change", "scene_replace", "event_missing", "penetration", "freeze", "blur",
    "flicker", "reobserve_failure",
)


def _first_path(row: dict[str, Any]) -> str:
    for key in VIDEO_KEYS:
        value = row.get(key)
        if value:
            return str(value)
    return ""


def _read_frames(path: str | Path, *, max_frames: int = 81) -> tuple[list[np.ndarray], str]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return [], "open_failed"
    frames: list[np.ndarray] = []
    while len(frames) < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        return [], "decode_failed"
    return frames, "ok"


def _uniform_indices(n: int, k: int) -> list[int]:
    if n <= 0:
        return []
    if n <= k:
        return list(range(n))
    return [int(round(x)) for x in np.linspace(0, n - 1, k)]


def _make_contact_sheet(frames: list[np.ndarray], out: Path, *, title: str, samples: int = 8) -> None:
    idx = _uniform_indices(len(frames), samples)
    thumbs = []
    for i in idx:
        fr = frames[i]
        h, w = fr.shape[:2]
        new_w = 240
        new_h = max(1, int(h * new_w / w))
        thumb = cv2.resize(fr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        label = f"f{i}"
        cv2.rectangle(thumb, (0, 0), (70, 22), (255, 255, 255), -1)
        cv2.putText(thumb, label, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    if not thumbs:
        return
    gap = 8
    pad = 42
    h = max(t.shape[0] for t in thumbs)
    w = sum(t.shape[1] for t in thumbs) + gap * (len(thumbs) - 1)
    canvas = np.full((h + pad, w, 3), 255, dtype=np.uint8)
    cv2.putText(canvas, title[:140], (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 1, cv2.LINE_AA)
    x = 0
    for t in thumbs:
        canvas[pad:pad + t.shape[0], x:x + t.shape[1]] = t
        x += t.shape[1] + gap
    ensure_dir(out.parent)
    cv2.imwrite(str(out), canvas)


def _heuristic_precheck(frames: list[np.ndarray]) -> dict[str, Any]:
    if len(frames) < 2:
        return {"freeze_rate": 1.0, "blur_laplacian": 0.0, "flicker_proxy": 0.0, "precheck_tags": "decode_too_short"}
    arr = np.stack([f.astype(np.float32) / 255.0 for f in frames], axis=0)
    diffs = np.mean(np.abs(arr[1:] - arr[:-1]), axis=(1, 2, 3))
    freeze_rate = float(np.mean(diffs < 0.002))
    grays = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    blur = float(np.mean([cv2.Laplacian(g, cv2.CV_64F).var() for g in grays]))
    means = np.array([float(g.mean()) / 255.0 for g in grays], dtype=np.float64)
    flicker = float(np.mean(np.abs(np.diff(means, n=2)))) if len(means) >= 3 else 0.0
    tags: list[str] = []
    if freeze_rate > 0.8:
        tags.append("freeze")
    if blur < 20.0:
        tags.append("blur")
    if flicker > 0.04:
        tags.append("flicker")
    return {"freeze_rate": freeze_rate, "blur_laplacian": blur, "flicker_proxy": flicker, "precheck_tags": ";".join(tags)}


def _load_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if args.candidate_manifest:
        manifest = Path(args.candidate_manifest)
        if manifest.suffix.lower() == ".csv":
            with manifest.open("r", newline="", encoding="utf-8") as f:
                manifest_rows = list(csv.DictReader(f))
        else:
            manifest_rows = list(read_jsonl(manifest))
        for row in manifest_rows:
            video = _first_path(row)
            if video:
                rows.append(dict(row, candidate_video=video))
    if args.video_dir:
        for p in sorted(Path(args.video_dir).rglob("*.mp4")):
            rows.append({"sample_id": p.stem, "candidate_video": str(p), "model": args.model_label})
    if args.max_videos:
        rows = rows[: args.max_videos]
    return rows


def run(args: argparse.Namespace) -> int:
    out_dir = ensure_dir(args.out_dir)
    sheet_dir = ensure_dir(out_dir / "contact_sheets")
    rows = _load_rows(args)
    audit_rows: list[dict[str, Any]] = []
    for row in rows:
        video = str(row.get("candidate_video") or "")
        sample_id = str(row.get("sample_id") or Path(video).stem)
        model = str(row.get("model") or args.model_label)
        frames, status = _read_frames(video, max_frames=args.max_frames)
        sheet = sheet_dir / f"{model}_{sample_id}.jpg"
        if frames:
            _make_contact_sheet(frames, sheet, title=f"{model} | {sample_id}", samples=args.sheet_frames)
        pre = _heuristic_precheck(frames) if frames else {"freeze_rate": "", "blur_laplacian": "", "flicker_proxy": "", "precheck_tags": "decode_failed"}
        failure_tags = [x for x in str(pre.get("precheck_tags", "")).split(";") if x]
        audit = {
            "sample_id": sample_id,
            "model": model,
            "checkpoint": row.get("checkpoint", ""),
            "template": row.get("template", ""),
            "camera_motion": row.get("camera_variant", row.get("camera_motion", "")),
            "video_path": video,
            "decode_status": status,
            "contact_sheet": str(sheet) if frames else "",
            "reviewer": "codex_precheck_needs_visual_review",
            "failure_tags": ";".join(t for t in failure_tags if t in FAILURE_TAGS),
            "written_reason": "Automatic precheck only; use contact sheet for final Codex visual audit.",
            **pre,
        }
        for field in SCORE_FIELDS:
            audit[field] = ""
        audit_rows.append(audit)
    ensure_dir(out_dir)
    csv_path = out_dir / "all_video_audit.csv"
    jsonl_path = out_dir / "all_video_audit.jsonl"
    keys: list[str] = []
    seen = set()
    for row in audit_rows:
        for key in row:
            if key not in seen:
                seen.add(key); keys.append(key)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys); writer.writeheader(); writer.writerows(audit_rows)
    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in audit_rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print({"videos": len(audit_rows), "csv": str(csv_path), "jsonl": str(jsonl_path), "contact_sheets": str(sheet_dir)})
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Create contact sheets and structured video audit templates.")
    ap.add_argument("--candidate_manifest", default="")
    ap.add_argument("--video_dir", default="")
    ap.add_argument("--model_label", default="candidate")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--max_videos", type=int, default=0)
    ap.add_argument("--max_frames", type=int, default=81)
    ap.add_argument("--sheet_frames", type=int, default=8)
    args = ap.parse_args(argv)
    if not args.candidate_manifest and not args.video_dir:
        raise SystemExit("Provide --candidate_manifest or --video_dir")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
