from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Iterator

import torch

from cam_physgeo.dpo.failure_diagnostics import _make_timestep_sample
from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy, PreparedEnergyInput, strict_future_latent_indices
from cam_physgeo.dpo.winner_anchor_cache_builder import sha256_file, tensor_tree_finite, to_cpu
from cam_physgeo.dpo.winner_anchor_only_runner import _cfg, cuda_stats, reviewed_pairs
from cam_physgeo.dpo.prefix5_dpo_dataset import decode_video_tensor, load_array, normalize_intrinsics, read_prompt


def cpu_rss_gb() -> float:
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / (1024.0 * 1024.0)
    except OSError:
        return 0.0
    return 0.0


def tensor_shape_dtype(obj: Any) -> Any:
    if torch.is_tensor(obj):
        return {"shape": list(obj.shape), "dtype": str(obj.dtype), "device": str(obj.device)}
    if isinstance(obj, dict):
        return {k: tensor_shape_dtype(v) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return [tensor_shape_dtype(v) for v in obj]
    if isinstance(obj, list):
        return [tensor_shape_dtype(v) for v in obj]
    return str(type(obj).__name__)


class StageLogger:
    def __init__(self, output: str | Path, *, heartbeat_seconds: float = 15.0, stage_timeout_seconds: float = 180.0) -> None:
        self.output = Path(output)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.heartbeat_seconds = float(heartbeat_seconds)
        self.stage_timeout_seconds = float(stage_timeout_seconds)
        self._lock = threading.Lock()

    def write(
        self,
        *,
        stage: str,
        event: str,
        status: str,
        pair_id: str = "",
        error_reason: str = "",
        notes: str = "",
        elapsed_seconds: float = 0.0,
    ) -> None:
        row: dict[str, Any] = {
            "timestamp": time.time(),
            "stage": stage,
            "event": event,
            "pair_id": pair_id,
            "elapsed_seconds": float(elapsed_seconds),
            "cpu_rss_gb": cpu_rss_gb(),
            "status": status,
            "error_reason": error_reason,
            "notes": notes,
        }
        row.update(cuda_stats())
        with self._lock:
            with self.output.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, sort_keys=True) + "\n")
                f.flush()

    @contextlib.contextmanager
    def stage(self, name: str, *, pair_id: str = "", notes: str = "") -> Iterator[None]:
        start = time.time()
        stop = threading.Event()
        timeout_written = threading.Event()
        self.write(stage=name, event="stage_start", status="START", pair_id=pair_id, notes=notes)

        def beat() -> None:
            while not stop.wait(self.heartbeat_seconds):
                elapsed = time.time() - start
                if elapsed >= self.stage_timeout_seconds and not timeout_written.is_set():
                    timeout_written.set()
                    self.write(
                        stage=name,
                        event="stage_timeout",
                        status="TIMEOUT",
                        pair_id=pair_id,
                        elapsed_seconds=elapsed,
                        notes=f"stage exceeded {self.stage_timeout_seconds:.1f}s but process kept heartbeat for diagnosis",
                    )
                else:
                    self.write(stage=name, event="heartbeat", status="RUNNING", pair_id=pair_id, elapsed_seconds=elapsed)

        thread = threading.Thread(target=beat, daemon=True)
        thread.start()
        try:
            yield
        except Exception as exc:  # noqa: BLE001
            elapsed = time.time() - start
            self.write(stage=name, event="stage_error", status="ERROR", pair_id=pair_id, elapsed_seconds=elapsed, error_reason=repr(exc))
            raise
        else:
            elapsed = time.time() - start
            self.write(stage=name, event="stage_done", status="PASS", pair_id=pair_id, elapsed_seconds=elapsed)
        finally:
            stop.set()
            thread.join(timeout=1.0)


def append_csv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
        f.flush()


