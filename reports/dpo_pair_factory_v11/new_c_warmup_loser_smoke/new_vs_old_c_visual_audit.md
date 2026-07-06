# Full-data LingBot-Fast Warmup C Loser Smoke Audit

Model label: `fulldata-lingbotfast-warmup-weights` / `M_C_all_available_warmup_final_safe`.

Input: first 2 v6b prefix5 conditions, compared against previous small-step `M_C_camera_self_temporal_r4`.

Visual audit by Codex:

- `01002_drop_orbit_left_72_seed40002`: new C is clear and decodable, but visually almost the same as old C. Both miss the GT physical event: red sphere drifts laterally/right rather than correctly colliding/reobserving with green sphere. Medium-hard loser candidate, but not visibly better than old C.
- `01008_drop_orbit_left_72_seed40008`: new C is clear and decodable, but red ball disappears and green duplicate/fragments appear near the right/top. Old C has a similar failure with slightly fewer fragments. New C is not better; if anything it is marginally more artifact-prone on this sample.

Decision: `NEW_C_SMOKE_NOT_BETTER_THAN_OLD_C_ON_2COND`; do not launch 500-video generation yet. Need either more representative 8/16-condition audit or checkpoint selection among step_103/206/309/412/final before scaling.

Runtime note: default WanI2VFast from_pretrained path stalled before GPU generation. The safe local safetensors/low_cpu_mem_usage patch allowed generation.
