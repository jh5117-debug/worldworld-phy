# Current Status Update - 2026-06-24

- New active branch: `research/quant-small-lora-dpo-probe-20260624` from `63d1b93`.
- Broad-LoRA is no longer the main route for candidate generation because generation quality was FAILED_OR_MIXED despite fixed-val loss improvement.
- Current focus: Quantitative Benchmark v1, small/low-rank LoRA scope sweep, Reward Calibration v2, and anchored DPO probe.
- GPU0-7 are authorized for this round; no full-data long StageA, no StageB, no GRPO, and no large-scale DPO.
- DPO data strategy: GT winners plus quality-bounded hard-negative losers selected from Original Fast, last-week camera-only tiny LoRA, small-LoRA sweep candidates, controlled corruptions, and broad-LoRA only if it passes loser quality floor.
- Diagnosis: last week's better visual stability came from the extremely constrained camera-only tiny LoRA; this week's broad-LoRA touched too much of the DiT and optimized loss without preserving generation quality. See `docs/broad_lora_vs_camera_only_diagnosis.md`.

---

# Project Refocus

We no longer define this project as fine-tuning LingBot with CSGO/action data. The current negative results indicate that game/navigation data can provide camera control, but it does not provide clean object-level physical supervision. PhyInOne provides physical events, but ordinary SFT does not explicitly optimize persistent world consistency, which leads to background drift, object deformation, and reobserve failure. Therefore the task is redefined as camera-conditioned physical world consistency alignment.

Given an initial image or prefix video, prompt, camera poses, and intrinsics, LingBot should generate a persistent physical world. The static background should follow rigid geometry induced by the input camera trajectory. Dynamic foreground objects should preserve identity and shape. Physical events should follow the regularities of drop, collision, roll, containment, and support. When the camera turns away and returns, the scene and objects should remain consistent.

Methodologically, we borrow GeoFlow's geometry reward idea but do not copy the setting. GeoFlow estimates camera, depth, and flow from generated T2V videos. In the LingBot plus PhyInOne plus moving-camera synthetic extension data setting, we have condition camera poses, intrinsics, simulator depth, ID masks, and event metadata. This lets us extend the reward from internal video geometric self-consistency to known-camera, simulator-grounded physical-geometric consistency.

We also borrow VideoREPA's TRD as an auxiliary physical spatiotemporal representation loss. TRD can help temporal relation learning, but it cannot by itself constrain camera following, background rigid geometry, or reobserve consistency.

We do not start from pure self-rollout DPO. LingBot-Fast may initially produce poor samples in the target domain, so the top rollout can still be a bad sample. We use bootstrapped anchored DPO: clean GT, teacher rollouts, corrupted negatives, and bad Fast rollouts first pull the model into a usable distribution; self-rollout DPO is added later after reward and human-quality thresholds are met.

Innovation points:

1. Shift from action/game world modeling to camera-conditioned physical world consistency.
2. Use PhyInOne plus moving-camera synthetic extension data for camera/depth/ID/event supervision.
3. Convert GeoFlow-style reward into a known-camera, simulator-grounded reward.
4. Add physical event reward and reobserve consistency reward.
5. Use bootstrapped anchored DPO instead of ordinary SFT or immediate self-rollout DPO.
6. Build a LingBot-specific I2V/V2V camera-conditioned benchmark.
