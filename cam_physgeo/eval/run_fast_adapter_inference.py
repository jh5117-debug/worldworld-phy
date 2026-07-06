"""LingBot-Fast camera-conditioned inference with optional StageA LoRA adapter.

The legacy eval_batch.py LoRA path is Base/low-noise/action-control oriented.
This wrapper loads WanI2VFast directly, keeps control_type=cam, and applies the
same project LoRA modules used by StageA training.
"""
from __future__ import annotations

import argparse, csv, json, logging, os, sys, time
from pathlib import Path
from typing import Any

import cv2
import torch
from PIL import Image

DEFAULT_FAST_ROOT = "/home/nvme03/workspace/lingbot-world/lingbot-world-base-cam"
DEFAULT_LINGBOT_CODE = "/home/nvme03/workspace/lingbot-world"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _install_paths(lingbot_code_dir: str) -> None:
    root = _repo_root()
    for path in (str(root / "src"), str(root), lingbot_code_dir):
        if path not in sys.path:
            sys.path.insert(0, path)


def _jsonl_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _nested(row: dict[str, Any], *path: str) -> Any:
    cur: Any = row
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _sample_id(row: dict[str, Any]) -> str:
    for value in (
        row.get("sample_id"),
        row.get("clip_name"),
        row.get("id"),
        row.get("stem"),
        _nested(row, "condition", "sample_id"),
        row.get("condition_id"),
        row.get("pair_id"),
    ):
        value = _safe_text(value)
        if value:
            return value
    for value in (
        row.get("target_mp4"), row.get("target_video"), row.get("video_path"), row.get("videopath"),
        row.get("video"), row.get("clip_path"), _nested(row, "winner", "full_video_path"),
        _nested(row, "winner", "future_video_path"), _nested(row, "condition", "gt_full_video_path"),
    ):
        value = _safe_text(value)
        if value:
            path = Path(value)
            return path.parent.name if path.suffix else path.name
    raise ValueError(f"Could not infer sample_id from row keys={sorted(row)}")


def _path_from_values(*values: Any) -> Path | None:
    for value in values:
        value = _safe_text(value)
        if value:
            return Path(value)
    return None


def _video_path(row: dict[str, Any]) -> Path:
    path = _path_from_values(
        row.get("target_mp4"), row.get("target_video"), row.get("reference_videopath"),
        row.get("video_path"), row.get("videopath"), row.get("video"),
        _nested(row, "winner", "full_video_path"), _nested(row, "winner", "future_video_path"),
        _nested(row, "condition", "gt_full_video_path"), _nested(row, "condition", "prefix_video_path"),
    )
    if path is not None:
        return path
    clip = _safe_text(row.get("clip_path"))
    if clip:
        path = Path(clip)
        return path if path.suffix else path / "video.mp4"
    raise ValueError(f"Could not infer video path for sample {_sample_id(row)}")


def _clip_dir(row: dict[str, Any]) -> Path:
    for value in (
        _nested(row, "condition", "poses_path"), _nested(row, "condition", "poses"),
        _nested(row, "condition", "intrinsics_path"), _nested(row, "condition", "intrinsics"),
        _nested(row, "condition", "image_path"), row.get("image_path"),
    ):
        value = _safe_text(value)
        if value:
            path = Path(value)
            return path.parent if path.suffix else path
    video = _video_path(row)
    return video.parent if video.suffix else video


def _prompt_text(row: dict[str, Any], clip_dir: Path) -> str:
    prompt = _safe_text(row.get("prompt"))
    cond_prompt = _safe_text(_nested(row, "condition", "prompt"))
    cond_prompt_path = _safe_text(_nested(row, "condition", "prompt_path"))
    for value in (prompt, cond_prompt, cond_prompt_path):
        if value:
            path = Path(value)
            if path.exists() and path.is_file():
                return path.read_text(encoding="utf-8").strip()
            return value
    prompt_path = clip_dir / "prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return "Synthetic indoor physical scene with camera motion."


def _image_path(row: dict[str, Any], clip_dir: Path, *, height: int, width: int) -> Path:
    path = _path_from_values(row.get("image_path"), _nested(row, "condition", "image_path"))
    if path is not None and path.exists():
        return path
    return _ensure_image(clip_dir, height=height, width=width)


