from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


def _gpu_snapshot() -> list[dict[str, Any]]:
    cmd = [
        "nvidia-smi",
        "--query-gpu=index,pci.bus_id,memory.used,memory.total,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        out = subprocess.check_output(cmd, text=True, timeout=30)
    except Exception as exc:
        return [{"error": repr(exc)}]
    rows = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 5:
            rows.append(
                {
                    "index": int(parts[0]),
                    "pci_bus_id": parts[1],
                    "memory_used_mib": int(parts[2]),
                    "memory_total_mib": int(parts[3]),
                    "utilization_gpu_pct": int(parts[4]),
                }
            )
    return rows


def _write(out_dir: Path, payload: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "forward_loss_dryrun_report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    (out_dir / "README.md").write_text(
        "# LingBot warmup forward-loss dry-run\n\n"
        f"Status: {payload.get('status')}\n\n"
        f"Reason: {payload.get('reason', '')}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="forward_loss_dryrun")
    parser.add_argument("--model_type", default="fast")
    parser.add_argument("--config", required=True)
    parser.add_argument("--train_manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--num_batches", type=int, default=2)
    parser.add_argument("--num_frames", type=int, default=8)
    parser.add_argument("--resolution", default="480x832")
    parser.add_argument("--dtype", default="bf16")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--use_action", default="false")
    parser.add_argument("--no_backward", default="true")
    parser.add_argument("--no_optimizer", default="true")
    parser.add_argument("--no_checkpoint", default="true")
    parser.add_argument("--local_files_only", default="true")
    args = parser.parse_args()

    out_dir = Path(args.out)
    snapshot = _gpu_snapshot()
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    allowed = {int(x) for x in visible.split(",") if x.strip().isdigit()}
    busy = [
        gpu
        for gpu in snapshot
        if gpu.get("index") in allowed and (gpu.get("memory_used_mib", 0) > 20000 or gpu.get("utilization_gpu_pct", 0) > 20)
    ]
    payload: dict[str, Any] = {
        "mode": args.mode,
        "status": "blocked",
        "reason": "",
        "cuda_visible_devices": visible,
        "gpu_snapshot": snapshot,
        "train_manifest": args.train_manifest,
        "batch_size": args.batch_size,
        "num_batches": args.num_batches,
        "num_frames": args.num_frames,
        "resolution": args.resolution,
        "no_backward": args.no_backward,
        "no_optimizer": args.no_optimizer,
        "no_checkpoint": args.no_checkpoint,
        "safety": {
            "no_training": True,
            "no_backward": str(args.no_backward).lower() == "true",
            "no_optimizer": str(args.no_optimizer).lower() == "true",
            "no_checkpoint": str(args.no_checkpoint).lower() == "true",
        },
    }
    if args.device == "cuda" and (not allowed):
        payload["reason"] = "CUDA_VISIBLE_DEVICES does not explicitly restrict to GPU6/7"
        _write(out_dir, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2
    if busy:
        payload["reason"] = "GPU6/7 are already busy; forward-loss dry-run skipped to avoid interfering with existing jobs"
        payload["busy_allowed_gpus"] = busy
        _write(out_dir, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2

    # Minimal non-training tensor dry-run. This intentionally does not construct
    # or mutate LingBot weights; real model loading should be approved separately
    # when GPU6/7 are free.
    try:
        import torch

        rows = [json.loads(line) for line in Path(args.train_manifest).read_text(encoding="utf-8").splitlines() if line.strip()]
        if not rows:
            raise RuntimeError("empty train manifest")
        device = torch.device("cuda" if args.device == "cuda" and torch.cuda.is_available() else "cpu")
        latent = torch.zeros((args.batch_size, 4, args.num_frames, 60, 104), device=device, dtype=torch.bfloat16 if args.dtype == "bf16" else torch.float32)
        camera = torch.zeros((args.batch_size, args.num_frames, 4, 4), device=device, dtype=torch.float32)
        loss = (latent.float().square().mean() + camera.square().mean()).detach()
        payload.update(
            {
                "status": "passed_placeholder_no_model_load",
                "reason": "GPU available; verified no-backward/no-optimizer tensor path only. Full LingBot-Fast model load remains a separate approval item.",
                "latent_shape": list(latent.shape),
                "camera_shape": list(camera.shape),
                "loss_value": float(loss.item()),
                "loss_finite": bool(torch.isfinite(loss).item()),
                "memory_after": _gpu_snapshot(),
            }
        )
        _write(out_dir, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        payload["reason"] = f"placeholder forward failed: {exc!r}"
        _write(out_dir, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
