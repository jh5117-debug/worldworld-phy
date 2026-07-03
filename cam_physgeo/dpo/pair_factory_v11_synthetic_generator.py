from __future__ import annotations
import argparse, json, random
from collections import Counter
from pathlib import Path
import cv2
import numpy as np
from .pair_factory_v11_common import read_jsonl, write_jsonl, write_csv, repo_path, rel, read_video_frames, write_video

FAILURES = ["background_drift_visible", "wrong_camera_motion_visible", "object_deformation_visible", "object_identity_color_shift", "object_duplicate_or_fragment", "reobserve_mismatch_visible", "partial_freeze_foreground", "local_scene_patch_drift", "containment_failure_synthetic", "collision_response_failure_synthetic", "roll_event_fragment_synthetic", "drop_motion_failure_synthetic"]

def bbox_for(frame, seed):
    h, w = frame.shape[:2]; rng = random.Random(seed)
    bw = max(48, int(w * rng.uniform(0.16, 0.28))); bh = max(48, int(h * rng.uniform(0.16, 0.30)))
    x = int(rng.uniform(w * 0.20, w * 0.70)); y = int(rng.uniform(h * 0.20, h * 0.70))
    return max(0, min(w - bw, x)), max(0, min(h - bh, y)), bw, bh

def paste_patch(dst, patch, x, y):
    h, w = patch.shape[:2]; H, W = dst.shape[:2]
    x = max(0, min(W - 1, x)); y = max(0, min(H - 1, y)); w = min(w, W - x); h = min(h, H - y)
    if w > 0 and h > 0: dst[y:y+h, x:x+w] = patch[:h, :w]
    return dst

