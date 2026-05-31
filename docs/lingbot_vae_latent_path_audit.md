# LingBot VAE Latent Path Audit

## VAE Path

- LingBot VAE class loaded by the adapter: `Wan2_1_VAE`
- Loaded module: `local_assets/third_party/lingbot_world/wan/modules/vae2_1.py`
- Runtime VAE path used by the adapter: `local_assets/cache/lingbot_fast_cam_runtime/Wan2.1_VAE.pth`
- Companion Base VAE candidate observed on disk: `local_assets/weights/lingbot_base/Wan2.1_VAE.pth`
- This is a LingBot/Wan VAE path, not a VideoGPA-native CogVideoX/Wan2.2 latent path.

## Compatibility

- VideoGPA native encode scripts exist for CogVideoX/CogVideoX-I2V/CogVideoX1.5/Wan2.2 TI2V.
- Those native scripts do not establish compatibility with LingBot-Fast camera-conditioned Wan2.1 latents.
- This round therefore uses the LingBot VAE directly and does not claim native VideoGPA latent compatibility.

## Encode / Decode Path

- The successful encode call pattern was `vae.encode([video_tensor])`.
- Input tensor convention used by this adapter after the resolution fix: `C,T,H,W`.
- For an 8-frame `480x832` input, the tensor shape was `[3, 8, 480, 832]`.
- The resulting latent shape was `[16, 2, 60, 104]`.
- Inferred temporal compression: `8 / 2 = 4`.
- Inferred spatial compression: `480 / 60 = 8`, `832 / 104 = 8`.
- The VAE returned `float32` latents while the VAE runtime was initialized with `bf16`.
- Decode/reconstruction was not wired in this dry-run; no reconstruction success is claimed.

## Notes

- The first remote encode attempt used the project resolution string as width x height and produced `[3,8,832,480]`. The adapter was fixed to parse project convention as `height x width`, then the encode was rerun successfully with `[3,8,480,832]`.
- No LingBot weights or videos were modified.

