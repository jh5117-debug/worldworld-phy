from __future__ import annotations

import argparse
import gc
import inspect
import json
import os
import resource
import signal
import sys
import time
import traceback
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from cam_physgeo.training.model_loading import resolve_t5_runtime_paths
from cam_physgeo.utils.io import load_yaml, write_json


T0 = time.time()


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data: str) -> int:
        for stream in self.streams:
            stream.write(data)
            stream.flush()
        return len(data)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


def mark(event: str, **kwargs: Any) -> None:
    payload = {"event": event, "elapsed_sec": round(time.time() - T0, 3)}
    payload.update(kwargs)
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    print(f"[MARK] {event} {body}", flush=True)


class StepTimeout(TimeoutError):
    pass


@contextmanager
def step_timeout(name: str, seconds: int):
    def handler(_signum, _frame):
        raise StepTimeout(f"{name} exceeded {seconds}s")

    old_handler = signal.signal(signal.SIGALRM, handler)
    old_timer = signal.setitimer(signal.ITIMER_REAL, max(1, int(seconds)))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, old_timer[0], old_timer[1])
        signal.signal(signal.SIGALRM, old_handler)


def parse_optional_bool(value: str | None) -> bool | None:
    if value in {None, "", "auto", "none", "null"}:
        return None
    lowered = str(value).lower()
    if lowered in {"1", "true", "yes", "y"}:
        return True
    if lowered in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false/auto, got {value!r}")


def dtype_from_name(name: str):
    import torch

    table = {
        "fp32": torch.float32,
        "float32": torch.float32,
        "fp16": torch.float16,
        "float16": torch.float16,
        "bf16": torch.bfloat16,
        "bfloat16": torch.bfloat16,
    }
    return table[str(name).lower()]


def rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    value = float(usage.ru_maxrss)
    # Linux reports KiB, macOS reports bytes. H20 is Linux.
    return round(value / 1024.0, 2)


def candidate_roots(fast_root: str, base_root: str = "", manual_path: str = "") -> dict[str, str]:
    cfg: dict[str, Any] = {}
    try:
        cfg = load_yaml("configs/cam_physgeo/paths.yaml")
    except Exception:
        cfg = {}
    if fast_root:
        cfg["LINGBOT_FAST_ROOT"] = fast_root
    if base_root:
        cfg["LINGBOT_BASE_ROOT"] = base_root
    paths = resolve_t5_runtime_paths(cfg)
    if manual_path:
        manual = Path(manual_path)
        if manual.is_file():
            paths["t5_checkpoint"] = str(manual)
        else:
            paths["tokenizer_root"] = str(manual)
            t5 = manual / "models_t5_umt5-xxl-enc-bf16.pth"
            if t5.exists():
                paths["t5_checkpoint"] = str(t5)
    return paths


def stat_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    st = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "is_symlink": path.is_symlink(),
        "realpath": str(path.resolve()),
        "size_bytes": st.st_size,
        "size_gb": round(st.st_size / (1024**3), 3),
        "mtime": st.st_mtime,
        "mode": oct(st.st_mode),
        "device": st.st_dev,
        "inode": st.st_ino,
    }


def path_status(paths: dict[str, str]) -> dict[str, Any]:
    tokenizer = Path(paths["tokenizer_root"])
    t5 = Path(paths["t5_checkpoint"])
    runtime = Path(paths.get("runtime_root", ""))
    runtime_tree = []
    if runtime.exists():
        for item in sorted(runtime.rglob("*"))[:200]:
            try:
                runtime_tree.append({
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "is_symlink": item.is_symlink(),
                    "size_bytes": item.stat().st_size if item.is_file() else 0,
                    "target": os.readlink(item) if item.is_symlink() else "",
                })
            except OSError:
                pass
    return {
        "fast_root": paths.get("fast_root"),
        "base_root": paths.get("base_root"),
        "runtime_root": paths.get("runtime_root"),
        "runtime_tree_head": runtime_tree,
        "tokenizer_root": str(tokenizer),
        "tokenizer_root_exists": tokenizer.exists(),
        "tokenizer_files": {name: (tokenizer / name).exists() for name in ["tokenizer.json", "spiece.model", "tokenizer_config.json", "config.json"]},
        "t5_checkpoint": str(t5),
        "t5_checkpoint_stat": stat_payload(t5),
    }


