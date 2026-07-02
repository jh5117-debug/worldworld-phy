
from __future__ import annotations

import argparse
import csv
import gc
import inspect
import json
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

class StageTimeout(TimeoutError):
    pass

def cpu_rss_gb() -> float:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return float(line.split()[1]) / (1024.0 * 1024.0)
    except Exception:
        return 0.0
    return 0.0

def cuda_stats() -> dict[str, float]:
    torch_mod = sys.modules.get("torch")
    if torch_mod is None:
        return {"gpu_allocated_gb": 0.0, "gpu_reserved_gb": 0.0, "gpu_max_allocated_gb": 0.0, "gpu_max_reserved_gb": 0.0}
    try:
        if not torch_mod.cuda.is_available():
            return {"gpu_allocated_gb": 0.0, "gpu_reserved_gb": 0.0, "gpu_max_allocated_gb": 0.0, "gpu_max_reserved_gb": 0.0}
        return {
            "gpu_allocated_gb": torch_mod.cuda.memory_allocated() / (1024**3),
            "gpu_reserved_gb": torch_mod.cuda.memory_reserved() / (1024**3),
            "gpu_max_allocated_gb": torch_mod.cuda.max_memory_allocated() / (1024**3),
            "gpu_max_reserved_gb": torch_mod.cuda.max_memory_reserved() / (1024**3),
        }
    except Exception:
        return {"gpu_allocated_gb": 0.0, "gpu_reserved_gb": 0.0, "gpu_max_allocated_gb": 0.0, "gpu_max_reserved_gb": 0.0}

class JsonlLogger:
    def __init__(self, output: str | Path, heartbeat_seconds: float = 15.0, stage_timeout_seconds: float = 180.0) -> None:
        self.output = Path(output); self.output.parent.mkdir(parents=True, exist_ok=True)
        if self.output.exists(): self.output.unlink()
        self.heartbeat_seconds = float(heartbeat_seconds); self.stage_timeout_seconds = float(stage_timeout_seconds)
        self._lock = threading.Lock(); self._stop = threading.Event(); self.current_stage = ""; self.last_stage = ""; self.stage_start_time = 0.0; self.timeout_written: set[str] = set()
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True); self.thread.start()
    def write(self, stage: str, event: str, *, status: str = "", error_reason: str = "", notes: str = "", elapsed_seconds: float = 0.0, **extra: Any) -> None:
        row = {"timestamp": time.time(), "stage": stage, "event": event, "elapsed_seconds": float(elapsed_seconds), "cpu_rss_gb": cpu_rss_gb(), **cuda_stats(), "status": status, "error_reason": error_reason, "notes": notes, **extra}
        with self._lock:
            with self.output.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, sort_keys=True) + "\n"); f.flush()
    def start_stage(self, stage: str, notes: str = "") -> float:
        start = time.time()
        with self._lock:
            self.current_stage = stage; self.last_stage = stage; self.stage_start_time = start; self.timeout_written.discard(stage)
        self.write(stage, "stage_start", status="START", notes=notes); return start
    def finish_stage(self, stage: str, event: str, status: str, start: float, error_reason: str = "", notes: str = "", **extra: Any) -> None:
        self.write(stage, event, status=status, error_reason=error_reason, notes=notes, elapsed_seconds=time.time() - start, **extra)
        with self._lock:
            self.current_stage = ""; self.stage_start_time = 0.0
    def _heartbeat_loop(self) -> None:
        while not self._stop.wait(self.heartbeat_seconds):
            with self._lock:
                stage = self.current_stage; start = self.stage_start_time
            if not stage or start <= 0: continue
            elapsed = time.time() - start; self.write(stage, "heartbeat", status="RUNNING", elapsed_seconds=elapsed)
            if elapsed > self.stage_timeout_seconds and stage not in self.timeout_written:
                self.timeout_written.add(stage); self.write(stage, "stage_timeout", status="TIMEOUT_RUNNING", elapsed_seconds=elapsed, notes="stage exceeded timeout while still running")
    def close(self) -> None:
        self._stop.set(); self.thread.join(timeout=2)

def _timeout_handler(signum: int, frame: Any) -> None:
    raise StageTimeout("stage exceeded timeout")