def resolve_repo_path(value: str, repo_root: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = Path(repo_root) / path
    return path


def finite_tensor(name: str, tensor: torch.Tensor) -> None:
    if not torch.isfinite(tensor.detach().float()).all().item():
        raise FloatingPointError(f"nonfinite tensor: {name}")


def load_condition_arrays(
    pair: dict[str, Any],
    *,
    repo_root: str | Path,
    frames: int,
    source_height: int,
    source_width: int,
) -> tuple[torch.Tensor, torch.Tensor, str]:
    condition = pair.get("condition") or {}
    poses = torch.from_numpy(load_array(condition["poses"], repo_root=repo_root, num_frames=int(frames)).astype("float32")).float()
    intrinsics = torch.from_numpy(
        normalize_intrinsics(
            load_array(condition["intrinsics"], repo_root=repo_root, num_frames=int(frames)),
            source_width=int(source_width),
            source_height=int(source_height),
        )
    ).float()
    prompt = read_prompt(condition.get("prompt_path") or condition.get("prompt"), repo_root=repo_root)
    return poses, intrinsics, prompt


def build_summary(path: Path, *, status: str, output: Path, cache_report: Path, cache_root: Path, notes: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Current Status:\n"
        f"{status}\n\n"
        "# v8i Backend Runtime Ready Debug Summary\n\n"
        f"- Status: `{status}`\n"
        f"- JSONL: `{output}`\n"
        f"- Cache report: `{cache_report}`\n"
        f"- Cache root: `{cache_root}`\n"
        + "\n".join(f"- {note}" for note in notes)
        + "\n",
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    output = Path(args.output)
    if output.exists():
        output.unlink()
    report = Path(args.cache_report) if args.cache_report else output.with_name("cache_build_one_pair_minimal_no_ref.csv")
    if report.exists():
        report.unlink()
    cache_root = Path(args.output_root) if args.output_root else Path("local_assets/dpo_objective_cache_v8i/one_pair_minimal_no_ref")
    cache_root.mkdir(parents=True, exist_ok=True)
    cache_index = cache_root / "cache_index.jsonl"
    if cache_index.exists():
        cache_index.unlink()
    if torch.cuda.is_available():
        torch.cuda.set_device(int(args.gpu))
        torch.cuda.reset_peak_memory_stats()
    logger = StageLogger(output, heartbeat_seconds=float(args.heartbeat_seconds), stage_timeout_seconds=float(args.stage_timeout_seconds))
    notes: list[str] = []
    status = "ENSURE_RUNTIME_READY_FAILED"
    pair_id = ""
    try:
        with logger.stage("0_initial", notes=f"gpu={args.gpu} cuda_visible={os.environ.get('CUDA_VISIBLE_DEVICES','')}"):
            pass
        with logger.stage("1_parse_manifest"):
            pairs = reviewed_pairs(args.pair_manifest, 1)
            if not pairs:
                raise ValueError("no reviewed DPO-ready pairs in manifest")
        with logger.stage("2_select_pair"):
            pair = pairs[0]
            pair_id = str(pair.get("pair_id") or "pair_0000")
        with logger.stage("3_resolve_paths", pair_id=pair_id):
            condition = pair.get("condition") or {}
            winner = pair.get("winner") or {}
            prefix_path = condition.get("prefix_video_path", "")
            winner_path = winner.get("full_video_path") or winner.get("video")
            future_path = winner.get("future_video_path", "")
            for label, value in [("winner_full", winner_path), ("poses", condition.get("poses", "")), ("intrinsics", condition.get("intrinsics", ""))]:
                if not value:
                    raise ValueError(f"missing {label} path")
                if not resolve_repo_path(value, args.repo_root).exists():
                    raise FileNotFoundError(f"missing {label}: {resolve_repo_path(value, args.repo_root)}")
            if prefix_path and not resolve_repo_path(prefix_path, args.repo_root).exists():
                notes.append(f"prefix path missing or not used: {prefix_path}")
            if future_path and not resolve_repo_path(future_path, args.repo_root).exists():
                notes.append(f"future path missing or not used: {future_path}")
        with logger.stage("4_decode_prefix_video_cpu", pair_id=pair_id):
            if prefix_path and resolve_repo_path(prefix_path, args.repo_root).exists():
                prefix_video, prefix_meta = decode_video_tensor(prefix_path, repo_root=args.repo_root, num_frames=int(args.prefix_len), height=int(args.height), width=int(args.width))
                finite_tensor("prefix_video", prefix_video)
                del prefix_video
            else:
                logger.write(stage="4_decode_prefix_video_cpu", event="diagnostic_skip", status="SKIPPED", pair_id=pair_id, notes="prefix path missing; winner full video still required")
        with logger.stage("5_decode_winner_future_cpu", pair_id=pair_id):
            video, meta = decode_video_tensor(winner_path, repo_root=args.repo_root, num_frames=int(args.used_window_frames), height=int(args.height), width=int(args.width))
            finite_tensor("winner_video", video)
            source_height = int(meta.get("source_height") or args.height)
            source_width = int(meta.get("source_width") or args.width)
        with logger.stage("6_load_policy_safe", pair_id=pair_id):
            cfg = _cfg(
                args.config,
                frames=int(args.used_window_frames),
                height=int(args.height),
                width=int(args.width),
                runtime_device=str(args.runtime_device),
                gradient_checkpointing=True,
            )
            cfg["dpo_policy_loader_mode"] = str(args.loader_mode)
            if str(args.loader_mode) == "safe_wan_policy_only":
                cfg["dpo_safe_loader_heartbeat_path"] = str(output.with_name(output.stem + "_safe_loader.jsonl"))
            backend = LingBotFastDpoEnergy(cfg, device=f"cuda:{int(args.gpu)}" if torch.cuda.is_available() else "cpu", prefix_len=int(args.prefix_len))
        with logger.stage("7_policy_runtime_ready_confirmed", pair_id=pair_id):
            if getattr(backend, "model", None) is None:
                raise RuntimeError("backend.model missing after policy load")
            logger.write(stage="7_policy_runtime_ready_confirmed", event="model_info", status="INFO", pair_id=pair_id, notes=f"trainable={backend.policy_trainable_params} runtime_device={backend.runtime_device}")
        with logger.stage("8_create_backend_object", pair_id=pair_id):
            if getattr(backend, "helper", None) is None:
                raise RuntimeError("backend.helper missing")
        with logger.stage("9_inspect_backend_components", pair_id=pair_id):
            helper = backend.helper
            component_notes = {
                "has_vae": getattr(helper, "vae", None) is not None,
                "has_t5": getattr(helper, "t5", None) is not None,
                "has_Wan2_1_VAE": hasattr(helper, "Wan2_1_VAE"),
                "has_T5EncoderModel": hasattr(helper, "T5EncoderModel"),
                "has_cam_utils": hasattr(helper, "cam_utils"),
            }
            logger.write(stage="9_inspect_backend_components", event="component_inventory", status="INFO", pair_id=pair_id, notes=json.dumps(component_notes, sort_keys=True))
        with logger.stage("10_backend_config_parse", pair_id=pair_id):
            shared = Path(getattr(backend.args, "shared_assets_dir", getattr(backend.args, "base_model_dir", "")))
            vae_path = shared / "Wan2.1_VAE.pth"
            t5_path = shared / "models_t5_umt5-xxl-enc-bf16.pth"
            tok_path = shared / "google" / "umt5-xxl"
            for label, path in [("vae", vae_path), ("t5", t5_path), ("tokenizer", tok_path)]:
                if not path.exists():
                    raise FileNotFoundError(f"missing {label}: {path}")
            logger.write(stage="10_backend_config_parse", event="paths", status="INFO", pair_id=pair_id, notes=json.dumps({"vae": str(vae_path), "t5": str(t5_path), "tokenizer": str(tok_path)}, sort_keys=True))
        with logger.stage("11_check_needed_components_for_minimal_cache", pair_id=pair_id):
            need_text = not bool(args.diagnostic_skip_text)
            need_vae = not bool(args.diagnostic_skip_vae)
            logger.write(stage="11_check_needed_components_for_minimal_cache", event="needs", status="INFO", pair_id=pair_id, notes=json.dumps({"need_text": need_text, "need_vae": need_vae, "cache_level": args.cache_level}, sort_keys=True))
        with logger.stage("12_load_or_skip_text_tokenizer", pair_id=pair_id):
            if args.diagnostic_skip_text:
                logger.write(stage="12_load_or_skip_text_tokenizer", event="diagnostic_skip", status="SKIPPED", pair_id=pair_id, notes="diagnostic_skip_text=true")
            else:
                logger.write(stage="12_load_or_skip_text_tokenizer", event="tokenizer_path_ready", status="INFO", pair_id=pair_id, notes=str(tok_path))
        with logger.stage("13_load_or_skip_t5_text_encoder", pair_id=pair_id):
            if args.diagnostic_skip_text:
                logger.write(stage="13_load_or_skip_t5_text_encoder", event="diagnostic_skip", status="SKIPPED", pair_id=pair_id, notes="diagnostic_skip_text=true")
            elif getattr(backend.helper, "t5", None) is None:
                backend.helper.t5 = backend.helper.T5EncoderModel(
                    text_len=512,
                    dtype=torch.bfloat16,
                    device=torch.device("cpu"),
                    checkpoint_path=str(t5_path),
                    tokenizer_path=str(tok_path),
                )
                module = getattr(backend.helper.t5, "model", None)
                if module is not None and hasattr(module, "to"):
                    module.to("cpu")
        with logger.stage("14_prompt_encode_or_stub", pair_id=pair_id):
            poses, intrinsics, prompt = load_condition_arrays(pair, repo_root=args.repo_root, frames=int(args.used_window_frames), source_height=source_height, source_width=source_width)
            if args.diagnostic_skip_text:
                context = [torch.zeros(1, 1, 1, device=backend.device, dtype=backend.lowp_dtype)]
                logger.write(stage="14_prompt_encode_or_stub", event="diagnostic_stub", status="INFO", pair_id=pair_id, notes="diagnostic_skip_text=true; context is not training-valid")
            else:
                context = backend._encode_text(prompt)
                for idx, tensor in enumerate(context):
                    finite_tensor(f"context_{idx}", tensor)
        with logger.stage("15_load_or_skip_vae", pair_id=pair_id):
            if args.diagnostic_skip_vae:
                logger.write(stage="15_load_or_skip_vae", event="diagnostic_skip", status="SKIPPED", pair_id=pair_id, notes="diagnostic_skip_vae=true")
            elif getattr(backend.helper, "vae", None) is None:
                backend.helper.vae = backend.helper.Wan2_1_VAE(vae_pth=str(vae_path), device=backend.runtime_device)
        with logger.stage("16_vae_ready_check", pair_id=pair_id):
            if args.diagnostic_skip_vae:
                latent = torch.zeros(16, 1, max(int(args.height) // 8, 1), max(int(args.width) // 8, 1), device=backend.device, dtype=backend.lowp_dtype)
                logger.write(stage="16_vae_ready_check", event="diagnostic_stub", status="INFO", pair_id=pair_id, notes="diagnostic_skip_vae=true; latent is not training-valid")
            else:
                if getattr(backend.helper, "vae", None) is None:
                    raise RuntimeError("VAE missing after load stage")
        with logger.stage("17_load_poses_intrinsics", pair_id=pair_id):
            finite_tensor("poses", poses)
            finite_tensor("intrinsics", intrinsics)
            logger.write(stage="17_load_poses_intrinsics", event="shape", status="INFO", pair_id=pair_id, notes=json.dumps({"poses": list(poses.shape), "intrinsics": list(intrinsics.shape)}, sort_keys=True))
        with logger.stage("18_normalize_camera_poses", pair_id=pair_id):
            if poses.ndim != 3 or poses.shape[-2:] != (4, 4):
                raise ValueError(f"unexpected poses shape: {tuple(poses.shape)}")
            if intrinsics.ndim < 2:
                raise ValueError(f"unexpected intrinsics shape: {tuple(intrinsics.shape)}")
        with logger.stage("23_encode_winner_latents_if_needed", pair_id=pair_id):
            if not args.diagnostic_skip_vae:
                latent = backend._encode_video(video)
                finite_tensor("latent", latent)
            lat_f, lat_h, lat_w = int(latent.shape[1]), int(latent.shape[2]), int(latent.shape[3])
            logger.write(stage="23_encode_winner_latents_if_needed", event="latent_shape", status="INFO", pair_id=pair_id, notes=json.dumps({"latent": list(latent.shape)}, sort_keys=True))
        with logger.stage("19_pack_camera_condition", pair_id=pair_id):
            dit_cond = backend.helper.prepare_control_signal(
                poses.to(backend.device),
                None,
                intrinsics.to(backend.device),
                int(video.shape[2]),
                int(video.shape[3]),
                lat_f,
                lat_h,
                lat_w,
                control_type="cam",
                source_height=int(source_height),
                source_width=int(source_width),
            )
            if not tensor_tree_finite(dit_cond):
                raise FloatingPointError("nonfinite camera condition")
        with logger.stage("20_pack_prefix_condition", pair_id=pair_id):
            if args.diagnostic_skip_vae:
                y = torch.zeros(20, lat_f, lat_h, lat_w, device=backend.device, dtype=backend.lowp_dtype)
                logger.write(stage="20_pack_prefix_condition", event="diagnostic_stub", status="INFO", pair_id=pair_id, notes="diagnostic_skip_vae=true; y is not training-valid")
            else:
                y = backend._prepare_y(video, latent)
                finite_tensor("y", y)
        with logger.stage("21_build_future_mask", pair_id=pair_id):
            if int(args.prefix_len) != 5:
                raise ValueError("prefix_len must remain 5 for v8i")
            logger.write(stage="21_build_future_mask", event="future_mask", status="INFO", pair_id=pair_id, notes=json.dumps({"prefix_len": int(args.prefix_len), "nonempty": True}, sort_keys=True))
        with logger.stage("22_build_latent_temporal_index_mapping", pair_id=pair_id):
            latent_loss_indices = strict_future_latent_indices(
                total_frames=int(args.used_window_frames),
                prefix_len=int(args.prefix_len),
                latent_frames=lat_f,
                temporal_compression=int(backend.temporal_compression),
            )
            if not latent_loss_indices:
                raise ValueError("empty latent future loss indices")
            logger.write(stage="22_build_latent_temporal_index_mapping", event="latent_indices", status="INFO", pair_id=pair_id, notes=json.dumps({"indices": latent_loss_indices}, sort_keys=True))
        with logger.stage("24_save_minimal_cache_tensors", pair_id=pair_id):
            ts = _make_timestep_sample(backend, float(args.target_sigma))
            generator = torch.Generator(device=backend.device)
            generator.manual_seed(int(args.seed))
            noise = torch.randn(tuple(latent.shape), device=backend.device, dtype=backend.lowp_dtype, generator=generator).to(dtype=latent.dtype)
            noisy = (1.0 - float(ts.sigma)) * latent + float(ts.sigma) * noise
            target = noise - latent
            seq_len = lat_f * lat_h * lat_w // (backend.helper.patch_size[1] * backend.helper.patch_size[2])
            prepared = PreparedEnergyInput(
                target=target.detach(),
                noisy_latent=noisy.detach(),
                context=[tensor.detach() for tensor in context],
                y=y.detach(),
                dit_cond=dit_cond,
                seq_len=int(seq_len),
                latent_loss_indices=list(latent_loss_indices),
            )
            cache_payload = {
                "target": to_cpu(prepared.target),
                "noisy_latent": to_cpu(prepared.noisy_latent),
                "context": to_cpu(prepared.context),
                "y": to_cpu(prepared.y),
                "dit_cond": to_cpu(prepared.dit_cond),
                "seq_len": int(prepared.seq_len),
                "latent_loss_indices": list(prepared.latent_loss_indices),
                "timestep_tensor": to_cpu(ts.timestep),
                "timestep_index": int(ts.index),
                "actual_sigma": float(ts.sigma),
                "timestep_weight": float(ts.weight),
                "diagnostic_skip_text": bool(args.diagnostic_skip_text),
                "diagnostic_skip_vae": bool(args.diagnostic_skip_vae),
            }
            if not tensor_tree_finite(cache_payload):
                raise FloatingPointError("nonfinite minimal cache payload")
            tensor_path = cache_root / f"000_{pair_id.replace('/', '_')}.pt"
            torch.save(cache_payload, tensor_path)
            digest = sha256_file(tensor_path)
        with logger.stage("25_write_cache_index_row", pair_id=pair_id):
            index_row = {
                "pair_id": pair_id,
                "cache_tensor_path": tensor_path.name,
                "cache_level": args.cache_level,
                "used_window_frames": int(args.used_window_frames),
                "prefix_len": int(args.prefix_len),
                "prediction_start_frame": int(args.prediction_start_frame),
                "latent_temporal_index_mapping": list(latent_loss_indices),
                "actual_sigma": float(ts.sigma),
                "timestep_index": int(ts.index),
                "sha256": digest,
                "status": "PASS",
                "diagnostic_skip_text": bool(args.diagnostic_skip_text),
                "diagnostic_skip_vae": bool(args.diagnostic_skip_vae),
                "shape_dtype": tensor_shape_dtype(cache_payload),
            }
            with cache_index.open("a", encoding="utf-8") as f:
                f.write(json.dumps(index_row, sort_keys=True) + "\n")
                f.flush()
            fieldnames = ["pair_id", "cache_status", "cache_tensor_path", "sha256", "actual_sigma", "used_window_frames", "prefix_len", "prediction_start_frame", "diagnostic_skip_text", "diagnostic_skip_vae", "allocated_gb", "reserved_gb", "max_allocated_gb", "max_reserved_gb", "error_reason"]
            row = {"pair_id": pair_id, "cache_status": "PASS", "cache_tensor_path": str(tensor_path), "sha256": digest, "actual_sigma": float(ts.sigma), "used_window_frames": int(args.used_window_frames), "prefix_len": int(args.prefix_len), "prediction_start_frame": int(args.prediction_start_frame), "diagnostic_skip_text": bool(args.diagnostic_skip_text), "diagnostic_skip_vae": bool(args.diagnostic_skip_vae), "error_reason": ""}
            row.update(cuda_stats())
            append_csv(report, row, fieldnames)
        with logger.stage("26_after_runtime_ready", pair_id=pair_id):
            pass
        with logger.stage("27_pair_start_ready", pair_id=pair_id):
            pass
        with logger.stage("28_final_empty_cache", pair_id=pair_id):
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        status = "ENSURE_RUNTIME_READY_PASS_FIRST_ROW_PASS"
        notes.append("one-pair minimal cache first row written")
    except Exception as exc:  # noqa: BLE001
        status = f"ENSURE_RUNTIME_READY_FAILED_{type(exc).__name__}"
        notes.append(f"error={exc!r}")
        raise
    finally:
        build_summary(output.with_name("backend_runtime_ready_debug_summary.md"), status=status, output=output, cache_report=report, cache_root=cache_root, notes=notes)
    return {"status": status, "output": str(output), "cache_report": str(report), "cache_root": str(cache_root)}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Split v8i backend runtime readiness before cache first-row build.")
    parser.add_argument("--pair_manifest", required=True)
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--loader_mode", default="safe_wan_policy_only", choices=["safe_wan_policy_only", "stage1_helper"])
    parser.add_argument("--prefix_len", type=int, default=5)
    parser.add_argument("--prediction_start_frame", type=int, default=5)
    parser.add_argument("--used_window_frames", type=int, default=49)
    parser.add_argument("--cache_level", default="minimal_no_ref")
    parser.add_argument("--output", required=True)
    parser.add_argument("--output_root", default="")
    parser.add_argument("--cache_report", default="")
    parser.add_argument("--heartbeat_seconds", type=float, default=15.0)
    parser.add_argument("--stage_timeout_seconds", type=float, default=180.0)
    parser.add_argument("--config", default="configs/cam_physgeo/fast_stageA_v2v5_camera_r4_100step.yaml")
    parser.add_argument("--repo_root", default=".")
    parser.add_argument("--runtime_device", default="cuda")
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--target_sigma", type=float, default=0.35)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--diagnostic_skip_text", action="store_true")
    parser.add_argument("--diagnostic_skip_vae", action="store_true")
    args = parser.parse_args(argv)
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
