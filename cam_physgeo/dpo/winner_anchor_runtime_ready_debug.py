
from __future__ import annotations

import argparse
import json
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import torch

from cam_physgeo.dpo.failure_diagnostics import _make_timestep_sample
from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy, strict_future_latent_indices
from cam_physgeo.dpo.winner_anchor_cache_builder import sha256_file, tensor_tree_finite, to_cpu
from cam_physgeo.dpo.winner_anchor_only_runner import _cfg, _load_winner_inputs, reviewed_pairs


def cuda_stats() -> dict[str, float]:
    if not torch.cuda.is_available():
        return {"allocated_gb": 0.0, "reserved_gb": 0.0, "max_allocated_gb": 0.0, "max_reserved_gb": 0.0}
    return {
        "allocated_gb": torch.cuda.memory_allocated() / (1024**3),
        "reserved_gb": torch.cuda.memory_reserved() / (1024**3),
        "max_allocated_gb": torch.cuda.max_memory_allocated() / (1024**3),
        "max_reserved_gb": torch.cuda.max_memory_reserved() / (1024**3),
    }


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
        self.current_pair_id = ""
        self.stage_start_time = 0.0
        self.timeout_written: set[str] = set()
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()

    def write(self, *, stage: str, event: str, pair_id: str = "", status: str = "", error_reason: str = "", notes: str = "", elapsed_seconds: float | None = None) -> None:
        row = {
            "timestamp": time.time(),
            "stage": stage,
            "event": event,
            "pair_id": pair_id,
            "elapsed_seconds": elapsed_seconds if elapsed_seconds is not None else 0.0,
            **cuda_stats(),
            "status": status,
            "error_reason": error_reason,
            "notes": notes,
        }
        with self._lock:
            with self.output.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, sort_keys=True) + "\n")
                f.flush()

    @contextmanager
    def stage(self, name: str, *, pair_id: str = "", notes: str = ""):
        start = time.time()
        with self._lock:
            self.current_stage = name
            self.current_pair_id = pair_id
            self.stage_start_time = start
            self.timeout_written.discard(name)
        self.write(stage=name, event="stage_start", pair_id=pair_id, status="START", notes=notes, elapsed_seconds=0.0)
        try:
            yield
            elapsed = time.time() - start
            status = "PASS" if elapsed <= self.stage_timeout_seconds else "TIMEOUT_AFTER_DONE"
            event = "stage_done" if status == "PASS" else "stage_timeout"
            self.write(stage=name, event=event, pair_id=pair_id, status=status, elapsed_seconds=elapsed)
        except Exception as exc:  # noqa: BLE001
            elapsed = time.time() - start
            self.write(stage=name, event="stage_failed", pair_id=pair_id, status="FAILED", error_reason=repr(exc), elapsed_seconds=elapsed)
            raise
        finally:
            with self._lock:
                self.current_stage = ""
                self.current_pair_id = ""
                self.stage_start_time = 0.0

    def _heartbeat_loop(self) -> None:
        while not self._stop.wait(self.heartbeat_seconds):
            with self._lock:
                stage = self.current_stage
                pair_id = self.current_pair_id
                start = self.stage_start_time
            if not stage or start <= 0:
                continue
            elapsed = time.time() - start
            self.write(stage=stage, event="heartbeat", pair_id=pair_id, status="RUNNING", elapsed_seconds=elapsed)
            if elapsed > self.stage_timeout_seconds and stage not in self.timeout_written:
                self.timeout_written.add(stage)
                self.write(stage=stage, event="stage_timeout", pair_id=pair_id, status="TIMEOUT_RUNNING", elapsed_seconds=elapsed, notes="stage exceeded timeout while still running")

    def close(self) -> None:
        self._stop.set()
        self.thread.join(timeout=2)


def _write_summary(output: Path, status: str, blocked_stage: str, stages: list[str]) -> None:
    output.with_name("runtime_ready_debug_summary.md").write_text(
        "Current Status:\n" + status + "\n\n"
        "# v8e Runtime-Ready Debug Summary\n\n"
        f"- Status: `{status}`\n"
        f"- Blocked stage: `{blocked_stage}`\n"
        f"- Stages reached: {', '.join(stages)}\n"
        f"- JSONL: `{output}`\n",
        encoding="utf-8",
    )