def run_stage(logger: JsonlLogger, stage: str, func: Callable[[], Any], notes: str = "") -> Any:
    start = logger.start_stage(stage, notes=notes); old = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _timeout_handler); signal.setitimer(signal.ITIMER_REAL, logger.stage_timeout_seconds)
    try:
        result = func()
    except StageTimeout as exc:
        logger.finish_stage(stage, "stage_timeout", "TIMEOUT", start, error_reason=repr(exc)); raise
    except Exception as exc:
        logger.finish_stage(stage, "stage_error", "FAILED", start, error_reason=repr(exc)); raise
    else:
        logger.finish_stage(stage, "stage_done", "PASS", start); return result
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0); signal.signal(signal.SIGALRM, old)

def _repo_root(repo_root: str | Path) -> Path:
    root = Path(repo_root).resolve()
    if not (root / "cam_physgeo").exists(): raise FileNotFoundError(f"bad repo root: {root}")
    return root

def _ensure_paths(repo_root: str | Path) -> None:
    root = _repo_root(repo_root); src = root / "src"
    if str(root) not in sys.path: sys.path.insert(0, str(root))
    if str(src) not in sys.path: sys.path.insert(0, str(src))

def _load_yaml(path: str | Path) -> dict[str, Any]:
    import yaml
    with Path(path).open("r", encoding="utf-8") as f: data = yaml.safe_load(f) or {}
    if not isinstance(data, dict): raise TypeError(path)
    return dict(data)

def _resolve_config(args: argparse.Namespace) -> dict[str, Any]:
    _ensure_paths(args.repo_root)
    from cam_physgeo.dpo.lingbot_fast_energy import build_stage1_args
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute(): cfg_path = _repo_root(args.repo_root) / cfg_path
    cfg = _load_yaml(cfg_path); cfg.setdefault("num_frames", 49); cfg.setdefault("height", 480); cfg.setdefault("width", 832); cfg["dpo_skip_runtime_components_on_load"] = True
    stage_args = build_stage1_args(cfg); shared = Path(stage_args.shared_assets_dir).resolve(); fast = Path(stage_args.fast_checkpoint_dir).resolve()
    return {"cfg_path": str(cfg_path), "cfg": cfg, "stage_args": stage_args, "shared_root": shared, "fast_root": fast, "subfolder": str(fast.relative_to(shared))}

def _import_wan(args: argparse.Namespace):
    _ensure_paths(args.repo_root); info = _resolve_config(args)
    from physical_consistency.trainers.stage1_components import LingBotStage1Helper
    helper = LingBotStage1Helper(info["stage_args"]); helper.bootstrap_imports(); return info, helper, helper.WanModelFast

def _source_path(obj: Any) -> str:
    try: return str(Path(inspect.getsourcefile(obj) or "").resolve())
    except Exception: return "unknown"

