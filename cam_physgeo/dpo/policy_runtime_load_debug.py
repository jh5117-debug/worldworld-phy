
from __future__ import annotations

import argparse
import importlib
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
                kb = float(line.split()[1])
                return kb / (1024.0 * 1024.0)
    except Exception:
        return 0.0
    return 0.0


def cuda_stats() -> dict[str, float]:
    torch_mod = sys.modules.get("torch")
    if torch_mod is None:
        return {"allocated_gb": 0.0, "reserved_gb": 0.0, "max_allocated_gb": 0.0, "max_reserved_gb": 0.0}
    try:
        if not torch_mod.cuda.is_available():
            return {"allocated_gb": 0.0, "reserved_gb": 0.0, "max_allocated_gb": 0.0, "max_reserved_gb": 0.0}
        return {
            "allocated_gb": torch_mod.cuda.memory_allocated() / (1024**3),
            "reserved_gb": torch_mod.cuda.memory_reserved() / (1024**3),
            "max_allocated_gb": torch_mod.cuda.max_memory_allocated() / (1024**3),
            "max_reserved_gb": torch_mod.cuda.max_memory_reserved() / (1024**3),
        }
    except Exception:
        return {"allocated_gb": 0.0, "reserved_gb": 0.0, "max_allocated_gb": 0.0, "max_reserved_gb": 0.0}


class StageLogger:
    def __init__(self, output: str | Path, *, heartbeat_seconds: float, stage_timeout_seconds: float) -> None:
        self.output = Path(output)
        self.heartbeat_seconds = float(heartbeat_seconds)
        self.stage_timeout_seconds = float(stage_timeout_seconds)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        if self.output.exists():
            self.output.unlink()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self.current_stage = ""
        self.stage_start_time = 0.0
        self.timeout_written: set[str] = set()
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()

    def write(self, *, stage: str, event: str, status: str = "", error_reason: str = "", notes: str = "", elapsed_seconds: float | None = None) -> None:
        row = {
            "timestamp": time.time(),
            "stage": stage,
            "event": event,
            "elapsed_seconds": float(elapsed_seconds or 0.0),
            **cuda_stats(),
            "cpu_rss_gb": cpu_rss_gb(),
            "status": status,
            "error_reason": error_reason,
            "notes": notes,
        }
        with self._lock:
            with self.output.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, sort_keys=True) + "\n")
                f.flush()

    def start_stage(self, name: str, notes: str = "") -> float:
        start = time.time()
        with self._lock:
            self.current_stage = name
            self.stage_start_time = start
            self.timeout_written.discard(name)
        self.write(stage=name, event="stage_start", status="START", notes=notes, elapsed_seconds=0.0)
        return start

    def finish_stage(self, name: str, event: str, status: str, *, start: float, error_reason: str = "", notes: str = "") -> None:
        elapsed = time.time() - start
        self.write(stage=name, event=event, status=status, error_reason=error_reason, notes=notes, elapsed_seconds=elapsed)
        with self._lock:
            self.current_stage = ""
            self.stage_start_time = 0.0

    def _heartbeat_loop(self) -> None:
        while not self._stop.wait(self.heartbeat_seconds):
            with self._lock:
                stage = self.current_stage
                start = self.stage_start_time
            if not stage or start <= 0:
                continue
            elapsed = time.time() - start
            self.write(stage=stage, event="heartbeat", status="RUNNING", elapsed_seconds=elapsed)
            if elapsed > self.stage_timeout_seconds and stage not in self.timeout_written:
                self.timeout_written.add(stage)
                self.write(stage=stage, event="stage_timeout", status="TIMEOUT_RUNNING", elapsed_seconds=elapsed, notes="stage exceeded timeout while still running")

    def close(self) -> None:
        self._stop.set()
        self.thread.join(timeout=2)


def _timeout_handler(signum: int, frame: Any) -> None:
    raise StageTimeout("stage exceeded timeout")


