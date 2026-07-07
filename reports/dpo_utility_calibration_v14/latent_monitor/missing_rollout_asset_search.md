# v14 Missing Rollout Asset Search

Timestamp: `2026-07-07T23:09:58Z`

Purpose: check whether S_pass / rollout-only loser videos were merely located outside the manifest paths.

Searched sample ids from:

- `manifests/dpo_v14_subsets/s_pass.jsonl`
- `manifests/dpo_v14_subsets/rollout_only.jsonl`

A bounded `find /home/nvme03 /home/nvme04 -maxdepth 9` search was run for representative missing sample ids and expected `M_C` / `future` / `video.mp4` patterns.

Representative searched ids:

- `04228_containment_orbit_left_44_seed43228`
- `01014_drop_orbit_left_72_seed40014`
- `03410_roll_orbit_right_60_seed42410`
- `02276_collision_orbit_right_64_seed41276`

Result: no matching rollout loser MP4 assets were found for these representative missing rows.

Conclusion: S_pass and rollout-only V-JEPA2 scoring remain blocked by missing old local_assets rollout loser videos. Available synthetic v11 rows score normally; unavailable rows are kept as explicit errors and are not faked.
