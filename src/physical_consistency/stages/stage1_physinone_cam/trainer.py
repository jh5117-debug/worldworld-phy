"""Stage-1 PhysInOne trainer."""

from __future__ import annotations

import csv
import gc
import hashlib
import json
import logging
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import accelerate
import torch
import torch.nn.functional as F
from accelerate import DistributedType
from accelerate.utils import (
    DataLoaderConfiguration,
    DistributedDataParallelKwargs,
    GradientAccumulationPlugin,
    InitProcessGroupKwargs,
    ProjectConfiguration,
)
from torch.utils.data import DataLoader, Subset

from physical_consistency.common.io import ensure_dir, write_json
from physical_consistency.common.subprocess_utils import run_command
from physical_consistency.eval.checkpoint_bundle import materialize_eval_checkpoint_bundle
from physical_consistency.trainers.stage1_components import (
    CSGODataset,
    LingBotStage1Helper,
    TimestepSample,
    apply_gradient_checkpointing,
    compute_scheduler_total_steps,
    configure_stage1_precision_env,
    export_pretrained_state_dict,
    resolve_stage1_low_precision_dtype,
)

from .config import Stage1PhysInOneConfig
from .dataset import PhysInOneCamDataset
from .eval import run_stage1_videophy2_eval

LOGGER = logging.getLogger(__name__)


def _now_local() -> datetime:
    return datetime.now().astimezone()


def _isoformat_local(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "")
    if raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "")
    if raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        LOGGER.warning("Ignoring invalid integer env %s=%r", name, raw)
        return default


@dataclass(slots=True)
class BranchTrainResult:
    """Outputs from one branch-specific Stage-1 run."""

    branch: str
    final_branch_dir: str
    final_eval_bundle_dir: str
    output_dir: str
    started_at: str
    finished_at: str
    duration_seconds: float
    global_step: int
    micro_step: int


def fixed_validation_noise_seed(
    *,
    base_seed: int,
    branch: str,
    validation_index: int,
    sample_id: str | int | None = None,
) -> int:
    """Return a checkpoint-invariant seed for fixed validation noise.

    The fixed validation gate must compare checkpoints under exactly the same
    condition, including the noise tensor. Do not include global step, epoch,
    wall-clock time, rank state, or any mutable training counter here.
    """

    normalized_branch = "high" if branch == "high_only" else str(branch)
    branch_offset = 500000 if normalized_branch == "high" else 0
    sample_text = "" if sample_id is None else str(sample_id)
    sample_hash = int(hashlib.sha256(sample_text.encode("utf-8")).hexdigest()[:8], 16)
    return int(base_seed) + 1000003 + int(validation_index) * 9176 + branch_offset + sample_hash


