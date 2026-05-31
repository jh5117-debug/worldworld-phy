# Camera Condition Effect Confirmation Report

This round confirmed camera embedding differences without generating new videos.

## Video-Level Ablation Status

No new video-level ablation was launched in this round. Reasons:

- The prior strong ablation already hit GPU/OOM/timeout pressure and completed only the `correct` low-resolution variant.
- GPU 6/7 were heavily occupied during this debug window.
- The new embedding probe was sufficient to answer the narrower question: camera variants produce different `c2ws_plucker_emb` tensors.

## Current Interpretation

- Camera enters LingBot-Fast as a nonzero Plucker/control tensor.
- `correct`, `frozen`, `reversed`, and `exaggerated_yaw` produce measurably different control embeddings.
- Dummy action remains zero and does not explain the embedding differences.
- Video-level effectiveness is still not proven because there is no complete same-seed repeat baseline and no complete correct/frozen/reversed/exaggerated video set.

## Next Minimal Camera Step

If the next round focuses on Gate C, run only one small same-seed ablation after GPU 6/7 are free:

- `repeat_correct_A`
- `repeat_correct_B`
- `frozen`
- `exaggerated_yaw`

Use 4 frames, 1 step, 256x448, and compare variant distance against repeat stochastic distance. Do not expand rollout count.
