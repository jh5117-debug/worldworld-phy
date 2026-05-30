# Final Report: VideoGPA + LingBot-Fast Minimal Adapter

## 1. Server Status

- Hostname: `instance-afs92r3e`.
- Branch: `physion-videogpa-lingbotfast-minimal-adapter`.
- GPU 6/7 final check: idle at 1 MiB each after the timed smoke.
- Long training process from this work: none.
- Existing unrelated `accelerate` jobs were observed on other paths/GPUs and were not touched.
- The original project root remains dirty from earlier work; this pass used a clean auxiliary worktree and did not overwrite those files.

## 2. Current Project Status

- `local_assets` remains the runtime root for data, weights, third-party repos, outputs, and reports.
- Physion-only scope is preserved.
- LingBot-Fast remains the main model path.
- LingBot-Base is only used as a baseline and as the VAE/T5/tokenizer source for the Fast runtime bundle; it is not used as a teacher.
- `action.npy` is still dummy fallback only; metadata says `use_action=false`.

## 3. LingBot-Fast Actual Inference

- Dry-run: passed path/shard/sample/runtime-bundle checks.
- Actual short inference: failed by timeout.
- Attempted sample: `physion_movingcam_07abddf5748b`.
- Requested frames: 8; normalized to 9 for Wan `4n+1` requirement.
- Steps: 1 timestep index `[0]`.
- Output video: not created.
- Contact sheet: not created.
- Log: `local_assets/outputs/smoke/lingbot_fast_inference/physion_movingcam_07abddf5748b/inference_log.txt`.
- Failure: child process killed after 180 seconds before generation completed.
- Follow-up diagnosis: direct `LINGBOT_ENV/bin/python -u` probes show `torch` import works, `wan` import works, and the process stalls inside `WanI2VFast.__init__`. A narrower T5-only probe stalls at `T5EncoderModel(...)`, making Base T5/tokenizer/checkpoint initialization the first confirmed blocker.
- Code update: `cam_physgeo/eval/run_inference.py` now prefers direct unbuffered env Python over `conda run` and writes flushed runtime markers for torch import, Wan import, image loading, pipeline init, generate, and save. Future smoke logs should identify whether the stall remains at `pipeline_init_start`.
- Next file to investigate: LingBot T5 initialization/offload/cache path under `wan/modules/t5.py` and the Fast `WanI2VFast` constructor. This is not an action-conditioning failure.

## 4. Fast Zero-Shot Rollout

- Generated rollouts: 0.
- Reason: prerequisite 1-sample Fast inference failed.
- Rollout reward testing is blocked until actual Fast videos exist.

## 5. Reward On Real Fast Rollout

- Clean GT avg: not available.
- Fast rollout avg: not available.
- Clean > Fast win rate: not available.
- Reason: no Fast rollout videos were generated.
- `eval_fast_rollouts.py` was added and produced a missing-rollout report, but no valid pairs.

## 6. Feature Backend

- DINOv2: checkpoint missing; proxy visual feature fallback active.
- V-JEPA2: checkpoint path exists, but real forward was not run; proxy temporal feature fallback active.
- VideoMAE2: not present.
- Optical flow: assets exist, but RAFT/GMFlow/WAFT forward is not wired; frame-diff proxy active.
- `R_fg` / `R_reobs` use proxy visual signatures, not real DINO/V-JEPA forward.
- `R_bg` / `R_cam` use frame-diff proxy, not real rigid-flow residual.
- `score_video --require_feature_backend true` recorded `feature_backend_met=false`.

## 7. Reward Calibration Expanded

- Samples: 50.
- Comparisons: 300.
- Clean avg `R_total`: 0.1041.
- Corrupt avg `R_total`: 0.0449.
- Clean > corrupt win rate: 0.6033.
- Gate >= 0.85: failed.
- Per-corruption win rate: background drift 0.04, reobserve mismatch 0.06, freeze/object corruptions 0.88.
- Interpretation: current reward separates freeze/object corruptions but not geometry/reobserve corruptions at scale. Do not expand DPO training pairs yet.

