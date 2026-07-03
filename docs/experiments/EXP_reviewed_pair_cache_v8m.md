# EXP reviewed pair cache v8m

Current Status: PASS

Generated: 2026-07-03T01:55:20.644150+00:00

## Current Status
- v8j built a validated winner-only cache for 10 reviewed GT>C pairs.
- v8k proved cache-only winner-anchor can complete 20/20 steps with positive post-update winner improvement.
- v8l blocked Strict SDPO / Linear-DPO because the cache has no loser branch or `E_ref_loser`.

## Problem
Pairwise DPO objectives require both winner and loser latents and reference energies. The current cache is scientifically valid for winner-anchor only, but invalid for SDPO / Linear-DPO.

## Hypothesis
A dual-branch cache can be built from `manifests/dpo_smoke_v7_gt_c_10.jsonl` because all 10 pairs are already Codex-reviewed and DPO-ready. Reusing the v8j safe runtime path with T5 fast-init should produce a bounded cache without training.

## Inputs
- `manifests/dpo_smoke_v7_gt_c_10.jsonl`
- reviewed field: `codex_visual_audit.reviewed=true`
- winner: clean GT future/full video
- loser: C camera+self/temporal rollout future/full video

## GPU
- H20 physical GPU4-7 only
- prefer GPU7 via `CUDA_VISIBLE_DEVICES=7` and process `--gpu 0`
- no GPU0-3

## Metrics / Checks
- cache row status
- winner and loser tensor presence
- `E_ref_winner_cached`
- `E_ref_loser_cached`
- same timestep / sigma / noise seed metadata
- finite tensors
- SHA256 validation
- reviewed loser provenance

## Success Gate
- 1-pair dual-branch cache smoke passes.
- 10/10 reviewed pairs build successfully.
- validation confirms winner and loser branches are present and finite.
- no unreviewed loser enters cache.
- no DPO/SDPO/Linear-DPO is run in this phase.

## Failure Gate
- any cache row lacks loser branch;
- loser visual review missing;
- reference energy nonfinite;
- cache builder silently uses image-only or prefix_len=1;
- GPU0-3 used;
- OOM / SIGFPE / NaN.

## Output Paths
- `local_assets/dpo_pair_cache_v8m/gt_c_10_window49/`
- `reports/dpo_objective_diagnosis_v8m/pair_cache_build_10pair.csv`
- `reports/dpo_objective_diagnosis_v8m/pair_cache_validation_10pair.csv`
- `docs/dpo_objective_diagnosis_v8m_report.md`

## What Is Not Run
- no DPO
- no SDPO
- no Linear-DPO
- no safe-linear
- no large DPO
- no StageB / GRPO / full-data StageA / broad-LoRA
- no pair rollout
- no checkpoint deletion
- no video / weight push


## Actual Results (2026-07-03T02:38:45.438241+00:00)
Current Status: PASS

### Commands Run
- `python3 -m cam_physgeo.dpo.pair_cache_builder_v8m --num_pairs 1 ...`
- `python3 -m cam_physgeo.dpo.pair_cache_validate_v8m --cache_root local_assets/dpo_pair_cache_v8m/one_pair_window49 ...`
- `python3 -m cam_physgeo.dpo.pair_cache_builder_v8m --num_pairs 10 ...`
- `python3 -m cam_physgeo.dpo.pair_cache_validate_v8m --cache_root local_assets/dpo_pair_cache_v8m/gt_c_10_window49 ...`

### Outputs
- Build CSV: `reports/dpo_objective_diagnosis_v8m/pair_cache_build_10pair.csv`
- Validation CSV: `reports/dpo_objective_diagnosis_v8m/pair_cache_validation_10pair.csv`
- Cache root, not committed: `local_assets/dpo_pair_cache_v8m/gt_c_10_window49`

### Metrics
- build PASS rows: 10 / 10
- validation PASS rows: 10 / 10
- Delta_ref positive: 8 / 10
- Delta_ref non-positive: 2 / 10
- Delta_ref mean: 0.10330507159233093
- Delta_ref min/max: -0.0973658561706543 / 0.2931232452392578

### Decision
`PAIR_CACHE10_VALIDATED_FOR_TINY_OBJECTIVE`

### Next Action
Run a tiny objective diagnosis only, using pair weighting/filtering because 2/10 reviewed pairs have non-positive `Delta_ref` under this energy backend.