def locate_source(args: argparse.Namespace) -> None:
    info, helper, cls = _import_wan(args); fp = getattr(cls, "from_pretrained")
    payload = {"wan_model_fast_module": getattr(cls, "__module__", ""), "class_file_path": _source_path(cls), "from_pretrained_source_file": _source_path(fp), "from_pretrained_qualname": getattr(fp, "__qualname__", ""), "mro": [f"{c.__module__}.{c.__qualname__}" for c in cls.mro()], "signature": str(inspect.signature(fp)), "inherited_from_diffusers": any("diffusers" in c.__module__ for c in cls.mro()), "call_stack": ["LingBotFastDpoEnergy.__init__", "LingBotStage1Helper.load_model", "WanModelFast.from_pretrained"], "checkpoint_root": str(info["shared_root"]), "fast_root": str(info["fast_root"]), "subfolder": info["subfolder"], "adapter_path": None, "torch_dtype_arg": "bf16 via resolve_stage1_low_precision_dtype", "local_files_only_arg": "not passed in current helper", "low_cpu_mem_usage_arg": False, "device_map_arg": None, "use_safetensors_arg": "implicit", "config_path": info["cfg_path"]}
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    out.with_suffix(".md").write_text("Current Status:\nSOURCE_DISCOVERY_PASS\n\n# WanModelFast Source Discovery\n\n" + f"- Class file: `{payload['class_file_path']}`\n- from_pretrained source: `{payload['from_pretrained_source_file']}`\n- Signature: `{payload['signature']}`\n- Checkpoint root: `{payload['checkpoint_root']}`\n- Subfolder: `{payload['subfolder']}`\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))

def _checkpoint_files(info: dict[str, Any]) -> list[Path]:
    fast = info["fast_root"]; files: list[Path] = []
    for name in ["config.json", "model_index.json", "diffusion_pytorch_model.safetensors.index.json", "pytorch_model.bin.index.json"]:
        p = fast / name
        if p.exists(): files.append(p)
    for pattern in ["*.safetensors", "*.bin", "*.pt", "*.pth"]: files.extend(sorted(fast.glob(pattern)))
    return files

def checkpoint_inventory(args: argparse.Namespace) -> None:
    info = _resolve_config(args); files = _checkpoint_files(info); index_json = info["fast_root"] / "diffusion_pytorch_model.safetensors.index.json"; referenced: set[str] = set()
    if index_json.exists():
        try:
            data = json.loads(index_json.read_text()); referenced = {str(info["fast_root"] / v) for v in (data.get("weight_map") or {}).values()}
        except Exception: referenced = set()
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); fields = ["path", "kind", "exists", "is_symlink", "target", "size_gb", "mtime", "on_nvme03", "on_nvme04", "referenced_by_index", "zero_size"]
    rows = []
    for p in files:
        kind = "config" if p.suffix == ".json" else "shard"; st = p.stat() if p.exists() else None
        rows.append({"path": str(p), "kind": kind, "exists": p.exists(), "is_symlink": p.is_symlink(), "target": str(p.resolve()) if p.exists() else "", "size_gb": (st.st_size / (1024**3)) if st else 0.0, "mtime": st.st_mtime if st else 0.0, "on_nvme03": str(p).startswith("/home/nvme03"), "on_nvme04": str(p).startswith("/home/nvme04"), "referenced_by_index": str(p) in referenced or not referenced, "zero_size": (st.st_size == 0) if st else False})
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    shard_rows = [r for r in rows if r["kind"] == "shard"]; total = sum(float(r["size_gb"]) for r in shard_rows); largest = max((float(r["size_gb"]) for r in shard_rows), default=0.0)
    out.with_suffix(".md").write_text("Current Status:\nCHECKPOINT_INVENTORY_PASS\n\n# v8g Checkpoint Inventory\n\n" + f"- Fast root: `{info['fast_root']}`\n- File rows: {len(rows)}\n- Shard count: {len(shard_rows)}\n- Total shard size GB: {total:.2f}\n- Largest shard GB: {largest:.2f}\n- Index json exists: {index_json.exists()}\n", encoding="utf-8")
    print(out.with_suffix(".md").read_text())

def _shards(info: dict[str, Any]) -> list[Path]: return sorted(info["fast_root"].glob("*.safetensors"))
def _alarm(seconds: float):
    old = signal.getsignal(signal.SIGALRM); signal.signal(signal.SIGALRM, _timeout_handler); signal.setitimer(signal.ITIMER_REAL, seconds); return old

def shard_timing(args: argparse.Namespace) -> None:
    from safetensors import safe_open
    from safetensors.torch import load_file
    info = _resolve_config(args); shards = _shards(info)
    if args.max_shards != "all": shards = shards[: int(args.max_shards)]
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); fields = ["shard_path", "size_gb", "metadata_time_sec", "tensor_load_time_sec", "num_tensors", "total_tensor_gb", "cpu_rss_before_gb", "cpu_rss_after_gb", "status", "error_reason"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); f.flush()
        for shard in shards:
            row = {"shard_path": str(shard), "size_gb": shard.stat().st_size / (1024**3), "metadata_time_sec": 0.0, "tensor_load_time_sec": 0.0, "num_tensors": 0, "total_tensor_gb": 0.0, "cpu_rss_before_gb": cpu_rss_gb(), "cpu_rss_after_gb": 0.0, "status": "START", "error_reason": ""}; w.writerow(row); f.flush()
            old = _alarm(float(args.per_shard_timeout_seconds))
            try:
                t0 = time.time()
                with safe_open(str(shard), framework="pt", device="cpu") as sf:
                    keys = list(sf.keys()); row["num_tensors"] = len(keys); _ = sf.metadata()
                row["metadata_time_sec"] = time.time() - t0
                if not args.metadata_only:
                    t1 = time.time(); tensors = load_file(str(shard), device="cpu"); row["tensor_load_time_sec"] = time.time() - t1; row["total_tensor_gb"] = sum(t.numel() * t.element_size() for t in tensors.values()) / (1024**3); del tensors; gc.collect()
                row["status"] = "PASS"
            except Exception as exc:
                row["status"] = "TIMEOUT" if isinstance(exc, StageTimeout) else "FAILED"; row["error_reason"] = repr(exc)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0.0); signal.signal(signal.SIGALRM, old); row["cpu_rss_after_gb"] = cpu_rss_gb(); w.writerow(row); f.flush()
                if row["status"] != "PASS": break
    final = [r for r in csv.DictReader(out.open()) if r["status"] != "START"]; failed = [r for r in final if r["status"] != "PASS"]
    status = "SHARD_TIMING_PASS" if not failed and final else ("BLOCKED_SHARD_METADATA_OR_FS" if args.metadata_only else "BLOCKED_SHARD_TENSOR_LOAD")
    out.with_name("shard_timing_summary.md").write_text("Current Status:\n" + status + "\n\n# v8g Shard Timing Summary\n\n" + f"- Output: `{out}`\n- Metadata only: {args.metadata_only}\n- Rows completed: {len(final)}\n- Failed rows: {len(failed)}\n", encoding="utf-8")
    print(out.with_name("shard_timing_summary.md").read_text())

