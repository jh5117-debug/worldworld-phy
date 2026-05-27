# Download And Weight Audit: Local Assets

| model / asset | purpose | local path | status | load test / notes |
| --- | --- | --- | --- | --- |
| LingBot-Fast | main model | `local_assets/weights/lingbot_fast` | copied, about 70G | dry-run loader found config and 16 safetensors shards; actual inference adapter still pending |
| LingBot-Base | baseline only | `local_assets/weights/lingbot_base` | copied, about 150G | available as baseline; not default teacher |
| LingBot code | legacy model imports | `local_assets/third_party/lingbot_world` | copied | `wan.modules.model` import succeeded |
| VideoGPA | DPO framework | `local_assets/third_party/VideoGPA/official_repo` | cloned | commit `551e63a5c2c493962f1e1d090bfa8324bf18b694`; inspected preference/encode/train files |
| DINOv2 | foreground/reobserve features | `local_assets/weights/dinov2` | directory present, checkpoint missing | proxy visual feature fallback active |
| V-JEPA2 / video feature | temporal/TRD feature | `local_assets/weights/vjepa2` | copied, about 1.6G | path smoke passed; heavy forward not run |
| VideoMAEv2 | optional temporal feature | `local_assets/weights/videomae2` | not present | V-JEPA2 path is preferred for now |
| Optical flow | R_bg/R_cam/P_freeze | `local_assets/weights/optical_flow` | copied, about 102M | proxy flow fallback active; RAFT/GMFlow forward not wired yet |
| Depth model | generated rollout depth fallback | `local_assets/weights/depth` | not required for clean/corrupt smoke | Physion HDF5 depth is used where available |

No new large model download was required during this pass. Missing DINOv2, RAFT forward wiring, and generated-rollout depth are recorded as next-step upgrades.