def _camera_paths(row: dict[str, Any], clip_dir: Path) -> tuple[Path, Path]:
    poses = _path_from_values(_nested(row, "condition", "poses_path"), _nested(row, "condition", "poses"), clip_dir / "poses.npy")
    intrinsics = _path_from_values(_nested(row, "condition", "intrinsics_path"), _nested(row, "condition", "intrinsics"), clip_dir / "intrinsics.npy")
    if poses is None or not poses.exists():
        raise FileNotFoundError(f"Missing poses for {_sample_id(row)}: {poses}")
    if intrinsics is None or not intrinsics.exists():
        raise FileNotFoundError(f"Missing intrinsics for {_sample_id(row)}: {intrinsics}")
    return poses, intrinsics


def _action_dir(row: dict[str, Any], clip_dir: Path) -> Path:
    poses, intrinsics = _camera_paths(row, clip_dir)
    if poses.parent == intrinsics.parent:
        return poses.parent
    return clip_dir


def _ensure_image(clip_dir: Path, *, height: int, width: int) -> Path:
    for name in ("image.jpg", "image.png", "first_frame.jpg"):
        candidate = clip_dir / name
        if candidate.exists():
            return candidate
    video = clip_dir / "video.mp4"
    if not video.exists():
        video = clip_dir / "target.mp4"
    if not video.exists():
        raise FileNotFoundError(f"No image or source video found under {clip_dir}")
    image = clip_dir / "image.jpg"
    cap = cv2.VideoCapture(str(video))
    ok, frame = cap.read(); cap.release()
    if not ok:
        raise RuntimeError(f"Could not read first frame from {video}")
    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(image), frame)
    return image


def _read_video_info(path: Path) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"readable": False}
    info = {
        "readable": True,
        "frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0),
        "fps": float(cap.get(cv2.CAP_PROP_FPS) or 0.0),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0),
    }
    cap.release(); return info


def _select_balanced(rows: list[dict[str, Any]], *, max_samples: int, per_template: int) -> list[dict[str, Any]]:
    if max_samples <= 0:
        return rows
    selected, counts = [], {}
    if per_template > 0:
        for row in rows:
            template = _safe_text(row.get("template")) or "unknown"
            if counts.get(template, 0) >= per_template:
                continue
            selected.append(row); counts[template] = counts.get(template, 0) + 1
            if len(selected) >= max_samples:
                return selected
    seen = {_sample_id(r) for r in selected}
    for row in rows:
        if _sample_id(row) in seen:
            continue
        selected.append(row)
        if len(selected) >= max_samples:
            break
    return selected


def _patch_wan_fast_from_pretrained_safe() -> None:
    """Force local safetensors streaming for WanModelFast construction."""
    try:
        from wan.modules import model_fast
        import wan.image2video_fast as image2video_fast
    except Exception as exc:
        logging.warning("Could not patch WanModelFast.from_pretrained: %r", exc)
        return
    cls = model_fast.WanModelFast
    init_weights = getattr(cls, "init_weights", None)
    if init_weights is not None and not getattr(init_weights, "_cam_physgeo_noop_patch", False):
        def no_init_weights(self):  # type: ignore[no-untyped-def]
            logging.info("Skipping WanModelFast.init_weights during from_pretrained; pretrained shards will populate weights")
            return None
        no_init_weights._cam_physgeo_noop_patch = True  # type: ignore[attr-defined]
        cls._cam_physgeo_original_init_weights = init_weights  # type: ignore[attr-defined]
        cls.init_weights = no_init_weights  # type: ignore[method-assign]
    current = getattr(cls, "from_pretrained")
    if getattr(current, "_cam_physgeo_safe_patch", False):
        return
    original = current
    def safe_from_pretrained(*args, **kwargs):
        kwargs["local_files_only"] = True
        kwargs["use_safetensors"] = True
        kwargs["low_cpu_mem_usage"] = True
        logging.info("Using safe WanModelFast.from_pretrained kwargs: local_files_only=True use_safetensors=True low_cpu_mem_usage=True; init_weights=noop")
        return original(*args, **kwargs)
    safe_from_pretrained._cam_physgeo_safe_patch = True  # type: ignore[attr-defined]
    cls.from_pretrained = safe_from_pretrained
    image2video_fast.WanModelFast.from_pretrained = safe_from_pretrained


