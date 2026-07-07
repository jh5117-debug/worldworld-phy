
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import time
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

CANDIDATE_IMPORTS = ["vjepa", "vijepa", "dinov2", "transformers", "torchvision", "clip", "open_clip", "pytorchvideo"]
CANDIDATE_PATTERNS = ["*vjepa*", "*VJEPA*", "*videorepa*", "*VideoREPA*", "*videomae*", "*VideoMAE*", "*dinov2*", "*i3d*", "*trd*"]
WEIGHT_PATTERNS = ["*.pt", "*.pth", "*.safetensors", "*.bin", "*.ckpt"]
DEFAULT_DINOV2_VITS14 = "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/weights/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth"
DEFAULT_VJEPA2_BASE = "/home/nvme04/workspace/world_model_phys/PHYS/weight/vjepa2_1/vjepa2_1_vitb_dist_vitG_384.pt"
DEFAULT_VJEPA2_REPO = "/home/nvme03/.cache/torch/hub/facebookresearch_vjepa2_main"
KNOWN_LOCAL_WEIGHT_CANDIDATES = [
    DEFAULT_DINOV2_VITS14,
    DEFAULT_VJEPA2_BASE,
    "/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys/local_assets/weights/vjepa2/vjepa2_1_vitb_dist_vitG_384.pt",
]


def find_files(roots: list[str], max_hits: int = 200, max_dirs: int = 20000, max_seconds: float = 30.0, *, weight_only: bool = False) -> tuple[list[str], dict[str, object]]:
    hits: list[str] = []
    visited_dirs = 0
    started = time.time()
    stop_reason = "completed"
    skip_names = {".git", "node_modules", "__pycache__", "wandb", "runs"}
    for root in roots:
        base = Path(root)
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            visited_dirs += 1
            dirnames[:] = [d for d in dirnames if d not in skip_names]
            if visited_dirs >= max_dirs:
                stop_reason = "max_dirs"
                break
            if time.time() - started > max_seconds:
                stop_reason = "max_seconds"
                break
            for name in filenames:
                lower = name.lower()
                if not any(fnmatch(name, pat) or fnmatch(lower, pat.lower()) for pat in CANDIDATE_PATTERNS):
                    continue
                if weight_only and not any(fnmatch(name, pat) or fnmatch(lower, pat.lower()) for pat in WEIGHT_PATTERNS):
                    continue
                path = Path(dirpath) / name
                try:
                    if path.stat().st_size > 0:
                        hits.append(str(path))
                except OSError:
                    continue
                if len(hits) >= max_hits:
                    stop_reason = "max_hits"
                    break
            if len(hits) >= max_hits or stop_reason != "completed":
                break
        if len(hits) >= max_hits or stop_reason != "completed":
            break
    meta = {"visited_dirs": visited_dirs, "elapsed_seconds": round(time.time() - started, 3), "stop_reason": stop_reason, "max_dirs": max_dirs, "max_seconds": max_seconds}
    return sorted(set(hits))[:max_hits], meta