def environment_status() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "python": sys.executable,
        "python_version": sys.version,
        "pythonpath": os.environ.get("PYTHONPATH", ""),
        "HF_HOME": os.environ.get("HF_HOME"),
        "TRANSFORMERS_CACHE": os.environ.get("TRANSFORMERS_CACHE"),
        "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
        "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    try:
        import torch

        payload["torch"] = torch.__version__
        payload["cuda_available"] = bool(torch.cuda.is_available())
    except Exception as exc:
        payload["torch_error"] = repr(exc)
    try:
        import transformers

        payload["transformers"] = transformers.__version__
    except Exception as exc:
        payload["transformers_error"] = repr(exc)
    try:
        import safetensors

        payload["safetensors"] = safetensors.__version__
    except Exception as exc:
        payload["safetensors_error"] = repr(exc)
    try:
        import sentencepiece

        payload["sentencepiece"] = sentencepiece.__version__
    except Exception as exc:
        payload["sentencepiece_error"] = repr(exc)
    return payload


def load_tokenizer(tokenizer_root: str, *, local_files_only: bool):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(tokenizer_root, local_files_only=local_files_only)


def load_wan_t5(
    *,
    lingbot_code: str,
    checkpoint_path: str,
    tokenizer_path: str,
    device: str,
    dtype_name: str,
):
    if lingbot_code and lingbot_code not in sys.path:
        sys.path.insert(0, lingbot_code)
    from wan.configs import WAN_CONFIGS
    from wan.modules.t5 import T5EncoderModel

    cfg = WAN_CONFIGS["i2v-A14B"]
    dtype = dtype_from_name(dtype_name)
    text_len = int(getattr(cfg, "text_len", 512))
    return T5EncoderModel(
        text_len=text_len,
        dtype=dtype,
        device=device,
        checkpoint_path=checkpoint_path,
        tokenizer_path=tokenizer_path,
        shard_fn=None,
    )


def encode_prompt(model, prompt: str, device: str):
    attempts = [
        lambda: model([prompt], device),
        lambda: model([prompt]),
        lambda: model.encode([prompt], device=device),
        lambda: model.encode([prompt]),
    ]
    last_exc: Exception | None = None
    for fn in attempts:
        try:
            return fn()
        except TypeError as exc:
            last_exc = exc
    if last_exc:
        raise last_exc
    raise RuntimeError("no encoding attempt executed")


def shape_summary(obj: Any) -> Any:
    if hasattr(obj, "shape"):
        return list(obj.shape)
    if isinstance(obj, (list, tuple)):
        return [shape_summary(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): shape_summary(v) for k, v in obj.items()}
    return type(obj).__name__


def tensor_summary(state: Any, *, limit: int) -> dict[str, Any]:
    import torch

    items: list[tuple[str, Any]] = []

    def walk(prefix: str, obj: Any) -> None:
        if torch.is_tensor(obj):
            items.append((prefix, obj))
        elif isinstance(obj, dict):
            for key, value in obj.items():
                walk(f"{prefix}.{key}" if prefix else str(key), value)
        elif isinstance(obj, (list, tuple)):
            for idx, value in enumerate(obj):
                walk(f"{prefix}.{idx}" if prefix else str(idx), value)

    walk("", state)
    dtype_counts = Counter(str(t.dtype) for _, t in items)
    max_tensor = None
    max_numel = -1
    for key, tensor in items:
        numel = int(tensor.numel())
        if numel > max_numel:
            max_numel = numel
            max_tensor = {"key": key, "shape": list(tensor.shape), "dtype": str(tensor.dtype), "numel": numel}
    top_keys = []
    if isinstance(state, dict):
        top_keys = list(state.keys())[:limit]
    return {
        "type": type(state).__name__,
        "top_level_keys": [str(k) for k in top_keys],
        "top_level_key_count": len(state) if isinstance(state, dict) else None,
        "tensor_count": len(items),
        "dtype_counts": dict(dtype_counts),
        "max_tensor": max_tensor,
        "first_tensor_keys": [key for key, _ in items[:limit]],
    }


def torch_load(path: str, *, map_location: str, weights_only: bool | None, mmap: bool | None):
    import torch

    kwargs: dict[str, Any] = {"map_location": map_location}
    sig = inspect.signature(torch.load)
    if weights_only is not None:
        if "weights_only" in sig.parameters:
            kwargs["weights_only"] = weights_only
        else:
            raise RuntimeError("torch.load does not support weights_only in this environment")
    if mmap is not None:
        if "mmap" in sig.parameters:
            kwargs["mmap"] = mmap
        else:
            raise RuntimeError("torch.load does not support mmap in this environment")
    return torch.load(path, **kwargs)


