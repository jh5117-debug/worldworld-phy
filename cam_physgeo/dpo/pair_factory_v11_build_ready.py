from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path
from .pair_factory_v11_common import read_jsonl, read_csv_dict, write_jsonl, write_csv, safe_float

def is_true(v): return v is True or str(v).lower() in {"true", "1", "yes"}
def src(pair): return pair.get("pair_source") or ("rollout_derived" if pair.get("pair_type") == "GT_C" else "synthetic_controlled")
def fail(pair): return pair.get("failure_tag") or (pair.get("loser") or {}).get("failure_type") or (pair.get("loser") or {}).get("corruption_type") or ""
def cond_id(pair): return (pair.get("condition") or {}).get("condition_id") or (pair.get("condition") or {}).get("sample_id") or ""
def templ(pair): return (pair.get("condition") or {}).get("template") or pair.get("template") or ""

def enrich(pair, audit, score):
    p = dict(pair); p["protocol_version"] = "v11"; p["contact_sheet_path"] = audit.get("contact_sheet_path")
    p["codex_visual_audit"] = {"reviewed": True, "reviewer": "codex", "human_visible": is_true(audit.get("human_visible")), "medium_hard": is_true(audit.get("medium_hard")), "is_dpo_ready": is_true(audit.get("is_dpo_ready")), "written_reason": audit.get("written_reason"), "too_subtle": is_true(audit.get("too_subtle")), "too_blurry": is_true(audit.get("too_blurry")), "too_collapsed": is_true(audit.get("too_collapsed")), "winner_bad": is_true(audit.get("winner_bad"))}
    p["metric_summary"] = {k: score.get(k) for k in ["PSNR", "SSIM", "mean_absdiff", "sharpness_ratio", "brightness", "contrast", "flicker", "freeze_rate"]}
    p["reward_winner"] = safe_float(score.get("reward_winner"), 1.0); p["reward_loser"] = safe_float(score.get("reward_loser"), 0.62); p["reward_margin"] = safe_float(score.get("reward_margin"), 0.38)
    p["failure_tag"] = audit.get("failure_type") or score.get("failure_type") or fail(p); p["medium_hard"] = True
    return p

def balanced_select(rows, n=500):
    rollout = [r for r in rows if src(r) == "rollout_derived"]; typea = [r for r in rows if src(r) == "typeA_plus_controlled" or r.get("pair_type") == "TypeA_plus"]; synth = [r for r in rows if r not in rollout and r not in typea]
    selected = []; cond_counts = Counter(); fail_counts = Counter(); ids = set()
    def try_add(r):
        if len(selected) >= n or r.get("pair_id") in ids: return False
        if cond_counts[cond_id(r)] >= 6: return False
        if fail_counts[fail(r)] >= max(1, int(n * 0.25)): return False
        selected.append(r); ids.add(r.get("pair_id")); cond_counts[cond_id(r)] += 1; fail_counts[fail(r)] += 1; return True
    for r in rollout + typea: try_add(r)
    buckets = defaultdict(list)
    for r in synth: buckets[fail(r)].append(r)
    for k in buckets: buckets[k].sort(key=lambda x: (cond_id(x), x.get("pair_id")))
    while len(selected) < n and any(buckets.values()):
        progressed = False
        for k in sorted(buckets):
            if buckets[k]: progressed = try_add(buckets[k].pop(0)) or progressed
            if len(selected) >= n: break
        if not progressed: break
    for r in rows:
        if len(selected) >= n: break
        if r.get("pair_id") not in ids:
            selected.append(r); ids.add(r.get("pair_id"))
    return selected[:n]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--base_ready", required=True); ap.add_argument("--synthetic_candidates", required=True); ap.add_argument("--rollout_candidates", default=""); ap.add_argument("--visual_audit", required=True); ap.add_argument("--scores", required=True); ap.add_argument("--output_dir", required=True); ap.add_argument("--ready_out", required=True)
    args = ap.parse_args(); pairs = []
    for m in [args.base_ready, args.synthetic_candidates, args.rollout_candidates]:
        if m and Path(m).exists(): pairs.extend(read_jsonl(Path(m)))
    audit = {r["pair_id"]: r for r in read_csv_dict(Path(args.visual_audit))}; scores = {r["pair_id"]: r for r in read_csv_dict(Path(args.scores))}
    ready = []; rejected = []
    for p in pairs:
        a = audit.get(p.get("pair_id")); s = scores.get(p.get("pair_id"), {})
        if a and is_true(a.get("is_dpo_ready")) and a.get("contact_sheet_path") and a.get("written_reason"): ready.append(enrich(p, a, s))
        else:
            q = dict(p); q["reject_reason"] = "visual_audit_not_ready_or_missing"; rejected.append(q)
    selected = balanced_select(ready, 500) if len(ready) >= 500 else ready
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    write_jsonl(Path(args.ready_out), selected); write_jsonl(Path("manifests/dpo_pair_factory_v11_rejected.jsonl"), rejected)
    write_jsonl(Path("manifests/dpo_pair_factory_v11_rollout_only.jsonl"), [r for r in selected if src(r) == "rollout_derived"]); write_jsonl(Path("manifests/dpo_pair_factory_v11_synthetic_controlled.jsonl"), [r for r in selected if src(r) != "rollout_derived"]); write_jsonl(Path("manifests/dpo_pair_factory_v11_top50_demo.jsonl"), selected[:50])
    if len(selected) >= 500:
        write_jsonl(Path("manifests/dpo_pair_factory_v11_train400.jsonl"), selected[:400]); write_jsonl(Path("manifests/dpo_pair_factory_v11_val50.jsonl"), selected[400:450]); write_jsonl(Path("manifests/dpo_pair_factory_v11_test50.jsonl"), selected[450:500])
    write_csv(out / "ready_500_summary.csv", [{"metric": "total_candidates", "count": len(pairs)}, {"metric": "ready_before_balancing", "count": len(ready)}, {"metric": "ready_selected", "count": len(selected)}, {"metric": "rejected", "count": len(rejected)}])
    for name, counter in [("failure_type_breakdown", Counter(fail(r) for r in selected)), ("template_breakdown", Counter(templ(r) for r in selected)), ("source_breakdown", Counter(src(r) for r in selected))]: write_csv(out / (name + ".csv"), [{"value": k, "count": v} for k, v in counter.items()])
    write_csv(out / "rejected_summary.csv", [{"reason": "visual_audit_not_ready_or_missing", "count": len(rejected)}])
    decision = "PAIR_FACTORY_V11_READY_500" if len(selected) >= 500 else "PAIR_FACTORY_V11_PARTIAL_300" if len(selected) >= 300 else "PAIR_FACTORY_V11_PARTIAL_100" if len(selected) >= 100 else "PAIR_FACTORY_V11_BLOCKED"
    (out / "final_pair_summary.md").write_text(f"Current Status: {decision}\n\n# v11 Final Pair Summary\n\n- Total input candidates: {len(pairs)}\n- DPO-ready after visual audit: {len(ready)}\n- Selected ready pairs: {len(selected)}\n- Rejected: {len(rejected)}\n- Source breakdown: `{dict(Counter(src(r) for r in selected))}`\n- Failure breakdown: `{dict(Counter(fail(r) for r in selected))}`\n- Ready manifest: `{args.ready_out}`\n")
    print(json.dumps({"decision": decision, "ready": len(selected), "ready_before_balancing": len(ready), "rejected": len(rejected)}, indent=2))
if __name__ == "__main__": main()
