# Camera Condition Effect Minimal Report

## Attempt

Command target:

- Sample: `physion_movingcam_07abddf5748b`
- Variants: `repeat_correct_A`, `repeat_correct_B`, `frozen`, `exaggerated_yaw`
- Requested frames: `4`
- Steps: `1`
- Resolution: `256x448`
- GPU: `CUDA_VISIBLE_DEVICES=6,7`
- Output root: `local_assets/data/physion/processed/rollouts/camera_ablation_effect_minimal/`

## Result

No new valid ablation videos were generated.

The 4-frame setting is not valid for this LingBot-Fast path. The successful 1-sample smoke used 8 frames, while this minimal run reached `ready_to_generate` and then failed inside `wan/image2video_fast.py` because the latent temporal dimension became negative:

- `RuntimeError: Trying to create tensor with negative dimension -3`
- Location: `local_assets/third_party/lingbot_world/wan/image2video_fast.py:323`
- Context: `msk = torch.ones(1, F, lat_h, lat_w, device=self.device)`

One variant also encountered CUDA OOM during model transfer while another process held most of the visible GPU memory. This was a resource collision, not evidence about camera condition.

## Metrics

No pixel L1, SSIM, or optical-flow comparison was computed because no valid variant videos were produced.

## Conclusion

Video-level camera effect remains not proven. Embedding/control tensor differences are real, but the next video-level ablation should use a known-valid frame count, likely 8 frames, with a clean GPU allocation and no more than the minimal set of variants.
