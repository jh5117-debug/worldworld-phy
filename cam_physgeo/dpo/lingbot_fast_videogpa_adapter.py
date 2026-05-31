from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from cam_physgeo.training.model_loading import inspect_checkpoint, resolve_model_paths
from cam_physgeo.utils.io import load_yaml, write_json


@dataclass
class AdapterStatus:
    name: str
    implemented: bool
    dependency: str
    input_shape: str
    output_shape: str
    supports_camera_poses: bool
    supports_intrinsics: bool
    uses_dummy_action: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class LingBotFastVideoGPAAdapter:
    """Minimal non-training adapter contract between LingBot-Fast and VideoGPA.

    This class intentionally implements only path inspection and batch-shape dry-run.
    Real model loading, latent encoding, and DPO energy/logprob computation must be
    wired to LingBot-Fast before any training command is allowed.
    """

    def __init__(self, config_path: str = "configs/cam_physgeo/paths.yaml"):
        self.config_path = config_path
        self.paths_cfg = load_yaml(config_path)
        self.paths = resolve_model_paths(self.paths_cfg)

    def load_model(self):
        raise NotImplementedError("Use WanI2VFast runtime bundle first; full VideoGPA policy-model loading is not implemented.")

    def load_policy_model(self):
        raise NotImplementedError("Policy loading for VideoGPA is not implemented. Reuse LingBot runtime loader only after the forward contract is known.")

    def load_reference_model(self):
        raise NotImplementedError("Frozen reference loading is not implemented. Do not start DPO before this is real.")

    def load_vae(self):
        raise NotImplementedError("LingBot/Wan VAE loading for VideoGPA latent encode is not implemented.")

    def encode_video_to_latent(self, video_path: str | Path):
        raise NotImplementedError("LingBot VAE latent encoding is not implemented for VideoGPA yet.")

    def encode_condition(self, sample_dir: str | Path) -> dict[str, Any]:
        sample_dir = Path(sample_dir)
        meta = _read_json(sample_dir / "metadata.json")
        prompt = (sample_dir / "prompt.txt").read_text(encoding="utf-8", errors="replace").strip() if (sample_dir / "prompt.txt").exists() else ""
        poses = np.load(sample_dir / "poses.npy", mmap_mode="r") if (sample_dir / "poses.npy").exists() else None
        intr = np.load(sample_dir / "intrinsics.npy", mmap_mode="r") if (sample_dir / "intrinsics.npy").exists() else None
        return {
            "sample_dir": str(sample_dir),
            "image": str(sample_dir / "image.jpg"),
            "prompt": prompt,
            "poses_shape": list(poses.shape) if poses is not None else None,
            "intrinsics_shape": list(intr.shape) if intr is not None else None,
            "metadata": meta,
            "use_action": bool(meta.get("use_action", False)),
            "dummy_action_exists": (sample_dir / "action.npy").exists(),
        }

    def prepare_winner_loser_batch(self, pair: dict[str, Any]) -> dict[str, Any]:
        cond = pair.get("condition") or pair.get("extra_condition") or {}
        videos = pair.get("videos") or []
        if "winner" in pair and "loser" in pair:
            videos = [pair["winner"], pair["loser"]]
        return {
            "prompt": pair.get("prompt") or pair.get("text_prompt"),
            "condition_keys": sorted(cond.keys()),
            "camera_pose_path": cond.get("poses"),
            "intrinsics_path": cond.get("intrinsics"),
            "winner_loser_video_count": len(videos),
            "video_paths": [v.get("video_path") or v.get("video") for v in videos],
            "batch_contract": {
                "winner_latent": "B,C,F,H,W after LingBot VAE encode (TODO)",
                "loser_latent": "B,C,F,H,W after LingBot VAE encode (TODO)",
                "condition": "image embedding + text tokens + camera Plucker embeddings",
                "same_noise_same_timestep": True,
            },
        }

    def collate_winner_loser_batch(self, pair: dict[str, Any]) -> dict[str, Any]:
        return self.prepare_winner_loser_batch(pair)

    def sample_same_noise_timestep(self, *args, **kwargs):
        raise NotImplementedError("Same-noise/same-timestep sampling must be wired to the LingBot scheduler before DPO dry-run.")

    def compute_dpo_energy_or_logprob(self, *args, **kwargs):
        raise NotImplementedError("No fake DPO energy/logprob. Wire LingBot denoising/velocity error first.")

    def save_lora_adapter(self, *args, **kwargs):
        raise NotImplementedError("LoRA save path belongs to the future training adapter.")

    def load_lora_adapter(self, *args, **kwargs):
        raise NotImplementedError("LoRA load path belongs to the future training adapter.")

    def status(self) -> dict[str, Any]:
        fast = inspect_checkpoint(self.paths["lingbot_fast"], label="LingBot-Fast")
        base = inspect_checkpoint(self.paths["lingbot_base"], label="LingBot-Base")
        methods = [
            AdapterStatus("load_policy_model", False, "wan.WanI2VFast + runtime symlink bundle", "paths/config", "policy model", True, True, False, "runtime inference exists separately; VideoGPA policy object not wired"),
            AdapterStatus("load_reference_model", False, "same as load_model", "paths/config", "frozen ref model", True, True, False, "required before DPO"),
            AdapterStatus("load_vae", False, "LingBot/Wan VAE", "paths/config", "VAE encoder/decoder", False, False, False, "required for real VideoGPA latent encode"),
            AdapterStatus("encode_video_to_latent", False, "LingBot Wan2_1_VAE", "mp4/video tensor", "latent B,C,F,H,W", False, False, False, "required for VideoGPA encode"),
            AdapterStatus("encode_condition", True, "cam-only sample files", "sample_dir", "metadata + shape dict", True, True, True, "shape dry-run only; dummy action is not a core condition"),
            AdapterStatus("collate_winner_loser_batch", True, "VideoGPA pair JSON", "pair dict", "batch contract dict", True, True, True, "shape/metadata dry-run only"),
            AdapterStatus("sample_same_noise_timestep", False, "LingBot scheduler", "batch size + latent shape", "noise tensor + timestep", False, False, False, "required before DPO energy comparison"),
            AdapterStatus("compute_dpo_energy_or_logprob", False, "LingBot forward/noise scheduler", "winner/loser latents + condition", "scalar energy/logprob delta", True, True, False, "must be real before any DPO train"),
        ]
        return {
            "paths": self.paths,
            "fast": fast.to_dict(),
            "base": base.to_dict(),
            "methods": [m.to_dict() for m in methods],
            "training_allowed": False,
            "reason": "DPO energy/logprob and latent encode are NotImplemented by design.",
        }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/cam_physgeo/paths.yaml")
    ap.add_argument("--sample", default="")
    ap.add_argument("--pair", default="")
    ap.add_argument("--out", default="docs/lingbot_fast_videogpa_minimal_adapter_plan.md")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    adapter = LingBotFastVideoGPAAdapter(args.config)
    status = adapter.status()
    if args.sample:
        status["condition_dry_run"] = adapter.encode_condition(args.sample)
    if args.pair:
        path = Path(args.pair)
        if path.suffix == ".jsonl":
            line = path.read_text(encoding="utf-8").splitlines()[0]
            pair = json.loads(line)
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
            pair = (payload.get("groups") or [payload])[0]
        status["batch_dry_run"] = adapter.prepare_winner_loser_batch(pair)
    write_plan(status, args.out)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


