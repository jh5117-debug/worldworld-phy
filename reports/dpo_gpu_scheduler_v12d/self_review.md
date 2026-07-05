# v12d Scheduler Self Review

Updated: 2026-07-05 10:49:58

- Confirmed scheduler only assigns physical GPU4-7.
- Job1 assigned GPU4 with `CUDA_VISIBLE_DEVICES=4`.
- GPU0-3 are forbidden and were not assigned.
- Job1 is running; current rows are interim only and not a pass claim.
- Scheduler blocks subsequent training behind checkpoint video, metrics, and Codex visual audit gates.
- No local_assets, videos, checkpoints, or weights should be staged.