def audit(args: argparse.Namespace) -> dict[str, object]:
    imports = {}
    for name in CANDIDATE_IMPORTS:
        imports[name] = importlib.util.find_spec(name) is not None
    files, search_meta = find_files(args.search_roots, max_dirs=int(args.max_dirs), max_seconds=float(args.max_seconds))
    weight_files, weight_search_meta = find_files(args.search_roots, max_hits=100, max_dirs=int(args.max_dirs), max_seconds=float(args.max_seconds), weight_only=True)
    if getattr(args, "include_known_candidates", True):
        for known in KNOWN_LOCAL_WEIGHT_CANDIDATES:
            known_path = Path(known)
            if known_path.exists() and known_path.stat().st_size > 0:
                weight_files.append(str(known_path))
    weight_files = sorted(set(weight_files))
    has_model_code = any(imports.get(k, False) for k in ("vjepa", "vijepa", "dinov2", "clip", "open_clip", "transformers", "pytorchvideo"))
    has_teacher = has_model_code and bool(weight_files)
    decision = "LATENT_MONITOR_BACKEND_FOUND_NEEDS_SCORING" if has_teacher else "LATENT_MONITOR_BLOCKED_BY_ENV"
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {"decision": decision, "imports": imports, "candidate_files": files[:100], "candidate_weight_files": weight_files[:100], "search_meta": search_meta, "weight_search_meta": weight_search_meta, "note": "No model download attempted. Monitor only; no training."}
    (out_dir / "backend_audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    md = ["# Latent Relation Monitor Backend Audit", "", f"Decision: `{decision}`", "", f"Search meta: `{search_meta}`", "", "## Imports"]
    for k, v in imports.items():
        md.append(f"- {k}: {v}")
    md += ["", "## Candidate Local Files", ""]
    if files:
        md += [f"- `{p}`" for p in files[:50]]
    else:
        md.append("- none found")
    md += ["", "## Candidate Local Weight Files", ""]
    if weight_files:
        md += [f"- `{p}`" for p in weight_files[:50]]
    else:
        md.append("- none found")
    md += ["", "No V-JEPA / VideoREPA / TRD values are produced by this audit. `LATENT_MONITOR_BACKEND_FOUND_NEEDS_SCORING` only means local code and weight candidates exist; scoring still must run before any latent-monitor PASS. Fake latent scores are forbidden."]
    (out_dir / "backend_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return result


def resolve_path(path: str | None, repo_root: Path) -> Path | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = repo_root / p
    return p


def map_dinov2_vits14_state_dict(state_dict: dict[str, Any]) -> dict[str, Any]:
    """Map official DINOv2 ViT-S/14 keys to transformers Dinov2Model keys."""
    mapped: dict[str, Any] = {}
    direct = {
        "cls_token": "embeddings.cls_token",
        "mask_token": "embeddings.mask_token",
        "pos_embed": "embeddings.position_embeddings",
        "patch_embed.proj.weight": "embeddings.patch_embeddings.projection.weight",
        "patch_embed.proj.bias": "embeddings.patch_embeddings.projection.bias",
        "norm.weight": "layernorm.weight",
        "norm.bias": "layernorm.bias",
    }
    for src, dst in direct.items():
        if src in state_dict:
            mapped[dst] = state_dict[src]
    for layer in range(12):
        prefix = f"blocks.{layer}"
        dst = f"encoder.layer.{layer}"
        for src_suffix, dst_suffix in (
            ("norm1.weight", "norm1.weight"),
            ("norm1.bias", "norm1.bias"),
            ("attn.proj.weight", "attention.output.dense.weight"),
            ("attn.proj.bias", "attention.output.dense.bias"),
            ("ls1.gamma", "layer_scale1.lambda1"),
            ("norm2.weight", "norm2.weight"),
            ("norm2.bias", "norm2.bias"),
            ("mlp.fc1.weight", "mlp.fc1.weight"),
            ("mlp.fc1.bias", "mlp.fc1.bias"),
            ("mlp.fc2.weight", "mlp.fc2.weight"),
            ("mlp.fc2.bias", "mlp.fc2.bias"),
            ("ls2.gamma", "layer_scale2.lambda1"),
        ):
            key = f"{prefix}.{src_suffix}"
            if key in state_dict:
                mapped[f"{dst}.{dst_suffix}"] = state_dict[key]
        qkv_w = state_dict.get(f"{prefix}.attn.qkv.weight")
        qkv_b = state_dict.get(f"{prefix}.attn.qkv.bias")
        if qkv_w is not None:
            q_w, k_w, v_w = qkv_w.chunk(3, dim=0)
            mapped[f"{dst}.attention.attention.query.weight"] = q_w
            mapped[f"{dst}.attention.attention.key.weight"] = k_w
            mapped[f"{dst}.attention.attention.value.weight"] = v_w
        if qkv_b is not None:
            q_b, k_b, v_b = qkv_b.chunk(3, dim=0)
            mapped[f"{dst}.attention.attention.query.bias"] = q_b
            mapped[f"{dst}.attention.attention.key.bias"] = k_b
            mapped[f"{dst}.attention.attention.value.bias"] = v_b
    return mapped


def load_dinov2_vits14(weight_path: Path, device: str):
    import torch
    from transformers import Dinov2Config, Dinov2Model

    cfg = Dinov2Config(
        image_size=518,
        patch_size=14,
        num_channels=3,
        hidden_size=384,
        num_hidden_layers=12,
        num_attention_heads=6,
        intermediate_size=1536,
    )
    model = Dinov2Model(cfg)
    raw = torch.load(weight_path, map_location="cpu")
    mapped = map_dinov2_vits14_state_dict(raw)
    missing, unexpected = model.load_state_dict(mapped, strict=False)
    model.eval().to(device)
    return model, {"missing_keys": list(missing), "unexpected_keys": list(unexpected), "mapped_keys": len(mapped)}


def read_video_frames(video_path: Path, frame_indices: list[int]) -> list[Any]:
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"could not open video: {video_path}")
    frames = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame)
    cap.release()
    if not frames:
        raise RuntimeError(f"no requested frames decoded from {video_path}")
    return frames


