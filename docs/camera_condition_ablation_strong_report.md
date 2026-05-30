# Strong Camera Condition Ablation Report

## Status

Strong ablation was attempted with:

```text
repeat_correct_A repeat_correct_B correct frozen reversed exaggerated_yaw
```

The first autoloop attempt at `8 frames / 480x832` failed with an outer timeout and OOM pressure on GPU 6/7. A fallback run used `4 frames / 256x448` with the same six variants.

## Outputs

- Output root: `local_assets/data/physion/processed/rollouts/camera_ablation_strong_smoke`
- Manual fallback log: `local_assets/reports/smoke/camera_reward_manual_ablation/run.log`
- Autoloop run dir: `local_assets/reports/smoke/camera_reward_debug_autoloop_20260530_234454`

Only one variant produced a `generated.mp4`:

```text
local_assets/data/physion/processed/rollouts/camera_ablation_strong_smoke/physion_movingcam_07abddf5748b/correct/physion_movingcam_07abddf5748b/generated.mp4
```

The other variants wrote condition debug summaries but did not produce video. Their subprocesses returned nonzero status, mostly after long model initialization/generation attempts under constrained GPU availability.

## Metrics

The requested stochastic baseline could not be computed because `repeat_correct_A` and `repeat_correct_B` did not generate videos. Correct-vs-frozen, correct-vs-reversed, and correct-vs-exaggerated metrics also could not be computed because those variants did not produce videos.

## Runtime Evidence

Runtime debug does show:

- `action_path` is in the Fast pipeline signature.
- The condition directory contains `poses.npy`, converted `intrinsics.npy`, and dummy `action.npy`.
- `poses.npy` and converted `intrinsics.npy` are nonzero.
- dummy `action.npy` has norm `0.0`.

## Conclusion

Gate C remains `not proven`. The code path passes camera tensors into LingBot-Fast through `action_path`, and LingBot-Fast has source code to convert that into `c2ws_plucker_emb`, but the generation-level ablation did not produce enough successful variants to show a camera-dependent output difference above stochastic baseline.

Next minimal action: add a direct instrumentation hook inside `wan/image2video_fast.py` around `get_plucker_embeddings` to dump `c2ws_plucker_emb` shape/norm per variant, and rerun at most `correct/frozen/reversed` after GPU 6/7 are free.
