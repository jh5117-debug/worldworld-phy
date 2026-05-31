# DiT Action Modulation Probe Report

## Result

- Runtime full-DiT hook: not run in this no-generation probe.
- Source-level DiT modulation path: found.
- Camera variants change the LingBot camera/control tensor before DiT.
- Dummy action remains zero and `use_action=false` remains the sample metadata setting.

## Paths

- Generator: `local_assets/third_party/lingbot_world/wan/image2video_fast.py`
- Fast DiT: `local_assets/third_party/lingbot_world/wan/modules/model_fast.py`
- Probe output: `local_assets/reports/smoke/dit_modulation_probe/`

## Source Evidence

The source-level scan found:

- `image2video_fast.py`: `get_plucker_embeddings(c2ws_infer, Ks, h, w, only_rays_d=...)`
- `image2video_fast.py`: `c2ws_plucker_emb` is chunked into `dit_cond_dict`.
- `model_fast.py`: `cam_injector_layer1`, `cam_injector_layer2`, `cam_scale_layer`, and `cam_shift_layer`.
- `model_fast.py`: DiT block checks `dit_cond_dict["c2ws_plucker_emb"]` and applies camera scale/shift to hidden states.

The probe did not load full Fast weights for a runtime forward hook, so the exact runtime scale/shift tensor was not captured. This is enough to confirm the intended code path, but not enough to prove video-level effect.

## Embedding / Control Tensor Summary

Sample: `physion_movingcam_07abddf5748b`

- Control tensor shape: `[1, 448, 2, 8, 14]`
- Plucker tensor shape: `[1, 192, 2, 8, 14]`
- Dummy action tensor shape: `[1, 256, 2, 8, 14]`
- Dummy action norm: `0.0`

Pairwise control tensor differences:

- correct vs frozen: L2 `12.8458`, cosine `0.9942`
- correct vs reversed: L2 `25.6122`, cosine `0.9771`
- correct vs exaggerated_yaw: L2 `83.0763`, cosine `0.7593`
- frozen vs zero_motion: L2 `0.0`, cosine `~1.0`

## Conclusion

Gate C is still partial: camera condition reaches the camera/control tensor and source-level DiT modulation path, but video-level behavior is not yet proven.