def encode_frames_dinov2(model: Any, frames: list[Any], device: str):
    import torch
    import torch.nn.functional as F

    tensors = []
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    for frame in frames:
        t = torch.from_numpy(frame).permute(2, 0, 1).float() / 255.0
        t = F.interpolate(t.unsqueeze(0), size=(518, 518), mode="bicubic", align_corners=False).squeeze(0)
        tensors.append((t - mean) / std)
    batch = torch.stack(tensors).to(device)
    with torch.inference_mode():
        out = model(pixel_values=batch)
        feats = out.last_hidden_state[:, 0].float()
        feats = F.normalize(feats, dim=-1)
    return feats.cpu()


def frames_to_video_tensor(frames: list[Any], device: str, size: int = 224):
    import torch
    import torch.nn.functional as F

    tensors = []
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    for frame in frames:
        t = torch.from_numpy(frame).permute(2, 0, 1).float() / 255.0
        t = F.interpolate(t.unsqueeze(0), size=(size, size), mode="bicubic", align_corners=False).squeeze(0)
        tensors.append((t - mean) / std)
    return torch.stack(tensors).permute(1, 0, 2, 3).unsqueeze(0).to(device)


def load_vjepa2_base_encoder(repo_path: Path, weight_path: Path, device: str, *, img_size: int = 224, num_frames: int = 8):
    import sys
    import torch

    sys.path.insert(0, str(repo_path))
    from src.hub.backbones import _clean_backbone_key, _make_vjepa2_1_model

    encoder, _ = _make_vjepa2_1_model(
        model_name="vjepa2_1_vit_base_384",
        checkpoint_key="ema_encoder",
        img_size=img_size,
        num_frames=num_frames,
        predictor_depth=12,
        predictor_num_mask_tokens=8,
        n_output_distillation=1,
        return_all_tokens=True,
        teacher_embed_dim=1664,
        pretrained=False,
    )
    state = torch.load(weight_path, map_location="cpu")
    missing, unexpected = encoder.load_state_dict(_clean_backbone_key(state["ema_encoder"]), strict=True)
    encoder.eval().to(device)
    return encoder, {"missing_keys": list(missing), "unexpected_keys": list(unexpected), "checkpoint_keys": sorted(state.keys())}


def encode_video_vjepa2(encoder: Any, frames: list[Any], device: str, *, size: int = 224):
    import torch
    import torch.nn.functional as F

    x = frames_to_video_tensor(frames, device, size=size)
    with torch.inference_mode():
        tokens = encoder(x).float().squeeze(0)
        tokens = F.normalize(tokens, dim=-1)
    return tokens.cpu()


def token_relation_distance(a: Any, b: Any) -> float:
    import torch

    n = min(a.shape[0], b.shape[0])
    if n < 2:
        return float("nan")
    aa = a[:n]
    bb = b[:n]
    da = torch.cdist(aa, aa, p=2)
    db = torch.cdist(bb, bb, p=2)
    return float((da - db).abs().mean().item())