def run_stage(logger: StageLogger, name: str, func: Callable[[], Any], *, notes: str = "") -> Any:
    start = logger.start_stage(name, notes=notes)
    old_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, logger.stage_timeout_seconds)
    try:
        result = func()
    except StageTimeout as exc:
        logger.finish_stage(name, "stage_timeout", "TIMEOUT", start=start, error_reason=repr(exc))
        raise
    except Exception as exc:  # noqa: BLE001
        logger.finish_stage(name, "stage_error", "FAILED", start=start, error_reason=repr(exc))
        raise
    else:
        logger.finish_stage(name, "stage_done", "PASS", start=start)
        return result
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old_handler)


def _load_yaml(path: str | Path) -> dict[str, Any]:
    import yaml

    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise TypeError(f"expected YAML mapping in {path}")
    return dict(data)


def _module_file(obj: Any) -> str:
    try:
        return str(Path(inspect.getsourcefile(obj) or "").resolve())
    except Exception:
        return "unknown"


def _bounded_sizes(paths: list[Path], *, max_files: int = 80) -> tuple[int, float, list[str]]:
    total = 0
    size = 0.0
    examples: list[str] = []
    for path in paths[:max_files]:
        if path.exists() and path.is_file():
            total += 1
            mb = path.stat().st_size / (1024.0 * 1024.0)
            size += mb
            if len(examples) < 12:
                examples.append(f"{path}:{mb:.1f}MB")
    return total, size, examples


def _write_summary(output: Path, status: str, blocked_stage: str, stages_done: list[str], notes: str = "") -> None:
    output.with_name("policy_runtime_load_debug_summary.md").write_text(
        "Current Status:\n" + status + "\n\n"
        "# v8f Policy Runtime Load Debug Summary\n\n"
        f"- Status: `{status}`\n"
        f"- Blocked stage: `{blocked_stage}`\n"
        f"- Stages done: {', '.join(stages_done) if stages_done else 'none'}\n"
        f"- JSONL: `{output}`\n"
        f"- Notes: {notes}\n",
        encoding="utf-8",
    )


def _write_blackbox(output: Path, stage: str, source_path: str, notes: str) -> None:
    output.with_name("blackbox_loader_split.md").write_text(
        "Current Status:\nBLACKBOX_STAGE_IDENTIFIED\n\n"
        "# v8f Black-Box Loader Split Note\n\n"
        f"- Blocked stage: `{stage}`\n"
        f"- Source path: `{source_path}`\n"
        f"- Notes: {notes}\n\n"
        "No DPO training was started. The next split should instrument the identified loader internals if source ownership allows it.\n",
        encoding="utf-8",
    )


