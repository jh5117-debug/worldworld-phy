from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from .pair_factory_v11_common import read_jsonl, write_jsonl, write_csv, repo_path, rel, video_info, read_video_frames, write_video, normalize_condition_from_pair, condition_key, append_blocker

KNOWN_MANIFESTS = [
    "manifests/dpo_pair_factory_v10_conditions.jsonl",
    "manifests/dpo_pair_factory_v10b_ready_all.jsonl",
    "manifests/targeted_BC_loser_mining_v6b_conditions.jsonl",
    "manifests/anchored_dpo_probe_pairs_prefix5.jsonl",
    "manifests/dpo_preference_protocol_v1_pairs.jsonl",
    "manifests/dpo_preference_protocol_v2_pairs.jsonl",
    "manifests/dpo_preference_protocol_v3_pairs.jsonl",
    "manifests/dpo_preference_protocol_v4_pairs.jsonl",
    "manifests/screen16_v2v5.jsonl",
    "manifests/quant_benchmark_v1_all.jsonl",
    "manifests/quant_benchmark_v1_core.jsonl",
    "manifests/quant_benchmark_v1_stress.jsonl",
]

def condition_from_row(row: dict, source: str) -> dict:
    if "winner" in row or "condition" in row:
        c = normalize_condition_from_pair(row)
    else:
        c = {
            "condition_id": row.get("condition_id") or row.get("benchmark_id") or row.get("sample_id") or row.get("pair_id"),
            "sample_id": row.get("sample_id") or row.get("condition_id") or row.get("benchmark_id") or row.get("pair_id"),
            "template": row.get("template") or "",
            "camera_motion": row.get("camera_motion") or row.get("camera_variant") or "",
            "prefix_len": int(row.get("prefix_len") or 5),
            "prediction_start_frame": int(row.get("prediction_start_frame") or 5),
            "prefix_video_path": row.get("prefix_video_path") or row.get("prefix") or "",
            "image_path": row.get("image_path") or row.get("condition_image_path") or row.get("image") or "",
            "prompt": row.get("prompt") or row.get("prompt_path") or "",
            "prompt_path": row.get("prompt_path") or row.get("prompt") or "",
            "poses_path": row.get("poses_path") or row.get("poses") or "",
            "intrinsics_path": row.get("intrinsics_path") or row.get("intrinsics") or "",
            "gt_full_video_path": row.get("gt_full_video_path") or row.get("full_video_path") or row.get("video") or "",
            "gt_future_video_path": row.get("gt_future_video_path") or row.get("future_video_path") or row.get("target_video") or "",
            "fps": float(row.get("fps") or 16.0),
            "height": int(row.get("height") or 0),
            "width": int(row.get("width") or 0),
            "num_frames": int(row.get("num_frames") or 0),
            "source_manifest": source,
            "source_pair_id": row.get("pair_id") or "",
        }
    c["source_manifest"] = c.get("source_manifest") or source
    c["source_pair_id"] = c.get("source_pair_id") or row.get("pair_id") or ""
    return c

def recover_condition(c: dict, out_root: Path) -> dict:
    c = dict(c)
    prefix = repo_path(c.get("prefix_video_path"))
    fut = repo_path(c.get("gt_future_video_path"))
    full = repo_path(c.get("gt_full_video_path"))
    sample = str(c.get("sample_id") or c.get("condition_id")).replace("/", "_")
    rec_dir = out_root / sample
    rec_dir.mkdir(parents=True, exist_ok=True)
    if (not prefix.exists() or not fut.exists()) and full.exists():
        try:
            frames, fps = read_video_frames(full)
            if len(frames) >= 81:
                if not prefix.exists():
                    p = rec_dir / "prefix_len5.mp4"
                    write_video(p, frames[:5], fps)
                    c["prefix_video_path"] = rel(p)
                if not fut.exists():
                    f = rec_dir / "clean_future_5_80.mp4"
                    write_video(f, frames[5:81], fps)
                    c["gt_future_video_path"] = rel(f)
                c["recover_method"] = "cut_from_full_video"
        except Exception as e:
            c["not_runnable_reason"] = f"recover_failed:{e}"
    return c

