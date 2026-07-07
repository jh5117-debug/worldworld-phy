from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import cv2

from cam_physgeo.dpo.prefix5_dpo_dataset import prefix5_schema_errors, resolve_asset_path


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _nested_get(data: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _repo_path(value: str | Path | None, repo_root: Path) -> Path | None:
    if not value:
        return None
    try:
        p = resolve_asset_path(value, repo_root=repo_root)
    except Exception:
        return None
    return p if p.exists() else None


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except Exception:
        return str(path)


def _read_frames(path: Path, *, width: int, height: int) -> tuple[list[Any], float]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 16.0)
    frames: list[Any] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if int(frame.shape[1]) != int(width) or int(frame.shape[0]) != int(height):
            frame = cv2.resize(frame, (int(width), int(height)), interpolation=cv2.INTER_LANCZOS4)
        frames.append(frame)
    cap.release()
    if not frames:
        raise RuntimeError(f"empty video: {path}")
    return frames, fps


def _write_video(path: Path, frames: list[Any], *, fps: float, width: int, height: int) -> None:
    if not frames:
        raise ValueError(f"no frames to write: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, float(fps or 16.0), (int(width), int(height)))
    if not writer.isOpened():
        raise RuntimeError(f"cannot open writer: {path}")
    try:
        for frame in frames:
            writer.write(frame)
    finally:
        writer.release()


def _slice_or_pad(frames: list[Any], start: int, end: int) -> list[Any]:
    if not frames:
        return []
    out = list(frames[start:end])
    while len(out) < max(0, end - start):
        out.append(out[-1].copy() if out else frames[-1].copy())
    return out


def _audit_ok(pair: dict[str, Any]) -> bool:
    audit = pair.get("codex_visual_audit") or pair.get("codex_audit") or {}
    if audit and audit.get("reviewed") is not True:
        return False
    if audit and audit.get("winner_bad") is True:
        return False
    if audit and audit.get("too_subtle") is True:
        return False
    if pair.get("medium_hard") is False:
        return False
    return True


def _first_existing(condition: dict[str, Any], names: tuple[str, ...], repo_root: Path) -> str | None:
    for name in names:
        value = condition.get(name)
        if value and (name == "prompt" or _repo_path(value, repo_root) is not None):
            return str(value)
    return None


def _candidate_sources(pair: dict[str, Any], repo_root: Path) -> tuple[Path | None, Path | None, dict[str, str | None], str]:
    condition = pair.get("condition") or {}
    winner = pair.get("winner") or {}
    loser = pair.get("loser") or {}
    winner_full = (
        _repo_path(winner.get("full_video_path"), repo_root)
        or _repo_path(condition.get("gt_full_video_path"), repo_root)
        or _repo_path(condition.get("full_video_path"), repo_root)
    )
    loser_future = _repo_path(loser.get("future_video_path"), repo_root)
    aliases = {
        "image": _first_existing(condition, ("image", "image_path"), repo_root),
        "prompt": _first_existing(condition, ("prompt", "prompt_path"), repo_root),
        "poses": _first_existing(condition, ("poses", "poses_path"), repo_root),
        "intrinsics": _first_existing(condition, ("intrinsics", "intrinsics_path"), repo_root),
    }
    reason = []
    if winner_full is None:
        reason.append("missing_winner_or_gt_full")
    if loser_future is None:
        reason.append("missing_loser_future")
    for key, value in aliases.items():
        if not value:
            reason.append(f"missing_condition_{key}")
    return winner_full, loser_future, aliases, "|".join(reason)


def build_adapter_manifest(
    *,
    input_manifest: str | Path,
    output_manifest: str | Path,
    output_root: str | Path,
    report_csv: str | Path,
    summary_json: str | Path,
    repo_root: str | Path = ".",
    limit: int = 4,
    prefix_len: int = 5,
    prediction_start_frame: int = 5,
    num_frames: int = 81,
    width: int = 832,
    height: int = 480,
    prefer_pair_type: str = "TypeM_v11_synthetic_visible",
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    out_root = Path(output_root)
    rows = _load_jsonl(input_manifest)
    selected: list[dict[str, Any]] = []
    report_rows: list[dict[str, Any]] = []
    future_indices = list(range(int(prediction_start_frame), int(num_frames)))

    def sort_key(pair: dict[str, Any]) -> tuple[int, str, str]:
        return (
            0 if pair.get("pair_type") == prefer_pair_type else 1,
            str(pair.get("failure_tag") or _nested_get(pair, "loser.failure_type", "")),
            str(pair.get("pair_id")),
        )

    for pair in sorted(rows, key=sort_key):
        pair_id = str(pair.get("pair_id") or "")
        if not pair_id or not _audit_ok(pair):
            continue
        winner_full, loser_future, aliases, reason = _candidate_sources(pair, repo)
        if reason:
            report_rows.append({"pair_id": pair_id, "status": "SKIP", "reason": reason})
            continue
        assert winner_full is not None and loser_future is not None
        pair_dir = out_root / pair_id
        try:
            winner_frames, fps = _read_frames(winner_full, width=width, height=height)
            loser_future_frames, loser_fps = _read_frames(loser_future, width=width, height=height)
            prefix_frames = _slice_or_pad(winner_frames, 0, prefix_len)
            winner_future_frames = _slice_or_pad(winner_frames, prediction_start_frame, num_frames)
            loser_future_padded = _slice_or_pad(loser_future_frames, 0, num_frames - prediction_start_frame)
            loser_full_frames = prefix_frames + loser_future_padded
            prefix_out = pair_dir / "prefix_len5.mp4"
            winner_future_out = pair_dir / "winner_future_5_80.mp4"
            loser_full_out = pair_dir / "loser_full_prefix5_plus_future.mp4"
            _write_video(prefix_out, prefix_frames, fps=fps, width=width, height=height)
            _write_video(winner_future_out, winner_future_frames, fps=fps, width=width, height=height)
            _write_video(loser_full_out, loser_full_frames, fps=loser_fps or fps, width=width, height=height)

            adapted = json.loads(json.dumps(pair))
            condition = adapted.setdefault("condition", {})
            winner = adapted.setdefault("winner", {})
            loser = adapted.setdefault("loser", {})
            condition["prefix_len"] = prefix_len
            condition["prediction_start_frame"] = prediction_start_frame
            condition["prefix_video_path"] = _rel(prefix_out, repo)
            condition["image"] = aliases["image"]
            condition["prompt"] = aliases["prompt"]
            condition["poses"] = aliases["poses"]
            condition["intrinsics"] = aliases["intrinsics"]
            condition.setdefault("gt_full_video_path", _rel(winner_full, repo))
            condition["gt_future_video_path"] = _rel(winner_future_out, repo)
            adapted["prefix_len"] = prefix_len
            adapted["prediction_start_frame"] = prediction_start_frame
            adapted["loss_frame_indices"] = future_indices
            adapted["reward_frame_indices"] = future_indices
            adapted["same_prefix"] = True
            adapted["same_prompt"] = True
            adapted["same_poses"] = True
            adapted["same_intrinsics"] = True
            adapted["margin"] = float(adapted.get("margin") or adapted.get("reward_margin") or 0.0)
            winner["full_video_path"] = _rel(winner_full, repo)
            winner["future_video_path"] = _rel(winner_future_out, repo)
            winner["future_frame_indices"] = future_indices
            loser["full_video_path"] = _rel(loser_full_out, repo)
            loser["future_video_path"] = _rel(loser_future, repo)
            loser["future_frame_indices"] = future_indices
            adapted["v14_asset_complete_adapter"] = {
                "source_winner_full": _rel(winner_full, repo),
                "source_loser_future": _rel(loser_future, repo),
                "prefix_out": _rel(prefix_out, repo),
                "winner_future_out": _rel(winner_future_out, repo),
                "loser_full_out": _rel(loser_full_out, repo),
            }
            errors = prefix5_schema_errors(adapted, repo_root=repo)
            if errors:
                report_rows.append({"pair_id": pair_id, "status": "SCHEMA_FAIL", "reason": "|".join(errors)})
                continue
            selected.append(adapted)
            report_rows.append({
                "pair_id": pair_id,
                "status": "ADAPTED",
                "pair_type": adapted.get("pair_type"),
                "pair_source": adapted.get("pair_source"),
                "failure_tag": adapted.get("failure_tag") or _nested_get(adapted, "loser.failure_type", ""),
                "winner_frames": len(winner_frames),
                "loser_future_frames": len(loser_future_frames),
                "prefix_path": _rel(prefix_out, repo),
                "winner_future_path": _rel(winner_future_out, repo),
                "loser_full_path": _rel(loser_full_out, repo),
            })
        except Exception as exc:
            report_rows.append({"pair_id": pair_id, "status": "ERROR", "reason": repr(exc)})
            continue
        if len(selected) >= int(limit):
            break

    _write_jsonl(output_manifest, selected)
    _write_csv(report_csv, report_rows)
    summary = {
        "input_manifest": str(input_manifest),
        "output_manifest": str(output_manifest),
        "output_root": str(output_root),
        "limit": int(limit),
        "selected_count": len(selected),
        "report_csv": str(report_csv),
        "status_counts": dict(Counter(r.get("status", "") for r in report_rows)),
        "pair_type_counts": dict(Counter(r.get("pair_type", "") for r in report_rows if r.get("status") == "ADAPTED")),
        "schema_validated": len(selected),
    }
    s = Path(summary_json)
    s.parent.mkdir(parents=True, exist_ok=True)
    s.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build asset-complete Prefix5 manifests for v14 real-energy calibration.")
    parser.add_argument("--input_manifest", required=True)
    parser.add_argument("--output_manifest", required=True)
    parser.add_argument("--output_root", required=True)
    parser.add_argument("--report_csv", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--repo_root", default=".")
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--prefix_len", type=int, default=5)
    parser.add_argument("--prediction_start_frame", type=int, default=5)
    parser.add_argument("--num_frames", type=int, default=81)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--prefer_pair_type", default="TypeM_v11_synthetic_visible")
    args = parser.parse_args()
    summary = build_adapter_manifest(**vars(args))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