def temporal_relation_distance(a: Any, b: Any) -> float:
    import torch

    if a.shape[0] < 2 or b.shape[0] < 2:
        return float("nan")
    da = torch.cdist(a, a, p=2)
    db = torch.cdist(b, b, p=2)
    return float((da - db).abs().mean().item())


def cosine_distance(a: Any, b: Any) -> float:
    import torch.nn.functional as F

    aa = F.normalize(a.mean(dim=0, keepdim=True), dim=-1)
    bb = F.normalize(b.mean(dim=0, keepdim=True), dim=-1)
    return float((1.0 - (aa * bb).sum(dim=-1)).item())


def select_video_path(pair: dict[str, Any], side: str, repo_root: Path) -> tuple[Path | None, str]:
    entry = pair.get(side, {}) if isinstance(pair.get(side, {}), dict) else {}
    candidates = [
        (entry.get("full_video_path"), "full"),
        (pair.get(f"{side}_video_path"), "full"),
        (entry.get("future_video_path"), "future"),
    ]
    if side == "winner":
        condition = pair.get("condition", {}) if isinstance(pair.get("condition", {}), dict) else {}
        candidates.extend([
            (condition.get("gt_full_video_path"), "full"),
            (condition.get("gt_video_path"), "full"),
            (condition.get("gt_future_video_path"), "future"),
        ])
        image_path = resolve_path(condition.get("image_path") or condition.get("image"), repo_root)
        if image_path:
            candidates.append((str(image_path.parent / "video.mp4"), "full"))
    for path, kind in candidates:
        resolved = resolve_path(path, repo_root)
        if resolved and resolved.exists():
            return resolved, kind
    fallback = resolve_path(entry.get("full_video_path") or pair.get(f"{side}_video_path") or entry.get("future_video_path"), repo_root)
    return fallback, "missing"