class Stage1BranchTrainer:
    """Train one LingBot MoE branch with PhysInOne conditioning and FM loss."""

    def __init__(
        self,
        cfg: Stage1PhysInOneConfig,
        *,
        branch: str,
        source_checkpoint_dir: str,
        companion_checkpoint_dir: str,
    ) -> None:
        if branch not in {"low", "high", "high_only"}:
            raise ValueError(f"Unsupported branch: {branch}")
        if cfg.model_family == "lingbot_world_fast" and branch != "high_only":
            raise ValueError("LingBot-Fast StageA only supports branch=high_only")
        self.cfg = cfg
        self.branch = branch
        self.source_checkpoint_dir = str(Path(source_checkpoint_dir).resolve())
        self.companion_checkpoint_dir = str(Path(companion_checkpoint_dir).resolve())
        self.precision_policy = configure_stage1_precision_env(
            cfg.student_precision_profile,
            cfg.student_low_precision_dtype,
        )
        LOGGER.info(
            "[Stage1][%s] Initializing accelerator (launcher_env rank=%s local_rank=%s world_size=%s)",
            branch,
            os.environ.get("RANK", ""),
            os.environ.get("LOCAL_RANK", ""),
            os.environ.get("WORLD_SIZE", ""),
        )

        ddp_kwargs = DistributedDataParallelKwargs(
            find_unused_parameters=bool(cfg.student_ddp_find_unused_parameters)
        )
        init_kwargs = InitProcessGroupKwargs(
            backend="nccl",
            timeout=timedelta(hours=cfg.distributed_timeout_hours),
        )
        grad_accum_plugin = GradientAccumulationPlugin(
            num_steps=cfg.gradient_accumulation_steps,
            sync_each_batch=True,
        )
        project_config = ProjectConfiguration(
            project_dir=str(Path(cfg.output_dir)),
            logging_dir=str(Path(cfg.output_root) / "logs" / "wandb"),
        )
        self.accelerator = accelerate.Accelerator(
            gradient_accumulation_plugin=grad_accum_plugin,
            dataloader_config=DataLoaderConfiguration(use_seedable_sampler=True),
            kwargs_handlers=[ddp_kwargs, init_kwargs],
            log_with=None,
            project_config=project_config,
        )
        LOGGER.info(
            "[Stage1][%s] Accelerator ready (distributed_type=%s num_processes=%s device=%s is_main=%s)",
            branch,
            self.accelerator.distributed_type,
            self.accelerator.num_processes,
            self.accelerator.device,
            self.accelerator.is_main_process,
        )
        self.helper = LingBotStage1Helper(cfg)
        self.model = None
        self.optimizer = None
        self.scheduler = None
        self.train_loader = None
        self.val_loader = None
        self.global_step = 0
        self.micro_step = 0
        self.total_optimizer_steps = 0
        self.output_dir = Path(cfg.output_dir) / f"{branch}_phase"
        ensure_dir(self.output_dir)
        self.branch_limits = cfg.branch_step_limits(branch)
        self.loss_ema20: float | None = None
        self.loss_ema100: float | None = None
        self.loss_history: list[float] = []
        self.clip_history: list[bool] = []
        self.metrics_jsonl_path = self.output_dir / "metrics.jsonl"
        self.metrics_csv_path = self.output_dir / "metrics.csv"
        self.fixed_val_jsonl_path = self.output_dir / "fixed_val_metrics.jsonl"
        self.fixed_val_csv_path = self.output_dir / "fixed_val_metrics.csv"
        self._metrics_csv_fields: list[str] | None = None
        self._fixed_val_csv_fields: list[str] | None = None
        self._last_lora_param_norm: float | None = None
        self.fixed_val_history: list[float] = []
        self.best_fixed_val_loss: float | None = None
        self.timing_enabled = _env_flag("PC_STAGE1_TIMING", False)
        self.timing_cuda_sync = _env_flag("PC_STAGE1_TIMING_CUDA_SYNC", False)
        self.timing_log_every = max(_env_int("PC_STAGE1_TIMING_EVERY", 1), 1)
        if self.timing_enabled and self.accelerator.is_main_process:
            LOGGER.info(
                "[Stage1][%s][timing] enabled cuda_sync=%s log_every_micro_steps=%s",
                self.branch,
                self.timing_cuda_sync,
                self.timing_log_every,
            )

    def run(self) -> BranchTrainResult:
        started_at = _now_local()
        LOGGER.info(
            "[Stage1][%s] Starting branch run at %s (source_ckpt=%s companion_ckpt=%s output_dir=%s)",
            self.branch,
            _isoformat_local(started_at),
            self.source_checkpoint_dir,
            self.companion_checkpoint_dir,
            self.output_dir,
        )
        LOGGER.info(
            "[Stage1][%s] Building dataset from %s (control_type=%s frames=%s size=%sx%s repeat=%s workers=%s)",
            self.branch,
            self.cfg.dataset_dir,
            self.cfg.control_type,
            self.cfg.num_frames,
            self.cfg.height,
            self.cfg.width,
            self.cfg.dataset_repeat,
            self.cfg.num_workers,
        )
        if self.cfg.control_type == "act":
            dataset = CSGODataset(
                self.cfg.dataset_dir,
                split="train",
                num_frames=self.cfg.num_frames,
                height=self.cfg.height,
                width=self.cfg.width,
                repeat=self.cfg.dataset_repeat,
            )
        else:
            dataset = PhysInOneCamDataset(
                self.cfg.dataset_dir,
                split="train",
                num_frames=self.cfg.num_frames,
                height=self.cfg.height,
                width=self.cfg.width,
                repeat=self.cfg.dataset_repeat,
                temporal_window_mode=self.cfg.temporal_window_mode,
            )
        LOGGER.info("[Stage1][%s] Dataset ready with %s samples", self.branch, len(dataset))
        raw_val_loader = None
        if self.cfg.control_type == "cam" and self.cfg.fixed_val_sample_count > 0:
            val_dataset = PhysInOneCamDataset(
                self.cfg.dataset_dir,
                split="val",
                num_frames=self.cfg.num_frames,
                height=self.cfg.height,
                width=self.cfg.width,
                repeat=1,
                temporal_window_mode="center_window",
            )
            val_count = min(int(self.cfg.fixed_val_sample_count), len(val_dataset))
            if val_count <= 0:
                raise ValueError("fixed validation requested but metadata_val.csv has no samples")
            val_subset = Subset(val_dataset, list(range(val_count)))
            raw_val_loader = DataLoader(
                val_subset,
                batch_size=1,
                shuffle=False,
                num_workers=self.cfg.num_workers,
                pin_memory=True,
                collate_fn=lambda items: items[0],
            )
            LOGGER.info(
                "[Stage1][%s] Fixed validation dataset ready with %s/%s samples (center temporal window)",
                self.branch,
                val_count,
                len(val_dataset),
            )
        LOGGER.info("[Stage1][%s] Constructing raw dataloader", self.branch)
        raw_loader = DataLoader(
            dataset,
            batch_size=1,
            shuffle=True,
            num_workers=self.cfg.num_workers,
            pin_memory=True,
            collate_fn=lambda items: items[0],
        )
        train_dataset_len = len(dataset)

        LOGGER.info("[Stage1][%s] Loading student model", self.branch)
        self.model = self.helper.load_model(
            self.accelerator.device,
            self.branch,
            checkpoint_dir=self.source_checkpoint_dir,
            control_type=self.cfg.control_type,
        )
        LOGGER.info("[Stage1][%s] Student model loaded", self.branch)
        if self.cfg.gradient_checkpointing:
            LOGGER.info(
                "[Stage1][%s] Applying gradient checkpointing (mode=%s)",
                self.branch,
                self.cfg.student_memory_efficient_checkpoint_mode,
            )
            use_reentrant = self._student_checkpoint_use_reentrant()
            apply_gradient_checkpointing(
                self.model,
                f"{self.branch}_noise_model",
                use_reentrant=use_reentrant,
                skip_block_indices=set(),
                memory_efficient_mode=self.cfg.student_memory_efficient_checkpoint_mode,
            )
            LOGGER.info("[Stage1][%s] Gradient checkpointing ready", self.branch)

        LOGGER.info("[Stage1][%s] Building optimizer and scheduler", self.branch)
        optimizer = torch.optim.AdamW(
            [parameter for parameter in self.model.parameters() if parameter.requires_grad],
            lr=self.cfg.learning_rate,
            weight_decay=self.cfg.weight_decay,
            betas=(self.cfg.optimizer_beta1, self.cfg.optimizer_beta2),
        )
        planned_optimizer_steps = compute_scheduler_total_steps(
            train_dataset_len,
            self.accelerator.num_processes,
            self.cfg.gradient_accumulation_steps,
            self.cfg.num_epochs,
        )
        branch_target = int(self.branch_limits.get("target_optimizer_steps") or planned_optimizer_steps)
        branch_hard_max = int(self.branch_limits.get("hard_max_optimizer_steps") or branch_target)
        branch_min = int(self.branch_limits.get("min_optimizer_steps") or self.cfg.min_train_optimizer_steps or 0)
        if self.cfg.max_train_optimizer_steps > 0:
            branch_hard_max = min(branch_hard_max, self.cfg.max_train_optimizer_steps)
            branch_target = min(branch_target, branch_hard_max)
            if branch_min > branch_hard_max:
                branch_min = min(int(self.cfg.min_train_optimizer_steps or 0), branch_hard_max)
        planned_optimizer_steps = max(branch_hard_max, 1)
        warmup_steps = max(int(planned_optimizer_steps * float(self.cfg.scheduler_warmup_fraction)), 1)
        eta_ratio = max(float(self.cfg.scheduler_eta_min) / max(float(self.cfg.learning_rate), 1.0e-12), 0.0)

        def _lr_lambda(step: int) -> float:
            if step < warmup_steps:
                return max(float(step + 1) / float(warmup_steps), eta_ratio)
            progress = min(max((step - warmup_steps) / max(planned_optimizer_steps - warmup_steps, 1), 0.0), 1.0)
            return eta_ratio + (1.0 - eta_ratio) * 0.5 * (1.0 + math.cos(math.pi * progress))

        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=_lr_lambda)
        self.total_optimizer_steps = branch_target
        self.branch_limits.update({"resolved_min_optimizer_steps": branch_min, "resolved_target_optimizer_steps": branch_target, "resolved_hard_max_optimizer_steps": branch_hard_max, "warmup_steps": warmup_steps})
        LOGGER.info(
            "[Stage1][%s] Optimizer-step plan: min=%s target=%s hard_max=%s warmup_steps=%s save_every_optimizer_steps=%s grad_accum=%s num_processes=%s",
            self.branch,
            branch_min,
            branch_target,
            branch_hard_max,
            warmup_steps,
            self.cfg.save_every_optimizer_steps,
            self.cfg.gradient_accumulation_steps,
            self.accelerator.num_processes,
        )
        LOGGER.info(
            "[Stage1][%s] Preparing model/optimizer/dataloader with accelerator; scheduler stays unwrapped",
            self.branch,
        )
        if raw_val_loader is not None:
            (
                self.model,
                self.optimizer,
                self.train_loader,
                self.val_loader,
            ) = self.accelerator.prepare(
                self.model,
                optimizer,
                raw_loader,
                raw_val_loader,
            )
        else:
            self.model, self.optimizer, self.train_loader = self.accelerator.prepare(
                self.model,
                optimizer,
                raw_loader,
            )
            self.val_loader = None
        self.scheduler = scheduler
        LOGGER.info(
            "[Stage1][%s] Accelerator.prepare complete; raw scheduler will step once per optimizer step",
            self.branch,
        )
        self.accelerator.wait_for_everyone()
        LOGGER.info("[Stage1][%s] Post-prepare barrier complete", self.branch)

        last_eval_bundle = ""
        branch_stop_requested = False
        for epoch in range(self.cfg.num_epochs):
            epoch_index = epoch + 1
            self.model.train()
            for batch in self.train_loader:
                self.micro_step += 1
                with self.accelerator.accumulate(self.model):
                    micro_start = self._timing_start()
                    loss, metrics = self.training_step(batch)
                    metrics["timing_training_step_sec"] = self._timing_elapsed(micro_start)

                    backward_start = self._timing_start()
                    self.accelerator.backward(loss)
                    metrics["timing_backward_sec"] = self._timing_elapsed(backward_start)

                    if self.accelerator.sync_gradients:
                        metrics.update(self._collect_lora_group_grad_norms())
                        clip_start = self._timing_start()
                        grad_norm_before = self.accelerator.clip_grad_norm_(self.model.parameters(), self.cfg.max_grad_norm)
                        metrics["grad_norm_before_clip"] = float(grad_norm_before.detach().item() if hasattr(grad_norm_before, "detach") else grad_norm_before)
                        metrics["grad_norm_after_clip"] = float(self._total_grad_norm())
                        metrics["clip_applied"] = float(metrics["grad_norm_before_clip"] > float(self.cfg.max_grad_norm))
                        metrics["timing_clip_grad_sec"] = self._timing_elapsed(clip_start)

                    optimizer_start = self._timing_start()
                    self.optimizer.step()
                    metrics["timing_optimizer_step_sec"] = self._timing_elapsed(optimizer_start)

                    if self.accelerator.sync_gradients:
                        metrics.update(self._lora_param_update_metrics())

                    scheduler_start = self._timing_start()
                    self.scheduler.step()
                    metrics["timing_scheduler_step_sec"] = self._timing_elapsed(scheduler_start)

                    zero_grad_start = self._timing_start()
                    self.optimizer.zero_grad(set_to_none=True)
                    metrics["timing_zero_grad_sec"] = self._timing_elapsed(zero_grad_start)
                    metrics["timing_total_micro_sec"] = self._timing_elapsed(micro_start)
                    self._log_timing(epoch_index, metrics)
                    if self.accelerator.sync_gradients:
                        self.global_step += 1
                        metrics["learning_rate"] = float(self.scheduler.get_last_lr()[0])
                        gate_status = self._record_and_write_metrics(epoch_index, metrics)
                        if self.accelerator.is_main_process:
                            LOGGER.info(
                                "[Stage1][%s] epoch=%s/%s step=%s/%s hard_max=%s loss=%.6f ema20=%.6f ema100=%.6f lr=%.3e sigma=%.4f grad=%.4f gate=%s reasons=%s",
                                self.branch,
                                epoch_index,
                                self.cfg.num_epochs,
                                self.global_step,
                                self.total_optimizer_steps,
                                self.branch_limits.get("resolved_hard_max_optimizer_steps"),
                                float(metrics["loss_fm_weighted"]),
                                float(metrics.get("loss_ema20", metrics["loss_fm_weighted"])),
                                float(metrics.get("loss_ema100", metrics["loss_fm_weighted"])),
                                float(metrics["learning_rate"]),
                                float(metrics["sample_sigma"]),
                                float(metrics.get("grad_norm_before_clip", 0.0)),
                                gate_status.get("status"),
                                ",".join(gate_status.get("reasons", [])),
                            )
                        if (
                            self.cfg.save_every_optimizer_steps > 0
                            and self.global_step > 0
                            and self.global_step % self.cfg.save_every_optimizer_steps == 0
                        ):
                            self._save_branch_checkpoint(tag=f"step_{self.global_step:06d}")
                        if (
                            self.cfg.diagnostic_stop_optimizer_steps > 0
                            and self.global_step >= self.cfg.diagnostic_stop_optimizer_steps
                        ):
                            if self.accelerator.is_main_process:
                                LOGGER.info(
                                    "[Stage1][%s] Diagnostic stop reached at optimizer_step=%s; branch gate is not evaluated as PASS",
                                    self.branch,
                                    self.global_step,
                                )
                            branch_stop_requested = True
                            break
                        if self._should_stop_branch(gate_status):
                            branch_stop_requested = True
                            break
                if branch_stop_requested:
                    break
                if self.cfg.max_train_micro_steps > 0 and self.micro_step >= self.cfg.max_train_micro_steps:
                    break
                if (
                    self.cfg.diagnostic_stop_optimizer_steps > 0
                    and self.global_step >= self.cfg.diagnostic_stop_optimizer_steps
                ):
                    break
                if self.global_step >= int(self.branch_limits.get("resolved_hard_max_optimizer_steps", self.total_optimizer_steps)):
                    break

            should_save = self.cfg.save_every_n_epochs > 0 and epoch_index % self.cfg.save_every_n_epochs == 0
            should_eval = (
                self.cfg.videophy2_eval.enabled
                and epoch_index % self.cfg.videophy2_eval.every_n_epochs == 0
            )
            checkpoint_root = None
            if should_save or should_eval:
                checkpoint_root = self._save_branch_checkpoint(tag=f"epoch_{epoch_index}")
            if should_eval and checkpoint_root is not None:
                last_eval_bundle = self._run_epoch_eval(epoch_index, checkpoint_root)
            if branch_stop_requested:
                break
            if self.cfg.max_train_micro_steps > 0 and self.micro_step >= self.cfg.max_train_micro_steps:
                break
            if (
                self.cfg.diagnostic_stop_optimizer_steps > 0
                and self.global_step >= self.cfg.diagnostic_stop_optimizer_steps
            ):
                break
            if self.global_step >= int(self.branch_limits.get("resolved_hard_max_optimizer_steps", self.total_optimizer_steps)):
                break

        final_branch_dir = self._save_branch_checkpoint(tag="final")
        final_bundle = final_branch_dir
        self.accelerator.wait_for_everyone()
        if self.cfg.videophy2_eval.enabled and self.accelerator.is_main_process:
            run_stage1_videophy2_eval(
                self.cfg.videophy2_eval,
                bundle_dir=final_bundle,
                output_dir=self.output_dir,
                experiment_name=self.cfg.experiment_name,
                epoch=self.cfg.num_epochs,
                branch=f"{self.branch}_final",
            )
        self.accelerator.wait_for_everyone()
        finished_at = _now_local()
        duration_seconds = (finished_at - started_at).total_seconds()
        final_gate_status = self._loss_gate_status()
        hard_max = int(self.branch_limits.get("resolved_hard_max_optimizer_steps", self.total_optimizer_steps))
        if final_gate_status.get("status") == "PASS":
            branch_status = "PASS"
        elif self.global_step >= hard_max:
            branch_status = "INCONCLUSIVE"
        else:
            branch_status = "STOPPED"
        final_fixed_val_loss = self.fixed_val_history[-1] if self.fixed_val_history else float("nan")
        if self.accelerator.is_main_process:
            write_json(
                self.output_dir / "branch_summary.json",
                {
                    "branch": self.branch,
                    "branch_status": branch_status,
                    "source_checkpoint_dir": self.source_checkpoint_dir,
                    "companion_checkpoint_dir": self.companion_checkpoint_dir,
                    "control_type": self.cfg.control_type,
                    "final_branch_dir": str(final_branch_dir),
                    "final_eval_bundle_dir": str(final_bundle),
                    "last_eval_bundle_dir": last_eval_bundle,
                    "started_at": _isoformat_local(started_at),
                    "finished_at": _isoformat_local(finished_at),
                    "duration_seconds": duration_seconds,
                    "global_step": self.global_step,
                    "micro_step": self.micro_step,
                    "loss_gate_status": str(final_gate_status.get("status")),
                    "loss_gate_reasons": list(final_gate_status.get("reasons", [])),
                    "loss_gate_advisories": list(final_gate_status.get("advisories", [])),
                    "loss_gate_spike_ratio": float(final_gate_status.get("spike_ratio", 0.0)),
                    "best_fixed_val_loss": float(self.best_fixed_val_loss if self.best_fixed_val_loss is not None else float("nan")),
                    "final_fixed_val_loss": float(final_fixed_val_loss),
                    "config_path": self.cfg.config_path,
                    "config_hash": self.cfg.config_hash,
                },
            )
            LOGGER.info(
                "[Stage1][%s] Branch finished at %s (duration_seconds=%.1f global_step=%s micro_step=%s final_branch_dir=%s final_eval_bundle_dir=%s)",
                self.branch,
                _isoformat_local(finished_at),
                duration_seconds,
                self.global_step,
                self.micro_step,
                final_branch_dir,
                final_bundle,
            )
        self._release_runtime()
        return BranchTrainResult(
            branch=self.branch,
            final_branch_dir=str(final_branch_dir),
            final_eval_bundle_dir=str(final_bundle),
            output_dir=str(self.output_dir),
            started_at=_isoformat_local(started_at),
            finished_at=_isoformat_local(finished_at),
            duration_seconds=duration_seconds,
            global_step=self.global_step,
            micro_step=self.micro_step,
        )

    def _timing_sync(self) -> None:
        if (
            self.timing_enabled
            and self.timing_cuda_sync
            and self.accelerator.device.type == "cuda"
            and torch.cuda.is_available()
        ):
            torch.cuda.synchronize(self.accelerator.device)

    def _timing_start(self) -> float:
        self._timing_sync()
        return time.perf_counter()

    def _timing_elapsed(self, start: float) -> float:
        self._timing_sync()
        return max(time.perf_counter() - start, 0.0)

    def _log_timing(self, epoch_index: int, metrics: dict[str, float]) -> None:
        if not self.timing_enabled or not self.accelerator.is_main_process:
            return
        if self.micro_step % self.timing_log_every != 0:
            return

        keys = (
            "batch_to_device",
            "encode_video",
            "encode_text",
            "prepare_y",
            "prepare_control_signal",
            "noise_target",
            "student_forward",
            "loss",
            "training_step",
            "backward",
            "clip_grad",
            "optimizer_step",
            "scheduler_step",
            "zero_grad",
            "total_micro",
        )
        timing_parts = []
        for key in keys:
            value = metrics.get(f"timing_{key}_sec")
            if value is not None:
                timing_parts.append(f"{key}={float(value):.3f}s")
        if not timing_parts:
            return
        LOGGER.info(
            "[Stage1][%s][timing] epoch=%s/%s micro_step=%s global_step=%s sync_gradients=%s %s",
            self.branch,
            epoch_index,
            self.cfg.num_epochs,
            self.micro_step,
            self.global_step,
            self.accelerator.sync_gradients,
            " ".join(timing_parts),
        )


    def _total_grad_norm(self) -> float:
        total = 0.0
        for parameter in self.model.parameters():
            grad = parameter.grad
            if grad is None:
                continue
            value = float(grad.detach().float().norm(2).item())
            total += value * value
        return math.sqrt(total)

    def _iter_lora_modules(self):
        unwrapped = self.accelerator.unwrap_model(self.model)
        for name, module in unwrapped.named_modules():
            if hasattr(module, "lora_A") and hasattr(module, "lora_B"):
                yield name, module, str(getattr(module, "_pc_lora_group", "unknown"))

    def _collect_lora_group_grad_norms(self) -> dict[str, float]:
        sums: dict[str, float] = {"camera_conditioning": 0.0, "self_attention": 0.0, "cross_attention": 0.0, "ffn": 0.0}
        nonzero: dict[str, int] = {key: 0 for key in sums}
        for _name, module, group in self._iter_lora_modules():
            group = group if group in sums else "unknown"
            sums.setdefault(group, 0.0)
            nonzero.setdefault(group, 0)
            for parameter in (module.lora_A.weight, module.lora_B.weight):
                grad = parameter.grad
                if grad is None:
                    continue
                value = float(grad.detach().float().norm(2).item())
                sums[group] += value * value
                if value > 0:
                    nonzero[group] += 1
        out: dict[str, float] = {}
        for group, value in sums.items():
            out[f"{group}_lora_grad_norm"] = math.sqrt(value)
            out[f"{group}_lora_grad_nonzero_tensors"] = float(nonzero.get(group, 0))
        return out

    def _lora_param_update_metrics(self) -> dict[str, float]:
        total = 0.0
        for _name, module, _group in self._iter_lora_modules():
            for parameter in (module.lora_A.weight, module.lora_B.weight):
                value = float(parameter.detach().float().norm(2).item())
                total += value * value
        norm = math.sqrt(total)
        prev = self._last_lora_param_norm
        self._last_lora_param_norm = norm
        return {"lora_parameter_norm": norm, "lora_update_norm": 0.0 if prev is None else abs(norm - prev)}

    def _record_and_write_metrics(self, epoch_index: int, metrics: dict[str, float]) -> dict[str, object]:
        loss = float(metrics.get("loss_fm_weighted", metrics.get("loss_fm", 0.0)))
        self.loss_history.append(loss)
        alpha20 = 2.0 / 21.0
        alpha100 = 2.0 / 101.0
        self.loss_ema20 = loss if self.loss_ema20 is None else alpha20 * loss + (1 - alpha20) * self.loss_ema20
        self.loss_ema100 = loss if self.loss_ema100 is None else alpha100 * loss + (1 - alpha100) * self.loss_ema100
        metrics["loss_ema20"] = float(self.loss_ema20)
        metrics["loss_ema100"] = float(self.loss_ema100)
        metrics["timestamp"] = time.time()
        metrics["branch"] = self.branch
        metrics["epoch"] = float(epoch_index)
        metrics["micro_step"] = float(self.micro_step)
        metrics["optimizer_step"] = float(self.global_step)
        metrics["samples_seen"] = float(self.global_step * max(self.accelerator.num_processes, 1))
        if torch.cuda.is_available() and self.accelerator.device.type == "cuda":
            metrics["gpu_memory_allocated_mb"] = float(torch.cuda.memory_allocated(self.accelerator.device) / 1024**2)
            metrics["gpu_memory_reserved_mb"] = float(torch.cuda.memory_reserved(self.accelerator.device) / 1024**2)
            metrics["gpu_memory_max_allocated_mb"] = float(torch.cuda.max_memory_allocated(self.accelerator.device) / 1024**2)
        if (
            self.cfg.val_every_optimizer_steps > 0
            and self.global_step > 0
            and self.global_step % self.cfg.val_every_optimizer_steps == 0
        ):
            fixed_val_metrics = self._run_fixed_validation(epoch_index)
            metrics.update({f"fixed_val_{key}": value for key, value in fixed_val_metrics.items()})
        gate_status = self._loss_gate_status()
        metrics["loss_gate_status"] = str(gate_status["status"])
        metrics["loss_gate_reasons"] = ";".join(gate_status.get("reasons", []))
        metrics["loss_gate_advisories"] = ";".join(gate_status.get("advisories", []))
        metrics["loss_gate_spike_ratio"] = float(gate_status.get("spike_ratio", 0.0))
        if self.accelerator.is_main_process:
            self._write_metrics_row(metrics)
        return gate_status

    def _write_metrics_row(self, metrics: dict[str, float]) -> None:
        row = {key: (float(value) if isinstance(value, (int, float)) else value) for key, value in metrics.items()}
        self.metrics_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.metrics_jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        fields = sorted(row)
        write_header = self._metrics_csv_fields != fields or not self.metrics_csv_path.exists()
        self._metrics_csv_fields = fields
        with self.metrics_csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            if write_header:
                writer.writeheader()
            writer.writerow({key: row.get(key, "") for key in fields})

    def _write_fixed_val_row(self, metrics: dict[str, float]) -> None:
        row = {key: (float(value) if isinstance(value, (int, float)) else value) for key, value in metrics.items()}
        self.fixed_val_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.fixed_val_jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        fields = sorted(row)
        write_header = self._fixed_val_csv_fields != fields or not self.fixed_val_csv_path.exists()
        self._fixed_val_csv_fields = fields
        with self.fixed_val_csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            if write_header:
                writer.writeheader()
            writer.writerow({key: row.get(key, "") for key in fields})

    def _loss_gate_status(self) -> dict[str, object]:
        """Return loss-normal gate status with blocking and advisory reasons.

        Sigma-weighted flow-matching loss can have legitimate single-step spikes,
        especially across mixed timestep bands. Spike statistics are still logged,
        but once fixed validation is finite and stable they should not be the sole
        reason to block a branch at target or hard-max steps.
        """
        blocking_reasons: list[str] = []
        advisory_reasons: list[str] = []
        min_steps = int(self.branch_limits.get("resolved_min_optimizer_steps", 0))
        if self.global_step < min_steps:
            blocking_reasons.append("below_min_steps")
        recent = self.loss_history[-200:]
        if any(not math.isfinite(v) for v in recent):
            blocking_reasons.append("nonfinite_loss")
        spike_ratio = 0.0
        if len(recent) >= 20:
            sorted_recent = sorted(recent)
            median = sorted_recent[len(sorted_recent) // 2]
            if median > 0:
                spikes = sum(v > 5.0 * median for v in recent)
                spike_ratio = float(spikes / len(recent))
                if spike_ratio >= 0.01:
                    advisory_reasons.append("spike_ratio_high")
                    if self.global_step < min_steps or not self.fixed_val_history:
                        blocking_reasons.append("spike_ratio_high")
        if self.loss_ema100 is not None and not math.isfinite(self.loss_ema100):
            blocking_reasons.append("ema100_nonfinite")
        if self.cfg.val_every_optimizer_steps > 0 and self.global_step >= self.cfg.val_every_optimizer_steps:
            if not self.fixed_val_history:
                blocking_reasons.append("fixed_val_missing")
            elif any(not math.isfinite(v) for v in self.fixed_val_history[-3:]):
                blocking_reasons.append("fixed_val_nonfinite")
            elif self.best_fixed_val_loss is not None and len(self.fixed_val_history) >= 3:
                recent_val = self.fixed_val_history[-3:]
                if all(v > self.best_fixed_val_loss * 1.10 for v in recent_val):
                    blocking_reasons.append("fixed_val_three_worse_than_best_10pct")
        status = "PASS" if not blocking_reasons else "WAIT"
        return {
            "status": status,
            "reasons": blocking_reasons,
            "advisories": advisory_reasons,
            "spike_ratio": spike_ratio,
        }

    def _should_stop_branch(self, gate_status: dict[str, object]) -> bool:
        target = int(self.branch_limits.get("resolved_target_optimizer_steps", self.total_optimizer_steps))
        hard_max = int(self.branch_limits.get("resolved_hard_max_optimizer_steps", target))
        if self.global_step >= hard_max:
            return True
        if self.global_step >= target and gate_status.get("status") == "PASS":
            return True
        return False

    def training_step(self, batch: dict[str, Any]) -> tuple[torch.Tensor, dict[str, float]]:
        timings: dict[str, float] = {}
        batch_to_device_start = self._timing_start()
        video = batch["video"].to(self.accelerator.device)
        timings["batch_to_device"] = self._timing_elapsed(batch_to_device_start)
        poses = batch["poses"]
        actions = batch.get("actions")
        intrinsics = batch["intrinsics"]
        prompt = batch["prompt"]
        height, width = int(video.shape[2]), int(video.shape[3])
        source_height = int(batch.get("source_height", height))
        source_width = int(batch.get("source_width", width))

        with torch.no_grad():
            encode_video_start = self._timing_start()
            video_latent = self.helper.encode_video(video)
            timings["encode_video"] = self._timing_elapsed(encode_video_start)

            encode_text_start = self._timing_start()
            context = self.helper.encode_text(prompt)
            timings["encode_text"] = self._timing_elapsed(encode_text_start)

            prepare_y_start = self._timing_start()
            y = self.helper.prepare_y(video, video_latent)
            timings["prepare_y"] = self._timing_elapsed(prepare_y_start)

            lat_f, lat_h, lat_w = video_latent.shape[1], video_latent.shape[2], video_latent.shape[3]
            seq_len = lat_f * lat_h * lat_w // (self.helper.patch_size[1] * self.helper.patch_size[2])
            prepare_control_start = self._timing_start()
            dit_cond = self.helper.prepare_control_signal(
                poses,
                actions,
                intrinsics,
                height,
                width,
                lat_f,
                lat_h,
                lat_w,
                control_type=self.cfg.control_type,
                source_height=source_height,
                source_width=source_width,
            )
            timings["prepare_control_signal"] = self._timing_elapsed(prepare_control_start)

            noise_target_start = self._timing_start()
            timestep_sample = self.helper.sample_timestep(self.branch)
            noise = torch.randn_like(video_latent)
            noisy_latent = (1.0 - timestep_sample.sigma) * video_latent + timestep_sample.sigma * noise
            target = noise - video_latent
            timings["noise_target"] = self._timing_elapsed(noise_target_start)

        device_type = self.accelerator.device.type
        if os.environ.get("PC_STAGE1_FORCE_FP32", "").strip().lower() in {"1", "true", "yes", "on"}:
            autocast_ctx = torch.autocast(device_type=device_type, enabled=False)
        else:
            autocast_ctx = (
                torch.amp.autocast(device_type=device_type, dtype=resolve_stage1_low_precision_dtype())
                if device_type == "cuda"
                else torch.autocast(device_type=device_type, enabled=False)
            )
        with autocast_ctx:
            student_forward_start = self._timing_start()
            pred = self.model(
                [noisy_latent],
                t=timestep_sample.timestep,
                context=context,
                seq_len=seq_len,
                y=[y],
                dit_cond_dict=dit_cond,
            )[0]
            timings["student_forward"] = self._timing_elapsed(student_forward_start)
        loss_start = self._timing_start()
        pred_rest = pred[:, 1:]
        target_rest = target[:, 1:]
        loss_unweighted = F.mse_loss(pred_rest.float(), target_rest.float())
        loss_fm = loss_unweighted * timestep_sample.weight
        timings["loss"] = self._timing_elapsed(loss_start)
        timestep_value = timestep_sample.timestep
        try:
            timestep_float = float(timestep_value.detach().flatten()[0].item())
        except Exception:
            timestep_float = float(timestep_value)
        metrics = {
            "loss_fm": float(loss_fm.detach().item()),
            "loss_fm_weighted": float(loss_fm.detach().item()),
            "loss_fm_unweighted": float(loss_unweighted.detach().item()),
            "sample_sigma": float(timestep_sample.sigma),
            "sample_timestep": timestep_float,
            "timestep_weight": float(timestep_sample.weight),
        }
        for key, value in timings.items():
            metrics[f"timing_{key}_sec"] = float(value)
        return loss_fm, metrics

    def _run_fixed_validation(self, epoch_index: int) -> dict[str, float]:
        if self.val_loader is None:
            summary = {
                "available": 0.0,
                "sample_count": 0.0,
                "loss_fm_weighted": float("nan"),
                "loss_fm_unweighted": float("nan"),
                "sample_sigma_mean": float("nan"),
                "sample_timestep_mean": float("nan"),
            }
            self.fixed_val_history.append(float("nan"))
            if self.accelerator.is_main_process:
                self._write_fixed_val_row(
                    {
                        "timestamp": time.time(),
                        "branch": self.branch,
                        "epoch": float(epoch_index),
                        "optimizer_step": float(self.global_step),
                        **summary,
                    }
                )
            return summary

        was_training = bool(getattr(self.model, "training", False))
        self.model.eval()
        local_weighted = 0.0
        local_unweighted = 0.0
        local_sigma = 0.0
        local_timestep = 0.0
        local_count = 0.0
        local_finite = 1.0
        with torch.no_grad():
            for local_index, batch in enumerate(self.val_loader):
                distributed_index = int(local_index * max(self.accelerator.num_processes, 1) + self.accelerator.process_index)
                _loss, metrics = self._forward_loss(
                    batch,
                    fixed_validation=True,
                    validation_index=distributed_index,
                )
                weighted = float(metrics["loss_fm_weighted"])
                unweighted = float(metrics["loss_fm_unweighted"])
                sigma = float(metrics["sample_sigma"])
                timestep = float(metrics["sample_timestep"])
                if not all(math.isfinite(v) for v in (weighted, unweighted, sigma, timestep)):
                    local_finite = 0.0
                local_weighted += weighted
                local_unweighted += unweighted
                local_sigma += sigma
                local_timestep += timestep
                local_count += 1.0
        if was_training:
            self.model.train()
        values = torch.tensor(
            [local_weighted, local_unweighted, local_sigma, local_timestep, local_count, local_finite],
            device=self.accelerator.device,
            dtype=torch.float64,
        )
        reduced = self.accelerator.reduce(values, reduction="sum")
        count = max(float(reduced[4].item()), 1.0)
        finite_count = float(reduced[5].item())
        summary = {
            "available": 1.0,
            "sample_count": count,
            "loss_fm_weighted": float(reduced[0].item() / count),
            "loss_fm_unweighted": float(reduced[1].item() / count),
            "sample_sigma_mean": float(reduced[2].item() / count),
            "sample_timestep_mean": float(reduced[3].item() / count),
            "all_finite": float(finite_count >= max(self.accelerator.num_processes, 1)),
        }
        self.fixed_val_history.append(float(summary["loss_fm_weighted"]))
        if math.isfinite(summary["loss_fm_weighted"]):
            self.best_fixed_val_loss = (
                float(summary["loss_fm_weighted"])
                if self.best_fixed_val_loss is None
                else min(self.best_fixed_val_loss, float(summary["loss_fm_weighted"]))
            )
        summary["best_loss_fm_weighted"] = float(
            self.best_fixed_val_loss if self.best_fixed_val_loss is not None else float("nan")
        )
        if self.accelerator.is_main_process:
            row = {
                "timestamp": time.time(),
                "branch": self.branch,
                "epoch": float(epoch_index),
                "optimizer_step": float(self.global_step),
                **summary,
            }
            self._write_fixed_val_row(row)
            LOGGER.info(
                "[Stage1][%s] fixed-val step=%s samples=%s loss=%.6f unweighted=%.6f best=%.6f sigma=%.4f timestep=%.2f finite=%s",
                self.branch,
                self.global_step,
                int(count),
                float(summary["loss_fm_weighted"]),
                float(summary["loss_fm_unweighted"]),
                float(summary["best_loss_fm_weighted"]),
                float(summary["sample_sigma_mean"]),
                float(summary["sample_timestep_mean"]),
                bool(summary["all_finite"]),
            )
        return summary

    def _fixed_timestep_sample(self, validation_index: int) -> TimestepSample:
        if self.branch in {"high", "high_only"}:
            indices = self.helper.high_noise_indices
            weights = self.helper.high_noise_weights
        else:
            indices = self.helper.low_noise_indices
            weights = self.helper.low_noise_weights
        if len(indices) <= 0:
            return self.helper.sample_timestep(self.branch)
        count = max(int(self.cfg.fixed_val_sample_count), 1)
        slot = int(validation_index) % count
        position = int(round(slot * max(len(indices) - 1, 0) / max(count - 1, 1)))
        position = min(max(position, 0), len(indices) - 1)
        idx = int(indices[position].item())
        sigma = float(self.helper.sigmas[idx].item())
        timestep = self.helper.timesteps_schedule[idx].to(self.accelerator.device).unsqueeze(0)
        weight = float(weights[position].item())
        return TimestepSample(
            index=idx,
            sigma=sigma,
            timestep=timestep,
            weight=weight,
            branch=self.helper.branch_for_timestep_index(idx),
        )

    def _forward_loss(
        self,
        batch: dict[str, Any],
        *,
        fixed_validation: bool = False,
        validation_index: int = 0,
    ) -> tuple[torch.Tensor, dict[str, float]]:
        timings: dict[str, float] = {}
        batch_to_device_start = self._timing_start()
        video = batch["video"].to(self.accelerator.device)
        timings["batch_to_device"] = self._timing_elapsed(batch_to_device_start)
        poses = batch["poses"]
        actions = batch.get("actions")
        intrinsics = batch["intrinsics"]
        prompt = batch["prompt"]
        height, width = int(video.shape[2]), int(video.shape[3])
        source_height = int(batch.get("source_height", height))
        source_width = int(batch.get("source_width", width))

        with torch.no_grad():
            encode_video_start = self._timing_start()
            video_latent = self.helper.encode_video(video)
            timings["encode_video"] = self._timing_elapsed(encode_video_start)

            encode_text_start = self._timing_start()
            context = self.helper.encode_text(prompt)
            timings["encode_text"] = self._timing_elapsed(encode_text_start)

            prepare_y_start = self._timing_start()
            y = self.helper.prepare_y(video, video_latent)
            timings["prepare_y"] = self._timing_elapsed(prepare_y_start)

            lat_f, lat_h, lat_w = video_latent.shape[1], video_latent.shape[2], video_latent.shape[3]
            seq_len = lat_f * lat_h * lat_w // (self.helper.patch_size[1] * self.helper.patch_size[2])
            prepare_control_start = self._timing_start()
            dit_cond = self.helper.prepare_control_signal(
                poses,
                actions,
                intrinsics,
                height,
                width,
                lat_f,
                lat_h,
                lat_w,
                control_type=self.cfg.control_type,
                source_height=source_height,
                source_width=source_width,
            )
            timings["prepare_control_signal"] = self._timing_elapsed(prepare_control_start)

            noise_target_start = self._timing_start()
            timestep_sample = (
                self._fixed_timestep_sample(validation_index)
                if fixed_validation
                else self.helper.sample_timestep(self.branch)
            )
            if fixed_validation:
                generator = torch.Generator(device=video_latent.device)
                generator.manual_seed(
                    fixed_validation_noise_seed(
                        base_seed=int(self.cfg.seed),
                        branch=self.branch,
                        validation_index=int(validation_index),
                        sample_id=batch.get("sample_id", batch.get("clip_id", "")),
                    )
                )
                noise = torch.randn(
                    video_latent.shape,
                    device=video_latent.device,
                    dtype=video_latent.dtype,
                    generator=generator,
                )
            else:
                noise = torch.randn_like(video_latent)
            noisy_latent = (1.0 - timestep_sample.sigma) * video_latent + timestep_sample.sigma * noise
            target = noise - video_latent
            timings["noise_target"] = self._timing_elapsed(noise_target_start)

        device_type = self.accelerator.device.type
        if os.environ.get("PC_STAGE1_FORCE_FP32", "").strip().lower() in {"1", "true", "yes", "on"}:
            autocast_ctx = torch.autocast(device_type=device_type, enabled=False)
        else:
            autocast_ctx = (
                torch.amp.autocast(device_type=device_type, dtype=resolve_stage1_low_precision_dtype())
                if device_type == "cuda"
                else torch.autocast(device_type=device_type, enabled=False)
            )
        with autocast_ctx:
            student_forward_start = self._timing_start()
            pred = self.model(
                [noisy_latent],
                t=timestep_sample.timestep,
                context=context,
                seq_len=seq_len,
                y=[y],
                dit_cond_dict=dit_cond,
            )[0]
            timings["student_forward"] = self._timing_elapsed(student_forward_start)
        loss_start = self._timing_start()
        pred_rest = pred[:, 1:]
        target_rest = target[:, 1:]
        loss_unweighted = F.mse_loss(pred_rest.float(), target_rest.float())
        loss_fm = loss_unweighted * timestep_sample.weight
        timings["loss"] = self._timing_elapsed(loss_start)
        timestep_value = timestep_sample.timestep
        try:
            timestep_float = float(timestep_value.detach().flatten()[0].item())
        except Exception:
            timestep_float = float(timestep_value)
        metrics = {
            "loss_fm": float(loss_fm.detach().item()),
            "loss_fm_weighted": float(loss_fm.detach().item()),
            "loss_fm_unweighted": float(loss_unweighted.detach().item()),
            "sample_sigma": float(timestep_sample.sigma),
            "sample_timestep": timestep_float,
            "timestep_weight": float(timestep_sample.weight),
        }
        for key, value in timings.items():
            metrics[f"timing_{key}_sec"] = float(value)
        return loss_fm, metrics

    def _student_checkpoint_use_reentrant(self) -> bool:
        if self.cfg.student_checkpoint_use_reentrant is not None:
            return bool(self.cfg.student_checkpoint_use_reentrant)
        if (
            self.accelerator.distributed_type in {DistributedType.MULTI_GPU, DistributedType.DEEPSPEED}
            and self.cfg.student_tuning_mode == "lora"
        ):
            return False
        return self.cfg.student_tuning_mode == "lora"

    def _save_branch_checkpoint(self, *, tag: str) -> Path:
        save_root = self.output_dir / "branches" / tag
        save_root.mkdir(parents=True, exist_ok=True)
        if self.cfg.model_family == "lingbot_world_fast":
            branch_dir = save_root / "fast_stageA_high_noise_adapter"
        else:
            branch_dir = save_root / ("low_noise_model" if self.branch == "low" else "high_noise_model")
        self.accelerator.wait_for_everyone()
        if self.accelerator.is_main_process:
            unwrapped = self.accelerator.unwrap_model(self.model)
            ensure_dir(branch_dir)
            adapter_state = {
                key: value.detach().cpu()
                for key, value in unwrapped.named_parameters()
                if ".lora_A.weight" in key or ".lora_B.weight" in key
            }
            torch.save(adapter_state, branch_dir / "adapter_state.pt")
            training_state = {
                "branch": self.branch,
                "tag": tag,
                "global_step": self.global_step,
                "micro_step": self.micro_step,
                "optimizer_state_dict": self.optimizer.state_dict() if self.optimizer is not None else None,
                "scheduler_state_dict": self.scheduler.state_dict() if self.scheduler is not None else None,
                "torch_rng_state": torch.get_rng_state(),
                "cuda_rng_state_all": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
                "branch_limits": dict(self.branch_limits),
            }
            torch.save(training_state, branch_dir / "training_state.pt")
            lora_config = getattr(unwrapped, "_pc_lora_config", {})
            lora_report = getattr(unwrapped, "_pc_lora_target_report", None)
            report_payload = {}
            if lora_report is not None:
                report_payload = {
                    "selected_by_group": {
                        group: list(names) for group, names in lora_report.selected_by_group.items()
                    },
                    "selected_count": int(lora_report.selected_count),
                    "trainable_params": int(lora_report.trainable_params),
                    "total_params": int(lora_report.total_params),
                    "unclassified_linear_count": int(lora_report.unclassified_linear_count),
                    "unclassified_linear_examples": list(lora_report.unclassified_linear_examples),
                }
            write_json(
                branch_dir / "adapter_metadata.json",
                {
                    "branch": self.branch,
                    "tag": tag,
                    "global_step": self.global_step,
                    "micro_step": self.micro_step,
                    "adapter_tensor_count": len(adapter_state),
                    "lora_config": lora_config,
                    "lora_target_report": report_payload,
                    "adapter_only": True,
                    "full_model_saved": False,
                    "full_model_weights_file": None,
                    "optimizer_state_file": "training_state.pt",
                    "scheduler_state_file": "training_state.pt",
                },
            )
            if hasattr(unwrapped, "save_config"):
                unwrapped.save_config(branch_dir)
        self.accelerator.wait_for_everyone()
        return save_root

    def _run_epoch_eval(self, epoch: int, branch_checkpoint_root: Path) -> str:
        bundle_dir = materialize_eval_checkpoint_bundle(
            ft_ckpt_dir=branch_checkpoint_root,
            output_root=self.output_dir / "eval_bundles",
            experiment_name=f"{self.cfg.experiment_name}_{self.branch}_epoch_{epoch}",
            companion_ckpt_dir=self.companion_checkpoint_dir,
        )
        run_stage1_videophy2_eval(
            self.cfg.videophy2_eval,
            bundle_dir=bundle_dir,
            output_dir=self.output_dir,
            experiment_name=self.cfg.experiment_name,
            epoch=epoch,
            branch=self.branch,
        )
        return str(bundle_dir)

    def _release_runtime(self) -> None:
        self.helper.release_runtime_components()
        self.model = None
        self.optimizer = None
        self.scheduler = None
        self.train_loader = None
        self.val_loader = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
