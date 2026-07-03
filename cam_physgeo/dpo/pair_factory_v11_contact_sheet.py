from __future__ import annotations
import argparse, json
from pathlib import Path
import cv2
import numpy as np
from .pair_factory_v11_common import read_jsonl, read_csv_dict, write_csv, repo_path, rel, read_video_frames, sample_frames, safe_float

def label(img, text, color=(255, 255, 255), bg=(0, 0, 0)):
    out = img.copy(); h, w = out.shape[:2]
    cv2.rectangle(out, (0, 0), (w, 34), bg, -1); cv2.putText(out, text[:95], (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2, cv2.LINE_AA)
    return out

def thumb_row(frames, width=220, height=124):
    thumbs = [cv2.resize(fr, (width, height)) for fr in frames]
    return np.hstack(thumbs) if thumbs else np.zeros((height, width, 3), np.uint8)

def make_sheet(pair, score, out_dir):
    prefix = (pair.get("condition") or {}).get("prefix_video_path") or pair.get("prefix_video_path")
    win = (pair.get("winner") or {}).get("future_video_path") or pair.get("winner_video_path")
    lose = (pair.get("loser") or {}).get("future_video_path") or pair.get("loser_video_path")
    pf, _ = read_video_frames(repo_path(prefix), max_frames=5); wf, _ = read_video_frames(repo_path(win), max_frames=76); lf, _ = read_video_frames(repo_path(lose), max_frames=76)
    p = sample_frames(pf, 5); w = sample_frames(wf, 5); l = sample_frames(lf, 5)
    if not (p and w and l): raise RuntimeError("missing frames")
    diff = []
    for a, b in zip(w, l):
        if a.shape != b.shape: b = cv2.resize(b, (a.shape[1], a.shape[0]))
        heat = cv2.applyColorMap(cv2.cvtColor(cv2.absdiff(a, b), cv2.COLOR_BGR2GRAY), cv2.COLORMAP_JET); diff.append(heat)
    row1 = label(thumb_row(p), "PREFIX / CONDITION frames 0-4", (255, 255, 255), (60, 60, 60))
    row2 = label(thumb_row(w), f"WIN clean future | R={safe_float(score.get('reward_winner'), 1.0):.3f}", (80, 255, 80), (0, 70, 0))
    row3 = label(thumb_row(l), f"LOSE {score.get('failure_type', '')} | R={safe_float(score.get('reward_loser'), 0):.3f} margin={safe_float(score.get('reward_margin'), 0):.3f}", (80, 80, 255), (0, 0, 90))
    row4 = label(thumb_row(diff), "DIFF heatmap / affected region proxy", (255, 255, 255), (70, 30, 30))
    sheet = np.vstack([row1, row2, row3, row4]); title = np.zeros((80, sheet.shape[1], 3), np.uint8); title[:] = (25, 25, 25)
    txt = f"{pair.get('pair_id')} | {pair.get('pair_type')} | source={pair.get('pair_source')} | failure={score.get('failure_type', '')}"
    cv2.putText(title, txt[:125], (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(title, "DPO CANDIDATE: requires Codex visual audit before ready500", (12, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (210, 210, 210), 1, cv2.LINE_AA)
    sheet = np.vstack([title, sheet]); out_dir.mkdir(parents=True, exist_ok=True); path = out_dir / (pair.get("pair_id") + ".jpg")
    cv2.imwrite(str(path), sheet, [int(cv2.IMWRITE_JPEG_QUALITY), 92]); return path

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidate_manifest", action="append", required=True); ap.add_argument("--score_csv", required=True); ap.add_argument("--output_dir", required=True); ap.add_argument("--manifest_out", required=True)
    args = ap.parse_args(); scores = {r["pair_id"]: r for r in read_csv_dict(Path(args.score_csv))}; pairs = []
    for m in args.candidate_manifest: pairs.extend(read_jsonl(Path(m)))
    rows = []; out = Path(args.output_dir)
    for p in pairs:
        pid = p.get("pair_id"); sc = scores.get(pid, {})
        try: path = make_sheet(p, sc, out); status = "CONTACT_SHEET_PASS"; err = ""
        except Exception as e: path = ""; status = "CONTACT_SHEET_FAIL"; err = str(e)
        rows.append({"pair_id": pid, "contact_sheet_path": rel(path) if path else "", "status": status, "error_reason": err, "pair_type": p.get("pair_type"), "source": p.get("pair_source"), "failure_type": sc.get("failure_type") or (p.get("loser") or {}).get("failure_type", "")})
    write_csv(Path(args.manifest_out), rows)
    print(json.dumps({"contact_sheets": sum(1 for r in rows if r["status"] == "CONTACT_SHEET_PASS"), "total": len(rows)}, indent=2))
if __name__ == "__main__": main()