def _load_adapter(pipe: Any, adapter_dir: Path) -> dict[str, Any]:
    from physical_consistency.trainers.stage1_components import apply_lora_to_wan_model, load_lora_state_dict
    metadata_path, adapter_path = adapter_dir / "adapter_metadata.json", adapter_dir / "adapter_state.pt"
    if not metadata_path.exists() or not adapter_path.exists():
        raise FileNotFoundError(f"Adapter directory is incomplete: {adapter_dir}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("branch") != "high_only" or not bool(metadata.get("adapter_only")):
        raise ValueError(f"Expected high_only adapter-only checkpoint: {adapter_dir}")
    lora_config = dict(metadata.get("lora_config") or {})
    if not lora_config:
        raise ValueError(f"Adapter metadata has no lora_config: {metadata_path}")
    os.environ.setdefault("PC_FORCE_LORA_FP32", "1" if lora_config.get("force_lora_fp32") else "0")
    os.environ.setdefault("PC_LORA_DISABLE_AUTOCAST", "1" if lora_config.get("disable_autocast") else "0")
    report = apply_lora_to_wan_model(
        pipe.model,
        model_name="fast_stageA_eval",
        rank=int(lora_config.get("rank", 16)),
        alpha=int(lora_config.get("alpha", 16)),
        dropout=0.0,
        target_prefixes=tuple(lora_config.get("target_prefixes") or ("blocks",)),
        block_start=int(lora_config.get("block_start", 0)),
        block_end=lora_config.get("block_end"),
        target_groups=tuple(lora_config.get("target_groups") or ("camera_conditioning", "self_attention", "cross_attention", "ffn")),
        required_groups=tuple(lora_config.get("required_groups") or ("camera_conditioning", "self_attention", "cross_attention", "ffn")),
        include_patterns=tuple(lora_config.get("include_patterns") or ()),
        exclude_patterns=tuple(lora_config.get("exclude_patterns") or ()),
        lora_chunk_size=lora_config.get("lora_chunk_size"),
        merge_mode=str(lora_config.get("merge_mode", "out_of_place")),
    )
    state = torch.load(adapter_path, map_location="cpu", weights_only=True)
    load_lora_state_dict(pipe.model, state, model_name="fast_stageA_eval")
    pipe.model.eval().requires_grad_(False)
    return {
        "adapter_dir": str(adapter_dir),
        "adapter_tensor_count": len(state),
        "metadata_tensor_count": metadata.get("adapter_tensor_count"),
        "global_step": metadata.get("global_step"),
        "tag": metadata.get("tag"),
        "selected_count": report.selected_count,
        "selected_by_group": {k: len(v) for k, v in report.selected_by_group.items()},
        "trainable_params": report.trainable_params,
    }


def run(args: argparse.Namespace) -> None:
    _install_paths(args.lingbot_code_dir)
    import wan
    from wan.configs import MAX_AREA_CONFIGS, SIZE_CONFIGS, WAN_CONFIGS
    from wan.utils.utils import save_video
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
    out_root = Path(args.out); videos_dir = out_root / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True); (out_root / "logs").mkdir(parents=True, exist_ok=True)
    rows = _select_balanced(_jsonl_rows(Path(args.manifest)), max_samples=args.max_samples, per_template=args.per_template)
    with (out_root / "selected_manifest.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    if args.size not in SIZE_CONFIGS:
        SIZE_CONFIGS[args.size] = tuple(int(x) for x in args.size.split("*"))
    if args.size not in MAX_AREA_CONFIGS:
        w, h = (int(x) for x in args.size.split("*")); MAX_AREA_CONFIGS[args.size] = w * h
    cfg = WAN_CONFIGS[args.task]
    _patch_wan_fast_from_pretrained_safe()
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")[0].strip()
    if visible == "0" and not args.allow_gpu0:
        raise RuntimeError("Refusing to run Fast inference with physical GPU0 visible first without --allow_gpu0")
    pipe = wan.WanI2VFast(
        config=cfg, checkpoint_dir=args.ckpt_dir, device_id=0, rank=0,
        t5_fsdp=False, dit_fsdp=False, use_sp=False, t5_cpu=bool(args.t5_cpu),
        convert_model_dtype=False, pipe_dtype=torch.bfloat16,
    )
    control_type = getattr(pipe, "control_type", None)
    if control_type != "cam":
        raise RuntimeError(f"Expected Fast camera-control model, got control_type={control_type}")
    adapter_info: dict[str, Any] = {"adapter_loaded": False}
    if args.adapter_dir:
        adapter_info = _load_adapter(pipe, Path(args.adapter_dir)); adapter_info["adapter_loaded"] = True
    manifest_rows=[]
    for index, row in enumerate(rows):
        sample_id = _sample_id(row); clip_dir = _clip_dir(row); source_video = _video_path(row)
        prompt = _prompt_text(row, clip_dir)
        image_path = _image_path(row, clip_dir, height=args.height, width=args.width)
        action_dir = _action_dir(row, clip_dir)
        save_path = videos_dir / f"{sample_id}_{args.model_label}.mp4"
        if not (save_path.exists() and args.skip_existing):
            logging.info("[%s/%s] generating %s", index + 1, len(rows), sample_id)
            img = Image.open(image_path).convert("RGB"); start = time.time()
            video = pipe.generate(
                prompt, img, action_path=str(action_dir) + "/", chunk_size=args.chunk_size,
                max_area=MAX_AREA_CONFIGS[args.size], frame_num=args.frame_num,
                shift=args.sample_shift, seed=args.seed, offload_model=bool(args.offload_model),
                max_attention_size=args.max_attention_size,
            )
            if video is None:
                raise RuntimeError(f"Generation returned None for {sample_id}")
            save_video(tensor=video[None], save_file=str(save_path), fps=cfg.sample_fps, nrow=1, normalize=True, value_range=(-1, 1))
            logging.info("saved %s in %.1fs", save_path, time.time() - start)
            del video; torch.cuda.empty_cache()
        manifest_rows.append({
            "sample_id": sample_id,
            "template": row.get("template", _nested(row, "condition", "template") or ""),
            "camera_variant": row.get("camera_variant", row.get("camera_motion", _nested(row, "condition", "camera_motion") or "")),
            "model_label": args.model_label,
            "prompt": prompt,
            "source_video": str(source_video),
            "clip_dir": str(clip_dir),
            "action_dir": str(action_dir),
            "image_path": str(image_path),
            "generated_video": str(save_path),
            "seed": args.seed,
            "frame_num": args.frame_num,
            "height": args.height,
            "width": args.width,
            **_read_video_info(save_path),
        })
    keys=list(manifest_rows[0].keys())
    with (out_root / "generated_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer=csv.DictWriter(handle, fieldnames=keys); writer.writeheader(); writer.writerows(manifest_rows)
    (out_root / "run_metadata.json").write_text(json.dumps({
        "model_label": args.model_label,
        "ckpt_dir": args.ckpt_dir,
        "adapter_info": adapter_info,
        "selected_count": len(rows),
        "seed": args.seed,
        "frame_num": args.frame_num,
        "size": args.size,
        "control_type": getattr(pipe, "control_type", None),
    }, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True); p.add_argument("--out", required=True); p.add_argument("--model_label", required=True)
    p.add_argument("--ckpt_dir", default=DEFAULT_FAST_ROOT); p.add_argument("--lingbot_code_dir", default=DEFAULT_LINGBOT_CODE); p.add_argument("--adapter_dir", default="")
    p.add_argument("--task", default="i2v-A14B"); p.add_argument("--size", default="832*480"); p.add_argument("--height", type=int, default=480); p.add_argument("--width", type=int, default=832)
    p.add_argument("--frame_num", type=int, default=81); p.add_argument("--seed", type=int, default=123); p.add_argument("--sample_shift", type=float, default=5.0)
    p.add_argument("--chunk_size", type=int, default=3); p.add_argument("--max_attention_size", type=int, default=None); p.add_argument("--max_samples", type=int, default=8); p.add_argument("--per_template", type=int, default=2)
    p.add_argument("--allow_gpu0", action="store_true", help="Allow physical GPU0 when CUDA_VISIBLE_DEVICES starts with 0; disabled by default for safety.")
    p.add_argument("--offload_model", action="store_true", default=False); p.add_argument("--t5_cpu", action="store_true", default=False); p.add_argument("--skip_existing", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
