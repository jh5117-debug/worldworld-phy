"""Small BF16/SIGFPE diagnostic for LingBot-Fast StageA.

This script does not train, save weights, or touch TDW. It isolates basic BF16
kernel/runtime failures before LingBot-Fast StageA preflight.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _optional_version(name: str) -> str:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return "not_installed"
    try:
        module = __import__(name)
        return str(getattr(module, "__version__", "installed_unknown_version"))
    except Exception as exc:
        return f"import_failed:{type(exc).__name__}:{exc}"


def _run_text(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=20).strip()
    except Exception as exc:
        return f"unavailable:{type(exc).__name__}:{exc}"


def _env_report() -> dict[str, Any]:
    import torch

    return {
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "torch_cuda": str(torch.version.cuda),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count_visible": int(torch.cuda.device_count()),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "cuda_bf16_supported": bool(torch.cuda.is_available() and torch.cuda.is_bf16_supported()),
        "cudnn": str(torch.backends.cudnn.version()),
        "nvidia_smi": _run_text(["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,utilization.gpu", "--format=csv"]),
        "flash_attn": _optional_version("flash_attn"),
        "triton": _optional_version("triton"),
        "xformers": _optional_version("xformers"),
        "transformers": _optional_version("transformers"),
        "accelerate": _optional_version("accelerate"),
        "deepspeed": _optional_version("deepspeed"),
        "gcc": _run_text(["gcc", "--version"]).splitlines()[0],
        "glibc": platform.libc_ver(),
    }


def _finite(name: str, tensor) -> dict[str, Any]:
    import torch

    t = tensor.detach().float()
    return {
        f"{name}_shape": list(tensor.shape),
        f"{name}_dtype": str(tensor.dtype),
        f"{name}_finite": bool(torch.isfinite(t).all().item()),
        f"{name}_min": float(t.min().item()),
        f"{name}_max": float(t.max().item()),
        f"{name}_mean": float(t.mean().item()),
    }


def run_basic(device: str, rows: list[dict[str, Any]]) -> None:
    import torch
    import torch.nn.functional as F

    torch.manual_seed(123)
    dev = torch.device(device)
    if dev.type == "cuda":
        torch.cuda.set_device(dev)
        torch.cuda.reset_peak_memory_stats(dev)
    result: dict[str, Any] = {"attempt": "basic_bf16_kernels", "device": str(dev), "result": "started"}
    start = time.perf_counter()
    try:
        a = torch.randn(512, 512, device=dev, dtype=torch.bfloat16)
        b = torch.randn(512, 512, device=dev, dtype=torch.bfloat16)
        c = a @ b
        x = torch.randn(2, 8, 64, 64, device=dev, dtype=torch.bfloat16)
        ln = torch.nn.LayerNorm(64, device=dev).to(dtype=torch.bfloat16)
        y = ln(x)
        q = torch.randn(2, 4, 128, 64, device=dev, dtype=torch.bfloat16)
        k = torch.randn(2, 4, 128, 64, device=dev, dtype=torch.bfloat16)
        v = torch.randn(2, 4, 128, 64, device=dev, dtype=torch.bfloat16)
        z = F.scaled_dot_product_attention(q, k, v)
        loss = c.float().square().mean() + y.float().square().mean() + z.float().square().mean()
        result.update(_finite("gemm", c))
        result.update(_finite("layernorm", y))
        result.update(_finite("sdpa", z))
        result["loss"] = float(loss.item())
        result["result"] = "pass"
    except BaseException as exc:
        result["result"] = "fail"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    finally:
        if dev.type == "cuda":
            torch.cuda.synchronize(dev)
            result["peak_memory_mb"] = float(torch.cuda.max_memory_allocated(dev) / 1024 / 1024)
        result["seconds"] = time.perf_counter() - start
        rows.append(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["env", "basic"], default="basic")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--out_csv", default="reports/fast_bf16_sigfpe_matrix.csv")
    parser.add_argument("--out_json", default="reports/fast_stageA/fast_bf16_env_report.json")
    args = parser.parse_args()
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    env = _env_report()
    Path(args.out_json).write_text(json.dumps(env, indent=2, sort_keys=True), encoding="utf-8")
    rows: list[dict[str, Any]] = []
    if args.mode == "basic":
        run_basic(args.device, rows)
    else:
        rows.append({"attempt": "env", "result": "pass"})
    fieldnames = sorted({key for row in rows for key in row})
    with Path(args.out_csv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"env_report": args.out_json, "matrix": args.out_csv, "rows": rows}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