def runnable(c: dict):
    prefix = repo_path(c.get("prefix_video_path")); fut = repo_path(c.get("gt_future_video_path"))
    poses = repo_path(c.get("poses_path")); intr = repo_path(c.get("intrinsics_path")); prompt = c.get("prompt") or c.get("prompt_path")
    reasons = []
    if int(c.get("prefix_len") or 0) != 5: reasons.append("prefix_len_not_5")
    if int(c.get("prediction_start_frame") or 0) != 5: reasons.append("prediction_start_not_5")
    if not prefix.exists(): reasons.append("missing_prefix")
    if not fut.exists(): reasons.append("missing_gt_future")
    if not prompt: reasons.append("missing_prompt")
    if not poses.exists(): reasons.append("missing_poses")
    if not intr.exists(): reasons.append("missing_intrinsics")
    pinfo = video_info(prefix) if prefix.exists() else {}
    finfo = video_info(fut) if fut.exists() else {}
    if prefix.exists() and not pinfo.get("decodable"): reasons.append("prefix_undecodable")
    if fut.exists() and not finfo.get("decodable"): reasons.append("future_undecodable")
    if pinfo.get("frames", 0) and pinfo.get("frames", 0) < 5: reasons.append("prefix_too_short")
    if finfo.get("frames", 0) and finfo.get("frames", 0) < 40: reasons.append("future_too_short")
    info = {"prefix_frames": pinfo.get("frames", 0), "future_frames": finfo.get("frames", 0), "width": finfo.get("width") or pinfo.get("width") or c.get("width", 0), "height": finfo.get("height") or pinfo.get("height") or c.get("height", 0), "fps": finfo.get("fps") or pinfo.get("fps") or c.get("fps", 16)}
    return (not reasons), ";".join(reasons), info

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="*", default=["manifests", "reports", "local_assets"])
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--target_manifest", required=True)
    args = ap.parse_args()
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    rec_root = Path("local_assets/dpo_pair_factory_v11/recovered_conditions")
    seen = {}; manifests = []
    for p in KNOWN_MANIFESTS:
        if Path(p).exists(): manifests.append(Path(p))
    for p in Path("manifests").glob("*.jsonl"):
        if p not in manifests: manifests.append(p)
    for mp in manifests:
        for row in read_jsonl(mp):
            c = condition_from_row(row, str(mp)); key = condition_key(c)
            if not key or key in seen: continue
            c = recover_condition(c, rec_root)
            ok, reason, info = runnable(c); c.update(info)
            c["status"] = "runnable" if ok else "not_runnable"; c["not_runnable_reason"] = "" if ok else reason
            seen[key] = c
    rows = list(seen.values()); runnable_rows = [r for r in rows if r.get("status") == "runnable"]
    write_jsonl(Path(args.target_manifest), runnable_rows); write_csv(out / "condition_pool.csv", rows)
    counts = Counter(r.get("status") for r in rows); templates = Counter(r.get("template") for r in runnable_rows); cameras = Counter(r.get("camera_motion") for r in runnable_rows)
    status = "PASS" if len(runnable_rows) >= 100 else "MIXED"
    (out / "condition_pool_summary.md").write_text(f"Current Status: {status}\n\n# v11 Condition Pool Summary\n\n- Total discovered rows: {len(rows)}\n- Runnable prefix5 conditions: {len(runnable_rows)}\n- Status counts: `{dict(counts)}`\n- Template distribution: `{dict(templates)}`\n- Camera distribution: `{dict(cameras)}`\n- Target manifest: `{args.target_manifest}`\n")
    if len(runnable_rows) < 100:
        append_blocker(Path("reports/dpo_pair_factory_v11"), "MANIFEST_SCHEMA", "condition pool below preferred 100", {"runnable": len(runnable_rows)})
    print(json.dumps({"runnable": len(runnable_rows), "total": len(rows)}, indent=2))
if __name__ == "__main__": main()
