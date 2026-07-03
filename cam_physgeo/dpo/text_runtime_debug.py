from __future__ import annotations

import argparse
import gc
import importlib
import inspect
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from cam_physgeo.dpo.policy_runtime_load_debug import StageLogger, _load_yaml, run_stage


def _ensure_repo_paths(repo_root: str | Path) -> Path:
    repo = Path(repo_root).resolve()
    src = repo / "src"
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    return repo


def _write_summary(output: Path, status: str, blocked_stage: str, notes: list[str]) -> None:
    summary = output.with_name("text_runtime_debug_summary.md")
    summary.write_text(
        "Current Status:\n" + status + "\n\n"
        "# v8i Text Runtime Debug Summary\n\n"
        f"- Status: `{status}`\n"
        f"- Blocked stage: `{blocked_stage or none}`\n"
        f"- JSONL: `{output}`\n"
        + "\n".join(f"- {note}" for note in notes)
        + "\n",
        encoding="utf-8",
    )


def _file_sha_note(path: Path) -> str:
    st = path.stat()
    return f"path={path} size_gb={st.st_size / (1024**3):.3f} mtime={st.st_mtime}"


def _count_params(model: Any) -> int:
    try:
        return int(sum(p.numel() for p in model.parameters()))
    except Exception:
        return -1