def pick_frame_indices(pair: dict[str, Any], max_frames: int, *, relative_to_future: bool = False) -> list[int]:
    future = pair.get("winner", {}).get("future_frame_indices") or pair.get("loss_frame_indices") or list(range(5, 81))
    future = [int(x) for x in future]
    if len(future) <= max_frames:
        selected = future
    elif max_frames <= 1:
        selected = [future[len(future) // 2]]
    else:
        positions = [round(i * (len(future) - 1) / (max_frames - 1)) for i in range(max_frames)]
        selected = [future[i] for i in positions]
    if relative_to_future:
        start = int(pair.get("prediction_start_frame") or pair.get("prefix_len") or min(future))
        selected = [max(0, idx - start) for idx in selected]
    return selected


def score_dinov2_frame_smoke(args: argparse.Namespace) -> dict[str, object]:
    import torch

    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_csv = Path(args.output_csv) if args.output_csv else out_dir / "dinov2_frame_smoke.csv"
    output_json = Path(args.output_json) if args.output_json else out_dir / "dinov2_frame_smoke_summary.json"
    output_md = Path(args.output_md) if args.output_md else out_dir / "dinov2_frame_smoke_summary.md"
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    device = "cuda:" + str(args.gpu) if args.gpu is not None and torch.cuda.is_available() else "cpu"
    weight_path = resolve_path(args.dinov2_weight, repo_root)
    if not weight_path or not weight_path.exists():
        raise FileNotFoundError(f"DINOv2 weight not found: {weight_path}")
    started = time.time()
    model, load_meta = load_dinov2_vits14(weight_path, device)
    rows: list[dict[str, object]] = []
    fields = [
        "pair_id", "backend", "frame_indices", "num_frames", "winner_video", "loser_video",
        "winner_distance_to_reference", "loser_distance_to_reference", "frame_cosine_margin",
        "temporal_relation_winner", "temporal_relation_loser", "temporal_relation_margin",
        "status", "error_reason", "seconds",
    ]
    with Path(args.pair_manifest).open("r", encoding="utf-8") as f, output_csv.open("w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=fields)
        writer.writeheader()
        for idx, line in enumerate(f):
            if args.num_pairs and idx >= args.num_pairs:
                break
            pair_started = time.time()
            pair = json.loads(line)
            row: dict[str, object] = {
                "pair_id": pair.get("pair_id", f"row_{idx}"),
                "backend": "dinov2_vits14_frame_relation_local_weight",
                "status": "ok",
                "error_reason": "",
            }
            try:
                winner_path, winner_kind = select_video_path(pair, "winner", repo_root)
                loser_path, loser_kind = select_video_path(pair, "loser", repo_root)
                if not winner_path or not winner_path.exists():
                    raise FileNotFoundError(f"winner video missing: {winner_path}")
                if not loser_path or not loser_path.exists():
                    raise FileNotFoundError(f"loser video missing: {loser_path}")
                winner_indices = pick_frame_indices(pair, int(args.max_frames), relative_to_future=(winner_kind == "future"))
                loser_indices = pick_frame_indices(pair, int(args.max_frames), relative_to_future=(loser_kind == "future"))
                winner_frames = read_video_frames(winner_path, winner_indices)
                loser_frames = read_video_frames(loser_path, loser_indices)
                n = min(len(winner_frames), len(loser_frames))
                winner_feats = encode_frames_dinov2(model, winner_frames[:n], device)
                loser_feats = encode_frames_dinov2(model, loser_frames[:n], device)
                winner_dist = 0.0
                loser_dist = cosine_distance(loser_feats, winner_feats)
                rel_winner = 0.0
                rel_loser = temporal_relation_distance(loser_feats, winner_feats)
                row.update({
                    "frame_indices": json.dumps({"winner": winner_indices[:n], "loser": loser_indices[:n], "winner_kind": winner_kind, "loser_kind": loser_kind}),
                    "num_frames": n,
                    "winner_video": str(winner_path),
                    "loser_video": str(loser_path),
                    "winner_distance_to_reference": winner_dist,
                    "loser_distance_to_reference": loser_dist,
                    "frame_cosine_margin": loser_dist - winner_dist,
                    "temporal_relation_winner": rel_winner,
                    "temporal_relation_loser": rel_loser,
                    "temporal_relation_margin": rel_loser - rel_winner,
                })
            except Exception as exc:  # noqa: BLE001 - report exact per-pair blocker and continue.
                row.update({"status": "error", "error_reason": f"{type(exc).__name__}: {exc}"})
            row["seconds"] = round(time.time() - pair_started, 3)
            writer.writerow(row)
            cf.flush()
            rows.append(row)
    ok = [r for r in rows if r.get("status") == "ok"]
    positive_frame = [r for r in ok if float(r.get("frame_cosine_margin") or 0.0) > 1e-6]
    positive_relation = [r for r in ok if float(r.get("temporal_relation_margin") or 0.0) > 1e-6]
    ratio = len(positive_relation) / len(ok) if ok else 0.0
    decision = "LATENT_MONITOR_DINO_FRAME_SMOKE_PASS" if ok and ratio >= 0.65 else "LATENT_MONITOR_DINO_FRAME_SMOKE_FAIL"
    summary = {
        "decision": decision,
        "backend": "dinov2_vits14_frame_relation_local_weight",
        "weight_path": str(weight_path),
        "device": device,
        "rows": len(rows),
        "ok_rows": len(ok),
        "positive_frame_margin_rows": len(positive_frame),
        "positive_temporal_relation_margin_rows": len(positive_relation),
        "temporal_relation_positive_ratio": ratio,
        "load_meta": load_meta,
        "elapsed_seconds": round(time.time() - started, 3),
        "note": "DINOv2 frame fallback monitor only. This is not a full V-JEPA/TRD auxiliary-loss PASS and no training was run.",
    }
    output_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md = [
        "# DINOv2 Frame Latent Monitor Smoke",
        "",
        f"Decision: `{decision}`",
        "",
        f"Rows: {len(rows)}; ok: {len(ok)}",
        f"Positive temporal-relation margin rows: {len(positive_relation)}/{len(ok) if ok else 0}",
        f"Positive frame cosine margin rows: {len(positive_frame)}/{len(ok) if ok else 0}",
        "",
        "This uses a local DINOv2 ViT-S/14 frame fallback. It does not download models, does not train, and does not claim full V-JEPA/TRD readiness.",
    ]
    output_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def score_vjepa2_video_smoke(args: argparse.Namespace) -> dict[str, object]:
    import torch

    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_csv = Path(args.output_csv) if args.output_csv else out_dir / "vjepa2_video_smoke.csv"
    output_json = Path(args.output_json) if args.output_json else out_dir / "vjepa2_video_smoke_summary.json"
    output_md = Path(args.output_md) if args.output_md else out_dir / "vjepa2_video_smoke_summary.md"
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    device = "cuda:" + str(args.gpu) if args.gpu is not None and torch.cuda.is_available() else "cpu"
    repo_path = resolve_path(args.vjepa2_repo, repo_root)
    weight_path = resolve_path(args.vjepa2_weight, repo_root)
    if not repo_path or not repo_path.exists():
        raise FileNotFoundError(f"V-JEPA2 repo not found: {repo_path}")
    if not weight_path or not weight_path.exists():
        raise FileNotFoundError(f"V-JEPA2 weight not found: {weight_path}")
    started = time.time()
    encoder, load_meta = load_vjepa2_base_encoder(repo_path, weight_path, device, img_size=int(args.vjepa_img_size), num_frames=int(args.max_frames))
    rows: list[dict[str, object]] = []
    fields = [
        "pair_id", "backend", "frame_indices", "num_frames", "winner_video", "loser_video",
        "winner_distance_to_reference", "loser_distance_to_reference", "vjepa_margin",
        "token_relation_winner", "token_relation_loser", "token_relation_margin",
        "status", "error_reason", "seconds",
    ]
    with Path(args.pair_manifest).open("r", encoding="utf-8") as f, output_csv.open("w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=fields)
        writer.writeheader()
        for idx, line in enumerate(f):
            if args.num_pairs and idx >= args.num_pairs:
                break
            pair_started = time.time()
            pair = json.loads(line)
            row: dict[str, object] = {
                "pair_id": pair.get("pair_id", f"row_{idx}"),
                "backend": "vjepa2_1_vit_base_224_local_ema_encoder",
                "status": "ok",
                "error_reason": "",
            }
            try:
                winner_path, winner_kind = select_video_path(pair, "winner", repo_root)
                loser_path, loser_kind = select_video_path(pair, "loser", repo_root)
                if not winner_path or not winner_path.exists():
                    raise FileNotFoundError(f"winner video missing: {winner_path}")
                if not loser_path or not loser_path.exists():
                    raise FileNotFoundError(f"loser video missing: {loser_path}")
                winner_indices = pick_frame_indices(pair, int(args.max_frames), relative_to_future=(winner_kind == "future"))
                loser_indices = pick_frame_indices(pair, int(args.max_frames), relative_to_future=(loser_kind == "future"))
                winner_frames = read_video_frames(winner_path, winner_indices)
                loser_frames = read_video_frames(loser_path, loser_indices)
                n = min(len(winner_frames), len(loser_frames), int(args.max_frames))
                winner_tokens = encode_video_vjepa2(encoder, winner_frames[:n], device, size=int(args.vjepa_img_size))
                loser_tokens = encode_video_vjepa2(encoder, loser_frames[:n], device, size=int(args.vjepa_img_size))
                winner_dist = 0.0
                loser_dist = cosine_distance(loser_tokens, winner_tokens)
                rel_winner = 0.0
                rel_loser = token_relation_distance(loser_tokens, winner_tokens)
                row.update({
                    "frame_indices": json.dumps({"winner": winner_indices[:n], "loser": loser_indices[:n], "winner_kind": winner_kind, "loser_kind": loser_kind}),
                    "num_frames": n,
                    "winner_video": str(winner_path),
                    "loser_video": str(loser_path),
                    "winner_distance_to_reference": winner_dist,
                    "loser_distance_to_reference": loser_dist,
                    "vjepa_margin": loser_dist - winner_dist,
                    "token_relation_winner": rel_winner,
                    "token_relation_loser": rel_loser,
                    "token_relation_margin": rel_loser - rel_winner,
                })
            except Exception as exc:  # noqa: BLE001
                row.update({"status": "error", "error_reason": f"{type(exc).__name__}: {exc}"})
            row["seconds"] = round(time.time() - pair_started, 3)
            writer.writerow(row)
            cf.flush()
            rows.append(row)
    ok = [r for r in rows if r.get("status") == "ok"]
    positive_margin = [r for r in ok if float(r.get("vjepa_margin") or 0.0) > 1e-6]
    positive_relation = [r for r in ok if float(r.get("token_relation_margin") or 0.0) > 1e-6]
    ratio = len(positive_relation) / len(ok) if ok else 0.0
    decision = "LATENT_MONITOR_VJEPA2_VIDEO_SMOKE_PASS" if ok and ratio >= 0.65 else "LATENT_MONITOR_VJEPA2_VIDEO_SMOKE_FAIL"
    summary = {
        "decision": decision,
        "backend": "vjepa2_1_vit_base_224_local_ema_encoder",
        "repo_path": str(repo_path),
        "weight_path": str(weight_path),
        "device": device,
        "rows": len(rows),
        "ok_rows": len(ok),
        "positive_vjepa_margin_rows": len(positive_margin),
        "positive_token_relation_margin_rows": len(positive_relation),
        "token_relation_positive_ratio": ratio,
        "load_meta": load_meta,
        "elapsed_seconds": round(time.time() - started, 3),
        "note": "V-JEPA2 monitor smoke only. No training or auxiliary loss integration was run.",
    }
    output_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md = [
        "# V-JEPA2 Video Latent Monitor Smoke",
        "",
        f"Decision: `{decision}`",
        "",
        f"Rows: {len(rows)}; ok: {len(ok)}",
        f"Positive token-relation margin rows: {len(positive_relation)}/{len(ok) if ok else 0}",
        f"Positive V-JEPA embedding margin rows: {len(positive_margin)}/{len(ok) if ok else 0}",
        "",
        "This uses local V-JEPA2.1 ViT-B EMA encoder weights with 8 sparse frames at 224px. It does not download models and does not train.",
    ]
    output_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["audit", "dinov2_frame_smoke", "vjepa2_video_smoke"], default="audit")
    p.add_argument("--search_roots", nargs="+", default=["/home/nvme03", "/home/nvme04"])
    p.add_argument("--output_dir", default="reports/dpo_utility_calibration_v14/latent_monitor")
    p.add_argument("--max_dirs", type=int, default=20000)
    p.add_argument("--max_seconds", type=float, default=30.0)
    p.add_argument("--pair_manifest", default="manifests/dpo_v14_subsets/asset_complete_prefix5_calibration4.jsonl")
    p.add_argument("--num_pairs", type=int, default=0)
    p.add_argument("--gpu", type=int, default=None)
    p.add_argument("--max_frames", type=int, default=5)
    p.add_argument("--repo_root", default=".")
    p.add_argument("--dinov2_weight", default=DEFAULT_DINOV2_VITS14)
    p.add_argument("--vjepa2_weight", default=DEFAULT_VJEPA2_BASE)
    p.add_argument("--vjepa2_repo", default=DEFAULT_VJEPA2_REPO)
    p.add_argument("--vjepa_img_size", type=int, default=224)
    p.add_argument("--output_csv", default=None)
    p.add_argument("--output_json", default=None)
    p.add_argument("--output_md", default=None)
    args = p.parse_args(argv)
    if args.mode == "audit":
        result = audit(args)
    elif args.mode == "dinov2_frame_smoke":
        result = score_dinov2_frame_smoke(args)
    else:
        result = score_vjepa2_video_smoke(args)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