def construct_empty_model(args: argparse.Namespace) -> None:
    logger = JsonlLogger(args.output, args.heartbeat_seconds, args.stage_timeout_seconds); stages=[]; status="CONSTRUCT_EMPTY_MODEL_FAILED"; blocked=""; notes=""
    try:
        info={}
        run_stage(logger, "read_config", lambda: info.update(_resolve_config(args))); stages.append("read_config")
        run_stage(logger, "resolve_model_class", lambda: info.update({"cls": _import_wan(args)[2]})); stages.append("resolve_model_class")
        def construct():
            cls=info["cls"]; cfg=cls.load_config(str(info["shared_root"]), subfolder=info["subfolder"], local_files_only=True)
            try:
                from accelerate import init_empty_weights
                with init_empty_weights(): model=cls.from_config(cfg)
            except Exception: model=cls.from_config(cfg)
            info["model"]=model
        run_stage(logger, "construct_class_meta_or_empty", construct); stages.append("construct_class_meta_or_empty")
        run_stage(logger, "count_parameters_if_available", lambda: logger.write("count_parameters_if_available", "param_summary", status="INFO", num_parameters=sum(p.numel() for p in info["model"].parameters()))); stages.append("count_parameters_if_available")
        run_stage(logger, "final", lambda: None); stages.append("final"); status="CONSTRUCT_EMPTY_MODEL_PASS"
    except Exception as exc:
        blocked=logger.current_stage or logger.last_stage or (stages[-1] if stages else "unknown"); status="BLOCKED_MODEL_CLASS_CONSTRUCTION"; notes=repr(exc); logger.write(blocked, "final_error", status=status, error_reason=repr(exc))
    finally:
        logger.close(); Path(args.output).with_suffix(".md").write_text("Current Status:\n"+status+f"\n\n# v8g Empty Model Construction\n\n- Blocked stage: `{blocked}`\n- Stages done: {', '.join(stages)}\n- Notes: {notes}\n", encoding="utf-8")
    print(Path(args.output).with_suffix(".md").read_text())

def state_dict_load_split(args: argparse.Namespace) -> None:
    logger=JsonlLogger(args.output,args.heartbeat_seconds,args.stage_timeout_seconds); stages=[]; status="STATE_DICT_LOAD_SPLIT_NOT_COMPLETED"; blocked=""
    try:
        info={}; run_stage(logger,"load_config",lambda: info.update(_resolve_config(args))); stages.append("load_config")
        run_stage(logger,"load_shard_index",lambda: json.loads((info["fast_root"] / "diffusion_pytorch_model.safetensors.index.json").read_text())); stages.append("load_shard_index")
        from safetensors.torch import load_file
        for idx, shard in enumerate(_shards(info), start=1):
            def load_one(shard=shard, idx=idx):
                tensors=load_file(str(shard),device="cpu"); gb=sum(t.numel()*t.element_size() for t in tensors.values())/(1024**3); logger.write(f"load_shard_{idx}","tensor_summary",status="INFO",num_keys=len(tensors),tensor_gb=gb); del tensors; gc.collect()
            run_stage(logger,f"load_shard_{idx}",load_one); stages.append(f"load_shard_{idx}")
            if idx >= int(args.max_state_dict_shards): break
        run_stage(logger,"final",lambda: None); stages.append("final"); status="STATE_DICT_SHARD_LOAD_PREFIX_PASS"
    except Exception as exc:
        blocked=logger.current_stage or logger.last_stage or (stages[-1] if stages else "unknown"); status="BLOCKED_SHARD_LOAD"; logger.write(blocked,"final_error",status=status,error_reason=repr(exc))
    finally:
        logger.close(); Path(args.output).with_suffix(".md").write_text("Current Status:\n"+status+f"\n\n# v8g State Dict Load Split\n\n- Blocked stage: `{blocked}`\n- Stages done: {', '.join(stages)}\n", encoding="utf-8")
    print(Path(args.output).with_suffix(".md").read_text())

