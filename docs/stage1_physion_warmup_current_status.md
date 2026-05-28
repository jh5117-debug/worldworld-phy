# Stage1 Physion Warm-Up Current Status

Stage1 warm-up was only dry-run checked:

```bash
CUDA_VISIBLE_DEVICES=6,7 python -m cam_physgeo.training.train_stage1_physion_warmup \
  --config configs/cam_physgeo/stage1_physion_warmup.yaml \
  --dry-run \
  --limit 2 \
  --max_steps 1
```

Result: dry-run passed as a guarded plan. No real warm-up training was launched.

Caveat: the default Python environment still reports a LingBot import mismatch around `transformers` and `huggingface-hub`; real LingBot execution must use the configured LingBot environment. Stage1 is not the current priority until Fast inference, rollout reward, and VideoGPA encode gates are fixed.