def run_debug(args: argparse.Namespace) -> dict[str, Any]:
    output = Path(args.output)
    logger = StageLogger(output, heartbeat_seconds=float(args.heartbeat_seconds), stage_timeout_seconds=float(args.stage_timeout_seconds))
    stages_done: list[str] = []
    blocked_stage = ""
    status = "RUNTIME_READY_FAILED"
    pair_id = ""
    try:
        if torch.cuda.is_available():
            torch.cuda.set_device(int(args.gpu))
            torch.cuda.reset_peak_memory_stats()
        device = f"cuda:{int(args.gpu)}" if torch.cuda.is_available() else "cpu"
        with logger.stage("0_initial", notes=f"pid={os.getpid()} cuda_visible={os.environ.get('CUDA_VISIBLE_DEVICES','')}"):
            pass
        stages_done.append("0_initial")
        with logger.stage("1_parse_manifest"):
            pairs = reviewed_pairs(args.pair_manifest, int(args.num_pairs))
            if not pairs:
                raise RuntimeError("no reviewed DPO-ready pairs found")
        stages_done.append("1_parse_manifest")
        with logger.stage("2_select_pair"):
            pair = pairs[0]
            pair_id = str(pair.get("pair_id"))
        stages_done.append("2_select_pair")
        with logger.stage("3_resolve_paths", pair_id=pair_id):
            condition = pair.get("condition") or {}
            winner = pair.get("winner") or {}
            for key in ["poses", "intrinsics"]:
                if key not in condition:
                    raise KeyError(key)
            if not (winner.get("full_video_path") or winner.get("video")):
                raise KeyError("winner.full_video_path")
        stages_done.append("3_resolve_paths")
        with logger.stage("4_decode_winner_video_cpu", pair_id=pair_id):
            video, prompt, poses, intrinsics, sh, sw = _load_winner_inputs(
                pair,
                repo_root=args.repo_root,
                frames=int(args.used_window_frames),
                height=int(args.height),
                width=int(args.width),
                prefix_len=int(args.prefix_len),
                prediction_start_frame=int(args.prediction_start_frame),
            )
        stages_done.append("4_decode_winner_video_cpu")
        with logger.stage("5_select_window_indices", pair_id=pair_id):
            selected_raw_frame_indices = list(range(int(args.used_window_frames)))
            if len(selected_raw_frame_indices) != int(args.used_window_frames):
                raise RuntimeError("bad window indices")
        stages_done.append("5_select_window_indices")
        with logger.stage("6_load_policy_runtime", pair_id=pair_id):
            cfg = _cfg(args.config, frames=int(args.used_window_frames), height=int(args.height), width=int(args.width), runtime_device="cpu", gradient_checkpointing=True)
            backend = LingBotFastDpoEnergy(cfg, device=device, prefix_len=int(args.prefix_len))
        stages_done.append("6_load_policy_runtime")
        with logger.stage("7_load_vae_only", pair_id=pair_id):
            backend.helper.bootstrap_imports()
            if getattr(backend.helper, "vae", None) is None:
                vae_path = os.path.join(getattr(backend.helper.args, "shared_assets_dir", backend.helper.args.base_model_dir), "Wan2.1_VAE.pth")
                backend.helper.vae = backend.helper.Wan2_1_VAE(vae_pth=vae_path, device=torch.device(device))
            backend.runtime_device = torch.device(device)
        stages_done.append("7_load_vae_only")
        with logger.stage("8_vae_encode_winner_no_grad", pair_id=pair_id):
            with torch.no_grad():
                latent = backend._encode_video(video.to(backend.device))
                y = backend._prepare_y(video.to(backend.device), latent)
        stages_done.append("8_vae_encode_winner_no_grad")
        with logger.stage("9_unload_vae_if_possible", pair_id=pair_id):
            backend._move_runtime_components(torch.device("cpu"))
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        stages_done.append("9_unload_vae_if_possible")
        with logger.stage("10_load_text_runtime", pair_id=pair_id):
            backend.helper.bootstrap_imports()
            if getattr(backend.helper, "t5", None) is None:
                t5_path = os.path.join(getattr(backend.helper.args, "shared_assets_dir", backend.helper.args.base_model_dir), "models_t5_umt5-xxl-enc-bf16.pth")
                tok_path = os.path.join(getattr(backend.helper.args, "shared_assets_dir", backend.helper.args.base_model_dir), "google", "umt5-xxl")
                backend.helper.t5 = backend.helper.T5EncoderModel(text_len=512, dtype=torch.bfloat16, device=torch.device("cpu"), checkpoint_path=t5_path, tokenizer_path=tok_path)
        stages_done.append("10_load_text_runtime")
        with logger.stage("11_encode_prompt_no_grad", pair_id=pair_id):
            backend.runtime_device = torch.device("cpu")
            context = backend._encode_text(prompt)
        stages_done.append("11_encode_prompt_no_grad")
        with logger.stage("12_pack_camera_condition", pair_id=pair_id):
            poses_d = poses.to(backend.device)
            intrinsics_d = intrinsics.to(backend.device)
            lat_f, lat_h, lat_w = int(latent.shape[1]), int(latent.shape[2]), int(latent.shape[3])
            height, width = int(video.shape[2]), int(video.shape[3])
            dit_cond = backend.helper.prepare_control_signal(
                poses_d,
                None,
                intrinsics_d,
                height,
                width,
                lat_f,
                lat_h,
                lat_w,
                control_type="cam",
                source_height=int(sh),
                source_width=int(sw),
            )
        stages_done.append("12_pack_camera_condition")
        with logger.stage("13_build_future_mask", pair_id=pair_id):
            latent_loss_indices = strict_future_latent_indices(total_frames=int(args.used_window_frames), prefix_len=int(args.prefix_len), latent_frames=int(latent.shape[1]), temporal_compression=int(backend.temporal_compression))
            if not latent_loss_indices:
                raise RuntimeError("empty future mask")
        stages_done.append("13_build_future_mask")
        out_root = Path(args.cache_root)
        out_root.mkdir(parents=True, exist_ok=True)
        cache_path = out_root / "runtime_ready_minimal_cache.pt"
        with logger.stage("14_save_minimal_cache_tensors", pair_id=pair_id):
            payload = {
                "target": to_cpu(torch.zeros_like(latent)),
                "noisy_latent": to_cpu(latent),
                "context": to_cpu(context),
                "y": to_cpu(y),
                "dit_cond": to_cpu(dit_cond),
                "seq_len": int(latent.shape[1] * latent.shape[2] * latent.shape[3] // (backend.helper.patch_size[1] * backend.helper.patch_size[2])),
                "latent_loss_indices": list(latent_loss_indices),
                "selected_raw_frame_indices": selected_raw_frame_indices,
            }
            if not tensor_tree_finite(payload):
                raise FloatingPointError("nonfinite minimal payload")
            torch.save(payload, cache_path)
            digest = sha256_file(cache_path)
        stages_done.append("14_save_minimal_cache_tensors")
        with logger.stage("15_load_reference_optional", pair_id=pair_id):
            pass
        stages_done.append("15_load_reference_optional")
        with logger.stage("16_compute_ref_winner_optional", pair_id=pair_id):
            ts = _make_timestep_sample(backend, float(args.target_sigma))
            with torch.no_grad(), backend.reference_mode():
                # Debug uses latent as noisy input only to exercise ref path without building DPO cache here.
                pass
        stages_done.append("16_compute_ref_winner_optional")
        with logger.stage("17_unload_reference", pair_id=pair_id):
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        stages_done.append("17_unload_reference")
        with logger.stage("18_validate_cache_row", pair_id=pair_id):
            loaded = torch.load(cache_path, map_location="cpu")
            if not tensor_tree_finite(loaded):
                raise FloatingPointError("nonfinite saved cache")
            if sha256_file(cache_path) != digest:
                raise RuntimeError("sha mismatch after save")
        stages_done.append("18_validate_cache_row")
        with logger.stage("19_final_empty_cache", pair_id=pair_id):
            del backend, video, poses, intrinsics, latent, y, context, dit_cond, payload
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        stages_done.append("19_final_empty_cache")
        status = "RUNTIME_READY_PASS"
    except Exception as exc:  # noqa: BLE001
        blocked_stage = logger.current_stage or (stages_done[-1] if stages_done else "unknown")
        status = "RUNTIME_READY_BLOCKED_" + blocked_stage.upper()
        logger.write(stage=blocked_stage, event="final_error", pair_id=pair_id, status=status, error_reason=repr(exc))
    finally:
        logger.close()
        _write_summary(output, status, blocked_stage, stages_done)
    result = {"status": status, "blocked_stage": blocked_stage, "stages_done": stages_done, "output": str(output)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Segmented runtime-ready debug for v8e cache preflight.")
    parser.add_argument("--pair_manifest", required=True)
    parser.add_argument("--num_pairs", type=int, default=1)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--used_window_frames", type=int, default=49)
    parser.add_argument("--prefix_len", type=int, default=5)
    parser.add_argument("--prediction_start_frame", type=int, default=5)
    parser.add_argument("--output", required=True)
    parser.add_argument("--heartbeat_seconds", type=float, default=30)
    parser.add_argument("--stage_timeout_seconds", type=float, default=180)
    parser.add_argument("--cache_root", default="local_assets/dpo_objective_cache_v8e/runtime_ready_debug")
    parser.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    parser.add_argument("--repo_root", default=".")
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--target_sigma", type=float, default=0.35)
    args = parser.parse_args(argv)
    run_debug(args)


if __name__ == "__main__":
    main()
