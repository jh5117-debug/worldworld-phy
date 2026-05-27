# Legacy Code Reuse Plan

## Directly Reused
- `src/physical_consistency/trainers/stage1_components.py`: LingBotStage1Helper, WanModel loading, VAE/T5 encode, LoRA insertion, camera Plucker control, optimizer utilities.
- `src/physical_consistency/stages/stage1_physinone_cam/*`: camera-only PhysInOne dataset and Stage1 branch runner.
- `src/physical_consistency/losses/trd.py`: VideoREPA-style Token Relation Distillation loss.
- `src/physical_consistency/teachers/vjepa2.py` and `videomaev2.py`: frozen SSL video teacher wrappers.
- `src/physical_consistency/eval/lingbot_fullval.py` and `lingbot_generate.py`: sharded LingBot generation / eval process model.

## Convert to Cam-Only
- Use `control_type=cam` everywhere in Cam-PhysGeo-DPO training/eval.
- Keep `action.npy` only as dummy zeros in converted samples when legacy LingBot file checks require it.
- Replace VideoPhy2/old action metrics as main conclusions with BRC/CAF/FG-ID/ODS/PES/RCS/Freeze/Quality.

## Stage Entrypoints
- Stage1: `cam_physgeo.training.train_stage1_warmup` wraps the legacy Stage1 runner and injects LingBot Base, LingBot code root and cam-only control.
- Stage2: `cam_physgeo.dpo.*` builds anchored pairs; next implementation step is a LingBot diffusion logprob adapter using the same helper encode/control path.
- Stage3: remains gated until anchored DPO produces acceptable pass@K and quality thresholds.
- Eval: `cam_physgeo.eval.run_inference` prints the exact Base/Fast/LingBot code paths and keeps long eval launch explicit.

## Deprecated Mainline
- Old CSGO/action scripts, configs and source modules remain only as legacy references; they are not data sources or benchmark mainline.
- VideoPhy2 remains an auxiliary historical metric only, not the primary benchmark.

## File-Level Modification Plan
- `cam_physgeo/training/model_loading.py`: maintain H20 LingBot path audit and guarded legacy helper loading.
- `cam_physgeo/data/*`: continue improving scanner key inference and conversion to LingBot-compatible camera samples.
- `cam_physgeo/rewards/*`: replace proxy scores with RAFT/depth/DINO/V-JEPA backends as load tests stabilize.
- `cam_physgeo/training/train_stage2_anchored_dpo.py`: add real LingBot chosen/rejected diffusion loss adapter before long training.
