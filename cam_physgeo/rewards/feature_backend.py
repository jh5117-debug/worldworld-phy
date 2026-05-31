from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cam_physgeo.trd.feature_extractors import inspect_backend
from cam_physgeo.utils.io import write_json


def dinov2_plan(weights_root: str | Path = "local_assets/weights") -> dict[str, Any]:
    status = inspect_backend("dinov2", weights_root, "cpu")
    root = Path(weights_root) / "dinov2"
    return {
        "status": status,
        "recommended_model": "dinov2_vits14",
        "target_path": str(root),
        "estimated_size": "hundreds of MB depending on checkpoint format",
        "requires_hf_token": "unknown; depends on download source",
        "requires_user_approval": True,
        "auto_download_performed": False,
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
    payload = {
        "check": args.check,
        "backend_status": status,
        "can_forward": False,
        "feature_shape": None,
        "plan": dinov2_plan(args.weights_root),
        "note": "No model is downloaded by this smoke. Real DINO forward requires a local checkpoint and loader.",
    }
    write_json(payload, out / "summary.json")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
