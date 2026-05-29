# Current State After Fast Inference Success

- LingBot-Fast 1-sample actual inference has passed.
- Previous generated video exists at `local_assets/reports/smoke/fast_inference_autoloop_20260529_144655/outputs/attempt_0005_actual_f8_s1_480x832_gpu6-7/physion_movingcam_07abddf5748b/generated.mp4`.
- Previous contact sheet exists at `local_assets/reports/smoke/fast_inference_autoloop_20260529_144655/outputs/attempt_0005_actual_f8_s1_480x832_gpu6-7/physion_movingcam_07abddf5748b/contact_sheet.jpg`.
- Successful sample: `physion_movingcam_07abddf5748b`.
- Successful inference used 8 requested frames, 9 LingBot-normalized frames, 1 step, and 480x832 resolution.
- T5 GPU bf16, VAE load, Fast init, generation, and video save all completed in the previous smoke.
- `action.npy` remains dummy compatibility data only; `use_action=false` is preserved.
- Camera poses/intrinsics are passed through the legacy `action_path` directory because LingBot-Fast expects camera condition files there.
- Physion source `intrinsics.npy` remains unchanged. Runtime inference writes converted LingBot intrinsics into per-attempt `lingbot_condition/intrinsics.npy`.
- The intrinsics conversion was formalized in `cam_physgeo.utils.camera.convert_projection_to_lingbot_intrinsics`.
- Next gates allowed in the current phase: 3-10 rollout smoke, camera condition ablation, and reward-on-rollout.
- Still disallowed: VideoGPA encode, DPO, Stage1 warm-up, training, and more than 10 rollouts.
