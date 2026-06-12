from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from cam_physgeo.utils.io import read_json, write_json


DEFAULT_VARIANTS = [
    ("base", "Base"),
    ("stageA_adapter", "Stage A"),
    ("stageB_adapter", "Stage B"),
]


def _bool_arg(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in {"1", "true", "yes", "y", "on"}


def _parse_size(value: str) -> tuple[int, int]:
    text = str(value).lower().replace(",", "x")
    left, right = text.split("x", 1)
    return int(left), int(right)


def _variant_pairs(spec: str) -> list[tuple[str, str]]:
    if not spec:
        return list(DEFAULT_VARIANTS)
    pairs: list[tuple[str, str]] = []
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            dirname, label = item.split(":", 1)
            pairs.append((dirname.strip(), label.strip()))
        else:
            pairs.append((item, item))
    return pairs


def _ffmpeg_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _font_expr() -> str:
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        if Path(path).exists():
            return f":fontfile='{path}'"
    return ""


def _ffmpeg_executable() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # type: ignore

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            return str(exe)
    except Exception:
        pass
    return ""


def _condition_dirs(rollout_root: Path) -> list[Path]:
    conditions = rollout_root / "conditions"
    if conditions.exists():
        return sorted(path for path in conditions.iterdir() if path.is_dir())

    summary = read_json(rollout_root / "rollout_summary.json", default={}) or {}
    dirs = []
    for raw in summary.get("condition_dirs") or []:
        path = Path(str(raw))
        if not path.is_absolute():
            path = rollout_root / path
        if path.exists():
            dirs.append(path)
    return sorted(dirs)


def _safe_metadata(condition_dir: Path) -> dict[str, Any]:
    return read_json(condition_dir / "metadata.json", default={}) or {}


def _make_one(
    *,
    rollout_root: Path,
    condition_id: str,
    variants: list[tuple[str, str]],
    out_path: Path,
    panel_width: int,
    panel_height: int,
    fps: int,
    overwrite: bool,
) -> dict[str, Any]:
    videos = []
    missing = []
    for dirname, label in variants:
        video = rollout_root / dirname / condition_id / "generated.mp4"
        if video.exists():
            videos.append((video, label))
        else:
            missing.append({"variant": dirname, "label": label, "path": str(video)})

    row: dict[str, Any] = {
        "condition_id": condition_id,
        "out": str(out_path),
        "variant_count": len(videos),
        "missing": missing,
        "ok": False,
    }
    if len(videos) < 2:
        row["error"] = "need at least two rollout videos for comparison"
        return row
    if out_path.exists() and not overwrite:
        row["ok"] = True
        row["skipped_existing"] = True
        return row

    ffmpeg = _ffmpeg_executable()
    if not ffmpeg:
        row["error"] = "ffmpeg not found; install ffmpeg or imageio_ffmpeg"
        return _make_one_python(
            row=row,
            videos=videos,
            out_path=out_path,
            panel_width=panel_width,
            panel_height=panel_height,
            fps=fps,
            overwrite=overwrite,
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    inputs: list[str] = []
    filter_parts: list[str] = []
    labels = []
    font_expr = _font_expr()
    for idx, (video, label) in enumerate(videos):
        inputs.extend(["-i", str(video)])
        labels.append(f"[v{idx}]")
        label_text = _ffmpeg_text(label)
        filter_parts.append(
            f"[{idx}:v]"
            f"scale={panel_width}:{panel_height}:force_original_aspect_ratio=decrease,"
            f"pad={panel_width}:{panel_height}:(ow-iw)/2:(oh-ih)/2:black,"
            "setsar=1,"
            "drawbox=x=0:y=0:w=220:h=46:color=black@0.68:t=fill,"
            f"drawtext=text='{label_text}'{font_expr}:x=14:y=11:fontsize=25:fontcolor=white"
            f"[v{idx}]"
        )
    filter_complex = ";".join(filter_parts) + ";" + "".join(labels) + f"hstack=inputs={len(labels)}[outv]"
    cmd = [
        ffmpeg,
        "-y" if overwrite else "-n",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-an",
        "-r",
        str(fps),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    row.update(
        {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stderr_tail": proc.stderr[-3000:],
            "stdout_tail": proc.stdout[-1000:],
            "ok": proc.returncode == 0 and out_path.exists(),
            "size_bytes": out_path.stat().st_size if out_path.exists() else 0,
        }
    )
    if not row["ok"]:
        fallback = _make_one_python(
            row=row,
            videos=videos,
            out_path=out_path,
            panel_width=panel_width,
            panel_height=panel_height,
            fps=fps,
            overwrite=True,
        )
        fallback["ffmpeg_error"] = row.get("stderr_tail")
        return fallback
    return row


def _make_one_python(
    *,
    row: dict[str, Any],
    videos: list[tuple[Path, str]],
    out_path: Path,
    panel_width: int,
    panel_height: int,
    fps: int,
    overwrite: bool,
) -> dict[str, Any]:
    fallback = dict(row)
    fallback["backend"] = "python_imageio_pillow"
    if out_path.exists():
        if overwrite:
            out_path.unlink()
        else:
            fallback["ok"] = True
            fallback["skipped_existing"] = True
            return fallback
    try:
        import numpy as np
        import imageio.v2 as imageio  # type: ignore
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:
        fallback.update({"ok": False, "error": f"python video fallback imports failed: {exc!r}"})
        return fallback

    font = None
    for font_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        try:
            if Path(font_path).exists():
                font = ImageFont.truetype(font_path, 26)
                break
        except Exception:
            font = None
    if font is None:
        font = ImageFont.load_default()

    readers = []
    writer = None
    frame_count = 0
    try:
        readers = [imageio.get_reader(str(video)) for video, _label in videos]
        writer = imageio.get_writer(str(out_path), fps=fps, macro_block_size=1)
        while True:
            frames = []
            for reader in readers:
                try:
                    frame = reader.get_next_data()
                except (IndexError, StopIteration, RuntimeError):
                    frame = None
                if frame is None:
                    raise StopIteration
                frames.append(frame)
            panels = []
            for frame, (_video, label) in zip(frames, videos):
                image = Image.fromarray(np.asarray(frame)[..., :3]).convert("RGB")
                image.thumbnail((panel_width, panel_height), Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", (panel_width, panel_height), "black")
                canvas.paste(image, ((panel_width - image.width) // 2, (panel_height - image.height) // 2))
                draw = ImageDraw.Draw(canvas, "RGBA")
                draw.rectangle((0, 0, 220, 48), fill=(0, 0, 0, 180))
                draw.text((14, 10), label, fill=(255, 255, 255), font=font)
                panels.append(canvas)
            merged = Image.new("RGB", (panel_width * len(panels), panel_height), "black")
            for idx, panel in enumerate(panels):
                merged.paste(panel, (idx * panel_width, 0))
            writer.append_data(np.asarray(merged))
            frame_count += 1
    except StopIteration:
        pass
    except Exception as exc:
        fallback.update({"ok": False, "error": f"python video fallback failed: {exc!r}", "frames_written": frame_count})
        return fallback
    finally:
        for reader in readers:
            try:
                reader.close()
            except Exception:
                pass
        if writer is not None:
            try:
                writer.close()
            except Exception:
                pass

    fallback.update(
        {
            "ok": frame_count > 0 and out_path.exists(),
            "returncode": 0 if frame_count > 0 and out_path.exists() else 2,
            "frames_written": frame_count,
            "size_bytes": out_path.stat().st_size if out_path.exists() else 0,
            "error": "" if frame_count > 0 and out_path.exists() else "no frames written",
        }
    )
    return fallback


def _write_gallery(rows: list[dict[str, Any]], out_dir: Path, rollout_root: Path) -> None:
    md_lines = [
        "# Rollout Comparison Videos",
        "",
        f"Rollout root: `{rollout_root}`",
        "",
        "| condition | comparison video | variants | status |",
        "| --- | --- | --- | --- |",
    ]
    html_lines = [
        "<!doctype html>",
        "<html><head><meta charset='utf-8'><title>Rollout Comparison Videos</title>",
        "<style>body{font-family:Arial,sans-serif;margin:24px;background:#111;color:#eee}"
        ".item{margin:0 0 32px 0}.meta{font-size:13px;color:#bbb;margin:6px 0 10px}"
        "video{max-width:100%;height:auto;border:1px solid #333;background:#000}</style>",
        "</head><body>",
        "<h1>Rollout Comparison Videos</h1>",
        f"<p>Rollout root: <code>{html.escape(str(rollout_root))}</code></p>",
    ]
    for row in rows:
        rel = Path(row["out"]).name
        variants = row.get("variant_count")
        status = "ok" if row.get("ok") else f"failed: {row.get('error', '')}"
        md_lines.append(f"| `{row.get('condition_id')}` | `{out_dir / rel}` | {variants} | {status} |")
        if row.get("ok"):
            html_lines.extend(
                [
                    "<div class='item'>",
                    f"<h2>{html.escape(str(row.get('condition_id')))}</h2>",
                    f"<div class='meta'>variants: {variants}</div>",
                    f"<video controls preload='metadata' src='{html.escape(rel)}'></video>",
                    "</div>",
                ]
            )
    html_lines.extend(["</body></html>"])
    (out_dir / "comparison_index.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    (out_dir / "video_gallery.html").write_text("\n".join(html_lines) + "\n", encoding="utf-8")


def build_comparison_videos(
    *,
    rollout_root: Path,
    out_subdir: str = "comparison_videos",
    variants: list[tuple[str, str]] | None = None,
    panel_width: int = 832,
    panel_height: int = 480,
    fps: int = 16,
    overwrite: bool = False,
) -> dict[str, Any]:
    rollout_root = rollout_root.resolve()
    out_dir = rollout_root / out_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    variants = variants or list(DEFAULT_VARIANTS)
    rows: list[dict[str, Any]] = []
    for condition_dir in _condition_dirs(rollout_root):
        condition_id = condition_dir.name
        out_path = out_dir / f"{condition_id}__comparison.mp4"
        row = _make_one(
            rollout_root=rollout_root,
            condition_id=condition_id,
            variants=variants,
            out_path=out_path,
            panel_width=panel_width,
            panel_height=panel_height,
            fps=fps,
            overwrite=overwrite,
        )
        row["metadata"] = _safe_metadata(condition_dir)
        rows.append(row)
    _write_gallery(rows, out_dir, rollout_root)
    summary = {
        "status": "passed" if rows and all(row.get("ok") for row in rows) else "partial_or_failed",
        "rollout_root": str(rollout_root),
        "out_dir": str(out_dir),
        "variant_labels": [{"dir": dirname, "label": label} for dirname, label in variants],
        "condition_count": len(rows),
        "ok_count": sum(1 for row in rows if row.get("ok")),
        "fail_count": sum(1 for row in rows if not row.get("ok")),
        "rows": rows,
    }
    write_json(summary, out_dir / "comparison_summary.json")
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollout_root", required=True)
    ap.add_argument("--out_subdir", default="comparison_videos")
    ap.add_argument("--variants", default="base:Base,stageA_adapter:Stage A,stageB_adapter:Stage B")
    ap.add_argument("--panel_size", default="832x480")
    ap.add_argument("--fps", type=int, default=16)
    ap.add_argument("--overwrite", default="false")
    args = ap.parse_args(argv)

    panel_width, panel_height = _parse_size(args.panel_size)
    summary = build_comparison_videos(
        rollout_root=Path(args.rollout_root),
        out_subdir=args.out_subdir,
        variants=_variant_pairs(args.variants),
        panel_width=panel_width,
        panel_height=panel_height,
        fps=int(args.fps),
        overwrite=_bool_arg(args.overwrite),
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary.get("fail_count") == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
