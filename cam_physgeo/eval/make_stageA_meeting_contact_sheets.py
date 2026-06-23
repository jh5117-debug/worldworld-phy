"""Create GT/M0/M1/M2 contact sheets and a manual qualitative-score template."""
from __future__ import annotations

import argparse, csv, json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

LABELS = ["GT", "M0 Original Fast", "M1 StageA step800", "M2 StageA final883"]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _sample_id(row: dict[str, Any]) -> str:
    for key in ("sample_id", "clip_name", "id", "stem"):
        if row.get(key):
            return str(row[key])
    for key in ("target_mp4", "target_video", "video_path", "video", "clip_path"):
        if row.get(key):
            p = Path(str(row[key])); return p.parent.name if p.suffix else p.name
    raise ValueError(f"No sample id in row: {row.keys()}")


def _video_path(row: dict[str, Any]) -> Path:
    for key in ("target_mp4", "target_video", "reference_videopath", "video_path", "videopath", "video"):
        if row.get(key):
            return Path(str(row[key]))
    clip = Path(str(row.get("clip_path")))
    return clip if clip.suffix else clip / "video.mp4"


def _frame_at(path: Path, frac: float, *, width: int, height: int) -> np.ndarray:
    cap = cv2.VideoCapture(str(path)); count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    idx = max(0, min(count - 1, int(round((count - 1) * frac)))) if count else 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx); ok, frame = cap.read(); cap.release()
    if not ok:
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.putText(frame, "BROKEN", (20, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        return frame
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)


def _label(frame: np.ndarray, text: str) -> np.ndarray:
    out = frame.copy(); cv2.rectangle(out, (0, 0), (out.shape[1], 34), (0, 0, 0), -1)
    cv2.putText(out, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    return out


def _write_sheet(paths: list[Path], labels: list[str], out_path: Path, *, thumb_w: int, thumb_h: int) -> None:
    rows = []
    for path, label in zip(paths, labels):
        frames = [_frame_at(path, f, width=thumb_w, height=thumb_h) for f in (0.0, 0.25, 0.5, 0.75, 1.0)]
        frames[0] = _label(frames[0], label)
        rows.append(np.concatenate(frames, axis=1))
    out_path.parent.mkdir(parents=True, exist_ok=True); cv2.imwrite(str(out_path), np.concatenate(rows, axis=0))


def _load_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["sample_id"]: row for row in csv.DictReader(handle)}


def run(args: argparse.Namespace) -> None:
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rows = _read_jsonl(Path(args.selected_manifest))
    manifests = {"m0": _load_manifest(Path(args.m0_manifest)), "m1": _load_manifest(Path(args.m1_manifest)), "m2": _load_manifest(Path(args.m2_manifest))}
    score_rows = []
    for row in rows:
        sid = _sample_id(row); gt = _video_path(row); vids = [gt]; missing = []
        for key in ("m0", "m1", "m2"):
            item = manifests[key].get(sid)
            if not item:
                missing.append(key); vids.append(Path("/nonexistent")); continue
            vids.append(Path(item["generated_video"]))
        sheet = out / f"{sid}_gt_m0_m1_m2.jpg"
        _write_sheet(vids, LABELS, sheet, thumb_w=args.thumb_w, thumb_h=args.thumb_h)
        base = {"sample_id": sid, "template": row.get("template", ""), "camera_variant": row.get("camera_variant", row.get("camera_motion", "")), "sheet": str(sheet), "missing": ";".join(missing), "blind_mapping": "A=M0 Original Fast; B=M1 StageA step800; C=M2 StageA final883"}
        for model in "ABC":
            for metric in ["background_persistence", "camera_adherence", "foreground_identity", "object_deformation", "physical_event", "reobserve_consistency", "freeze", "visual_quality"]:
                base[f"{metric}_{model}"] = ""
        score_rows.append(base)
    fields = list(score_rows[0].keys()) if score_rows else []
    with (out / "qualitative_scores_template.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(score_rows)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected_manifest", required=True); p.add_argument("--m0_manifest", required=True); p.add_argument("--m1_manifest", required=True); p.add_argument("--m2_manifest", required=True); p.add_argument("--out", required=True)
    p.add_argument("--thumb_w", type=int, default=208); p.add_argument("--thumb_h", type=int, default=120)
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
