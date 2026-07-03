Current Status:
CACHE10_VALIDATED_PASS

# DPO Objective Diagnosis v8j Report

Updated: 2026-07-03T09:15:05

## Summary
- Final status: `CACHE10_VALIDATED_PASS`
- Cache build rows: 10/10 PASS, 0 fail
- Cache validation rows: 10/10 PASS, 0 fail
- Cache root: `local_assets/dpo_objective_cache_v8j/gt_c_10_window49`
- Cache level: `with_ref_energy`
- used_window_frames/prefix/prediction_start: 49 / 5 / 5
- E_ref_winner_cached mean: 0.803331
- Max allocated/reserved GB during build: 46.215 / 51.168
- Loser branch cached: no; validator checks actual loser-named fields.
- DPO/training run: no.

## Validator Fix
The first validation run exposed an inconsistent `no_loser_fields=False` with status PASS. The root cause was validator logic searching the entire JSON row text, which can match unrelated strings, and not treating `no_loser_fields` as a failure. The validator now checks actual field names recursively and fails if any loser-named field exists. The rerun passed 10/10.

## Decision
`CACHE10_VALIDATED_PASS`. Cache10 is ready for v8k cache-only winner-anchor diagnosis. DPO-family objectives remain blocked until v8k passes.