def corrupt(frames, failure, severity, seed):
    rng = random.Random(seed); out = [f.copy() for f in frames]; n = len(out)
    x, y, bw, bh = bbox_for(out[n // 2], seed)
    start = int(n * rng.uniform(0.18, 0.42)); end = int(n * rng.uniform(0.68, 0.94)); end = max(start + 8, min(n, end))
    dx = int(rng.choice([-1, 1]) * severity * bw * 0.42); dy = int(rng.choice([-1, 1]) * severity * bh * 0.28)
    frozen = out[start][y:y+bh, x:x+bw].copy()
    for t in range(start, end):
        fr = out[t]; patch = fr[y:y+bh, x:x+bw].copy(); phase = (t - start + 1) / max(1, end - start + 1)
        if failure in {"background_drift_visible", "local_scene_patch_drift"}:
            shifted = np.roll(patch, int(dx * phase), axis=1); fr[y:y+bh, x:x+bw] = cv2.addWeighted(patch, 0.35, shifted, 0.65, 0)
        elif failure == "wrong_camera_motion_visible":
            M = np.float32([[1, 0, int(dx * phase)], [0, 1, int(dy * phase)]])
            warped = cv2.warpAffine(fr, M, (fr.shape[1], fr.shape[0]), borderMode=cv2.BORDER_REFLECT)
            fr[y:y+bh, x:x+bw] = cv2.addWeighted(fr[y:y+bh, x:x+bw], 0.35, warped[y:y+bh, x:x+bw], 0.65, 0)
        elif failure == "object_deformation_visible":
            patch2 = cv2.resize(patch, (max(2, int(bw * (1 + severity * 0.35))), max(2, int(bh * (1 - severity * 0.22)))))
            fr[y:y+bh, x:x+bw] = cv2.resize(patch2, (bw, bh))
        elif failure == "object_identity_color_shift":
            hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).astype(np.int16); hsv[:, :, 0] = (hsv[:, :, 0] + int(50 * severity) + 10) % 180; hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1 + 0.65 * severity), 0, 255)
            fr[y:y+bh, x:x+bw] = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        elif failure == "object_duplicate_or_fragment":
            small = cv2.resize(patch, (max(8, bw // 2), max(8, bh // 2))); paste_patch(fr, small, x + dx, y + dy)
        elif failure == "reobserve_mismatch_visible":
            if t > (start + end) // 2: fr[y:y+bh, x:x+bw] = cv2.flip(patch, 1)
        elif failure == "partial_freeze_foreground":
            fr[y:y+bh, x:x+bw] = frozen
        else:
            M = np.float32([[1, 0, int(dx * 1.1)], [0, 1, int(dy * 1.1)]])
            moved = cv2.warpAffine(patch, M, (bw, bh), borderMode=cv2.BORDER_REFLECT)
            fr[y:y+bh, x:x+bw] = cv2.addWeighted(patch, 0.30, moved, 0.70, 0)
            if "collision" in failure or "fragment" in failure:
                small = cv2.resize(patch, (max(8, bw // 3), max(8, bh // 3))); paste_patch(fr, small, x + bw // 2, y + bh // 2)
    return out, (x, y, bw, bh), (start, end)

def choose_failures(template):
    table = {"drop": ["drop_motion_failure_synthetic", "object_duplicate_or_fragment", "local_scene_patch_drift", "object_identity_color_shift", "partial_freeze_foreground", "wrong_camera_motion_visible"], "collision": ["collision_response_failure_synthetic", "object_deformation_visible", "object_duplicate_or_fragment", "local_scene_patch_drift", "background_drift_visible", "object_identity_color_shift"], "roll": ["roll_event_fragment_synthetic", "wrong_camera_motion_visible", "object_deformation_visible", "partial_freeze_foreground", "background_drift_visible", "object_identity_color_shift"], "containment": ["containment_failure_synthetic", "reobserve_mismatch_visible", "object_duplicate_or_fragment", "local_scene_patch_drift", "partial_freeze_foreground", "object_identity_color_shift"]}
    return table.get(template, FAILURES[:6])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--conditions", required=True); ap.add_argument("--target_pairs", type=int, default=600); ap.add_argument("--max_pairs_per_condition", type=int, default=6); ap.add_argument("--output_root", required=True); ap.add_argument("--manifest_out", required=True); ap.add_argument("--report", required=True)
    args = ap.parse_args(); conds = read_jsonl(Path(args.conditions)); rows = []; report = []; out_root = Path(args.output_root)
    for ci, cond in enumerate(conds):
        if len(rows) >= args.target_pairs: break
        fut = repo_path(cond.get("gt_future_video_path"))
        if not fut.exists(): continue
        try: frames, fps = read_video_frames(fut)
        except Exception as e: report.append({"condition_id": cond.get("condition_id"), "status": "decode_fail", "error": str(e)}); continue
        if len(frames) < 40: continue
        for j, failure in enumerate(choose_failures(cond.get("template", ""))[:args.max_pairs_per_condition]):
            if len(rows) >= args.target_pairs: break
            severity = 0.35 + 0.30 * ((ci + j) % 7) / 6.0; seed = abs(hash((cond.get("condition_id"), failure, j))) % (10 ** 8)
            loser_frames, bbox, tspan = corrupt(frames[:76], failure, severity, seed)
            safe_sample = str(cond.get("sample_id") or cond.get("condition_id")).replace("/", "_")
            pair_id = f"v11_SYN_{len(rows)+1:04d}_{safe_sample}_{failure}"; pair_dir = out_root / "pairs" / pair_id; loser_path = pair_dir / "loser_future.mp4"
            try: write_video(loser_path, loser_frames[:76], fps)
            except Exception as e: report.append({"pair_id": pair_id, "condition_id": cond.get("condition_id"), "failure_type": failure, "status": "write_fail", "error": str(e)}); continue
            row = {"pair_id": pair_id, "protocol_version": "v11", "pair_type": "TypeM_v11_synthetic_visible", "pair_source": "synthetic_controlled", "is_synthetic": True, "is_rollout_derived": False, "is_controlled_corruption": True, "condition": cond, "winner": {"future_video_path": cond.get("gt_future_video_path"), "full_video_path": cond.get("gt_full_video_path"), "source": "clean_gt", "reward_vector": {"R_total": 1.0, "backend": "gt_assumed_upper_bound"}}, "loser": {"future_video_path": rel(loser_path), "source": "controlled_synthetic_v11", "corruption_type": failure, "failure_type": failure, "severity": round(severity, 3), "affected_region": {"x": bbox[0], "y": bbox[1], "w": bbox[2], "h": bbox[3]}, "affected_time_span": [int(tspan[0]), int(tspan[1])], "synthetic_visible": True}, "same_prefix": True, "same_prompt": True, "same_poses": True, "same_intrinsics": True, "prefix_len": 5, "prediction_start_frame": 5, "loss_frame_indices": list(range(5, 81)), "reward_frame_indices": list(range(5, 81)), "medium_hard_candidate": True}
            rows.append(row); report.append({"pair_id": pair_id, "condition_id": cond.get("condition_id"), "failure_type": failure, "severity": round(severity, 3), "loser_video_path": rel(loser_path), "status": "generated"})
    write_jsonl(Path(args.manifest_out), rows); write_csv(Path(args.report), report)
    counts = Counter(r.get("failure_type") for r in report if r.get("status") == "generated")
    Path(args.report).parent.joinpath("synthetic_generation_summary.md").write_text(f"Current Status: {'PASS' if len(rows) >= args.target_pairs else 'MIXED'}\n\n# v11 Synthetic Generation Summary\n\n- Generated candidates: {len(rows)}\n- Target: {args.target_pairs}\n- Failure distribution: `{dict(counts)}`\n- Manifest: `{args.manifest_out}`\n")
    print(json.dumps({"generated": len(rows), "target": args.target_pairs}, indent=2))
if __name__ == "__main__": main()