def stage_path_audit(status: dict[str, Any], _args: argparse.Namespace, _paths: dict[str, str]) -> int:
    mark("path_audit_done")
    status["ok"] = True
    return 0


def stage_ckpt_stat(status: dict[str, Any], _args: argparse.Namespace, paths: dict[str, str]) -> int:
    mark("ckpt_stat_start")
    status["ckpt_stat"] = stat_payload(Path(paths["t5_checkpoint"]))
    mark("ckpt_stat_done", **status["ckpt_stat"])
    status["ok"] = True
    return 0


def stage_tokenizer_only(status: dict[str, Any], args: argparse.Namespace, paths: dict[str, str]) -> int:
    mark("tokenizer_load_start", path=paths["tokenizer_root"])
    start = time.time()
    with step_timeout("tokenizer_load", args.timeout):
        tokenizer = load_tokenizer(paths["tokenizer_root"], local_files_only=args.local_files_only)
    status["steps"]["tokenizer"] = {"ok": True, "elapsed_sec": round(time.time() - start, 3), "class": tokenizer.__class__.__name__}
    mark("tokenizer_load_done", **status["steps"]["tokenizer"])
    status["ok"] = True
    return 0


def stage_read_benchmark(status: dict[str, Any], args: argparse.Namespace, paths: dict[str, str]) -> int:
    path = Path(paths["t5_checkpoint"])
    mark("ckpt_read_benchmark_start", path=str(path), size_bytes=path.stat().st_size if path.exists() else 0)
    start = time.time()
    total = 0
    chunk_size = 64 * 1024 * 1024
    with step_timeout("ckpt_read_benchmark", args.timeout):
        with path.open("rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                total += len(data)
    elapsed = time.time() - start
    status["read_benchmark"] = {
        "bytes_read": total,
        "elapsed_sec": round(elapsed, 3),
        "mb_per_sec": round(total / (1024**2) / max(elapsed, 1e-9), 3),
        "gb_per_sec": round(total / (1024**3) / max(elapsed, 1e-9), 3),
    }
    mark("ckpt_read_benchmark_done", **status["read_benchmark"])
    status["ok"] = True
    return 0


def stage_torch_load_only(status: dict[str, Any], args: argparse.Namespace, paths: dict[str, str]) -> int:
    mark(
        "torch_load_start",
        path=paths["t5_checkpoint"],
        map_location=args.map_location,
        weights_only=args.weights_only,
        mmap=args.mmap,
        rss_mb=rss_mb(),
    )
    start = time.time()
    with step_timeout("torch_load", args.timeout):
        state = torch_load(paths["t5_checkpoint"], map_location=args.map_location, weights_only=args.weights_only, mmap=args.mmap)
    elapsed = time.time() - start
    mark("torch_load_done", seconds=round(elapsed, 3), rss_mb=rss_mb())
    mark("state_dict_keys_start")
    summary = tensor_summary(state, limit=args.print_keys_limit)
    mark("state_dict_keys_done", tensor_count=summary["tensor_count"], top_level_key_count=summary["top_level_key_count"])
    status["torch_load"] = {
        "elapsed_sec": round(elapsed, 3),
        "rss_peak_mb": rss_mb(),
        "summary": summary,
    }
    del state
    gc.collect()
    status["ok"] = True
    return 0


def stage_full_t5(status: dict[str, Any], args: argparse.Namespace, paths: dict[str, str]) -> int:
    stage_tokenizer_only(status, args, paths)
    mark("t5_model_load_start", checkpoint=paths["t5_checkpoint"], tokenizer=paths["tokenizer_root"], rss_mb=rss_mb())
    start = time.time()
    with step_timeout("t5_model_load", args.timeout):
        model = load_wan_t5(
            lingbot_code=args.lingbot_code,
            checkpoint_path=paths["t5_checkpoint"],
            tokenizer_path=paths["tokenizer_root"],
            device=args.device,
            dtype_name=args.dtype,
        )
    status["steps"]["t5_model"] = {"ok": True, "elapsed_sec": round(time.time() - start, 3), "class": model.__class__.__name__, "rss_peak_mb": rss_mb()}
    mark("t5_model_load_done", **status["steps"]["t5_model"])
    mark("prompt_encode_start")
    start = time.time()
    with step_timeout("prompt_encode", args.timeout):
        embedding = encode_prompt(model, args.prompt, args.device)
    status["steps"]["prompt_encode"] = {"ok": True, "elapsed_sec": round(time.time() - start, 3), "shape": shape_summary(embedding)}
    mark("prompt_encode_done", **status["steps"]["prompt_encode"])
    if args.save_embedding:
        import torch

        out = Path(args.save_embedding)
        out.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"prompt": args.prompt, "embedding": embedding, "shape": shape_summary(embedding)}, out)
        status["saved_embedding"] = str(out)
        mark("embedding_saved", path=str(out))
    status["ok"] = True
    return 0


