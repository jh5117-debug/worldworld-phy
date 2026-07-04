"""Run v12 winner-anchor-only LoRA scope sanity on a reviewed pair cache."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from cam_physgeo.dpo.lora_scope_config_v12 import SCOPE_CANDIDATES
from cam_physgeo.dpo.pair_cache_builder_v8m import build_pair_cache
from cam_physgeo.dpo.pair_cache_objective_runner import run_objective


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows=[]
    if path.exists():
        with path.open() as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def _ensure_cache(args: argparse.Namespace) -> Path:
    cache_root = Path(args.cache_root)
    index = cache_root / "cache_index.jsonl"
    if index.exists():
        cached_rows = _read_jsonl(index)
        pass_rows = [row for row in cached_rows if str(row.get('status', row.get('cache_status', ''))).upper() in {'PASS', 'PAIR_CACHE_PASS'} and row.get('cache_tensor_path')]
        if len(pass_rows) >= int(args.num_pairs):
            return index
    ns = SimpleNamespace(
        pair_manifest=args.pair_manifest,
        num_pairs=int(args.num_pairs),
        gpu=int(args.gpu),
        prefix_len=5,
        prediction_start_frame=5,
        future_only="true",
        used_window_frames=int(args.used_window_frames),
        output_root=str(cache_root),
        report=str(Path(args.output_dir) / "scope_sanity_cache_build.csv"),
        progress=str(Path(args.output_dir) / "scope_sanity_cache_progress.jsonl"),
        heartbeat_seconds=15.0,
        per_stage_timeout_seconds=180.0,
        per_pair_timeout_seconds=600.0,
        config=args.config,
        repo_root=".",
        runtime_device="cuda",
        height=int(args.height),
        width=int(args.width),
        target_sigma=float(args.target_sigma),
        seed=int(args.seed),
        loader_mode="safe_wan_policy_only",
    )
    build_pair_cache(ns)
    if not index.exists():
        raise RuntimeError(f"cache index not written: {index}")
    return index


def _summarize_one(csv_path: Path, summary_json: Path, scope: str) -> dict[str, Any]:
    rows=[]
    if csv_path.exists():
        with csv_path.open() as f:
            rows=list(csv.DictReader(f))
    js={}
    if summary_json.exists():
        js=json.loads(summary_json.read_text())
    pass_rows=[r for r in rows if r.get("status")=="PASS"]
    def mean(key):
        vals=[]
        for r in pass_rows:
            try: vals.append(float(r.get(key,"")))
            except Exception: pass
        return "" if not vals else sum(vals)/len(vals)
    return {
        "scope": scope,
        "status": js.get("status", "NO_SUMMARY"),
        "rows_written": len(rows),
        "pass_rows": len(pass_rows),
        "mean_winner_improvement_post": js.get("mean_winner_improvement_post", mean("winner_improvement_post")),
        "final_winner_improvement_post": js.get("final_winner_improvement_post", pass_rows[-1].get("winner_improvement_post", "") if pass_rows else ""),
        "mean_loser_degradation_post": js.get("mean_loser_degradation_post", mean("loser_degradation_post")),
        "mean_winner_contribution_ratio_post": js.get("mean_winner_contribution_ratio_post", mean("winner_contribution_ratio_post")),
        "csv": str(csv_path),
    }


def _write_summary(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    fields=["scope","status","rows_written","pass_rows","mean_winner_improvement_post","final_winner_improvement_post","mean_loser_degradation_post","mean_winner_contribution_ratio_post","csv"]
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir/"scope_sanity_summary.csv").open("w", newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    passing=[]
    for r in rows:
        try:
            if r["status"] == "WINNER_ANCHOR_REPEAT_PASS" and float(r["mean_winner_improvement_post"]) > 0 and float(r["final_winner_improvement_post"]) > 0:
                passing.append(r)
        except Exception:
            pass
    best=None
    if passing:
        passing.sort(key=lambda r: (float(r["mean_winner_improvement_post"]), -float(r.get("mean_loser_degradation_post") or 0)), reverse=True)
        best=passing[0]
    decision={"passing_scopes":[r["scope"] for r in passing],"best_scope": best["scope"] if best else None,"decision":"SCOPE_PASS" if best else "SCOPE_BLOCKED"}
    (out_dir.parent/"best_lora_scope_decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True)+"\n")
    with (out_dir/"scope_sanity_summary.md").open("w") as f:
        f.write("Current Status: {}\n\n# v12 LoRA Scope Winner-Anchor Sanity\n\n".format(decision["decision"]))
        for r in rows:
            f.write("## {}\n\n".format(r["scope"]))
            f.write("- Status: `{}`\n".format(r["status"]))
            f.write("- Rows/pass: {} / {}\n".format(r["rows_written"], r["pass_rows"]))
            f.write("- Mean winner improvement post: `{}`\n".format(r["mean_winner_improvement_post"]))
            f.write("- Final winner improvement post: `{}`\n".format(r["final_winner_improvement_post"]))
            f.write("- Mean loser degradation post: `{}`\n".format(r["mean_loser_degradation_post"]))
            f.write("- Winner contribution ratio: `{}`\n\n".format(r["mean_winner_contribution_ratio_post"]))
        f.write("Decision: `{}`; best scope: `{}`. DPO may run only if decision is SCOPE_PASS.\n".format(decision["decision"], decision["best_scope"]))


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--pair_manifest", required=True)
    ap.add_argument("--cache_root", required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--scopes", default="L0_camera_r4,L1_camera_r8,L2_camera_temporal_r4,L3_camera_cross_r4")
    ap.add_argument("--steps", type=int, default=5)
    ap.add_argument("--num_pairs", type=int, default=16)
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--width", type=int, default=832)
    ap.add_argument("--used_window_frames", type=int, default=49)
    ap.add_argument("--target_sigma", type=float, default=0.35)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--lr", type=float, default=1e-6)
    args=ap.parse_args()
    out_dir=Path(args.output_dir)
    index=_ensure_cache(args)
    rows=[]
    for scope in [s.strip() for s in args.scopes.split(",") if s.strip()]:
        if scope not in SCOPE_CANDIDATES:
            raise KeyError(scope)
        csv_path=out_dir / f"{scope}_{int(args.steps)}step.csv"
        ns=SimpleNamespace(
            cache_root=args.cache_root,
            pair_subset=str(index),
            objective="winner_anchor_repeat",
            steps=int(args.steps),
            gpu=int(args.gpu),
            output=str(csv_path),
            scope=scope,
            config=args.config,
            height=int(args.height),
            width=int(args.width),
            used_window_frames=int(args.used_window_frames),
            lr=float(args.lr),
            beta=1.0,
            u_clip=1.0,
            lambda_winner_anchor=1.0,
            max_lambda_loser=0.0,
            gradient_checkpointing=True,
        )
        try:
            run_objective(ns)
        except Exception as exc:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            with csv_path.open("w", newline="") as f:
                w=csv.DictWriter(f, fieldnames=["scope","status","error_reason"]); w.writeheader(); w.writerow({"scope":scope,"status":"RUNTIME_FAIL","error_reason":repr(exc)})
            csv_path.with_suffix(".summary.json").write_text(json.dumps({"status":"RUNTIME_FAIL","error_reason":repr(exc)}, indent=2)+"\n")
        rows.append(_summarize_one(csv_path, csv_path.with_suffix(".summary.json"), scope))
    _write_summary(out_dir, rows)


if __name__ == "__main__":
    main()
