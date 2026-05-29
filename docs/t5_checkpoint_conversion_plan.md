# T5 Checkpoint Conversion Plan

## Recommendation

Do not convert the 10.582 GiB `.pth` checkpoint yet.

Reason:

- Full file read is acceptable: `25.793s`.
- `torch.load` is acceptable: `21.895s`.
- `torch.load(mmap=True)` returns in `0.111s` with low RSS.
- The main cost is model architecture construction/random initialization, not checkpoint deserialization.

## Safetensors Option

If conversion is later desired:

- Source: `local_assets/cache/lingbot_fast_cam_runtime/models_t5_umt5-xxl-enc-bf16.pth`
- Target directory: `local_assets/cache/lingbot_fast_cam_runtime/t5_safetensors/`
- Expected size: roughly `10.6 GiB`

Draft conversion command:

```bash
PY=/home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python
$PY - <<'PY'
import torch
from safetensors.torch import save_file
src = "local_assets/cache/lingbot_fast_cam_runtime/models_t5_umt5-xxl-enc-bf16.pth"
dst = "local_assets/cache/lingbot_fast_cam_runtime/t5_safetensors/model.safetensors"
state = torch.load(src, map_location="cpu", weights_only=True)
save_file(state, dst)
PY
```

## Risks

- Produces another 10+ GiB file.
- Requires user confirmation before creating large new artifacts.
- LingBot `t5.py` would need a loader branch for safetensors.
- It likely will not solve the dominant 263s CPU model construction cost.

## Better First Fix

Prefer:

1. increase T5 timeout to `600/900s` for CPU debug;
2. use GPU bf16 T5 for actual inference smoke;
3. consider lazy/mmap checkpoint load;
4. avoid fp32 CPU construction for smoke unless explicitly debugging CPU path.