def run_debug(args: argparse.Namespace) -> dict[str, Any]:
    output = Path(args.output)
    logger = StageLogger(output, heartbeat_seconds=args.heartbeat_seconds, stage_timeout_seconds=args.stage_timeout_seconds)
    state: dict[str, Any] = {}
    stages_done: list[str] = []
    blocked_stage = ""
    status = "POLICY_RUNTIME_LOAD_FAILED"
    notes = ""
    try:
        run_stage(logger, "0_initial", lambda: None, notes=f"pid={os.getpid()} cuda_visible={os.environ.get('CUDA_VISIBLE_DEVICES','')} cwd={Path.cwd()}")
        stages_done.append("0_initial")

        def import_basic() -> None:
            for name in ("json", "yaml", "numpy"):
                importlib.import_module(name)
        run_stage(logger, "1_import_basic_python", import_basic)
        stages_done.append("1_import_basic_python")

        def import_torch() -> None:
            torch = importlib.import_module("torch")
            state["torch"] = torch
            if torch.cuda.is_available():
                torch.cuda.set_device(int(args.gpu))
                torch.cuda.reset_peak_memory_stats()
        run_stage(logger, "2_import_torch", import_torch)
        stages_done.append("2_import_torch")

        def import_hf() -> None:
            for name in ("diffusers", "transformers", "peft"):
                mod = importlib.import_module(name)
                state[f"{name}_version"] = getattr(mod, "__version__", "unknown")
        run_stage(logger, "3_import_diffusers_transformers_peft", import_hf)
        stages_done.append("3_import_diffusers_transformers_peft")

        def import_lingbot() -> None:
            repo = Path(args.repo_root).resolve()
            src = repo / "src"
            if str(src) not in sys.path:
                sys.path.insert(0, str(src))
            energy = importlib.import_module("cam_physgeo.dpo.lingbot_fast_energy")
            energy._ensure_src_path()
            stage1 = importlib.import_module("physical_consistency.trainers.stage1_components")
            state.update({"energy": energy, "stage1": stage1, "LingBotStage1Helper": stage1.LingBotStage1Helper, "build_stage1_args": energy.build_stage1_args})
        run_stage(logger, "4_import_lingbot_modules", import_lingbot)
        stages_done.append("4_import_lingbot_modules")

        def resolve_repo() -> None:
            repo = Path(args.repo_root).resolve()
            if not (repo / "cam_physgeo").exists():
                raise FileNotFoundError(f"bad repo_root={repo}")
            state["repo"] = repo
        run_stage(logger, "5_resolve_repo_paths", resolve_repo)
        stages_done.append("5_resolve_repo_paths")

        def resolve_cfg() -> None:
            cfg_path = Path(args.config)
            if not cfg_path.is_absolute():
                cfg_path = state["repo"] / cfg_path
            if not cfg_path.exists():
                raise FileNotFoundError(cfg_path)
            state["config_path"] = cfg_path
        run_stage(logger, "6_resolve_config_path", resolve_cfg)
        stages_done.append("6_resolve_config_path")

        def read_config() -> None:
            cfg = _load_yaml(state["config_path"])
            cfg.update({"num_frames": int(args.used_window_frames), "height": int(args.height), "width": int(args.width), "dpo_runtime_device": "cpu", "dpo_skip_runtime_components_on_load": True, "gradient_checkpointing": True})
            state["cfg"] = cfg
            state["stage_args"] = state["build_stage1_args"](cfg)
        run_stage(logger, "7_read_config", read_config)
        stages_done.append("7_read_config")

        def resolve_weights() -> None:
            stage_args = state["stage_args"]
            shared = Path(stage_args.shared_assets_dir).resolve()
            fast = Path(stage_args.fast_checkpoint_dir).resolve()
            if not shared.exists():
                raise FileNotFoundError(shared)
            if not fast.exists():
                raise FileNotFoundError(fast)
            state.update({"shared_root": shared, "fast_root": fast, "vae_path": shared / "Wan2.1_VAE.pth", "t5_path": shared / "models_t5_umt5-xxl-enc-bf16.pth", "tokenizer_path": shared / "google" / "umt5-xxl", "checkpoint_root": str(shared), "fast_subfolder": str(fast.relative_to(shared))})
        run_stage(logger, "8_resolve_model_weight_paths", resolve_weights)
        stages_done.append("8_resolve_model_weight_paths")

        def check_sizes() -> None:
            fast = state["fast_root"]
            files = [state["vae_path"], state["t5_path"]]
            for pattern in ("*.json", "*.bin", "*.safetensors", "*.pt", "*.pth"):
                files.extend(sorted(fast.glob(pattern)))
            count, mb, examples = _bounded_sizes(files)
            logger.write(stage="9_check_weight_file_sizes", event="file_size_summary", status="INFO", notes=f"files={count} total_mb={mb:.1f} examples={examples}")
            if not state["vae_path"].exists():
                raise FileNotFoundError(state["vae_path"])
            if not state["t5_path"].exists():
                raise FileNotFoundError(state["t5_path"])
        run_stage(logger, "9_check_weight_file_sizes", check_sizes)
        stages_done.append("9_check_weight_file_sizes")

        def load_tokenizer() -> None:
            transformers = importlib.import_module("transformers")
            state["tokenizer"] = transformers.AutoTokenizer.from_pretrained(str(state["tokenizer_path"]), local_files_only=True)
        run_stage(logger, "10_load_tokenizer_or_text_runtime_cpu", load_tokenizer, notes=str(state.get("tokenizer_path", "")))
        stages_done.append("10_load_tokenizer_or_text_runtime_cpu")

        def ensure_helper() -> Any:
            helper = state.get("helper")
            if helper is None:
                helper = state["LingBotStage1Helper"](state["stage_args"])
                helper.bootstrap_imports()
                state["helper"] = helper
            return helper

        def load_t5() -> None:
            torch = state["torch"]
            helper = ensure_helper()
            state["t5"] = helper.T5EncoderModel(text_len=512, dtype=torch.bfloat16, device=torch.device("cpu"), checkpoint_path=str(state["t5_path"]), tokenizer_path=str(state["tokenizer_path"]))
        run_stage(logger, "11_load_t5_or_text_encoder_cpu", load_t5)
        stages_done.append("11_load_t5_or_text_encoder_cpu")

        def load_vae() -> None:
            torch = state["torch"]
            helper = ensure_helper()
            state["vae"] = helper.Wan2_1_VAE(vae_pth=str(state["vae_path"]), device=torch.device("cpu"))
        run_stage(logger, "12_load_vae_cpu", load_vae)
        stages_done.append("12_load_vae_cpu")

        def policy_config() -> None:
            torch = state["torch"]
            stage1 = state["stage1"]
            stage1.configure_stage1_precision_env(str(state["cfg"].get("student_precision_profile", "mixed_safe")), str(state["cfg"].get("student_low_precision_dtype", "bf16")))
            state["model_dtype"] = torch.float32 if stage1._stage1_force_fp32() else stage1.resolve_stage1_low_precision_dtype()
            ensure_helper()
        run_stage(logger, "13_load_policy_config_cpu", policy_config)
        stages_done.append("13_load_policy_config_cpu")

        def construct_policy() -> None:
            helper = ensure_helper()
            state["model"] = helper.WanModelFast.from_pretrained(state["checkpoint_root"], subfolder=state["fast_subfolder"], torch_dtype=state["model_dtype"], low_cpu_mem_usage=False, control_type="cam")
        run_stage(logger, "14_construct_policy_model_cpu", construct_policy, notes="WanModelFast.from_pretrained includes checkpoint/shard loading")
        stages_done.append("14_construct_policy_model_cpu")

        def verify_weights() -> None:
            total = sum(p.numel() for p in state["model"].parameters())
            logger.write(stage="15_load_policy_weights_cpu", event="param_summary", status="INFO", notes=f"total_params={total}")
        run_stage(logger, "15_load_policy_weights_cpu", verify_weights)
        stages_done.append("15_load_policy_weights_cpu")

        def apply_lora() -> None:
            stage1 = state["stage1"]
            model = state["model"]
            args_ns = state["stage_args"]
            if getattr(args_ns, "student_memory_efficient_modulation", True):
                stage1.apply_memory_efficient_wan_block_patch(model, state["fast_subfolder"], ffn_chunk_size=getattr(args_ns, "student_ffn_chunk_size", None), norm_chunk_size=getattr(args_ns, "student_norm_chunk_size", None))
            if getattr(args_ns, "student_tuning_mode", "full") == "lora":
                stage1.apply_lora_to_wan_model(model, model_name=state["fast_subfolder"], rank=getattr(args_ns, "student_lora_rank", 16), alpha=getattr(args_ns, "student_lora_alpha", 16), dropout=getattr(args_ns, "student_lora_dropout", 0.0), block_start=getattr(args_ns, "student_lora_block_start", 0), block_end=getattr(args_ns, "student_lora_block_end", None), target_groups=getattr(args_ns, "student_lora_target_groups", None), required_groups=getattr(args_ns, "student_lora_required_groups", None), include_patterns=getattr(args_ns, "student_lora_include_patterns", None), exclude_patterns=getattr(args_ns, "student_lora_exclude_patterns", None), lora_chunk_size=getattr(args_ns, "student_lora_chunk_size", None), merge_mode=getattr(args_ns, "student_lora_merge_mode", "inplace"))
        run_stage(logger, "16_load_lora_adapter_cpu_if_needed", apply_lora)
        stages_done.append("16_load_lora_adapter_cpu_if_needed")

        def grad_ckpt() -> None:
            stage1 = state["stage1"]
            if hasattr(stage1, "apply_gradient_checkpointing"):
                stage1.apply_gradient_checkpointing(state["model"], model_name="v8f_policy_runtime_debug", use_reentrant=False, memory_efficient_mode=str(state["cfg"].get("student_memory_efficient_checkpoint_mode", "full")))
        run_stage(logger, "17_enable_gradient_checkpointing_if_available", grad_ckpt)
        stages_done.append("17_enable_gradient_checkpointing_if_available")

        run_stage(logger, "18_configure_sdpa_or_xformers", lambda: logger.write(stage="18_configure_sdpa_or_xformers", event="sdpa_note", status="INFO", notes="SDPA/xformers patches are applied during helper.bootstrap_imports when available"))
        stages_done.append("18_configure_sdpa_or_xformers")

        def move_gpu() -> None:
            torch = state["torch"]
            device = torch.device(f"cuda:{int(args.gpu)}" if torch.cuda.is_available() else "cpu")
            if device.type == "cuda":
                torch.cuda.set_device(int(args.gpu))
            state["model"].to(device)
            state["device"] = device
        run_stage(logger, "19_move_policy_to_gpu", move_gpu)
        stages_done.append("19_move_policy_to_gpu")

        run_stage(logger, "20_cast_policy_dtype", lambda: logger.write(stage="20_cast_policy_dtype", event="dtype_note", status="INFO", notes=f"model_dtype={state.get('model_dtype')} from_pretrained already applied dtype"))
        stages_done.append("20_cast_policy_dtype")

        def freeze_lora() -> None:
            model = state["model"]
            trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
            total = sum(p.numel() for p in model.parameters())
            logger.write(stage="21_freeze_base_set_lora_trainable", event="trainable_summary", status="INFO", notes=f"trainable={trainable} total={total}")
            if trainable <= 0:
                raise RuntimeError("no trainable LoRA parameters")
        run_stage(logger, "21_freeze_base_set_lora_trainable", freeze_lora)
        stages_done.append("21_freeze_base_set_lora_trainable")

        run_stage(logger, "22_policy_runtime_ready", lambda: None)
        stages_done.append("22_policy_runtime_ready")
        run_stage(logger, "23_empty_cache_final", lambda: state["torch"].cuda.empty_cache() if state.get("torch") is not None and state["torch"].cuda.is_available() else None)
        stages_done.append("23_empty_cache_final")
        status = "POLICY_RUNTIME_LOAD_PASS"
    except Exception as exc:  # noqa: BLE001
        blocked_stage = logger.current_stage or (stages_done[-1] if stages_done else "unknown")
        status = f"POLICY_RUNTIME_LOAD_BLOCKED_{blocked_stage.upper().replace('-', '_')}"
        notes = repr(exc)
        logger.write(stage=blocked_stage, event="final_error", status=status, error_reason=repr(exc))
        if blocked_stage == "14_construct_policy_model_cpu":
            source = "unknown"
            try:
                source = _module_file(state["helper"].WanModelFast.from_pretrained)
            except Exception:
                pass
            _write_blackbox(output, blocked_stage, source, "WanModelFast.from_pretrained is inherited/black-box for this run and combines model construction with checkpoint/shard loading. Further split requires instrumenting the LingBot/diffusers loader internals, not DPO training code.")
    finally:
        logger.close()
        _write_summary(output, status, blocked_stage, stages_done, notes=notes)
    result = {"status": status, "blocked_stage": blocked_stage, "stages_done": stages_done, "output": str(output)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Fine-grained policy runtime load debug for v8f.")
    parser.add_argument("--pair_manifest", required=True)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--output", required=True)
    parser.add_argument("--heartbeat_seconds", type=float, default=15)
    parser.add_argument("--stage_timeout_seconds", type=float, default=180)
    parser.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    parser.add_argument("--repo_root", default=".")
    parser.add_argument("--used_window_frames", type=int, default=49)
    parser.add_argument("--prefix_len", type=int, default=5)
    parser.add_argument("--prediction_start_frame", type=int, default=5)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    args = parser.parse_args(argv)
    run_debug(args)


if __name__ == "__main__":
    main()