def real_from_pretrained_safe(args: argparse.Namespace) -> None:
    logger=JsonlLogger(args.output,args.heartbeat_seconds,args.stage_timeout_seconds); stages=[]; status="REAL_FROM_PRETRAINED_SAFE_FAILED"; blocked=""
    try:
        state={}
        def load():
            import torch
            info, helper, cls = _import_wan(args); dtype=torch.bfloat16 if args.torch_dtype=="bf16" else torch.float32
            model=cls.from_pretrained(str(info["shared_root"]), subfolder=info["subfolder"], torch_dtype=dtype, low_cpu_mem_usage=args.low_cpu_mem_usage, local_files_only=args.local_files_only, use_safetensors=args.use_safetensors, control_type="cam"); state["model"]=model
        run_stage(logger,"from_pretrained_safe_cpu",load); stages.append("from_pretrained_safe_cpu")
        if args.move_to_gpu:
            def move():
                import torch; torch.cuda.set_device(int(args.gpu)); state["model"].to(torch.device(f"cuda:{int(args.gpu)}"))
            run_stage(logger,"move_to_gpu",move); stages.append("move_to_gpu"); status="POLICY_FROM_PRETRAINED_SAFE_GPU_PASS"
        else: status="POLICY_FROM_PRETRAINED_SAFE_CPU_PASS"
    except Exception as exc:
        blocked=logger.current_stage or logger.last_stage or (stages[-1] if stages else "unknown"); status="REAL_FROM_PRETRAINED_SAFE_BLOCKED"; logger.write(blocked,"final_error",status=status,error_reason=repr(exc))
    finally:
        logger.close(); Path(args.output).with_suffix(".md").write_text("Current Status:\n"+status+f"\n\n- Blocked stage: `{blocked}`\n- Stages done: {', '.join(stages)}\n",encoding="utf-8")
    print(Path(args.output).with_suffix(".md").read_text())

def main(argv: list[str] | None = None) -> None:
    p=argparse.ArgumentParser(); p.add_argument("--mode",required=True,choices=["locate_source","checkpoint_inventory","shard_timing","construct_empty_model","state_dict_load_split","real_from_pretrained_safe"]); p.add_argument("--output",required=True); p.add_argument("--repo_root",default="."); p.add_argument("--config",default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml"); p.add_argument("--max_shards",default="all"); p.add_argument("--metadata_only",type=lambda x:str(x).lower() in {"1","true","yes"},default=True); p.add_argument("--per_shard_timeout_seconds",type=float,default=180); p.add_argument("--heartbeat_seconds",type=float,default=15); p.add_argument("--stage_timeout_seconds",type=float,default=180); p.add_argument("--max_state_dict_shards",type=int,default=3); p.add_argument("--low_cpu_mem_usage",type=lambda x:str(x).lower() in {"1","true","yes"},default=True); p.add_argument("--local_files_only",type=lambda x:str(x).lower() in {"1","true","yes"},default=True); p.add_argument("--use_safetensors",type=lambda x:str(x).lower() in {"1","true","yes"},default=True); p.add_argument("--torch_dtype",default="bf16"); p.add_argument("--gpu",type=int,default=0); p.add_argument("--move_to_gpu",type=lambda x:str(x).lower() in {"1","true","yes"},default=False)
    args=p.parse_args(argv)
    {"locate_source": locate_source, "checkpoint_inventory": checkpoint_inventory, "shard_timing": shard_timing, "construct_empty_model": construct_empty_model, "state_dict_load_split": state_dict_load_split, "real_from_pretrained_safe": real_from_pretrained_safe}[args.mode](args)
if __name__ == "__main__": main()
