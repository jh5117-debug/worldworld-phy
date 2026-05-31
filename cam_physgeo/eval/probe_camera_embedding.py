from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

from cam_physgeo.eval.camera_condition_ablation import variant_poses
from cam_physgeo.training.model_loading import resolve_model_paths
from cam_physgeo.utils.camera import convert_projection_to_lingbot_intrinsics
from cam_physgeo.utils.io import load_yaml, write_json


def _bool_arg(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "y", "on"}


def _sample_dirs(root: Path, limit: int) -> list[Path]:
    dirs = [p for p in sorted(root.iterdir()) if p.is_dir()] if root.exists() else []
    return dirs[:limit] if limit else dirs


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _image_size(sample_dir: Path) -> tuple[int, int]:
    try:
        from PIL import Image  # type: ignore

        with Image.open(sample_dir / "image.jpg") as image:
            return int(image.width), int(image.height)
    except Exception:
        meta = _read_json(sample_dir / "metadata.json")
        return int(meta.get("width") or 832), int(meta.get("height") or 480)


def _add_lingbot_path(config_path: str, explicit_root: str | None = None) -> Path:
    cfg = load_yaml(config_path)
    if explicit_root:
        root = Path(explicit_root)
    else:
        root = Path(resolve_model_paths(cfg).get("lingbot_code", "local_assets/third_party/lingbot_world"))
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def _load_cam_utils(config_path: str, lingbot_code_root: str | None = None) -> dict[str, Any]:
    root = _add_lingbot_path(config_path, lingbot_code_root)
    try:
        from wan.utils.cam_utils import (  # type: ignore
            compute_relative_poses,
            get_Ks_transformed,
            get_plucker_embeddings,
            interpolate_camera_poses,
        )
    except Exception as exc:  # pragma: no cover - depends on LingBot runtime.
        raise RuntimeError(f"failed to import wan.utils.cam_utils from {root}: {exc!r}") from exc
    return {
        "root": root,
        "compute_relative_poses": compute_relative_poses,
        "get_Ks_transformed": get_Ks_transformed,
        "get_plucker_embeddings": get_plucker_embeddings,
        "interpolate_camera_poses": interpolate_camera_poses,
    }


def _make_torch_device(requested: str):
    import torch  # type: ignore

    if requested == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _load_intrinsics(sample_dir: Path, width: int, height: int) -> tuple[np.ndarray, dict[str, Any]]:
    raw = np.load(sample_dir / "intrinsics.npy")
    converted, meta = convert_projection_to_lingbot_intrinsics(raw, width=width, height=height, convention="auto")
    meta["raw_shape"] = list(raw.shape)
    meta["converted_shape"] = list(converted.shape)
    return converted, meta


