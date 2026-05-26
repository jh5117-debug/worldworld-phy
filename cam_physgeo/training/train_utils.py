from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from cam_physgeo.training.model_loading import resolve_model_paths
from cam_physgeo.utils.io import load_yaml


def load_training_config(path: str) -> dict:
    return load_yaml(path)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_legacy_src_on_path(root: str | Path | None = None) -> None:
    src = Path(root or project_root()) / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def dry_run_payload(stage: str, cfg: dict, **extra) -> dict:
    payload = {
        "stage": stage,
        "dry_run": True,
        "config": cfg,
        "model_paths": resolve_model_paths(load_yaml("configs/cam_physgeo/paths.yaml")),
        "pid": os.getpid(),
    }
    payload.update(extra)
    return payload


def print_dry_run_plan(stage: str, cfg: dict, **extra) -> None:
    print(json.dumps(dry_run_payload(stage, cfg, **extra), indent=2, sort_keys=True))
