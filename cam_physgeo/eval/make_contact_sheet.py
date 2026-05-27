from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Iterable

from cam_physgeo.utils.io import read_jsonl


def read_selected_video_frames(video_path: str | Path | None, indices: list[int], *, thumb_size=(160, 96)) -> list:
    if not video_path or not Path(str(video_path)).exists():
        return []
    try:
        import cv2  # type: ignore

        cap = cv2.VideoCapture(str(video_path))
        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if not ok:
                continue
            frame = cv2.resize(frame, thumb_size, interpolation=cv2.INTER_AREA)
            frames.append(frame)
        cap.release()
        return frames
    except Exception:
        return []


def read_selected_hdf5_frames(hdf5_path: str | Path | None, indices: list[int], *, thumb_size=(160, 96)) -> list:
    if not hdf5_path or not Path(str(hdf5_path)).exists():
        return []
    try:
        import cv2  # type: ignore

        from cam_physgeo.data.physion_hdf5_reader import read_physion_sample

        payload = read_physion_sample(hdf5_path, limit_frames=max(indices) + 1 if indices else 1)
        rgb = payload.get("rgb")
        if rgb is None:
            return []
        frames = []
        for idx in indices:
            if idx >= len(rgb):
                continue
            frame = rgb[idx]
            if frame.ndim == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frame = cv2.resize(frame, thumb_size, interpolation=cv2.INTER_AREA)
            frames.append(frame)
        return frames
    except Exception:
        return []


def make_sheet(sample: dict, frames: list, out_path: Path) -> bool:
    if not frames:
        return False
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        title = f"{sample.get('sample_id')} | {sample.get('template')} | {sample.get('camera_motion')}"
        h, w = frames[0].shape[:2]
        label_h = 42
        canvas = np.zeros((h + label_h, w * len(frames), 3), dtype=np.uint8)
        for i, frame in enumerate(frames):
            canvas[label_h:, i * w : (i + 1) * w] = frame
        cv2.putText(canvas, title[:140], (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (230, 230, 230), 1, cv2.LINE_AA)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        return bool(cv2.imwrite(str(out_path), canvas))
    except Exception:
        return False


def render_index(rows: list[dict], out_dir: Path) -> None:
    lines = [
        "<!doctype html><html><head><meta charset='utf-8'><title>Physion Data Preview</title>",
        "<style>body{font-family:sans-serif;margin:24px} img{max-width:100%;border:1px solid #ddd} .row{margin-bottom:24px}</style>",
        "</head><body><h1>Physion Data Preview</h1>",
    ]
    for row in rows:
        rel = html.escape(row["sheet"])
        lines.append("<div class='row'>")
        lines.append(f"<h3>{html.escape(row['sample_id'])}</h3>")
        lines.append(f"<p>{html.escape(row['template'])} | {html.escape(row['camera_motion'])}</p>")
        lines.append(f"<p><code>{html.escape(row['hdf5_path'] or '')}</code><br><code>{html.escape(row['video_path'] or '')}</code></p>")
        lines.append(f"<img src='{rel}' />")
        lines.append("</div>")
    lines.append("</body></html>")
    (out_dir / "index.html").write_text("\n".join(lines), encoding="utf-8")
    md = ["# Physion Data Preview", ""]
    for row in rows:
        md.append(f"## {row['sample_id']}")
        md.append(f"- template: {row['template']}")
        md.append(f"- camera_motion: {row['camera_motion']}")
        md.append(f"- hdf5_path: `{row['hdf5_path']}`")
        md.append(f"- video_path: `{row['video_path']}`")
        md.append(f"![{row['sample_id']}]({row['sheet']})")
        md.append("")
    (out_dir / "gallery.md").write_text("\n".join(md), encoding="utf-8")
    (out_dir / "index.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--source", default="", choices=["", "physion_official", "physion_movingcam"])
    ap.add_argument("--out_dir", default="local_assets/reports/contact_sheets/physion_data_preview")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--frames", nargs="+", type=int, default=[0, 10, 20, 30, 40, 50, 60, 70, 80])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    out_dir = Path(args.out_dir)
    rows = []
    seen = 0
    for sample in read_jsonl(args.manifest):
        if args.source and sample.get("source") != args.source:
            continue
        if args.limit and seen >= args.limit:
            break
        sample_id = str(sample.get("sample_id") or f"sample_{seen:04d}")
        sheet_name = f"{sample_id}.jpg"
        if not args.dry_run:
            frames = read_selected_video_frames(sample.get("video_path"), args.frames)
            if not frames:
                frames = read_selected_hdf5_frames(sample.get("hdf5_path"), args.frames)
            make_sheet(sample, frames, out_dir / sheet_name)
        rows.append(
            {
                "sample_id": sample_id,
                "template": str(sample.get("template") or "unknown"),
                "camera_motion": str(sample.get("camera_motion") or "unknown"),
                "hdf5_path": sample.get("hdf5_path"),
                "video_path": sample.get("video_path"),
                "sheet": sheet_name,
            }
        )
        seen += 1
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        render_index(rows, out_dir)
    print({"samples": seen, "out_dir": str(out_dir), "dry_run": args.dry_run})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
