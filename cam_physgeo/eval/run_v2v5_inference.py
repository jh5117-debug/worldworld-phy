"""Run honest prefix-aware V2V-5 LingBot-Fast inference."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.eval.prefix_video_condition import (
    extract_prefix_future,
    make_prefix_future_contact_sheet,
    read_video_tensor,
    write_video_tensor,
)
from cam_physgeo.eval.run_fast_adapter_inference import DEFAULT_FAST_ROOT, DEFAULT_LINGBOT_CODE, _install_paths, _load_adapter
from cam_physgeo.eval.v2v5_generation_wrapper import generate_v2v5_fast


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _resolve(path: str | Path, *, repo_root: Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root / p


def _read_prompt(value: str, *, repo_root: Path) -> str:
    p = _resolve(value, repo_root=repo_root)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8").strip()
    return str(value).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _screen_row_from_pair(pair: dict[str, Any]) -> dict[str, Any]:
    condition = pair.get("condition") or {}
    winner = pair.get("winner") or {}
    return {
        "sample_id": pair.get("pair_id") or condition.get("sample_id") or "pair",
        "template": pair.get("template") or condition.get("template") or "",
        "camera_motion": pair.get("camera_motion") or condition.get("camera_motion") or condition.get("camera_variant") or "",
        "prefix_len": condition.get("prefix_len", pair.get("prefix_len", 5)),
        "prediction_start_frame": condition.get("prediction_start_frame", pair.get("prediction_start_frame", 5)),
        "prefix_video_path": condition.get("prefix_video_path"),
        "condition_image_path": condition.get("image"),
        "prompt": condition.get("prompt"),
        "poses": condition.get("poses"),
        "intrinsics": condition.get("intrinsics"),
        "gt_full_video_path": winner.get("full_video_path"),
        "gt_future_video_path": winner.get("future_video_path"),
        "source_pair_id": pair.get("pair_id"),
    }


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    if "condition" in row and "winner" in row:
        return _screen_row_from_pair(row)
    out = dict(row)
    out.setdefault("prefix_len", 5)
    out.setdefault("prediction_start_frame", 5)
    out.setdefault("prefix_video_path", row.get("prefix") or row.get("condition_prefix_path"))
    out.setdefault("poses", row.get("poses_path"))
    out.setdefault("intrinsics", row.get("intrinsics_path"))
    out.setdefault("gt_full_video_path", row.get("target_mp4") or row.get("target_video") or row.get("video"))
    out.setdefault("gt_future_video_path", row.get("future_video_path") or row.get("gt_future_video_path"))
    return out


def _copy_condition_files(row: dict[str, Any], dst: Path, *, repo_root: Path) -> Path:
    dst.mkdir(parents=True, exist_ok=True)
    for key, name in (("poses", "poses.npy"), ("intrinsics", "intrinsics.npy")):
        src = _resolve(str(row.get(key) or ""), repo_root=repo_root)
        if not src.exists():
            raise FileNotFoundError(f"missing {key}: {src}")
        shutil.copy2(src, dst / name)
    return dst


def run(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo_root).resolve()
    _install_paths(args.lingbot_code_dir)
    import wan
    from wan.configs import MAX_AREA_CONFIGS, SIZE_CONFIGS, WAN_CONFIGS
    from wan.utils.utils import save_video

    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
    if args.prefix_len != 5 or args.prediction_start_frame != 5:
        raise ValueError("run_v2v5_inference intentionally supports only prefix_len=5 / prediction_start_frame=5")
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")[0].strip()
    if visible == "0" and not args.allow_gpu0:
        raise RuntimeError("physical GPU0 visible first; pass --allow_gpu0 if intentional")

    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "conditions").mkdir(exist_ok=True)
    (out_root / "videos").mkdir(exist_ok=True)
    (out_root / "contact_sheets").mkdir(exist_ok=True)
    rows = [_normalize_row(row) for row in _rows(Path(args.manifest))]
    if args.max_samples > 0:
        rows = rows[: args.max_samples]
    with (out_root / "selected_manifest.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    if args.size not in SIZE_CONFIGS:
        SIZE_CONFIGS[args.size] = tuple(int(x) for x in args.size.split("*"))
    if args.size not in MAX_AREA_CONFIGS:
        w, h = (int(x) for x in args.size.split("*"))
        MAX_AREA_CONFIGS[args.size] = w * h
    cfg = WAN_CONFIGS[args.task]
    pipe = wan.WanI2VFast(
        config=cfg,
        checkpoint_dir=args.ckpt_dir,
        device_id=0,
        rank=0,
        t5_fsdp=False,
        dit_fsdp=False,
        use_sp=False,
        t5_cpu=bool(args.t5_cpu),
        convert_model_dtype=False,
        pipe_dtype=torch.bfloat16 if args.bf16 else torch.float32,
    )
    if getattr(pipe, "control_type", None) != "cam":
        raise RuntimeError(f"expected camera-control Fast checkpoint, got {getattr(pipe, 'control_type', None)}")
    adapter_info: dict[str, Any] = {"adapter_loaded": False}
    if args.adapter_path:
        adapter_info = _load_adapter(pipe, Path(args.adapter_path))
        adapter_info["adapter_loaded"] = True

    generated: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        sample_id = str(row.get("sample_id") or f"sample_{index:04d}").replace("/", "_")
        prefix_path = _resolve(str(row.get("prefix_video_path") or ""), repo_root=repo_root)
        gt_full = _resolve(str(row.get("gt_full_video_path") or ""), repo_root=repo_root)
        gt_future = _resolve(str(row.get("gt_future_video_path") or ""), repo_root=repo_root) if row.get("gt_future_video_path") else None
        if not prefix_path.exists():
            raise FileNotFoundError(f"missing prefix video for {sample_id}: {prefix_path}")
        if not gt_full.exists():
            raise FileNotFoundError(f"missing gt full video for {sample_id}: {gt_full}")
        prompt = _read_prompt(str(row.get("prompt") or "Synthetic indoor physical scene with camera motion."), repo_root=repo_root)
        condition_dir = _copy_condition_files(row, out_root / "conditions" / sample_id, repo_root=repo_root)
        prefix_tensor, _ = read_video_tensor(prefix_path, repo_root=repo_root, num_frames=args.num_frames, height=args.height, width=args.width)
        gt_tensor, _ = read_video_tensor(gt_full, repo_root=repo_root, num_frames=args.num_frames, height=args.height, width=args.width)
        prefix_only, _ = extract_prefix_future(prefix_tensor, prefix_len=args.prefix_len)
        _, gt_future_tensor = extract_prefix_future(gt_tensor, prefix_len=args.prefix_len)
        start = time.time()
        status = "ok"
        error_reason = ""
        generated_full = out_root / "videos" / f"{sample_id}_{args.model}.mp4"
        generated_future = out_root / "videos" / f"{sample_id}_{args.model}_future.mp4"
        copied_prefix = out_root / "videos" / f"{sample_id}_prefix.mp4"
        contact_sheet = out_root / "contact_sheets" / f"{sample_id}_{args.model}_prefix_future.jpg"
        proof_dict: dict[str, Any] = {}
        peak_memory = 0.0
        try:
            if not (generated_full.exists() and generated_future.exists() and args.skip_existing):
                video, proof = generate_v2v5_fast(
                    pipe,
                    input_prompt=prompt,
                    prefix_video=prefix_tensor,
                    action_path=condition_dir,
                    prefix_len=args.prefix_len,
                    prediction_start_frame=args.prediction_start_frame,
                    chunk_size=args.chunk_size,
                    max_area=MAX_AREA_CONFIGS[args.size],
                    frame_num=args.num_frames,
                    shift=args.sample_shift,
                    seed=args.seed,
                    offload_model=bool(args.offload_model),
                    max_attention_size=args.max_attention_size,
                )
                if not torch.is_tensor(video):
                    raise RuntimeError("V2V-5 generator did not return a video tensor")
                save_video(tensor=video[None], save_file=str(generated_full), fps=cfg.sample_fps, nrow=1, normalize=True, value_range=(-1, 1))
                _, future = extract_prefix_future(video.detach().cpu(), prefix_len=args.prefix_len)
                write_video_tensor(future, generated_future, fps=cfg.sample_fps)
                write_video_tensor(prefix_only, copied_prefix, fps=cfg.sample_fps)
                make_prefix_future_contact_sheet(
                    prefix=prefix_only,
                    gt_future=gt_future_tensor,
                    generated_future=future,
                    output_path=contact_sheet,
                    title=f"{sample_id} | {args.model} | prefix_len=5 | future=5-80",
                )
                proof_dict = proof.__dict__
                del video
                torch.cuda.empty_cache()
            if torch.cuda.is_available():
                peak_memory = float(torch.cuda.max_memory_reserved() / (1024 ** 3))
        except Exception as exc:
            status = "error"
            error_reason = repr(exc)
            logging.exception("generation failed for %s", sample_id)
        generated.append({
            "sample_id": sample_id,
            "template": row.get("template", ""),
            "camera_motion": row.get("camera_motion", row.get("camera_variant", "")),
            "prefix_len": args.prefix_len,
            "prediction_start_frame": args.prediction_start_frame,
            "model_name": args.model,
            "adapter_path": args.adapter_path,
            "condition_prefix_path": str(copied_prefix),
            "condition_image_path": str(row.get("condition_image_path") or ""),
            "prompt_path": str(row.get("prompt") or ""),
            "poses_path": str(row.get("poses") or ""),
            "intrinsics_path": str(row.get("intrinsics") or ""),
            "gt_full_video_path": str(gt_full),
            "gt_future_video_path": str(gt_future or ""),
            "generated_full_video_path": str(generated_full),
            "generated_future_video_path": str(generated_future),
            "contact_sheet": str(contact_sheet),
            "seed": args.seed,
            "num_frames": args.num_frames,
            "height": args.height,
            "width": args.width,
            "fps": cfg.sample_fps,
            "inference_steps": "native_fast_4",
            "scheduler": "FlowUniPC/native_fast",
            "model_fingerprint": args.ckpt_dir,
            "adapter_sha256": _sha256(Path(args.adapter_path) / "adapter_state.pt") if args.adapter_path and (Path(args.adapter_path) / "adapter_state.pt").exists() else "",
            "status": status,
            "error_reason": error_reason,
            "generation_seconds": time.time() - start,
            "peak_memory_gib": peak_memory,
            "proof": json.dumps(proof_dict, sort_keys=True),
        })
    keys = sorted({key for row in generated for key in row})
    with (out_root / "generated_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader(); writer.writerows(generated)
    with (out_root / "generated_manifest.jsonl").open("w", encoding="utf-8") as f:
        for row in generated:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    (out_root / "run_metadata.json").write_text(json.dumps({
        "model": args.model,
        "ckpt_dir": args.ckpt_dir,
        "adapter_info": adapter_info,
        "selected_count": len(rows),
        "prefix_len": args.prefix_len,
        "prediction_start_frame": args.prediction_start_frame,
        "eval_future_only": args.eval_future_only,
    }, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True)
    p.add_argument("--model", default="original_fast")
    p.add_argument("--adapter_path", default="")
    p.add_argument("--output_root", required=True)
    p.add_argument("--repo_root", default=".")
    p.add_argument("--ckpt_dir", default=DEFAULT_FAST_ROOT)
    p.add_argument("--lingbot_code_dir", default=DEFAULT_LINGBOT_CODE)
    p.add_argument("--task", default="i2v-A14B")
    p.add_argument("--size", default="832*480")
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--width", type=int, default=832)
    p.add_argument("--num_frames", type=int, default=81)
    p.add_argument("--prefix_len", type=int, default=5)
    p.add_argument("--prediction_start_frame", type=int, default=5)
    p.add_argument("--eval_future_only", type=lambda x: str(x).lower() in {"1", "true", "yes"}, default=True)
    p.add_argument("--seed", type=int, default=123)
    p.add_argument("--sample_shift", type=float, default=5.0)
    p.add_argument("--chunk_size", type=int, default=3)
    p.add_argument("--max_samples", type=int, default=0)
    p.add_argument("--max_attention_size", type=int, default=None)
    p.add_argument("--allow_gpu0", action="store_true")
    p.add_argument("--bf16", type=lambda x: str(x).lower() in {"1", "true", "yes"}, default=True)
    p.add_argument("--t5_cpu", action="store_true")
    p.add_argument("--offload_model", action="store_true", default=True)
    p.add_argument("--skip_existing", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
