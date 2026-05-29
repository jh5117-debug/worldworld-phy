from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from cam_physgeo.training.model_loading import resolve_t5_runtime_paths
from cam_physgeo.utils.io import load_yaml, write_json


T0 = time.time()


def mark(event: str, **kwargs: Any) -> None:
    payload = {"event": event, "elapsed_sec": round(time.time() - T0, 3)}
    payload.update(kwargs)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


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


def path_status(paths: dict[str, str]) -> dict[str, Any]:
    tokenizer = Path(paths["tokenizer_root"])
    t5 = Path(paths["t5_checkpoint"])
    return {
        "fast_root": paths.get("fast_root"),
        "base_root": paths.get("base_root"),
        "runtime_root": paths.get("runtime_root"),
        "tokenizer_root": str(tokenizer),
        "tokenizer_root_exists": tokenizer.exists(),
        "tokenizer_files": {name: (tokenizer / name).exists() for name in ["tokenizer.json", "spiece.model", "tokenizer_config.json", "config.json"]},
        "t5_checkpoint": str(t5),
        "t5_checkpoint_exists": t5.exists(),
        "t5_checkpoint_size_gb": round(t5.stat().st_size / (1024**3), 3) if t5.exists() else 0.0,
    }


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Probe LingBot-Fast companion T5/tokenizer without WanI2VFast.")
    ap.add_argument("--fast_root", default="local_assets/weights/lingbot_fast")
    ap.add_argument("--base_root", default="")
    ap.add_argument("--path", default="", help="Manual tokenizer root or T5 checkpoint override.")
    ap.add_argument("--lingbot_code", default="")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--dtype", default="fp32", choices=["fp32", "fp16", "bf16"])
    ap.add_argument("--prompt", default="A synthetic physical scene.")
    ap.add_argument("--local-files-only", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--timeout", type=int, default=120, help="Per-step timeout in seconds.")
    ap.add_argument("--save_embedding", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    if args.offline or args.local_files_only:
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    cfg = load_yaml("configs/cam_physgeo/paths.yaml")
    if not args.lingbot_code:
        args.lingbot_code = str(cfg.get("LINGBOT_CODE_ROOT") or "local_assets/third_party/lingbot_world")
    paths = candidate_roots(args.fast_root, args.base_root, args.path)
    status: dict[str, Any] = {
        "ok": False,
        "device": args.device,
        "dtype": args.dtype,
        "prompt": args.prompt,
        "offline": bool(args.offline or args.local_files_only),
        "local_files_only": args.local_files_only,
        "lingbot_code": args.lingbot_code,
        "paths": path_status(paths),
        "steps": {},
    }
    mark("probe_start", device=args.device, dtype=args.dtype)
    mark("path_status", **status["paths"])

    try:
        mark("import_transformers_start")
        with step_timeout("import_transformers", args.timeout):
            import transformers

        status["transformers_version"] = transformers.__version__
        mark("import_transformers_done", version=transformers.__version__)

        mark("tokenizer_load_start", path=paths["tokenizer_root"])
        start = time.time()
        with step_timeout("tokenizer_load", args.timeout):
            tokenizer = load_tokenizer(paths["tokenizer_root"], local_files_only=args.local_files_only)
        status["steps"]["tokenizer"] = {"ok": True, "elapsed_sec": round(time.time() - start, 3), "class": tokenizer.__class__.__name__}
        mark("tokenizer_load_done", elapsed_sec=status["steps"]["tokenizer"]["elapsed_sec"], cls=tokenizer.__class__.__name__)

        mark("import_torch_start")
        with step_timeout("import_torch", args.timeout):
            import torch

        mark("import_torch_done", torch_version=torch.__version__, cuda_available=bool(torch.cuda.is_available()))
        if args.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("device=cuda requested but torch.cuda.is_available() is false")

        mark("t5_model_load_start", checkpoint=paths["t5_checkpoint"], tokenizer=paths["tokenizer_root"])
        start = time.time()
        with step_timeout("t5_model_load", args.timeout):
            model = load_wan_t5(
                lingbot_code=args.lingbot_code,
                checkpoint_path=paths["t5_checkpoint"],
                tokenizer_path=paths["tokenizer_root"],
                device=args.device,
                dtype_name=args.dtype,
            )
        status["steps"]["t5_model"] = {"ok": True, "elapsed_sec": round(time.time() - start, 3), "class": model.__class__.__name__}
        mark("t5_model_load_done", elapsed_sec=status["steps"]["t5_model"]["elapsed_sec"], cls=model.__class__.__name__)

        mark("prompt_encode_start")
        start = time.time()
        with step_timeout("prompt_encode", args.timeout):
            embedding = encode_prompt(model, args.prompt, args.device)
        status["steps"]["prompt_encode"] = {"ok": True, "elapsed_sec": round(time.time() - start, 3), "shape": shape_summary(embedding)}
        mark("prompt_encode_done", elapsed_sec=status["steps"]["prompt_encode"]["elapsed_sec"], shape=status["steps"]["prompt_encode"]["shape"])

        if args.save_embedding:
            import torch

            out = Path(args.save_embedding)
            out.parent.mkdir(parents=True, exist_ok=True)
            torch.save({"prompt": args.prompt, "embedding": embedding, "shape": shape_summary(embedding)}, out)
            status["saved_embedding"] = str(out)
            mark("embedding_saved", path=str(out))

        status["ok"] = True
        mark("probe_done", ok=True)
        rc = 0
    except BaseException as exc:
        status["ok"] = False
        status["error"] = repr(exc)
        status["traceback"] = traceback.format_exc()
        mark("probe_failed", error=repr(exc))
        rc = 124 if isinstance(exc, StepTimeout) else 1

    if args.out:
        write_json(status, args.out)
    else:
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
