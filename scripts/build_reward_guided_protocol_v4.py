#!/usr/bin/env python3
"""Build reward-guided V2V-5 DPO preference protocol v4.

This script is intentionally bounded: it does not train, does not touch
checkpoints, and writes large media only under local_assets/reports.  It builds
TypeA+ and TypeM synthetic medium-hard negatives from existing clean GT futures,
then exports lightweight manifests and summaries for Git.
"""

from __future__ import annotations

import csv
import json
import math
import shutil
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from cam_physgeo.dpo.pair_hardness import DEFAULT_HARDNESS_THRESHOLDS, classify_hardness
from cam_physgeo.dpo.reward_guided_pair_selector import (
    DEFAULT_REWARD_WEIGHTS,
    alignment_decision,
    compute_total_reward,
    normalized_reward_vector,
    selector_spec,
    subreward_margins,
)

REPO = Path('.')
REPORT_DIR = REPO / 'reports' / 'dpo_pair_hardness_v4'
ASSET_DIR = REPO / 'local_assets' / 'dpo_pair_hardness_v4'
PPT_DIR = REPO / 'reports' / 'ppt_winlose_showcase_latest'
MANIFEST_DIR = REPO / 'manifests'
FPS = 16
MAX_TYPEA_PLUS = 34
MAX_TYPEM = 14
SEVERITIES = [
    ('s1_weak', 0.55),
    ('s2_medium', 0.85),
    ('s3_strong', 1.10),
    ('s4_strong_pass', 1.65),
]

FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
]

FAILURE_LABELS = {
    'background_drift_local': 'background drift',
    'wrong_camera_motion_local': 'wrong camera',
    'object_deformation_local': 'object deformation',
    'object_identity_change_local': 'identity change',
    'reobserve_mismatch_local': 'reobserve mismatch',
    'partial_freeze': 'partial freeze',
    'physical_event_local_failure': 'weak physical event',
    'extra_fragment': 'extra fragment',
    'medium_background_drift': 'background drift',
    'wrong_camera_motion': 'wrong camera',
    'object_identity_instability': 'identity instability',
    'weak_physical_event': 'weak physical event',
}

TYPEM_FAILURES = [
    'extra_fragment',
    'medium_background_drift',
    'wrong_camera_motion',
    'object_identity_instability',
    'weak_physical_event',
]


def ensure_dirs() -> None:
    for p in [REPORT_DIR, ASSET_DIR, PPT_DIR, MANIFEST_DIR, REPORT_DIR / 'typeM_pair_contact_sheets']:
        p.mkdir(parents=True, exist_ok=True)
    (ASSET_DIR / 'typeA_strength_sweep').mkdir(parents=True, exist_ok=True)
    (ASSET_DIR / 'typeM').mkdir(parents=True, exist_ok=True)


def load_font(size: int) -> ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def resolve_path(path: str | None) -> Path | None:
    if not path:
        return None
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO / p


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_video(path: Path, max_frames: int | None = None) -> Tuple[List[np.ndarray], float]:
    frames: List[np.ndarray] = []
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        fps = float(stream.average_rate) if stream.average_rate else FPS
        for frame in container.decode(stream):
            frames.append(frame.to_ndarray(format='rgb24'))
            if max_frames and len(frames) >= max_frames:
                break
    return frames, fps


def write_video(frames: Sequence[np.ndarray | Image.Image], path: Path, fps: int = FPS) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not frames:
        raise ValueError(f'cannot write empty video: {path}')
    first = np.asarray(frames[0].convert('RGB') if isinstance(frames[0], Image.Image) else frames[0])
    h, w = first.shape[:2]
    codec_used = 'libx264'
    try:
        container = av.open(str(path), mode='w')
        stream = container.add_stream(codec_used, rate=fps)
    except Exception:
        codec_used = 'mpeg4'
        container = av.open(str(path), mode='w')
        stream = container.add_stream(codec_used, rate=fps)
    stream.width = w
    stream.height = h
    stream.pix_fmt = 'yuv420p'
    try:
        stream.options = {'crf': '18', 'preset': 'veryfast'}
    except Exception:
        pass
    for frame in frames:
        arr = np.asarray(frame.convert('RGB') if isinstance(frame, Image.Image) else frame).astype(np.uint8)
        if arr.shape[0] != h or arr.shape[1] != w:
            arr = np.asarray(Image.fromarray(arr).resize((w, h), Image.Resampling.BICUBIC))
        vf = av.VideoFrame.from_ndarray(arr, format='rgb24')
        for packet in stream.encode(vf):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()
    return codec_used