def run(args: argparse.Namespace) -> dict[str, Any]:
    output = Path(args.output)
    logger = StageLogger(output, heartbeat_seconds=args.heartbeat_seconds, stage_timeout_seconds=args.stage_timeout_seconds)
    state: dict[str, Any] = {}
    stages_done: list[str] = []
    notes: list[str] = []
    status = "TEXT_RUNTIME_DEBUG_FAILED"
    blocked_stage = ""
    try:
        cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        run_stage(logger, "0_initial", lambda: None, notes=f"pid={os.getpid()} cuda_visible={cuda_visible} cwd={Path.cwd()}")
        stages_done.append("0_initial")

        def import_basic() -> None:
            importlib.import_module("torch")
            importlib.import_module("yaml")
            importlib.import_module("numpy")
        run_stage(logger, "1_import_basic", import_basic)
        stages_done.append("1_import_basic")

        def read_config() -> None:
            repo = _ensure_repo_paths(args.repo_root)
            cfg_path = Path(args.config)
            if not cfg_path.is_absolute():
                cfg_path = repo / cfg_path
            cfg = _load_yaml(cfg_path)
            cfg.update({
                "num_frames": int(args.used_window_frames),
                "height": int(args.height),
                "width": int(args.width),
                "dpo_runtime_device": "cpu",
                "dpo_skip_runtime_components_on_load": True,
                "gradient_checkpointing": True,
            })
            state["repo"] = repo
            state["cfg"] = cfg
            state["cfg_path"] = cfg_path
        run_stage(logger, "2_read_config", read_config)
        stages_done.append("2_read_config")

        def build_args() -> None:
            energy = importlib.import_module("cam_physgeo.dpo.lingbot_fast_energy")
            energy._ensure_src_path()
            state["energy"] = energy
            state["stage_args"] = energy.build_stage1_args(state["cfg"])
        run_stage(logger, "3_build_stage1_args", build_args)
        stages_done.append("3_build_stage1_args")

        def resolve_paths() -> None:
            stage_args = state["stage_args"]
            shared = Path(getattr(stage_args, "shared_assets_dir", getattr(stage_args, "base_model_dir", ""))).resolve()
            t5_path = shared / "models_t5_umt5-xxl-enc-bf16.pth"
            tok_path = shared / "google" / "umt5-xxl"
            if not t5_path.exists():
                raise FileNotFoundError(t5_path)
            if not tok_path.exists():
                raise FileNotFoundError(tok_path)
            state.update({"shared": shared, "t5_path": t5_path, "tokenizer_path": tok_path})
            logger.write(stage="4_resolve_text_paths", event="paths", status="INFO", notes=json.dumps({"t5": str(t5_path), "tokenizer": str(tok_path)}, sort_keys=True))
        run_stage(logger, "4_resolve_text_paths", resolve_paths)
        stages_done.append("4_resolve_text_paths")

        def file_inventory() -> None:
            tok_files = [p for p in state["tokenizer_path"].glob("**/*") if p.is_file()]
            tok_size = sum(p.stat().st_size for p in tok_files) / (1024**2)
            logger.write(stage="5_text_file_inventory", event="inventory", status="INFO", notes=json.dumps({"t5": _file_sha_note(state["t5_path"]), "tokenizer_files": len(tok_files), "tokenizer_mb": round(tok_size, 3)}, sort_keys=True))
        run_stage(logger, "5_text_file_inventory", file_inventory)
        stages_done.append("5_text_file_inventory")

        def bootstrap_imports() -> None:
            stage1 = importlib.import_module("physical_consistency.trainers.stage1_components")
            helper = stage1.LingBotStage1Helper(state["stage_args"])
            helper.bootstrap_imports()
            state.update({"stage1": stage1, "helper": helper})
            logger.write(stage="6_bootstrap_wan_imports", event="source", status="INFO", notes=json.dumps({"T5EncoderModel": inspect.getsourcefile(helper.T5EncoderModel), "module": getattr(helper.T5EncoderModel, "__module__", "")}, sort_keys=True))
        run_stage(logger, "6_bootstrap_wan_imports", bootstrap_imports)
        stages_done.append("6_bootstrap_wan_imports")

        def import_tokenizer_class() -> None:
            mod = importlib.import_module("wan.modules.tokenizers")
            state["HuggingfaceTokenizer"] = mod.HuggingfaceTokenizer
            logger.write(stage="7_import_tokenizer_class", event="source", status="INFO", notes=str(inspect.getsourcefile(mod.HuggingfaceTokenizer)))
        run_stage(logger, "7_import_tokenizer_class", import_tokenizer_class)
        stages_done.append("7_import_tokenizer_class")

        def tokenizer_only() -> None:
            Tok = state["HuggingfaceTokenizer"]
            tok = Tok(name=str(state["tokenizer_path"]), seq_len=int(args.text_len), clean="whitespace")
            state["tokenizer"] = tok
        run_stage(logger, "8_init_huggingface_tokenizer", tokenizer_only)
        stages_done.append("8_init_huggingface_tokenizer")

        def import_t5_module() -> None:
            mod = importlib.import_module("wan.modules.t5")
            state["t5_module"] = mod
            if args.disable_random_init:
                def _no_init_weights(_module):
                    return None
                mod.init_weights = _no_init_weights
                logger.write(stage="9_import_t5_module", event="no_random_init_patch", status="INFO", notes="patched wan.modules.t5.init_weights to no-op for checkpoint-covered construction")
            if args.disable_default_param_init:
                torch = importlib.import_module("torch")
                nn = torch.nn
                def _noop_reset(self):
                    return None
                patches = []
                for cls_name in ("Linear", "Embedding", "LayerNorm"):
                    cls = getattr(nn, cls_name, None)
                    if cls is not None and hasattr(cls, "reset_parameters"):
                        patches.append(cls_name)
                        cls.reset_parameters = _noop_reset
                logger.write(stage="9_import_t5_module", event="default_param_init_patch", status="INFO", notes="patched reset_parameters for " + ",".join(patches))
            logger.write(stage="9_import_t5_module", event="source", status="INFO", notes=str(inspect.getsourcefile(mod)))
        run_stage(logger, "9_import_t5_module", import_t5_module)
        stages_done.append("9_import_t5_module")

        def construct_empty_encoder() -> None:
            torch = importlib.import_module("torch")
            mod = state["t5_module"]
            model = mod.umt5_xxl(encoder_only=True, return_tokenizer=False, dtype=torch.bfloat16, device="cpu").eval().requires_grad_(False)
            state["model"] = model
            logger.write(stage="10_construct_umt5_xxl_encoder_cpu", event="param_summary", status="INFO", notes=f"params={_count_params(model)}")
        run_stage(logger, "10_construct_umt5_xxl_encoder_cpu", construct_empty_encoder)
        stages_done.append("10_construct_umt5_xxl_encoder_cpu")

        def torch_load_checkpoint() -> None:
            torch = importlib.import_module("torch")
            state["state_dict"] = torch.load(state["t5_path"], map_location="cpu")
            num_keys = len(state["state_dict"])
            logger.write(stage="11_torch_load_t5_checkpoint_cpu", event="state_dict", status="INFO", notes=f"keys={num_keys}")
        run_stage(logger, "11_torch_load_t5_checkpoint_cpu", torch_load_checkpoint)
        stages_done.append("11_torch_load_t5_checkpoint_cpu")

        def load_state_dict() -> None:
            result = state["model"].load_state_dict(state["state_dict"])
            state["load_result"] = result
            logger.write(stage="12_load_state_dict_into_t5", event="load_result", status="INFO", notes=str(result))
            del state["state_dict"]
            gc.collect()
        run_stage(logger, "12_load_state_dict_into_t5", load_state_dict)
        stages_done.append("12_load_state_dict_into_t5")

        def full_constructor() -> None:
            if not args.run_full_constructor:
                logger.write(stage="13_full_T5EncoderModel_constructor", event="stage_skipped", status="SKIPPED", notes="run_full_constructor=false")
                return
            torch = importlib.import_module("torch")
            helper = state["helper"]
            t5 = helper.T5EncoderModel(text_len=int(args.text_len), dtype=torch.bfloat16, device=torch.device("cpu"), checkpoint_path=str(state["t5_path"]), tokenizer_path=str(state["tokenizer_path"]))
            state["full_t5"] = t5
        run_stage(logger, "13_full_T5EncoderModel_constructor", full_constructor)
        stages_done.append("13_full_T5EncoderModel_constructor")

        def prompt_encode() -> None:
            if not args.run_prompt_encode:
                logger.write(stage="14_prompt_encode_smoke", event="stage_skipped", status="SKIPPED", notes="run_prompt_encode=false")
                return
            torch = importlib.import_module("torch")
            prompt = args.prompt or "A short physical scene."
            if "full_t5" in state:
                context = state["full_t5"]([prompt], device=torch.device("cpu"))
            else:
                ids, mask = state["tokenizer"]([prompt], return_mask=True, add_special_tokens=True)
                with torch.no_grad():
                    context_tensor = state["model"](ids, mask)
                seq_lens = mask.gt(0).sum(dim=1).long()
                context = [u[:v] for u, v in zip(context_tensor, seq_lens)]
            logger.write(stage="14_prompt_encode_smoke", event="context", status="INFO", notes=json.dumps([list(t.shape) for t in context]))
        run_stage(logger, "14_prompt_encode_smoke", prompt_encode)
        stages_done.append("14_prompt_encode_smoke")

        status = "TEXT_RUNTIME_SPLIT_PASS"
    except Exception as exc:  # noqa: BLE001
        blocked_stage = logger.current_stage or getattr(logger, "last_stage", "") or (stages_done[-1] if stages_done else "unknown")
        status = f"TEXT_RUNTIME_BLOCKED_{blocked_stage.upper()}"
        notes.append(f"error={exc!r}")
        logger.write(stage=blocked_stage, event="final_error", status=status, error_reason=repr(exc))
    finally:
        logger.close()
        _write_summary(output, status, blocked_stage, notes)
    result = {"status": status, "blocked_stage": blocked_stage, "stages_done": stages_done, "output": str(output)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Split T5/text runtime initialization for v8i blocker resolution.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--repo_root", default=".")
    parser.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    parser.add_argument("--used_window_frames", type=int, default=49)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--text_len", type=int, default=512)
    parser.add_argument("--heartbeat_seconds", type=float, default=15.0)
    parser.add_argument("--stage_timeout_seconds", type=float, default=180.0)
    parser.add_argument("--disable_random_init", action="store_true", help="Patch wan.modules.t5.init_weights to no-op before constructing checkpoint-covered UMT5.")
    parser.add_argument("--disable_default_param_init", action="store_true", help="Patch torch nn reset_parameters to no-op before constructing checkpoint-covered UMT5.")
    parser.add_argument("--run_full_constructor", action="store_true")
    parser.add_argument("--run_prompt_encode", action="store_true")
    parser.add_argument("--prompt", default="")
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