def write_plan(status: dict[str, Any], out: str | Path) -> None:
    lines = [
        "# LingBot-Fast VideoGPA Minimal Adapter Plan",
        "",
        "This document defines the minimum adapter surface. It is not a trainer and does not fake DPO logprobs.",
        "",
        "## Minimal Integration Path",
        "1. Keep VideoGPA official code unchanged.",
        "2. Export Physion clean/corrupt pairs as VideoGPA `groups` JSON.",
        "3. Use this adapter to preserve image/prompt/poses/intrinsics and prepare winner/loser batch metadata.",
        "4. Implement LingBot VAE latent encoding and camera-condition encoding in wrapper code.",
        "5. Collate winner/loser with the same sampled timestep and same noise before any DPO loss.",
        "6. Only after real `compute_dpo_energy_or_logprob` exists, call VideoGPA train logic through a wrapper.",
        "",
        "## Method Status",
    ]
    for m in status.get("methods", []):
        lines.append(f"- `{m['name']}`: implemented={m['implemented']}; dependency={m['dependency']}; input={m['input_shape']}; output={m['output_shape']}; camera={m['supports_camera_poses']}; intrinsics={m['supports_intrinsics']}; dummy_action={m['uses_dummy_action']}; notes={m['notes']}")
    lines.extend([
        "",
        "## Current Gate",
        f"- Training allowed: {status.get('training_allowed')}",
        f"- Reason: {status.get('reason')}",
        "",
        "If VideoGPA source changes become unavoidable, prefer a small wrapper or patch file over editing `local_assets/third_party/VideoGPA/official_repo` directly.",
        "",
        "## Training Forward Contract",
        "- Winner and loser must share prompt tokens, image condition, poses/intrinsics-derived Plucker control, timestep, and noise.",
        "- `use_action=false` remains part of metadata; dummy zero action is compatibility only and must not replace camera condition.",
        "- Reference model must be frozen and should reuse the same LingBot-Fast architecture without LoRA trainable layers.",
        "- LoRA should attach only to the policy DiT/control projection modules after a real energy/logprob path is validated.",
    ])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
