from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from cam_physgeo.eval.run_inference import (
    prepare_fast_runtime_bundle,
    run_one_sample,
)
from cam_physgeo.eval.make_rollout_comparison_videos import build_comparison_videos
from cam_physgeo.training.model_loading import resolve_model_paths
from cam_physgeo.utils.io import load_yaml, read_jsonl, write_json


def _bool_arg(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in {"1", "true", "yes", "y", "on"}


def _row_id(row: dict[str, Any]) -> str:
    return str(row.get("condition_id") or row.get("sample_id") or Path(str(row.get("sample_dir") or "")).name)


def _link_or_copy(src: str | Path, dst: Path) -> str:
    src = Path(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        return str(dst)
    try:
        os.symlink(src.resolve(), dst)
    except OSError:
        shutil.copy2(src, dst)
    return str(dst)


def _condition_dir_from_manifest(row: dict[str, Any], out_dir: Path) -> Path:
    sid = _row_id(row)
    sample_dir = out_dir / "conditions" / sid
    sample_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "image.jpg": row.get("image_path") or Path(str(row.get("sample_dir"))) / "image.jpg",
        "target.mp4": row.get("target_video_path") or Path(str(row.get("sample_dir"))) / "target.mp4",
        "poses.npy": row.get("poses_path") or Path(str(row.get("sample_dir"))) / "poses.npy",
        "intrinsics.npy": row.get("intrinsics_path") or Path(str(row.get("sample_dir"))) / "intrinsics.npy",
        "action.npy": row.get("action_path") or Path(str(row.get("sample_dir"))) / "action.npy",
        "prompt.txt": row.get("prompt_path") or Path(str(row.get("sample_dir"))) / "prompt.txt",
        "metadata.json": row.get("metadata_path") or Path(str(row.get("sample_dir"))) / "metadata.json",
    }
    for name, src in mapping.items():
        if src and Path(src).exists():
            _link_or_copy(src, sample_dir / name)
    return sample_dir


def _select_conditions(rows: list[dict[str, Any]], templates: list[str], count: int, seed: int) -> list[dict[str, Any]]:
    by_template: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        template = str(row.get("template") or "")
        if not template:
            sid = _row_id(row)
            for candidate in templates:
                if f"_{candidate}_" in f"_{sid}_":
                    template = candidate
                    row = dict(row)
                    row["template"] = candidate
                    break
        if template in templates:
            by_template[template].append(row)
    rng = random.Random(int(seed))
    for values in by_template.values():
        rng.shuffle(values)
    selected: list[dict[str, Any]] = []
    cursor = {template: 0 for template in templates}
    while len(selected) < count:
        made_progress = False
        for template in templates:
            values = by_template.get(template) or []
            idx = cursor[template]
            if idx >= len(values):
                continue
            selected.append(values[idx])
            cursor[template] = idx + 1
            made_progress = True
            if len(selected) >= count:
                break
        if not made_progress:
            break
    return selected


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(rows),
        "template_distribution": dict(Counter(str(r.get("template") or "unknown") for r in rows)),
        "camera_distribution": dict(Counter(str(r.get("camera_variant") or "unknown") for r in rows)),
        "sample_ids": [_row_id(r) for r in rows],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/cam_physgeo/eval.yaml")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--condition_manifest", default="")
    ap.add_argument("--adapter_checkpoint", required=True)
    ap.add_argument("--stageB_adapter_checkpoint", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--num_conditions", type=int, default=12)
    ap.add_argument("--samples_per_condition", type=int, default=1)
    ap.add_argument("--templates", nargs="+", default=["drop", "collision", "roll", "containment"])
    ap.add_argument("--num_frames", type=int, default=81)
    ap.add_argument("--num_steps", type=int, default=2)
    ap.add_argument("--resolution", default="480x832")
    ap.add_argument("--use_action", default="false")
    ap.add_argument("--seed", type=int, default=123)
    ap.add_argument("--run_base", default="true")
    ap.add_argument("--run_adapter", default="true")
    ap.add_argument("--make_contact_sheet", default="true")
    ap.add_argument("--make_comparison_videos", default="true")
    ap.add_argument("--comparison_panel_size", default="832x480")
    ap.add_argument("--local_files_only", default="true")
    ap.add_argument("--lingbot_env", default="")
    ap.add_argument("--timeout_sec", type=int, default=1200)
    ap.add_argument("--timeout_per_video", type=int, default=0)
    ap.add_argument("--stop_on_first_adapter_load_failure", default="false")
    ap.add_argument("--dry_run", default="false")
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.condition_manifest:
        rows = list(read_jsonl(args.condition_manifest))
        selected = rows[: int(args.num_conditions)]
    elif args.manifest:
        rows = list(read_jsonl(args.manifest))
        selected = _select_conditions(rows, args.templates, int(args.num_conditions), int(args.seed))
    else:
        raise SystemExit("pass --condition_manifest or --manifest")
    if len(selected) < int(args.num_conditions):
        raise SystemExit(f"selected only {len(selected)} conditions")
    condition_dirs = [_condition_dir_from_manifest(row, out_dir) for row in selected]

    payload: dict[str, Any] = {
        "status": "planned",
        "manifest": args.manifest,
        "condition_manifest": args.condition_manifest,
        "adapter_checkpoint": args.adapter_checkpoint,
        "stageB_adapter_checkpoint": args.stageB_adapter_checkpoint,
        "out": str(out_dir),
        "selected": _summarize_rows(selected),
        "selected_rows": selected,
        "condition_dirs": [str(path) for path in condition_dirs],
        "run_base": _bool_arg(args.run_base),
        "run_adapter": _bool_arg(args.run_adapter),
        "use_action": _bool_arg(args.use_action),
        "num_frames": int(args.num_frames),
        "num_steps": int(args.num_steps),
        "resolution": args.resolution,
        "dry_run": _bool_arg(args.dry_run),
        "timeout_per_video": int(args.timeout_per_video or args.timeout_sec),
        "stop_on_first_adapter_load_failure": _bool_arg(args.stop_on_first_adapter_load_failure),
        "make_comparison_videos": _bool_arg(args.make_comparison_videos),
        "comparison_panel_size": args.comparison_panel_size,
        "results": [],
    }
    write_json(payload, out_dir / "rollout_plan.json")
    if _bool_arg(args.dry_run):
        payload["status"] = "dry_run_only"
        write_json(payload, out_dir / "rollout_summary.json")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    paths_cfg = load_yaml("configs/cam_physgeo/paths.yaml")
    paths = resolve_model_paths(paths_cfg)
    runtime_bundle = prepare_fast_runtime_bundle(paths, paths_cfg)
    if not runtime_bundle.get("ok"):
        payload["status"] = "blocked_runtime_bundle"
        payload["runtime_bundle"] = runtime_bundle
        write_json(payload, out_dir / "rollout_summary.json")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2

    variants = []
    if _bool_arg(args.run_base):
        variants.append(("base", ""))
    if _bool_arg(args.run_adapter):
        variants.append(("stageA_adapter", args.adapter_checkpoint))
    if args.stageB_adapter_checkpoint:
        variants.append(("stageB_adapter", args.stageB_adapter_checkpoint))

    start = time.time()
    for label, ckpt in variants:
        variant_root = out_dir / label
        for sample_dir in condition_dirs:
            result = run_one_sample(
                sample_dir=sample_dir,
                out_root=variant_root,
                paths=paths,
                runtime_bundle=runtime_bundle,
                num_frames=int(args.num_frames),
                num_steps=int(args.num_steps),
                resolution=args.resolution,
                save_contact_sheet=_bool_arg(args.make_contact_sheet),
                env_path=args.lingbot_env or str(paths_cfg.get("LINGBOT_ENV") or ""),
                timeout_sec=int(args.timeout_per_video or args.timeout_sec),
                local_files_only=_bool_arg(args.local_files_only),
                debug_camera_condition=True,
                save_condition_summary=True,
                assert_camera_used=True,
                fail_if_camera_unused=True,
                adapter_checkpoint=ckpt,
            )
            result["eval_label"] = label
            result["condition_sample_id"] = sample_dir.name
            payload["results"].append(result)
            write_json(payload, out_dir / "rollout_summary.json")
            if label == "stageA_adapter" and not result.get("ok") and _bool_arg(args.stop_on_first_adapter_load_failure):
                log_tail = str(result.get("log_tail") or result.get("error") or "")
                if "adapter_load_failed" in log_tail or "adapter_load" in log_tail:
                    payload.update(
                        {
                            "status": "failed_adapter_load",
                            "ok_count": sum(1 for row in payload["results"] if row.get("ok")),
                            "fail_count": sum(1 for row in payload["results"] if not row.get("ok")),
                            "failed_condition": sample_dir.name,
                        }
                    )
                    write_json(payload, out_dir / "rollout_summary.json")
                    print(json.dumps(payload, indent=2, ensure_ascii=False))
                    return 2
        if label == "base":
            base_fail = sum(1 for row in payload["results"] if row.get("eval_label") == "base" and not row.get("ok"))
            if base_fail:
                payload.update(
                    {
                        "status": "blocked_adapter_due_base_failure",
                        "ok_count": sum(1 for row in payload["results"] if row.get("ok")),
                        "fail_count": sum(1 for row in payload["results"] if not row.get("ok")),
                        "base_fail_count": base_fail,
                    }
                )
                write_json(payload, out_dir / "rollout_summary.json")
                print(json.dumps(payload, indent=2, ensure_ascii=False))
                return 2

    ok = sum(1 for row in payload["results"] if row.get("ok"))
    fail = len(payload["results"]) - ok
    comparison_summary: dict[str, Any] | None = None
    if _bool_arg(args.make_comparison_videos):
        width, height = [int(x) for x in str(args.comparison_panel_size).lower().split("x", 1)]
        comparison_variants = [("base", "Base"), ("stageA_adapter", "Stage A")]
        if args.stageB_adapter_checkpoint:
            comparison_variants.append(("stageB_adapter", "Stage B"))
        comparison_summary = build_comparison_videos(
            rollout_root=out_dir,
            variants=comparison_variants,
            panel_width=width,
            panel_height=height,
            overwrite=True,
        )
    payload.update(
        {
            "status": "passed_rollout_compare" if fail == 0 else "failed_rollout_compare",
            "ok_count": ok,
            "fail_count": fail,
            "elapsed_sec": time.time() - start,
            "comparison_videos": comparison_summary,
        }
    )
    write_json(payload, out_dir / "rollout_summary.json")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
