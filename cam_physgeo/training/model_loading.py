"""LingBot runtime discovery and guarded loading helpers.

This module intentionally keeps heavyweight model construction behind explicit
``smoke_run`` / ``load_branch`` calls. Dry-runs validate paths and legacy import
roots without allocating the 70G/150G checkpoints.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from cam_physgeo.utils.io import load_yaml, write_json


PROJECT_ROOT = Path("/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys")
LOCAL_ASSETS_ROOT = PROJECT_ROOT / "local_assets"
WEIGHT_ROOT = LOCAL_ASSETS_ROOT / "weights"
DEFAULT_FAST_CANDIDATES = (
    WEIGHT_ROOT / "lingbot_fast",
)
DEFAULT_BASE_CANDIDATES = (
    WEIGHT_ROOT / "lingbot_base",
)
DEFAULT_LINGBOT_CODE_CANDIDATES = (
    LOCAL_ASSETS_ROOT / "third_party" / "lingbot_world",
)


@dataclass(slots=True)
class LingBotCheckpointInfo:
    label: str
    path: str
    exists: bool
    size_bytes: int = 0
    files: dict[str, int] = field(default_factory=dict)
    has_config: bool = False
    has_model_index: bool = False
    has_tokenizer: bool = False
    has_vae: bool = False
    has_t5: bool = False
    has_high_noise_model: bool = False
    has_low_noise_model: bool = False
    has_fast_shards: bool = False
    recognized_by_legacy_loader: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def size_gb(self) -> float:
        return round(self.size_bytes / (1024**3), 3)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "label": self.label,
            "path": self.path,
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "size_gb": self.size_gb,
            "files": self.files,
            "has_config": self.has_config,
            "has_model_index": self.has_model_index,
            "has_tokenizer": self.has_tokenizer,
            "has_vae": self.has_vae,
            "has_t5": self.has_t5,
            "has_high_noise_model": self.has_high_noise_model,
            "has_low_noise_model": self.has_low_noise_model,
            "has_fast_shards": self.has_fast_shards,
            "recognized_by_legacy_loader": self.recognized_by_legacy_loader,
            "notes": self.notes,
        }
        return payload


def _path_from_cfg(cfg: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = cfg.get(key)
        if value not in {"", None, "null"}:
            return str(value)
    return ""


def resolve_model_paths(cfg: dict[str, Any] | None = None) -> dict[str, str]:
    """Resolve LingBot Base/Fast and LingBot code roots from config + known H20 paths."""

    cfg = dict(cfg or {})

    def first_existing(config_path: str, candidates: tuple[Path, ...]) -> str:
        ordered = []
        if config_path:
            ordered.append(Path(config_path).expanduser())
        ordered.extend(candidates)
        for path in ordered:
            if path.exists():
                return str(path.resolve())
        return str(ordered[0]) if ordered else ""

    base = first_existing(
        _path_from_cfg(cfg, "LINGBOT_BASE_ROOT", "lingbot_base_root", "base_model_dir"),
        DEFAULT_BASE_CANDIDATES,
    )
    fast = first_existing(
        _path_from_cfg(cfg, "LINGBOT_FAST_ROOT", "lingbot_fast_root", "fast_model_dir"),
        DEFAULT_FAST_CANDIDATES,
    )
    code = first_existing(
        _path_from_cfg(cfg, "LINGBOT_CODE_ROOT", "lingbot_code_dir"),
        DEFAULT_LINGBOT_CODE_CANDIDATES,
    )
    return {"lingbot_base": base, "lingbot_fast": fast, "lingbot_code": code}


def directory_size_bytes(path: str | Path) -> int:
    path = Path(path)
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total


def inspect_checkpoint(path: str | Path, *, label: str) -> LingBotCheckpointInfo:
    root = Path(path).expanduser()
    info = LingBotCheckpointInfo(label=label, path=str(root), exists=root.exists())
    if not root.exists():
        info.notes.append("path missing")
        return info
    info.size_bytes = directory_size_bytes(root)
    counters = {
        "safetensors": 0,
        "bin": 0,
        "pth": 0,
        "config_json": 0,
        "tokenizer_json": 0,
        "model_index_json": 0,
    }
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        name = item.name
        suffix = item.suffix.lower()
        if suffix == ".safetensors":
            counters["safetensors"] += 1
        elif suffix == ".bin":
            counters["bin"] += 1
        elif suffix == ".pth":
            counters["pth"] += 1
        elif name == "config.json":
            counters["config_json"] += 1
        elif name == "tokenizer.json":
            counters["tokenizer_json"] += 1
        elif name == "model_index.json":
            counters["model_index_json"] += 1
    info.files = counters
    info.has_config = (root / "config.json").exists() or counters["config_json"] > 0
    info.has_model_index = counters["model_index_json"] > 0
    info.has_tokenizer = (root / "google" / "umt5-xxl" / "tokenizer.json").exists() or counters["tokenizer_json"] > 0
    info.has_vae = (root / "Wan2.1_VAE.pth").exists()
    info.has_t5 = (root / "models_t5_umt5-xxl-enc-bf16.pth").exists()
    info.has_high_noise_model = (root / "high_noise_model" / "config.json").exists()
    info.has_low_noise_model = (root / "low_noise_model" / "config.json").exists()
    info.has_fast_shards = (root / "model.safetensors.index.json").exists() or any(root.glob("model-*-of-*.safetensors"))
    info.recognized_by_legacy_loader = info.has_high_noise_model and info.has_low_noise_model and info.has_vae and info.has_t5
    if info.has_fast_shards:
        info.notes.append("fast-style sharded checkpoint")
    if info.recognized_by_legacy_loader:
        info.notes.append("legacy WanModel.from_pretrained branch layout present")
    if not info.has_tokenizer:
        info.notes.append("tokenizer not inside checkpoint root; may rely on companion base root")
    return info


def load_lingbot_paths_from_config(config_path: str | Path = "configs/cam_physgeo/paths.yaml") -> dict[str, str]:
    return resolve_model_paths(load_yaml(config_path))


def build_legacy_stage1_helper_args(
    *,
    base_model_dir: str,
    lingbot_code_dir: str,
    student_tuning_mode: str = "lora",
    control_type: str = "cam",
) -> SimpleNamespace:
    """Build the minimal arg namespace expected by legacy LingBotStage1Helper."""

    return SimpleNamespace(
        base_model_dir=str(base_model_dir),
        stage1_ckpt_dir=str(base_model_dir),
        lingbot_code_dir=str(lingbot_code_dir),
        control_type=str(control_type),
        student_tuning_mode=str(student_tuning_mode),
        student_lora_rank=16,
        student_lora_alpha=16,
        student_lora_dropout=0.0,
        student_lora_block_start=0,
        student_lora_chunk_size=0,
        student_lora_merge_mode="inplace",
        student_memory_efficient_modulation=True,
        student_ffn_chunk_size=4096,
        student_norm_chunk_size=0,
    )


def import_legacy_stage1_helper(project_root: str | Path | None = None):
    root = Path(project_root or Path.cwd()).resolve()
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from physical_consistency.trainers.stage1_components import LingBotStage1Helper

    return LingBotStage1Helper


def check_legacy_lingbot_import(lingbot_code_dir: str) -> dict[str, Any]:
    """Check whether the LingBot checkout exposes the Wan runtime modules."""

    root = Path(lingbot_code_dir)
    result = {
        "lingbot_code_dir": str(root),
        "exists": root.exists(),
        "has_wan_model": (root / "wan" / "modules" / "model.py").exists(),
        "import_ok": False,
        "error": "",
    }
    if not result["has_wan_model"]:
        return result
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        import wan.modules.model  # noqa: F401

        result["import_ok"] = True
    except Exception as exc:  # pragma: no cover - environment dependent
        result["error"] = repr(exc)
    return result


def load_lingbot_branch(
    *,
    model_root: str,
    lingbot_code_dir: str,
    branch: str = "low",
    device: str = "cpu",
    control_type: str = "cam",
    project_root: str | Path | None = None,
):
    """Load a LingBot low/high branch through the legacy WanModel loader.

    This is intentionally an explicit call because it can allocate tens of GB.
    """

    import torch

    helper_cls = import_legacy_stage1_helper(project_root)
    args = build_legacy_stage1_helper_args(
        base_model_dir=model_root,
        lingbot_code_dir=lingbot_code_dir,
        control_type=control_type,
    )
    helper = helper_cls(args)
    model = helper.load_model(torch.device(device), branch, checkpoint_dir=model_root, control_type=control_type)
    return helper, model


def write_lingbot_weight_audit(
    *,
    config_path: str | Path = "configs/cam_physgeo/paths.yaml",
    out_path: str | Path = "docs/lingbot_weight_audit.md",
) -> dict[str, Any]:
    cfg = load_yaml(config_path)
    paths = resolve_model_paths(cfg)
    base_info = inspect_checkpoint(paths["lingbot_base"], label="LingBot-Base")
    fast_info = inspect_checkpoint(paths["lingbot_fast"], label="LingBot-Fast")
    import_info = check_legacy_lingbot_import(paths["lingbot_code"])
    payload = {
        "paths": paths,
        "base": base_info.to_dict(),
        "fast": fast_info.to_dict(),
        "legacy_import": import_info,
    }
    lines = [
        "# LingBot Weight Audit",
        "",
        f"- LingBot-Base found: `{base_info.exists}` at `{base_info.path}` ({base_info.size_gb} GB)",
        f"- LingBot-Fast found: `{fast_info.exists}` at `{fast_info.path}` ({fast_info.size_gb} GB)",
        f"- LingBot code root: `{paths['lingbot_code']}` import_ok=`{import_info['import_ok']}`",
        "",
        "## Base",
        "```json",
        json.dumps(base_info.to_dict(), indent=2, sort_keys=True),
        "```",
        "",
        "## Fast",
        "```json",
        json.dumps(fast_info.to_dict(), indent=2, sort_keys=True),
        "```",
        "",
        "## Loader Recognition",
        "",
        "- Base is directly usable by the legacy Stage1 helper when it has `high_noise_model`, `low_noise_model`, `Wan2.1_VAE.pth`, and T5 files.",
        "- Fast is present as a fast-style 16-shard checkpoint. It is available for Fast baseline/rollout loading through the LingBot fast runtime; if a Stage1 branch loader is requested, use Base or a branch-style adapted bundle.",
        "- No duplicate download is needed when the Fast path above exists.",
    ]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit and optionally smoke-load LingBot models.")
    parser.add_argument("--config", default="configs/cam_physgeo/paths.yaml")
    parser.add_argument("--model_type", default="fast", choices=["base", "fast"])
    parser.add_argument("--branch", default="low", choices=["low", "high"])
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke-run", action="store_true")
    parser.add_argument("--out", default="docs/lingbot_weight_audit.json")
    args = parser.parse_args(argv)

    payload = write_lingbot_weight_audit(config_path=args.config)
    write_json(payload, args.out)
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.dry_run:
        return 0
    if args.smoke_run:
        key = "lingbot_base" if args.model_type == "base" else "lingbot_fast"
        load_lingbot_branch(
            model_root=payload["paths"][key],
            lingbot_code_dir=payload["paths"]["lingbot_code"],
            branch=args.branch,
            device=args.device,
            control_type="cam",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