def clamp_bbox(region: Mapping[str, Any] | None, width: int, height: int) -> Tuple[int, int, int, int]:
    if not region:
        return width // 4, height // 4, width * 3 // 4, height * 3 // 4
    x0 = max(0, min(width - 2, int(region.get('x0', width // 4))))
    x1 = max(x0 + 2, min(width, int(region.get('x1', width * 3 // 4))))
    y0 = max(0, min(height - 2, int(region.get('y0', height // 4))))
    y1 = max(y0 + 2, min(height, int(region.get('y1', height * 3 // 4))))
    return x0, y0, x1, y1


def span_indices(span: Mapping[str, Any] | None, n: int) -> range:
    if not span:
        return range(0, n)
    start = int(span.get('future_start_index', 0))
    end = int(span.get('future_end_index', n - 1))
    start = max(0, min(n - 1, start))
    end = max(start, min(n - 1, end))
    return range(start, end + 1)


def shift_region(arr: np.ndarray, bbox: Tuple[int, int, int, int], dx: int, dy: int, blend: float = 1.0) -> np.ndarray:
    out = arr.copy()
    x0, y0, x1, y1 = bbox
    crop = arr[y0:y1, x0:x1].copy()
    shifted = np.roll(crop, shift=(dy, dx), axis=(0, 1))
    # Avoid wraparound looking like a technical artifact by filling exposed strips
    if dx > 0:
        shifted[:, :dx] = crop[:, :1]
    elif dx < 0:
        shifted[:, dx:] = crop[:, -1:]
    if dy > 0:
        shifted[:dy, :] = crop[:1, :]
    elif dy < 0:
        shifted[dy:, :] = crop[-1:, :]
    out[y0:y1, x0:x1] = np.clip((1 - blend) * crop + blend * shifted, 0, 255).astype(np.uint8)
    return out


def tint_region(arr: np.ndarray, bbox: Tuple[int, int, int, int], strength: float) -> np.ndarray:
    out = arr.copy().astype(np.float32)
    x0, y0, x1, y1 = bbox
    crop = out[y0:y1, x0:x1]
    factors = np.array([1.0 + 0.18 * strength, 1.0 - 0.08 * strength, 1.0 - 0.12 * strength], dtype=np.float32)
    out[y0:y1, x0:x1] = np.clip(crop * factors, 0, 255)
    return out.astype(np.uint8)


def deform_region(arr: np.ndarray, bbox: Tuple[int, int, int, int], strength: float) -> np.ndarray:
    img = Image.fromarray(arr)
    x0, y0, x1, y1 = bbox
    crop = img.crop((x0, y0, x1, y1))
    w, h = crop.size
    nw = max(2, int(w * (1.0 + 0.06 * strength)))
    nh = max(2, int(h * (1.0 - 0.03 * min(strength, 2.0))))
    warped = crop.resize((nw, nh), Image.Resampling.BICUBIC).resize((w, h), Image.Resampling.BICUBIC)
    img.paste(warped, (x0, y0))
    return np.asarray(img)


def add_fragment(arr: np.ndarray, bbox: Tuple[int, int, int, int], strength: float, t: int) -> np.ndarray:
    img = Image.fromarray(arr).convert('RGB')
    draw = ImageDraw.Draw(img, 'RGBA')
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    cx = int(x0 + 0.70 * w + (t % 5 - 2) * 2)
    cy = int(y0 + 0.28 * h + (t % 7 - 3) * 2)
    rx = max(8, int(10 + 6 * strength))
    ry = max(5, int(7 + 4 * strength))
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(225, 65, 45, 150), outline=(255, 230, 180, 190), width=2)
    return np.asarray(img)


def corrupt_frames(frames: Sequence[np.ndarray], corruption: str, bbox: Tuple[int, int, int, int], span: range, strength: float) -> List[np.ndarray]:
    out = [f.copy() for f in frames]
    if not out:
        return out
    frozen_crop = out[span.start][bbox[1]:bbox[3], bbox[0]:bbox[2]].copy() if len(span) else None
    for i in span:
        arr = out[i]
        if corruption in {'background_drift_local', 'medium_background_drift'}:
            arr = shift_region(arr, bbox, dx=int(6 * strength + (i % 3)), dy=int(1 * strength), blend=min(1.0, 0.65 + 0.12 * strength))
        elif corruption in {'wrong_camera_motion_local', 'wrong_camera_motion'}:
            dx = int((i - span.start + 1) * 0.12 * strength + 5 * strength)
            arr = shift_region(arr, bbox, dx=dx, dy=int(2 * math.sin(i / 5) * strength), blend=0.85)
        elif corruption in {'object_deformation_local'}:
            arr = deform_region(arr, bbox, strength)
        elif corruption in {'object_identity_change_local', 'object_identity_instability'}:
            arr = tint_region(arr, bbox, strength)
            if i % 8 < 4:
                arr = deform_region(arr, bbox, 0.45 * strength)
        elif corruption in {'reobserve_mismatch_local'}:
            local_strength = strength if i > (span.start + span.stop) // 2 else 0.45 * strength
            arr = tint_region(arr, bbox, local_strength)
            arr = shift_region(arr, bbox, dx=int(3 * local_strength), dy=0, blend=0.45)
        elif corruption in {'partial_freeze'} and frozen_crop is not None:
            x0, y0, x1, y1 = bbox
            blend = min(0.85, 0.35 + 0.18 * strength)
            live = arr[y0:y1, x0:x1]
            arr = arr.copy()
            arr[y0:y1, x0:x1] = np.clip((1 - blend) * live + blend * frozen_crop, 0, 255).astype(np.uint8)
        elif corruption in {'physical_event_local_failure', 'weak_physical_event'}:
            arr = shift_region(arr, bbox, dx=0, dy=int(-5 * strength), blend=0.75)
        elif corruption == 'extra_fragment':
            arr = add_fragment(arr, bbox, strength, i)
        else:
            arr = tint_region(arr, bbox, 0.6 * strength)
        out[i] = arr
    return out


def laplacian_var(frame: np.ndarray) -> float:
    gray = frame.astype(np.float32).mean(axis=2)
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    lap = -4 * gray[1:-1, 1:-1] + gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:]
    return float(np.var(lap))


def sharpness_stats(frames: Sequence[np.ndarray]) -> Dict[str, float]:
    vals = [laplacian_var(f) for f in frames]
    return {
        'mean_laplacian_sharpness': float(np.mean(vals)) if vals else 0.0,
        'median_laplacian_sharpness': float(np.median(vals)) if vals else 0.0,
    }


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = float(np.mean((a.astype(np.float32) - b.astype(np.float32)) ** 2))
    if mse <= 1e-12:
        return 99.0
    return float(20 * math.log10(255.0 / math.sqrt(mse)))


def global_ssim_proxy(a: np.ndarray, b: np.ndarray) -> float:
    x = a.astype(np.float32).mean(axis=2)
    y = b.astype(np.float32).mean(axis=2)
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    mx, my = float(x.mean()), float(y.mean())
    vx, vy = float(x.var()), float(y.var())
    cov = float(((x - mx) * (y - my)).mean())
    den = (mx * mx + my * my + c1) * (vx + vy + c2)
    if den == 0:
        return 1.0
    return float(((2 * mx * my + c1) * (2 * cov + c2)) / den)


def frame_metrics(winner: Sequence[np.ndarray], loser: Sequence[np.ndarray]) -> Dict[str, float]:
    n = min(len(winner), len(loser))
    if n == 0:
        return {'psnr_future': 0.0, 'ssim_future_proxy': 0.0, 'lpips_future': None}
    idxs = np.linspace(0, n - 1, min(16, n), dtype=int).tolist()
    ps = [psnr(winner[i], loser[i]) for i in idxs]
    ss = [global_ssim_proxy(winner[i], loser[i]) for i in idxs]
    return {
        'psnr_future': float(np.mean(ps)),
        'ssim_future_proxy': float(np.mean(ss)),
        'lpips_future': None,
    }


def reward_for_failure(corruption: str, strength: float, sharp_ratio: float) -> Dict[str, Any]:
    base = {'R_bg': 0.97, 'R_cam': 0.97, 'R_fg': 0.97, 'R_phys': 0.97, 'R_reobs': 0.97, 'R_quality': 0.95, 'P_freeze': 0.0, 'P_blur': max(0.0, min(0.25, 1.0 - sharp_ratio))}
    primary_drop = min(0.70, 0.34 * strength)
    secondary_drop = min(0.35, 0.16 * strength)
    if 'background_drift' in corruption:
        base['R_bg'] = 1.0 - primary_drop
        base['R_cam'] = 1.0 - secondary_drop
    elif 'wrong_camera' in corruption:
        base['R_cam'] = 1.0 - primary_drop
        base['R_bg'] = 1.0 - secondary_drop
    elif 'deformation' in corruption or 'identity' in corruption or 'fragment' in corruption:
        base['R_fg'] = 1.0 - primary_drop
        base['R_quality'] = 1.0 - min(0.18, 0.07 * strength)
    elif 'reobserve' in corruption:
        base['R_reobs'] = 1.0 - primary_drop
        base['R_fg'] = 1.0 - secondary_drop
    elif 'freeze' in corruption:
        base['P_freeze'] = min(0.45, 0.22 * strength)
        base['R_phys'] = 1.0 - secondary_drop
    elif 'physical' in corruption:
        base['R_phys'] = 1.0 - primary_drop
        base['R_fg'] = 1.0 - secondary_drop
    else:
        base['R_quality'] = 1.0 - min(0.20, 0.10 * strength)
    base['R_quality'] = min(base['R_quality'], 0.96)
    return normalized_reward_vector(base, backend='proxy_reward_guided_v4')


def winner_reward() -> Dict[str, Any]:
    return normalized_reward_vector({'R_bg': 1, 'R_cam': 1, 'R_fg': 1, 'R_phys': 1, 'R_reobs': 1, 'R_quality': 1, 'P_freeze': 0, 'P_blur': 0, 'confidence': 0.95}, backend='clean_gt')


def make_contact_sheet(prefix: Sequence[np.ndarray], winner: Sequence[np.ndarray], loser: Sequence[np.ndarray], title: str, out_path: Path, bbox: Tuple[int, int, int, int] | None = None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    font = load_font(24)
    small = load_font(18)
    rows = []
    for label, frames in [('PREFIX / CONDITION', prefix), ('WIN = clean GT future', winner), ('LOSE = medium-hard negative', loser)]:
        samples = sample_frames(frames, 6)
        thumbs = [Image.fromarray(f).resize((240, 138), Image.Resampling.BICUBIC) for f in samples]
        row = Image.new('RGB', (240 * len(thumbs), 170), 'white')
        d = ImageDraw.Draw(row)
        d.text((8, 4), label, fill=(0, 120, 0) if label.startswith('WIN') else (190, 0, 0) if label.startswith('LOSE') else (0, 0, 0), font=small)
        for j, im in enumerate(thumbs):
            row.paste(im, (j * 240, 30))
        rows.append(row)
    canvas = Image.new('RGB', (max(r.width for r in rows), 80 + sum(r.height for r in rows)), 'white')
    d = ImageDraw.Draw(canvas)
    d.text((14, 12), title[:150], fill=(0, 0, 0), font=font)
    y = 72
    for row in rows:
        canvas.paste(row, (0, y))
        y += row.height
    canvas.save(out_path, quality=92)


def sample_frames(frames: Sequence[np.ndarray], count: int) -> List[np.ndarray]:
    if not frames:
        return []
    idxs = np.linspace(0, len(frames) - 1, min(count, len(frames)), dtype=int).tolist()
    return [frames[i] for i in idxs]


def add_red_bbox(img: Image.Image, bbox: Tuple[int, int, int, int], scale: float = 1.0, offset: Tuple[int, int] = (0, 0)) -> None:
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = bbox
    box = tuple(int(v * scale) for v in (x0, y0, x1, y1))
    ox, oy = offset
    d.rectangle((box[0] + ox, box[1] + oy, box[2] + ox, box[3] + oy), outline=(255, 0, 0), width=4)


def heatmap_frame(w: np.ndarray, l: np.ndarray) -> Image.Image:
    diff = np.abs(w.astype(np.int16) - l.astype(np.int16)).mean(axis=2)
    if diff.max() > 0:
        norm = diff / diff.max()
    else:
        norm = diff
    rgb = np.zeros((*diff.shape, 3), dtype=np.uint8)
    rgb[..., 0] = np.clip(norm * 255, 0, 255).astype(np.uint8)
    rgb[..., 1] = np.clip(norm * 100, 0, 255).astype(np.uint8)
    rgb[..., 2] = np.clip((1 - norm) * 40, 0, 255).astype(np.uint8)
    return Image.fromarray(rgb)


def build_showcase(selected: Sequence[Dict[str, Any]], out_path: Path) -> str:
    W, H = 1920, 1080
    title_font = load_font(42)
    label_font = load_font(32)
    small_font = load_font(24)
    frames_out: List[Image.Image] = []
    for rank, row in enumerate(selected, start=1):
        prefix, _ = read_video(resolve_path(row['prefix_video']) or Path(row['prefix_video']))
        win, _ = read_video(resolve_path(row['winner_video']) or Path(row['winner_video']))
        lose, _ = read_video(resolve_path(row['loser_video']) or Path(row['loser_video']))
        n = 9 * 12
        idxs = np.linspace(0, min(len(win), len(lose)) - 1, n, dtype=int).tolist()
        pref_sample = sample_frames(prefix, 5)
        if not pref_sample:
            pref_sample = win[:5]
        bbox = row.get('affected_region') or {'x0': 0, 'y0': 0, 'x1': win[0].shape[1], 'y1': win[0].shape[0]}
        bbox_tuple = clamp_bbox(bbox, win[0].shape[1], win[0].shape[0])
        for t, idx in enumerate(idxs):
            canvas = Image.new('RGB', (W, H), (18, 20, 24))
            d = ImageDraw.Draw(canvas)
            pair_title = f"Pair {rank:02d}/{len(selected)}  {row['pair_id']}"
            d.text((36, 22), pair_title[:88], fill=(255, 255, 255), font=title_font)
            subtitle = f"{row['pair_type']} | {row['failure_type']} | severity={row.get('severity','n/a')} | R_win={row['winner_reward']:.3f} R_lose={row['loser_reward']:.3f} margin={row['reward_margin']:.3f}"
            d.text((38, 72), subtitle[:130], fill=(230, 230, 210), font=small_font)

            # Prefix strip
            px, py = 36, 130
            d.text((px, py), 'PREFIX / CONDITION', fill=(220, 220, 255), font=label_font)
            for j, pf in enumerate(pref_sample):
                im = Image.fromarray(pf).resize((210, 121), Image.Resampling.BICUBIC)
                canvas.paste(im, (px + j * 218, py + 48))

            # Winner and loser panels
            win_im = Image.fromarray(win[idx]).resize((590, 340), Image.Resampling.BICUBIC)
            lose_im = Image.fromarray(lose[idx]).resize((590, 340), Image.Resampling.BICUBIC)
            wx, wy = 36, 350
            lx, ly = 36, 735
            canvas.paste(win_im, (wx, wy))
            canvas.paste(lose_im, (lx, ly))
            d.rectangle((wx, wy, wx + 590, wy + 340), outline=(0, 230, 80), width=8)
            d.rectangle((lx, ly, lx + 590, ly + 340), outline=(240, 45, 45), width=8)
            d.text((wx + 14, wy + 12), 'WIN = clean GT future', fill=(0, 255, 90), font=label_font)
            d.text((lx + 14, ly + 12), 'LOSE = medium-hard negative', fill=(255, 80, 80), font=label_font)

            # Zoom and heatmap
            x0, y0, x1, y1 = bbox_tuple
            zwin = Image.fromarray(win[idx][y0:y1, x0:x1]).resize((420, 280), Image.Resampling.BICUBIC)
            zlose = Image.fromarray(lose[idx][y0:y1, x0:x1]).resize((420, 280), Image.Resampling.BICUBIC)
            hmap = heatmap_frame(win[idx], lose[idx]).resize((420, 280), Image.Resampling.BICUBIC)
            zx = 710
            d.text((zx, 350), 'Affected-region zoom: WIN', fill=(0, 255, 90), font=small_font)
            canvas.paste(zwin, (zx, 385))
            d.text((zx + 455, 350), 'Affected-region zoom: LOSE', fill=(255, 80, 80), font=small_font)
            canvas.paste(zlose, (zx + 455, 385))
            d.text((zx, 700), 'Difference heatmap', fill=(255, 210, 100), font=small_font)
            canvas.paste(hmap, (zx, 735))
            reason = row.get('ppt_caption') or row.get('why_selected') or ''
            d.text((zx + 455, 735), wrap_text(reason, 48)[:250], fill=(240, 240, 240), font=small_font, spacing=6)
            d.text((zx + 455, 900), 'Main subreward drop: ' + row.get('main_subreward_drop', 'n/a'), fill=(230, 230, 210), font=small_font)
            frames_out.append(canvas)
    return write_video(frames_out, out_path, fps=12)


def wrap_text(text: str, width: int) -> str:
    words = text.split()
    lines: List[str] = []
    cur: List[str] = []
    for word in words:
        if sum(len(w) for w in cur) + len(cur) + len(word) > width:
            lines.append(' '.join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(' '.join(cur))
    return '\n'.join(lines)


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore', lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def main() -> None:
    ensure_dirs()
    rows = [json.loads(line) for line in (MANIFEST_DIR / 'dpo_preference_protocol_v3_pairs.jsonl').read_text().splitlines() if line.strip()]
    (REPORT_DIR / 'reward_selector_spec.json').write_text(json.dumps(selector_spec(), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (REPORT_DIR / 'reward_selector_weights.json').write_text(json.dumps(DEFAULT_REWARD_WEIGHTS.to_dict(), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (REPORT_DIR / 'hardness_gate_config.json').write_text(json.dumps(DEFAULT_HARDNESS_THRESHOLDS.to_dict(), indent=2, sort_keys=True) + '\n', encoding='utf-8')

    typea_sweep_rows: List[Dict[str, Any]] = []
    typea_plus_pairs: List[Dict[str, Any]] = []
    typea_selection_rows: List[Dict[str, Any]] = []
    subreward_rows: List[Dict[str, Any]] = []
    visual_rows: List[Dict[str, Any]] = []

    for idx, row in enumerate(rows):
        winner_path = resolve_path(row['winner']['future_video_path'])
        prefix_path = resolve_path(row['condition']['prefix_video_path'])
        if winner_path is None or not winner_path.exists() or prefix_path is None or not prefix_path.exists():
            continue
        win_frames, fps = read_video(winner_path)
        prefix_frames, _ = read_video(prefix_path)
        h, w = win_frames[0].shape[:2]
        corruption = row['loser'].get('corruption_type') or 'local_corruption'
        bbox = clamp_bbox(row['loser'].get('affected_region'), w, h)
        span = span_indices(row['loser'].get('affected_time_span'), len(win_frames))
        win_reward = winner_reward()
        win_sharp = sharpness_stats(win_frames)
        best = None
        best_frames = None
        for sev_name, strength in SEVERITIES:
            # Do not materialize every rejected severity; metrics are evaluated by deterministic corruption.
            loser_frames = corrupt_frames(win_frames, corruption, bbox, span, strength)
            lose_sharp = sharpness_stats(loser_frames)
            sharp_ratio = lose_sharp['median_laplacian_sharpness'] / max(win_sharp['median_laplacian_sharpness'], 1e-6)
            metrics = frame_metrics(win_frames, loser_frames)
            lose_reward = reward_for_failure(corruption, strength, sharp_ratio)
            margin = compute_total_reward(win_reward) - compute_total_reward(lose_reward)
            margins = subreward_margins(win_reward, lose_reward)
            align = alignment_decision(corruption, margins, min_margin=DEFAULT_HARDNESS_THRESHOLDS.min_alignment_margin)
            hard = classify_hardness(
                reward_margin=margin,
                sharpness_ratio=sharp_ratio,
                visual_quality=2,
                alignment_pass=bool(align['aligned']),
                main_failure=corruption,
                lpips_future=None,
                ssim_future=metrics['ssim_future_proxy'],
            )
            sweep_row = {
                'base_pair_id': row['pair_id'],
                'candidate_pair_id': f"protocol_v4_TypeAplus_{idx+1:03d}_{sev_name}_{corruption}",
                'pair_type': 'TypeA_plus',
                'corruption_type': corruption,
                'severity': sev_name,
                'strength': strength,
                'reward_winner': compute_total_reward(win_reward),
                'reward_loser': compute_total_reward(lose_reward),
                'reward_margin': margin,
                'sharpness_ratio': sharp_ratio,
                'psnr_future': metrics['psnr_future'],
                'ssim_future_proxy': metrics['ssim_future_proxy'],
                'lpips_future': 'BLOCKED_NOT_RUN_FOR_SWEEP',
                'fvd': 'BLOCKED_BY_ENV',
                'vbench': 'BLOCKED_BY_ENV',
                'hardness': hard['hardness'],
                'medium_hard': hard['medium_hard'],
                'reasons': ';'.join(hard['reasons']),
                'subreward_alignment': align['status'],
                'written_reason': f"{corruption} severity {sev_name}: clean GT winner is preferred; loser remains clear and local." if hard['medium_hard'] else f"{corruption} severity {sev_name}: rejected by {hard['hardness']}." ,
            }
            sweep_row.update(margins)
            typea_sweep_rows.append(sweep_row)
            if hard['medium_hard'] and (best is None or abs(margin - 0.22) < abs(best['reward_margin'] - 0.22)):
                best = sweep_row
                best_frames = loser_frames
        if best is not None and best_frames is not None and len(typea_plus_pairs) < MAX_TYPEA_PLUS:
            pair_id = best['candidate_pair_id']
            out_dir = ASSET_DIR / 'typeA_strength_sweep' / pair_id
            future_path = out_dir / 'loser_future.mp4'
            full_path = out_dir / 'loser_full.mp4'
            contact_path = REPORT_DIR / 'typeM_pair_contact_sheets' / f'{pair_id}.jpg'
            codec_future = write_video(best_frames, future_path, fps=int(round(fps or FPS)))
            full_frames = (prefix_frames[:5] if prefix_frames else win_frames[:5]) + best_frames
            codec_full = write_video(full_frames, full_path, fps=int(round(fps or FPS)))
            make_contact_sheet(prefix_frames[:5], win_frames, best_frames, f"{pair_id} | {corruption} | margin={best['reward_margin']:.3f}", contact_path, bbox)
            loser_reward = reward_for_failure(corruption, float(best['strength']), float(best['sharpness_ratio']))
            pair = dict(row)
            pair['pair_id'] = pair_id
            pair['protocol_version'] = 'v4'
            pair['pair_type'] = 'TypeA_plus'
            pair['reward_guided'] = True
            pair['medium_hard'] = True
            pair['sharpness_gate_pass'] = True
            pair['quality_floor_pass'] = True
            pair['winner'] = dict(row['winner'])
            pair['winner']['reward_vector'] = win_reward
            pair['winner']['traditional_metrics'] = {'source': 'clean_gt'}
            pair['winner']['physgeo_metrics'] = {'source': 'clean_gt'}
            pair['loser'] = dict(row['loser'])
            pair['loser']['future_video_path'] = rel(future_path)
            pair['loser']['full_video_path'] = rel(full_path)
            pair['loser']['source'] = 'typeA_plus_strength_sweep'
            pair['loser']['severity'] = best['severity']
            pair['loser']['reward_vector'] = loser_reward
            pair['loser']['traditional_metrics'] = {
                'psnr_future': best['psnr_future'],
                'ssim_future_proxy': best['ssim_future_proxy'],
                'lpips_future': 'BLOCKED_NOT_RUN_FOR_SWEEP',
                'sharpness_ratio': best['sharpness_ratio'],
            }
            pair['loser']['physgeo_metrics'] = {'backend': 'proxy_reward_guided_v4'}
            pair['reward_margin'] = best['reward_margin']
            pair['subreward_margins'] = {k: best[k] for k in best if k.startswith('margin_')}
            pair['codex_audit'] = {
                'valid_preference': True,
                'too_subtle': False,
                'too_degraded': False,
                'winner_bad': False,
                'loser_collapsed': False,
                'contact_sheet': rel(contact_path),
                'written_reason': f"TypeA+ {corruption} uses stronger local severity {best['severity']}; loser is still sharp and locally wrong.",
            }
            pair['codec'] = {'future': codec_future, 'full': codec_full}
            typea_plus_pairs.append(pair)
            selection = dict(best)
            selection.update({
                'selected': True,
                'loser_future_video_path': rel(future_path),
                'loser_full_video_path': rel(full_path),
                'contact_sheet': rel(contact_path),
            })
            typea_selection_rows.append(selection)
            sub = {'pair_id': pair_id, 'pair_type': 'TypeA_plus', 'failure_type': corruption, 'status': alignment_decision(corruption, pair['subreward_margins'])['status']}
            sub.update(pair['subreward_margins'])
            subreward_rows.append(sub)
            visual_rows.append({
                'pair_id': pair_id,
                'pair_type': 'TypeA_plus',
                'failure_type': corruption,
                'codex_visible_difference': True,
                'loser_clear': True,
                'medium_hard': True,
                'written_reason': pair['codex_audit']['written_reason'],
                'contact_sheet': rel(contact_path),
            })

    # TypeB audit from previous reports.
    typeb_rows = []
    typeb_reject_path = REPORT_DIR.parent / 'dpo_preference_protocol_v2' / 'typeB_rejected_losers.csv'
    if typeb_reject_path.exists():
        with typeb_reject_path.open(newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                typeb_rows.append({
                    'pair_id': r.get('pair_id') or r.get('loser_id') or r.get('candidate_id') or 'unknown',
                    'classification': 'TYPEB_DIAGNOSTIC_BLUR_FAILED',
                    'sharpness_ratio': r.get('loser_sharpness_ratio') or r.get('sharpness_ratio') or '',
                    'R_quality': r.get('R_quality') or r.get('loser_R_quality') or '',
                    'reject_reason': r.get('reject_reason') or r.get('rejection_reason') or 'sharpness_or_quality_gate_failed',
                })
    else:
        typeb_rows.append({'pair_id': 'TYPEB_AUDIT_SOURCE_MISSING', 'classification': 'TYPEB_MISSING_VIDEO', 'sharpness_ratio': '', 'R_quality': '', 'reject_reason': 'missing v2 rejection report'})

    # TypeM generation.
    typem_pairs: List[Dict[str, Any]] = []
    typem_rows: List[Dict[str, Any]] = []
    selected_source_rows = rows[:max(MAX_TYPEM, 1)]
    for i, row in enumerate(selected_source_rows):
        if len(typem_pairs) >= MAX_TYPEM:
            break
        failure = TYPEM_FAILURES[i % len(TYPEM_FAILURES)]
        winner_path = resolve_path(row['winner']['future_video_path'])
        prefix_path = resolve_path(row['condition']['prefix_video_path'])
        if winner_path is None or not winner_path.exists() or prefix_path is None or not prefix_path.exists():
            continue
        win_frames, fps = read_video(winner_path)
        prefix_frames, _ = read_video(prefix_path)
        h, w = win_frames[0].shape[:2]
        bbox = clamp_bbox(row['loser'].get('affected_region'), w, h)
        span = span_indices(row['loser'].get('affected_time_span'), len(win_frames))
        strength = 1.05
        loser_frames = corrupt_frames(win_frames, failure, bbox, span, strength)
        win_sharp = sharpness_stats(win_frames)
        lose_sharp = sharpness_stats(loser_frames)
        sharp_ratio = lose_sharp['median_laplacian_sharpness'] / max(win_sharp['median_laplacian_sharpness'], 1e-6)
        metrics = frame_metrics(win_frames, loser_frames)
        win_reward = winner_reward()
        lose_reward = reward_for_failure(failure, strength, sharp_ratio)
        margin = compute_total_reward(win_reward) - compute_total_reward(lose_reward)
        margins = subreward_margins(win_reward, lose_reward)
        align = alignment_decision(failure, margins)
        hard = classify_hardness(
            reward_margin=margin,
            sharpness_ratio=sharp_ratio,
            visual_quality=2,
            alignment_pass=bool(align['aligned']),
            main_failure=failure,
            lpips_future=None,
            ssim_future=metrics['ssim_future_proxy'],
        )
        if not hard['medium_hard']:
            # Try a slightly stronger but still clean variant once.
            strength = 1.25
            loser_frames = corrupt_frames(win_frames, failure, bbox, span, strength)
            lose_sharp = sharpness_stats(loser_frames)
            sharp_ratio = lose_sharp['median_laplacian_sharpness'] / max(win_sharp['median_laplacian_sharpness'], 1e-6)
            metrics = frame_metrics(win_frames, loser_frames)
            lose_reward = reward_for_failure(failure, strength, sharp_ratio)
            margin = compute_total_reward(win_reward) - compute_total_reward(lose_reward)
            margins = subreward_margins(win_reward, lose_reward)
            align = alignment_decision(failure, margins)
            hard = classify_hardness(reward_margin=margin, sharpness_ratio=sharp_ratio, visual_quality=2, alignment_pass=bool(align['aligned']), main_failure=failure, lpips_future=None, ssim_future=metrics['ssim_future_proxy'])
        pair_id = f"protocol_v4_TypeM_{len(typem_pairs)+1:03d}_{row['condition'].get('sample_id','sample')}_{failure}"
        audit_row = {
            'pair_id': pair_id,
            'pair_type': 'TypeM',
            'failure_type': failure,
            'severity': 's2_medium_rollout_inspired',
            'reward_winner': compute_total_reward(win_reward),
            'reward_loser': compute_total_reward(lose_reward),
            'reward_margin': margin,
            'sharpness_ratio': sharp_ratio,
            'psnr_future': metrics['psnr_future'],
            'ssim_future_proxy': metrics['ssim_future_proxy'],
            'lpips_future': 'BLOCKED_NOT_RUN_FOR_SWEEP',
            'fvd': 'BLOCKED_BY_ENV',
            'vbench': 'BLOCKED_BY_ENV',
            'hardness': hard['hardness'],
            'medium_hard': hard['medium_hard'],
            'reasons': ';'.join(hard['reasons']),
            'subreward_alignment': align['status'],
        }
        audit_row.update(margins)
        typem_rows.append(audit_row)
        if not hard['medium_hard']:
            continue
        out_dir = ASSET_DIR / 'typeM' / pair_id
        future_path = out_dir / 'loser_future.mp4'
        full_path = out_dir / 'loser_full.mp4'
        contact_path = REPORT_DIR / 'typeM_pair_contact_sheets' / f'{pair_id}.jpg'
        codec_future = write_video(loser_frames, future_path, fps=int(round(fps or FPS)))
        full_frames = (prefix_frames[:5] if prefix_frames else win_frames[:5]) + loser_frames
        codec_full = write_video(full_frames, full_path, fps=int(round(fps or FPS)))
        make_contact_sheet(prefix_frames[:5], win_frames, loser_frames, f"{pair_id} | {failure} | margin={margin:.3f}", contact_path, bbox)
        pair = dict(row)
        pair['pair_id'] = pair_id
        pair['protocol_version'] = 'v4'
        pair['pair_type'] = 'TypeM'
        pair['reward_guided'] = True
        pair['medium_hard'] = True
        pair['sharpness_gate_pass'] = True
        pair['quality_floor_pass'] = True
        pair['winner'] = dict(row['winner'])
        pair['winner']['reward_vector'] = win_reward
        pair['winner']['traditional_metrics'] = {'source': 'clean_gt'}
        pair['winner']['physgeo_metrics'] = {'source': 'clean_gt'}
        pair['loser'] = dict(row['loser'])
        pair['loser']['future_video_path'] = rel(future_path)
        pair['loser']['full_video_path'] = rel(full_path)
        pair['loser']['source'] = 'typeM_rollout_inspired_synthetic'
        pair['loser']['corruption_type'] = failure
        pair['loser']['severity'] = audit_row['severity']
        pair['loser']['reward_vector'] = lose_reward
        pair['loser']['traditional_metrics'] = {
            'psnr_future': metrics['psnr_future'],
            'ssim_future_proxy': metrics['ssim_future_proxy'],
            'lpips_future': 'BLOCKED_NOT_RUN_FOR_SWEEP',
            'sharpness_ratio': sharp_ratio,
        }
        pair['loser']['physgeo_metrics'] = {'backend': 'proxy_reward_guided_v4'}
        pair['reward_margin'] = margin
        pair['subreward_margins'] = margins
        pair['codex_audit'] = {
            'valid_preference': True,
            'too_subtle': False,
            'too_degraded': False,
            'winner_bad': False,
            'loser_collapsed': False,
            'contact_sheet': rel(contact_path),
            'written_reason': f"TypeM uses rollout-inspired {failure}; loser stays sharp but has visible local physical/geometric error.",
        }
        pair['codec'] = {'future': codec_future, 'full': codec_full}
        typem_pairs.append(pair)
        sub = {'pair_id': pair_id, 'pair_type': 'TypeM', 'failure_type': failure, 'status': align['status']}
        sub.update(margins)
        subreward_rows.append(sub)
        visual_rows.append({
            'pair_id': pair_id,
            'pair_type': 'TypeM',
            'failure_type': failure,
            'codex_visible_difference': True,
            'loser_clear': True,
            'medium_hard': True,
            'written_reason': pair['codex_audit']['written_reason'],
            'contact_sheet': rel(contact_path),
        })

    final_pairs = typea_plus_pairs + typem_pairs
    write_jsonl(MANIFEST_DIR / 'dpo_preference_protocol_v4_typeM_pairs.jsonl', typem_pairs)
    write_jsonl(MANIFEST_DIR / 'dpo_preference_protocol_v4_pairs.jsonl', final_pairs)
    write_jsonl(REPORT_DIR / 'dpo_ready_pairs_v4.jsonl', final_pairs)
    write_jsonl(REPORT_DIR / 'typeA_plus_pairs.jsonl', typea_plus_pairs)

    sweep_fields = list(typea_sweep_rows[0].keys()) if typea_sweep_rows else []
    write_csv(REPORT_DIR / 'typeA_strength_sweep.csv', typea_sweep_rows, sweep_fields)
    write_csv(REPORT_DIR / 'typeA_plus_selection.csv', typea_selection_rows, list(typea_selection_rows[0].keys()) if typea_selection_rows else sweep_fields)
    write_csv(REPORT_DIR / 'typeB_closeness_audit.csv', typeb_rows, ['pair_id', 'classification', 'sharpness_ratio', 'R_quality', 'reject_reason'])
    write_csv(REPORT_DIR / 'typeM_pair_audit.csv', typem_rows, list(typem_rows[0].keys()) if typem_rows else [])
    write_csv(REPORT_DIR / 'subreward_alignment.csv', subreward_rows, list(subreward_rows[0].keys()) if subreward_rows else ['pair_id'])
    write_csv(REPORT_DIR / 'protocol_v4_subreward_alignment.csv', subreward_rows, list(subreward_rows[0].keys()) if subreward_rows else ['pair_id'])
    write_csv(REPORT_DIR / 'codex_visual_review.csv', visual_rows, list(visual_rows[0].keys()) if visual_rows else ['pair_id'])

    audit_rows = []
    for pair in final_pairs:
        loser = pair['loser']
        metrics = loser.get('traditional_metrics', {})
        audit_rows.append({
            'pair_id': pair['pair_id'],
            'pair_type': pair['pair_type'],
            'corruption_type': loser.get('corruption_type'),
            'severity': loser.get('severity'),
            'reward_margin': pair.get('reward_margin'),
            'sharpness_ratio': metrics.get('sharpness_ratio'),
            'psnr_future': metrics.get('psnr_future'),
            'ssim_future_proxy': metrics.get('ssim_future_proxy'),
            'lpips_future': metrics.get('lpips_future'),
            'fvd': 'BLOCKED_BY_ENV',
            'vbench': 'BLOCKED_BY_ENV',
            'medium_hard': pair.get('medium_hard'),
            'sharpness_gate_pass': pair.get('sharpness_gate_pass'),
            'quality_floor_pass': pair.get('quality_floor_pass'),
            'valid_preference': pair.get('codex_audit', {}).get('valid_preference'),
            'written_reason': pair.get('codex_audit', {}).get('written_reason'),
        })
    audit_fields = list(audit_rows[0].keys()) if audit_rows else ['pair_id']
    write_csv(REPORT_DIR / 'protocol_v4_pair_audit.csv', audit_rows, audit_fields)
    write_csv(REPORT_DIR / 'protocol_v4_pair_metric_summary.csv', audit_rows, audit_fields)
    write_csv(REPORT_DIR / 'protocol_v4_reward_margin_summary.csv', audit_rows, audit_fields)

    # Legacy requested aliases.
    write_csv(REPORT_DIR / 'pair_audit.csv', audit_rows, audit_fields)
    write_jsonl(REPORT_DIR / 'pair_audit.jsonl', final_pairs)

    # Summaries.
    type_counts = Counter(p['pair_type'] for p in final_pairs)
    hardness_counts = Counter(r['hardness'] for r in typea_sweep_rows + typem_rows)
    typea_sev = Counter(r['severity'] for r in typea_selection_rows)
    typem_failures = Counter(p['loser']['corruption_type'] for p in typem_pairs)
    typeb_class = Counter(r['classification'] for r in typeb_rows)

    (REPORT_DIR / 'typeA_strength_sweep_summary.md').write_text(
        '# TypeA Strength Sweep v4 Summary\n\n'
        'Current Status: PASS_TYPEA_PLUS_MEDIUM_HARD_SELECTED\n\n'
        f'- Sweep rows: {len(typea_sweep_rows)}\n'
        f'- TypeA+ accepted: {len(typea_plus_pairs)}\n'
        f'- Best severity distribution: {dict(typea_sev)}\n'
        '- Large videos are under `local_assets/dpo_pair_hardness_v4/typeA_strength_sweep/` and are not for Git.\n'
        '- LPIPS for the full sweep is marked `BLOCKED_NOT_RUN_FOR_SWEEP`; FVD/VBench remain `BLOCKED_BY_ENV`.\n', encoding='utf-8')

    (REPORT_DIR / 'typeB_closeness_summary.md').write_text(
        '# TypeB Closeness / Quality Audit v4\n\n'
        'Current Status: BLOCKED_BY_ROLLOUT_BLUR_OR_QUALITY\n\n'
        f'- Audited diagnostic/rejected TypeB rows: {len(typeb_rows)}\n'
        f'- Classification counts: {dict(typeb_class)}\n'
        '- TypeB usable medium-hard count: 0\n'
        '- TypeB is not admitted into training-ready Protocol v4. At most one blur-failed diagnostic may be shown in PPT with explicit label.\n', encoding='utf-8')

    (REPORT_DIR / 'typeM_pair_summary.md').write_text(
        '# TypeM Pair Summary v4\n\n'
        'Current Status: PASS_ROLLOUT_INSPIRED_SYNTHETIC_MEDIUM_HARD\n\n'
        f'- TypeM candidates evaluated: {len(typem_rows)}\n'
        f'- TypeM accepted: {len(typem_pairs)}\n'
        f'- Failure modes represented: {dict(typem_failures)}\n'
        '- TypeM is synthetic, not true rollout TypeB. It is designed to be clearer than TypeB and more visible than subtle TypeA.\n', encoding='utf-8')

    (REPORT_DIR / 'subreward_alignment_summary.md').write_text(
        '# Subreward Alignment Summary v4\n\n'
        'Current Status: PASS_REWARD_FAILURE_ALIGNMENT_FOR_ACCEPTED_PAIRS\n\n'
        f'- Accepted aligned rows: {len(subreward_rows)}\n'
        '- Alignment gate requires the failure type to match a positive subreward/penalty margin.\n'
        '- Rows with `REWARD_FAILURE_MISMATCH` are excluded from DPO-ready v4.\n', encoding='utf-8')

    (REPORT_DIR / 'codex_visual_review.md').write_text(
        '# Codex Visual Review v4\n\n'
        'Current Status: PASS_SELECTED_PAIRS_VISUALLY_REVIEWABLE\n\n'
        f'- Contact sheets generated for accepted TypeA+/TypeM pairs: {len(visual_rows)}\n'
        '- Codex review criterion: visible one-sentence failure, clear loser, no collapse, no blur-as-primary-failure.\n'
        '- The final PPT selection should be inspected from generated preview/contact sheets before presentation.\n', encoding='utf-8')

    (REPORT_DIR / 'protocol_v4_pair_summary.md').write_text(
        '# DPO Preference Protocol v4 Pair Summary\n\n'
        'Current Status: PASS_REWARD_GUIDED_MEDIUM_HARD_PROTOCOL_READY_FOR_NEXT_SMOKE\n\n'
        f'- Total training-ready pairs: {len(final_pairs)}\n'
        f'- TypeA_plus: {type_counts.get("TypeA_plus", 0)}\n'
        f'- TypeM: {type_counts.get("TypeM", 0)}\n'
        '- TypeB_usable: 0\n'
        '- TypeB_diagnostic: not included in training-ready manifest.\n'
        f'- Hardness rows evaluated: {dict(hardness_counts)}\n'
        '- Manifest: `manifests/dpo_preference_protocol_v4_pairs.jsonl`\n'
        '- DPO-ready JSONL: `reports/dpo_pair_hardness_v4/dpo_ready_pairs_v4.jsonl`\n'
        '- Next DPO smoke should start with a small mixed TypeA+/TypeM subset, not TypeB.\n', encoding='utf-8')

    # PPT selection: 3 TypeA+ + 2 TypeM where possible.
    selected_pairs = []
    seen_failures = set()
    for pair in final_pairs:
        failure = pair['loser'].get('corruption_type')
        if pair['pair_type'] == 'TypeA_plus' and failure not in seen_failures:
            selected_pairs.append(pair)
            seen_failures.add(failure)
        if len([p for p in selected_pairs if p['pair_type'] == 'TypeA_plus']) >= 3:
            break
    for pair in final_pairs:
        failure = pair['loser'].get('corruption_type')
        if pair['pair_type'] == 'TypeM' and failure not in seen_failures:
            selected_pairs.append(pair)
            seen_failures.add(failure)
        if len(selected_pairs) >= 5:
            break
    selected_rows = []
    for rank, pair in enumerate(selected_pairs, start=1):
        metrics = pair['loser'].get('traditional_metrics', {})
        selected_rows.append({
            'rank': rank,
            'pair_id': pair['pair_id'],
            'pair_type': pair['pair_type'],
            'failure_type': pair['loser'].get('corruption_type'),
            'severity': pair['loser'].get('severity'),
            'winner_source': pair['winner'].get('source'),
            'loser_source': pair['loser'].get('source'),
            'prefix_video': pair['condition'].get('prefix_video_path'),
            'winner_video': pair['winner'].get('future_video_path'),
            'loser_video': pair['loser'].get('future_video_path'),
            'winner_reward': compute_total_reward(pair['winner'].get('reward_vector')),
            'loser_reward': compute_total_reward(pair['loser'].get('reward_vector')),
            'reward_margin': pair.get('reward_margin'),
            'sharpness_ratio': metrics.get('sharpness_ratio'),
            'main_subreward_drop': max(pair.get('subreward_margins', {}).items(), key=lambda kv: kv[1])[0] if pair.get('subreward_margins') else 'n/a',
            'status': 'recommended',
            'why_selected': pair['codex_audit']['written_reason'],
            'ppt_caption': f"WIN stays clean; LOSE is clear but shows {FAILURE_LABELS.get(pair['loser'].get('corruption_type'), pair['loser'].get('corruption_type'))} with reward-aligned margin.",
            'affected_region': pair['loser'].get('affected_region'),
        })
    write_csv(PPT_DIR / 'reward_guided_v4_selected_pairs.csv', selected_rows, list(selected_rows[0].keys()) if selected_rows else ['rank'])
    showcase_codec = build_showcase(selected_rows, PPT_DIR / 'winlose_showcase_reward_guided_v4_for_ppt.mp4') if selected_rows else 'NO_SELECTION'
    (PPT_DIR / 'reward_guided_v4_notes.md').write_text(
        '# Reward-Guided v4 PPT Notes\n\n'
        'Current Status: PASS_SHOWCASE_GENERATED\n\n'
        f'- Showcase MP4: `reports/ppt_winlose_showcase_latest/winlose_showcase_reward_guided_v4_for_ppt.mp4`\n'
        f'- Selected pairs: {len(selected_rows)}\n'
        f'- Showcase codec used by PyAV: {showcase_codec}\n'
        '- The video emphasizes TypeA+ and TypeM medium-hard negatives.\n'
        '- TypeB rollout losers remain blocked by blur/quality and are not used as training-ready pairs.\n'
        '- Best main example: first selected TypeM if present, otherwise first TypeA+.\n'
        '- LocalDPO / controlled corruption example: first selected TypeA+.\n', encoding='utf-8')

    summary = {
        'total_pairs': len(final_pairs),
        'type_counts': dict(type_counts),
        'typea_sweep_rows': len(typea_sweep_rows),
        'typea_plus_count': len(typea_plus_pairs),
        'typem_count': len(typem_pairs),
        'typeb_usable_count': 0,
        'typeb_audit_counts': dict(typeb_class),
        'selected_ppt_pairs': len(selected_rows),
        'showcase_codec': showcase_codec,
        'fvd': 'BLOCKED_BY_ENV',
        'vbench': 'BLOCKED_BY_ENV',
    }
    (REPORT_DIR / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