def stage_unimplemented(status: dict[str, Any], args: argparse.Namespace, _paths: dict[str, str]) -> int:
    status["ok"] = False
    status["error"] = f"stage {args.stage!r} requires instrumenting LingBot t5.py internals and is not faked by the standalone probe"
    mark("stage_not_implemented", stage=args.stage, reason=status["error"])
    return 2


STAGE_RUNNERS = {
    "path_audit": stage_path_audit,
    "tokenizer_only": stage_tokenizer_only,
    "ckpt_stat": stage_ckpt_stat,
    "ckpt_read_benchmark": stage_read_benchmark,
    "torch_load_only": stage_torch_load_only,
    "model_construct_only": stage_unimplemented,
    "load_state_dict_only": stage_unimplemented,
    "full_t5": stage_full_t5,
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Probe LingBot-Fast companion T5/tokenizer without WanI2VFast.")
    ap.add_argument("--fast_root", default="local_assets/weights/lingbot_fast")
    ap.add_argument("--base_root", default="")
    ap.add_argument("--path", default="", help="Manual tokenizer root or T5 checkpoint override.")
    ap.add_argument("--lingbot_code", default="")
    ap.add_argument("--stage", default="full_t5", choices=sorted(STAGE_RUNNERS))
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--dtype", default="fp32", choices=["fp32", "fp16", "bf16"])
    ap.add_argument("--prompt", default="A synthetic physical scene.")
    ap.add_argument("--local-files-only", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--timeout", type=int, default=120, help="Per-step timeout in seconds.")
    ap.add_argument("--map-location", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--weights-only", type=parse_optional_bool, default=None)
    ap.add_argument("--mmap", type=parse_optional_bool, default=None)
    ap.add_argument("--profile-memory", action="store_true")
    ap.add_argument("--print-keys-limit", type=int, default=20)
    ap.add_argument("--save_embedding", default="")
    ap.add_argument("--save-json", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--log-file", default="")
    args = ap.parse_args(argv)

    log_f = None
    if args.log_file:
        Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
        log_f = open(args.log_file, "w", encoding="utf-8", errors="replace")
        sys.stdout = Tee(sys.stdout, log_f)  # type: ignore[assignment]
        sys.stderr = Tee(sys.stderr, log_f)  # type: ignore[assignment]

    if args.offline or args.local_files_only:
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    cfg = load_yaml("configs/cam_physgeo/paths.yaml")
    if not args.lingbot_code:
        args.lingbot_code = str(cfg.get("LINGBOT_CODE_ROOT") or "local_assets/third_party/lingbot_world")
    if args.lingbot_code and args.lingbot_code not in sys.path:
        sys.path.insert(0, args.lingbot_code)
    paths = candidate_roots(args.fast_root, args.base_root, args.path)
    status: dict[str, Any] = {
        "ok": False,
        "stage": args.stage,
        "device": args.device,
        "dtype": args.dtype,
        "prompt": args.prompt,
        "offline": bool(args.offline or args.local_files_only),
        "local_files_only": args.local_files_only,
        "map_location": args.map_location,
        "weights_only": args.weights_only,
        "mmap": args.mmap,
        "lingbot_code": args.lingbot_code,
        "environment": environment_status(),
        "paths": path_status(paths),
        "steps": {},
    }
    mark("probe_start", stage=args.stage, device=args.device, dtype=args.dtype)
    mark("path_status", **status["paths"]["t5_checkpoint_stat"])

    try:
        rc = STAGE_RUNNERS[args.stage](status, args, paths)
        if status.get("ok"):
            mark("probe_done", ok=True, stage=args.stage)
    except BaseException as exc:
        status["ok"] = False
        status["error"] = repr(exc)
        status["traceback"] = traceback.format_exc()
        mark("probe_failed", error=repr(exc), stage=args.stage)
        rc = 124 if isinstance(exc, StepTimeout) else 1

    out = args.save_json or args.out
    if out:
        write_json(status, out)
    else:
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
    if log_f:
        log_f.close()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