## 8. VideoGPA Integration

- Repo: `local_assets/third_party/VideoGPA/official_repo`.
- Commit: `551e63a5c2c493962f1e1d090bfa8324bf18b694`.
- Inspected: README, `train/01_preference_pair.py`, `train/dataset.py`, `train/*/02_encode.py`, `train/*/03_train.py`.
- Pair JSON: readable and metadata-compatible; 51 groups.
- Encode smoke: did not run native latent encoding. It verified pair JSON, prompt, winner/loser videos, and camera metadata, then stopped honestly because LingBot-Fast VAE/condition adapter is missing.
- Camera condition is preserved in `extra_condition`.
- Do not edit official VideoGPA repo yet; keep adapter code under `cam_physgeo/dpo`.

## 9. LingBotFastVideoGPAAdapter

- Added: `cam_physgeo/dpo/lingbot_fast_videogpa_adapter.py`.
- Implemented: condition metadata shape dry-run and winner/loser batch contract dry-run.
- Not implemented by design: `load_model`, `load_reference_model`, `encode_video_to_latent`, `compute_dpo_energy_or_logprob`, LoRA save/load.
- Shape dry-run succeeded for one Physion sample and one VideoGPA pair.
- Real DPO training still needs LingBot VAE latent encoding, camera-condition tensor encoding, frozen reference loading, and real energy/logprob computation.

## 10. DPO Gate

Superseding update after the LingBot-Fast 1-sample inference autoloop:

- Gate A, Fast 1-sample actual inference: passed.
- Gate B, 3-10 Fast rollouts: being validated in the Fast rollout/reward smoke phase.
- Gate C, camera condition ablation: being validated with correct/frozen/reversed poses.
- Gate D, reward on real Fast failures: being validated after the small rollout set exists.
- Gate E, VideoGPA export + encode smoke: export passed earlier, but real encode is not allowed in the current phase.
- Gate F, adapter batch shape dry-run: partially passed for metadata only; no model/latent adapter yet.
- Gate G, real DPO energy/logprob: not implemented.

Conclusion: DPO remains disallowed. The next gate is small Fast rollout plus camera/reward audit, not VideoGPA encode or training.

## 11. Stage1 Warm-Up

- Dry-run: passed.
- Real warm-up: not launched.
- Recommendation: do not run Stage1 now; Fast inference, reward backend, and VideoGPA encode are higher priority.

## 12. GitHub

- Branch: `physion-videogpa-lingbotfast-minimal-adapter`.
- Latest diagnostic-code commit hash: `badb9e60d94318ee033a892f0ec3ca62ed489a4e`.
- Exact branch head after report metadata updates: use `git rev-parse HEAD`.
- Push status: successful.
- Large files: not staged; `local_assets` is ignored.

## 13. Next Steps

1. Finish the bounded Fast rollout/reward smoke: 3-10 rollouts, camera ablation, and reward-on-rollout.
2. If camera ablation shows no visible difference, repair the camera adapter before any VideoGPA work.
3. If reward-on-rollout is insensitive to visible failures, repair reward backends before pair expansion.
4. Wire real RAFT/GMFlow and DINO/V-JEPA forward before trusting geometry/reobserve reward at scale.
5. Only after rollout, camera, and reward gates are reasonable, attempt VideoGPA encode smoke.
6. Only after all gates pass, consider a tiny DPO training dry-run. Do not long-train.

## Camera / Reward Debug Addendum

- Gate A remains passed.
- Gate B is passed with 3 Fast rollout videos.
- Gate C is still not proven: camera tensors are passed through `action_path` and LingBot-Fast source has a `c2ws_plucker_emb` injection path, but strong ablation did not generate enough comparable variants.
- Gate D remains failed/provisional: raw reward ranks Fast above clean, and confidence-weighted reward still only gives clean a 1/3 win rate.
- Gate E, VideoGPA encode, is still blocked.
- DPO remains disallowed.

The next minimal action is not VideoGPA. First hook `get_plucker_embeddings` to confirm camera embedding differences, then repair `R_phys` and `P_freeze` backends.
