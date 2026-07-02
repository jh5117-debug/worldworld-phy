from __future__ import annotations

import importlib
import json
import os
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _repo_src() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def _write_jsonl(path: str | Path | None, row: dict[str, Any]) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
        f.flush()


def _cpu_rss_gb() -> float:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return float(line.split()[1]) / (1024.0 * 1024.0)
    except Exception:
        return 0.0
    return 0.0


def _cuda_stats() -> dict[str, float]:
    try:
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError("cuda unavailable")
        return {
            "gpu_allocated_gb": torch.cuda.memory_allocated() / (1024**3),
            "gpu_reserved_gb": torch.cuda.memory_reserved() / (1024**3),
            "gpu_max_allocated_gb": torch.cuda.max_memory_allocated() / (1024**3),
            "gpu_max_reserved_gb": torch.cuda.max_memory_reserved() / (1024**3),
        }
    except Exception:
        return {"gpu_allocated_gb": 0.0, "gpu_reserved_gb": 0.0, "gpu_max_allocated_gb": 0.0, "gpu_max_reserved_gb": 0.0}


class _Heartbeat:
    def __init__(self, path: str | Path | None, *, seconds: float = 15.0) -> None:
        self.path = path
        self.seconds = float(seconds)
        self.stage = ""
        self.stage_start = 0.0
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def write(self, stage: str, event: str, status: str = "", notes: str = "", error_reason: str = "") -> None:
        elapsed = time.time() - self.stage_start if self.stage == stage and self.stage_start else 0.0
        _write_jsonl(self.path, {"timestamp": time.time(), "stage": stage, "event": event, "status": status, "elapsed_seconds": elapsed, "cpu_rss_gb": _cpu_rss_gb(), "notes": notes, "error_reason": error_reason, **_cuda_stats()})

    def start(self, stage: str, notes: str = "") -> None:
        with self._lock:
            self.stage = stage
            self.stage_start = time.time()
        self.write(stage, "stage_start", "START", notes=notes)

    def done(self, stage: str, status: str = "PASS") -> None:
        self.write(stage, "stage_done", status)
        with self._lock:
            self.stage = ""
            self.stage_start = 0.0

    def error(self, stage: str, exc: BaseException) -> None:
        self.write(stage, "stage_error", "FAILED", error_reason=repr(exc))
        with self._lock:
            self.stage = ""
            self.stage_start = 0.0

    def _loop(self) -> None:
        while not self._stop.wait(self.seconds):
            with self._lock:
                stage = self.stage
            if stage:
                self.write(stage, "heartbeat", "RUNNING")

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)


@dataclass(slots=True)
class SafeWanPolicyLoadResult:
    model: Any
    model_root: str
    subfolder: str
    dtype: str
    device: str
    local_files_only: bool
    use_safetensors: bool
    low_cpu_mem_usage: bool
    moved_to_gpu: bool
    elapsed_seconds: float


def _dtype_from_name(dtype: str):
    import torch
    value = str(dtype).lower()
    if value in {"bf16", "bfloat16"}:
        return torch.bfloat16
    if value in {"fp16", "float16", "half"}:
        return torch.float16
    if value in {"fp32", "float32", "full"}:
        return torch.float32
    raise ValueError(f"unsupported dtype={dtype}")


def _resolve_model_paths(model_path: str | Path) -> tuple[Path, str]:
    path = Path(model_path).expanduser().resolve()
    if path.name == "lingbot_world_fast":
        return path.parent, "lingbot_world_fast"
    fast = path / "lingbot_world_fast"
    if fast.exists():
        return path, "lingbot_world_fast"
    raise FileNotFoundError(f"cannot resolve LingBot-Fast model root from {path}")


def _import_wan_model_fast():
    lingbot_root = Path(os.environ.get("LINGBOT_CODE_DIR", "/home/nvme03/workspace/lingbot-world")).resolve()
    for item in (str(_repo_src()), str(lingbot_root)):
        if item not in sys.path:
            sys.path.insert(0, item)
    importlib.invalidate_caches()
    from wan.modules.model_fast import WanModelFast
    return WanModelFast


def load_wan_policy_safe(
    model_path: str | Path,
    dtype: str = "bf16",
    device: str = "cpu",
    local_files_only: bool = True,
    use_safetensors: bool = True,
    low_cpu_mem_usage: bool = True,
    policy_only: bool = True,
    load_text: bool = False,
    load_vae: bool = False,
    load_lora: bool = False,
    adapter_path: str | Path | None = None,
    move_to_gpu: bool = False,
    heartbeat_path: str | Path | None = None,
    control_type: str = "cam",
    heartbeat_seconds: float = 15.0,
) -> SafeWanPolicyLoadResult:
    if not policy_only:
        raise ValueError("safe loader only supports policy_only=True")
    if load_text or load_vae:
        raise ValueError("safe loader does not load T5/VAE")
    if load_lora or adapter_path:
        raise ValueError("safe loader keeps LoRA as a separate stage")
    start = time.time()
    hb = _Heartbeat(heartbeat_path, seconds=heartbeat_seconds)
    stage = "safe_loader"
    try:
        stage = "safe_resolve_model_path"
        hb.start(stage, str(model_path))
        root, subfolder = _resolve_model_paths(model_path)
        hb.done(stage)
        stage = "safe_import_wan_model_fast"
        hb.start(stage)
        WanModelFast = _import_wan_model_fast()
        hb.done(stage)
        stage = "safe_from_pretrained_cpu"
        hb.start(stage, json.dumps({"root": str(root), "subfolder": subfolder, "dtype": dtype, "local_files_only": local_files_only, "use_safetensors": use_safetensors, "low_cpu_mem_usage": low_cpu_mem_usage}))
        model = WanModelFast.from_pretrained(str(root), subfolder=subfolder, torch_dtype=_dtype_from_name(dtype), local_files_only=bool(local_files_only), use_safetensors=bool(use_safetensors), low_cpu_mem_usage=bool(low_cpu_mem_usage), control_type=control_type)
        hb.done(stage)
        moved = False
        if move_to_gpu:
            import torch
            stage = "safe_move_to_gpu"
            hb.start(stage, str(device))
            dev = torch.device(device)
            if dev.type == "cuda":
                torch.cuda.set_device(dev.index or 0)
            model.to(dev)
            moved = dev.type == "cuda"
            hb.done(stage)
        hb.write("safe_loader_done", "final", "PASS", notes=f"elapsed={time.time() - start:.2f}")
        return SafeWanPolicyLoadResult(model=model, model_root=str(root), subfolder=subfolder, dtype=str(dtype), device=str(device), local_files_only=bool(local_files_only), use_safetensors=bool(use_safetensors), low_cpu_mem_usage=bool(low_cpu_mem_usage), moved_to_gpu=moved, elapsed_seconds=time.time() - start)
    except Exception as exc:
        hb.error(stage, exc)
        raise
    finally:
        hb.close()