def _build_embedding(
    *,
    poses_np: np.ndarray,
    intrinsics_np: np.ndarray,
    actions_np: np.ndarray | None,
    cam_utils: dict[str, Any],
    source_width: int,
    source_height: int,
    height: int,
    width: int,
    lat_f: int,
    lat_h: int,
    lat_w: int,
    control_type: str,
    device: str,
) -> dict[str, Any]:
    import torch  # type: ignore
    from einops import rearrange  # type: ignore

    if poses_np.ndim != 3 or poses_np.shape[-2:] != (4, 4):
        raise ValueError(f"poses must have shape (F,4,4), got {poses_np.shape}")
    if intrinsics_np.ndim != 2 or intrinsics_np.shape[-1] != 4:
        raise ValueError(f"intrinsics must have shape (F,4), got {intrinsics_np.shape}")

    device_obj = _make_torch_device(device)
    num_frames = int(poses_np.shape[0])
    lat_f = max(1, min(int(lat_f), num_frames))
    control_type = str(control_type).lower()
    if control_type not in {"act", "cam"}:
        raise ValueError(f"control_type must be act|cam, got {control_type!r}")

    poses = torch.from_numpy(np.asarray(poses_np, dtype=np.float32)).float()
    intrinsics = torch.from_numpy(np.asarray(intrinsics_np, dtype=np.float32)).float()
    actions = torch.from_numpy(np.asarray(actions_np, dtype=np.float32)).float() if actions_np is not None else None

    ks = cam_utils["get_Ks_transformed"](
        intrinsics,
        height_org=source_height,
        width_org=source_width,
        height_resize=height,
        width_resize=width,
        height_final=height,
        width_final=width,
    )
    ks_single = ks[0]
    c2ws_infer = cam_utils["interpolate_camera_poses"](
        src_indices=np.linspace(0, num_frames - 1, num_frames),
        src_rot_mat=poses[:, :3, :3].cpu().numpy(),
        src_trans_vec=poses[:, :3, 3].cpu().numpy(),
        tgt_indices=np.linspace(0, num_frames - 1, lat_f),
    )
    c2ws_infer = cam_utils["compute_relative_poses"](c2ws_infer, framewise=True).to(device_obj)
    ks_repeated = ks_single.repeat(len(c2ws_infer), 1).to(device_obj)
    only_rays_d = control_type == "act"
    raw_plucker = cam_utils["get_plucker_embeddings"](
        c2ws_infer,
        ks_repeated,
        height,
        width,
        only_rays_d=only_rays_d,
    )
    if height % lat_h or width % lat_w:
        raise ValueError(f"height/width must be divisible by latent grid, got {height}x{width} and {lat_h}x{lat_w}")
    plucker = rearrange(
        raw_plucker,
        "f (h c1) (w c2) c -> (f h w) (c c1 c2)",
        c1=int(height // lat_h),
        c2=int(width // lat_w),
    )[None]
    plucker = rearrange(plucker, "b (f h w) c -> b c f h w", f=lat_f, h=lat_h, w=lat_w).float()

    action_tensor = None
    if control_type == "act":
        if actions is None:
            actions = torch.zeros((num_frames, 4), dtype=torch.float32)
        if actions.ndim != 2:
            raise ValueError(f"actions must have shape (F,C), got {tuple(actions.shape)}")
        action_indices = np.linspace(0, len(actions) - 1, len(c2ws_infer)).round().astype(int)
        wasd = actions[action_indices].to(device_obj)
        wasd_tensor = wasd[:, None, None, :].repeat(1, height, width, 1)
        wasd_tensor = rearrange(
            wasd_tensor,
            "f (h c1) (w c2) c -> (f h w) (c c1 c2)",
            c1=int(height // lat_h),
            c2=int(width // lat_w),
        )[None]
        action_tensor = rearrange(wasd_tensor, "b (f h w) c -> b c f h w", f=lat_f, h=lat_h, w=lat_w).float()
        control = torch.cat([plucker, action_tensor.cpu()], dim=1)
    else:
        control = plucker

    return {
        "raw_plucker": raw_plucker.detach().cpu(),
        "plucker": plucker.detach().cpu(),
        "action_tensor": action_tensor.detach().cpu() if action_tensor is not None else None,
        "control": control.detach().cpu(),
        "ks_shape": list(ks.shape),
        "c2ws_infer_shape": list(c2ws_infer.shape),
        "only_rays_d": only_rays_d,
        "control_type": control_type,
    }


def _tensor_summary(tensor) -> dict[str, Any]:
    import torch  # type: ignore

    t = tensor.float()
    flat = t.reshape(-1)
    norm = float(torch.linalg.vector_norm(flat).item()) if flat.numel() else 0.0
    return {
        "shape": list(t.shape),
        "numel": int(t.numel()),
        "norm": norm,
        "mean": float(t.mean().item()) if t.numel() else 0.0,
        "std": float(t.std(unbiased=False).item()) if t.numel() else 0.0,
        "min": float(t.min().item()) if t.numel() else 0.0,
        "max": float(t.max().item()) if t.numel() else 0.0,
    }


def _pairwise(embeddings: dict[str, Any]) -> list[dict[str, Any]]:
    import torch  # type: ignore

    rows: list[dict[str, Any]] = []
    names = sorted(embeddings)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            x = embeddings[a].float().reshape(-1)
            y = embeddings[b].float().reshape(-1)
            if x.numel() != y.numel():
                rows.append({"variant_a": a, "variant_b": b, "available": False, "reason": "shape_mismatch"})
                continue
            diff = x - y
            denom = float(torch.linalg.vector_norm(x).item() * torch.linalg.vector_norm(y).item())
            cosine = float(torch.dot(x, y).item() / denom) if denom > 1e-12 else float("nan")
            rows.append(
                {
                    "variant_a": a,
                    "variant_b": b,
                    "available": True,
                    "l2": float(torch.linalg.vector_norm(diff).item()),
                    "mean_abs": float(torch.mean(torch.abs(diff)).item()),
                    "max_abs": float(torch.max(torch.abs(diff)).item()),
                    "cosine_similarity": cosine,
                }
            )
    return rows


def _write_pairwise_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = ["variant_a", "variant_b", "available", "l2", "mean_abs", "max_abs", "cosine_similarity", "reason"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in keys})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/cam_physgeo/paths.yaml")
    ap.add_argument("--samples", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--variants", nargs="+", default=["correct", "frozen", "reversed", "exaggerated_yaw", "zero_motion"])
    ap.add_argument("--local-files-only", action="store_true")
    ap.add_argument("--lingbot-code-root", default="")
    ap.add_argument("--height", type=int, default=64)
    ap.add_argument("--width", type=int, default=112)
    ap.add_argument("--lat-f", type=int, default=2)
    ap.add_argument("--lat-h", type=int, default=8)
    ap.add_argument("--lat-w", type=int, default=14)
    ap.add_argument("--control-type", default="act", choices=["act", "cam"])
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--save_summary", action="store_true")
    ap.add_argument("--save_npz", default="false")
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.local_files_only:
        import os

        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
    cam_utils = _load_cam_utils(args.config, args.lingbot_code_root or None)
    rows = []
    all_pairwise: list[dict[str, Any]] = []
    for sample_dir in _sample_dirs(Path(args.samples), args.limit):
        width_src, height_src = _image_size(sample_dir)
        poses = np.load(sample_dir / "poses.npy")
        intrinsics, intr_meta = _load_intrinsics(sample_dir, width=width_src, height=height_src)
        actions = np.load(sample_dir / "action.npy") if (sample_dir / "action.npy").exists() else None
        variant_embeddings: dict[str, Any] = {}
        variant_payload: dict[str, Any] = {}
        for variant in args.variants:
            vposes = variant_poses(poses, variant)
            result = _build_embedding(
                poses_np=vposes,
                intrinsics_np=intrinsics,
                actions_np=actions,
                cam_utils=cam_utils,
                source_width=width_src,
                source_height=height_src,
                height=args.height,
                width=args.width,
                lat_f=args.lat_f,
                lat_h=args.lat_h,
                lat_w=args.lat_w,
                control_type=args.control_type,
                device=args.device,
            )
            control = result["control"]
            variant_embeddings[variant] = control
            variant_payload[variant] = {
                "control_summary": _tensor_summary(control),
                "plucker_summary": _tensor_summary(result["plucker"]),
                "raw_plucker_summary": _tensor_summary(result["raw_plucker"]),
                "action_summary": _tensor_summary(result["action_tensor"]) if result["action_tensor"] is not None else None,
                "ks_shape": result["ks_shape"],
                "c2ws_infer_shape": result["c2ws_infer_shape"],
                "control_type": result["control_type"],
                "only_rays_d": result["only_rays_d"],
            }
        pairwise = _pairwise(variant_embeddings)
        for row in pairwise:
            row["sample_id"] = sample_dir.name
        all_pairwise.extend(pairwise)
        if _bool_arg(args.save_npz):
            np.savez_compressed(out / f"{sample_dir.name}_camera_embeddings.npz", **{k: v.numpy() for k, v in variant_embeddings.items()})
        changed = any(
            bool(row.get("available")) and float(row.get("l2") or 0.0) > 1e-5
            for row in pairwise
            if row.get("variant_a") == "correct" or row.get("variant_b") == "correct"
        )
        rows.append(
            {
                "sample_id": sample_dir.name,
                "source_width": width_src,
                "source_height": height_src,
                "poses_shape": list(poses.shape),
                "intrinsics_metadata": intr_meta,
                "action_shape": list(actions.shape) if actions is not None else None,
                "action_norm": float(np.linalg.norm(actions)) if actions is not None else None,
                "lingbot_code_root": str(cam_utils["root"]),
                "probe_grid": {"height": args.height, "width": args.width, "lat_f": args.lat_f, "lat_h": args.lat_h, "lat_w": args.lat_w},
                "variants": variant_payload,
                "pairwise": pairwise,
                "camera_embedding_changes_with_variant": changed,
                "note": "This probes LingBot's actual Plucker utility without running video generation.",
            }
        )
    _write_pairwise_csv(all_pairwise, out / "pairwise_distances.csv")
    payload = {"samples": rows, "pairwise_csv": str(out / "pairwise_distances.csv")}
    write_json(payload, out / "summary.json")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
