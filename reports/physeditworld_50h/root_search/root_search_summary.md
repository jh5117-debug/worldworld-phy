# PhysEditWorld Root Search Summary

Updated: 2026-07-08T18:23:02 CST

Decision: `PHYS_EDIT_WORLD_ROOT_NOT_VISIBLE`

## Scope

- Roots checked: `/home/nvme03`, `/home/nvme04`, `/mnt/workspace/hj/nas_hj`.
- Max depth: 7.
- Metadata-only search: no video decode, no training, no GPU.

## Counts

- Candidate directories/roots: 261
- True-name PhysEditWorld candidates: 3
- False-positive legacy candidates: 7

## NAS Mount

```text
not visible
```

## Interpretation

The visible H20 filesystem still does not expose a clear PhysEditWorld selected 50h root. Most gravity/action/replay hits are legacy PhysInOne-style directories or background-id false positives such as `__bg###` / `missing77`, not explicit gravity labels from PhysEditWorld matched replay.

Required next evidence is an explicit data root containing action trace, camera trajectory, intrinsics, gravity labels, replay group metadata, and target video for matched replay.

## Outputs

- `reports/physeditworld_50h/root_search/candidate_root_search.csv`
