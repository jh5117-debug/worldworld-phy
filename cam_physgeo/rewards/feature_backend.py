from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cam_physgeo.trd.feature_extractors import inspect_backend
from cam_physgeo.utils.io import write_json


def dinov2_plan(weights_root: str | Path = "local_assets/weights") -> dict[str, Any]:
    status = inspect_backend("dinov2", weights_root, "cpu")
    root = Path(weights_root) / "dinov2" / "dinov2_vits14"
    return {
        "status": status,
        "recommended_model": "dinov2_vits14",
        "target_path": str(root),
        "estimated_size": "hundreds of MB depending on checkpoint format",
        "requires_hf_token": "unknown; depends on download source",
        "requires_user_approval": True,
        "auto_download_performed": False,
        "download_command_draft": (
            "mkdir -p local_assets/weights/dinov2/dinov2_vits14 && "
            "# download dinov2_vits14 checkpoint here after approval"
        ),
        "reward_uses": ["R_fg foreground identity", "R_reobs object/background feature similarity", "GeoFlow-style R_dino"],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", required=True, choices=["dinov2"])
    ap.add_argument("--weights_root", default="local_assets/weights")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--limit", type=int, default=1)
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    status = inspect_backend(args.check, args.weights_root, args.device)
    has_checkpoint = bool(status.get("file_count"))
    payload = {
        "check": args.check,
        "backend_status": status,
        "can_forward": False,
        "feature_shape": None,
        "plan": dinov2_plan(args.weights_root),
        "note": "No model is downloaded by this smoke. Real DINO forward requires a local checkpoint and loader.",
        "local_checkpoint_present": has_checkpoint,
        "R_fg_R_reobs_dpo_ready": False,
    }
    if has_checkpoint:
        payload["note"] = "A local file exists, but no DINOv2 architecture loader is wired in this smoke; forward is still disabled until the loader is added."
    write_json(payload, out / "summary.json")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
