
from __future__ import annotations

import argparse
import contextlib
import json
import resource
import threading
import time
from pathlib import Path
from typing import Any, Iterator

import torch

from cam_physgeo.dpo.full_real_energy_audit import _load_condition_index, _load_yaml, _normalize_protocol_v1_pairs_for_loader
from cam_physgeo.dpo.lingbot_fast_energy import LingBotFastDpoEnergy
from cam_physgeo.dpo.prefix5_dpo_dataset import Prefix5DpoDataset


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


class StageRecorder:
    def __init__(self, output: str | Path, *, heartbeat_seconds: float = 30.0, device: str = "cuda") -> None:
        self.output = Path(output)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.heartbeat_seconds = float(heartbeat_seconds)
        self.device = str(device)
        self.started = time.time()
        self.current_stage = "initial"
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._heartbeat_thread: threading.Thread | None = None

    def _gpu_mem(self) -> dict[str, float]:
        if self.device.startswith("cuda") and torch.cuda.is_available():
            return {
                "allocated_gb": torch.cuda.memory_allocated() / 1e9,
                "reserved_gb": torch.cuda.memory_reserved() / 1e9,
                "max_allocated_gb": torch.cuda.max_memory_allocated() / 1e9,
                "max_reserved_gb": torch.cuda.max_memory_reserved() / 1e9,
            }
        return {"allocated_gb": 0.0, "reserved_gb": 0.0, "max_allocated_gb": 0.0, "max_reserved_gb": 0.0}

    def _cpu_rss_gb(self) -> float:
        # Linux ru_maxrss is KiB.
        return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / (1024.0 * 1024.0)

    def write(self, *, stage: str, event: str, status: str = "RUNNING", error_reason: str = "", notes: dict[str, Any] | None = None) -> None:
        row: dict[str, Any] = {
            "timestamp": _now(),
            "stage": stage,
            "event": event,
            "elapsed_seconds": time.time() - self.started,
            "cpu_rss_gb": self._cpu_rss_gb(),
            "status": status,
            "error_reason": error_reason,
            "notes": notes or {},
        }
        row.update(self._gpu_mem())
        with self._lock:
            with self.output.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, sort_keys=True) + "\n")
                f.flush()

    def start_heartbeat(self) -> None:
        def loop() -> None:
            while not self._stop.wait(self.heartbeat_seconds):
                self.write(stage=self.current_stage, event="heartbeat", status="RUNNING")

        self._heartbeat_thread = threading.Thread(target=loop, name="v14-energy-stage-heartbeat", daemon=True)
        self._heartbeat_thread.start()

    def stop_heartbeat(self) -> None:
        self._stop.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join(timeout=2.0)

    @contextlib.contextmanager
    def stage(self, name: str, *, notes: dict[str, Any] | None = None) -> Iterator[None]:
        self.current_stage = name
        stage_started = time.time()
        self.write(stage=name, event="stage_start", notes=notes)
        try:
            yield
        except Exception as exc:
            self.write(
                stage=name,
                event="stage_error",
                status="FAILED",
                error_reason=f"{type(exc).__name__}: {exc}",
                notes={"stage_seconds": time.time() - stage_started},
            )
            raise
        else:
            self.write(stage=name, event="stage_done", status="PASS", notes={"stage_seconds": time.time() - stage_started})


def run(args: argparse.Namespace) -> None:
    rec = StageRecorder(args.output, heartbeat_seconds=args.heartbeat_seconds, device=args.device)
    rec.write(stage="0_initial", event="stage_start", notes={"argv": vars(args)})
    rec.start_heartbeat()
    try:
        with rec.stage("1_load_config"):
            cfg = _load_yaml(args.config)
            cfg["num_frames"] = int(args.num_frames)
            cfg["height"] = int(args.height)
            cfg["width"] = int(args.width)
            if args.runtime_device:
                cfg["dpo_runtime_device"] = args.runtime_device
        with rec.stage("2_load_dataset"):
            dataset = Prefix5DpoDataset(
                args.pair_manifest,
                repo_root=args.repo_root,
                limit_pairs=1,
                num_frames=args.num_frames,
                height=args.height,
                width=args.width,
            )
            if len(dataset) <= 0:
                raise RuntimeError("empty dataset")
        with rec.stage("3_normalize_protocol"):
            condition_index = _load_condition_index(args.condition_manifest)
            _normalize_protocol_v1_pairs_for_loader(dataset.rows, condition_index)
        with rec.stage("4_init_energy_runtime"):
            energy = LingBotFastDpoEnergy(cfg, device=args.device, prefix_len=args.prefix_len)
        with rec.stage("5_decode_example"):
            example = dataset[0]
        rec.write(stage="5_decode_example", event="pair_loaded", notes={"pair_id": example.pair_id})
        with torch.no_grad():
            with rec.stage("6_move_winner_video_to_device"):
                winner_video = example.winner_video.to(energy.device)
            with rec.stage("7_encode_winner_probe"):
                winner_latent = energy._encode_video(winner_video)
            with rec.stage("8_sample_timestep_noise"):
                timestep_sample, noise = energy.sample_timestep_and_noise(tuple(winner_latent.shape), seed=args.seed)
            with rec.stage("9_prepare_winner"):
                winner = energy.prepare(
                    winner_video,
                    prompt=example.prompt,
                    poses=example.poses,
                    intrinsics=example.intrinsics,
                    source_height=example.source_height,
                    source_width=example.source_width,
                    timestep_sample=timestep_sample,
                    noise=noise,
                )
            with rec.stage("10_move_loser_video_to_device"):
                loser_video = example.loser_video.to(energy.device)
            with rec.stage("11_prepare_loser"):
                loser = energy.prepare(
                    loser_video,
                    prompt=example.prompt,
                    poses=example.poses,
                    intrinsics=example.intrinsics,
                    source_height=example.source_height,
                    source_width=example.source_width,
                    timestep_sample=timestep_sample,
                    noise=noise,
                )
            with rec.stage("12_policy_winner_energy"):
                policy_winner = energy.energy(winner, timestep_sample).detach()
            with rec.stage("13_policy_loser_energy"):
                policy_loser = energy.energy(loser, timestep_sample).detach()
            with energy.reference_mode():
                with rec.stage("14_ref_winner_energy"):
                    ref_winner = energy.energy(winner, timestep_sample).detach()
                with rec.stage("15_ref_loser_energy"):
                    ref_loser = energy.energy(loser, timestep_sample).detach()
        result = {
            "pair_id": example.pair_id,
            "policy_winner": float(policy_winner.float().cpu()),
            "policy_loser": float(policy_loser.float().cpu()),
            "ref_winner": float(ref_winner.float().cpu()),
            "ref_loser": float(ref_loser.float().cpu()),
            "sigma": float(timestep_sample.sigma),
            "timestep_index": int(timestep_sample.index),
        }
        rec.write(stage="16_final", event="stage_done", status="PASS", notes=result)
        Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
        Path(args.summary).write_text(json.dumps({"decision": "REAL_ENERGY_STAGE_DEBUG_PASS", **result}, indent=2, sort_keys=True), encoding="utf-8")
    except Exception as exc:
        Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
        Path(args.summary).write_text(
            json.dumps({"decision": "REAL_ENERGY_STAGE_DEBUG_FAILED", "error_reason": f"{type(exc).__name__}: {exc}"}, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        raise
    finally:
        rec.stop_heartbeat()


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage-by-stage v14 LingBot real-energy heartbeat diagnostic.")
    parser.add_argument("--pair_manifest", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--repo_root", default=".")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--runtime_device", default="cpu")
    parser.add_argument("--condition_manifest", default="manifests/screen16_v2v5.jsonl")
    parser.add_argument("--prefix_len", type=int, default=5)
    parser.add_argument("--num_frames", type=int, default=81)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--seed", type=int, default=91430)
    parser.add_argument("--heartbeat_seconds", type=float, default=30.0)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
