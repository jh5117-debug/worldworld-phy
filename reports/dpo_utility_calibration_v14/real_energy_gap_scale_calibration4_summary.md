# Real-Energy Gap Scale Calibration4 Summary

Decision: `REAL_ENERGY_GAP_SCALE_CALIBRATION4_DONE`

## Evidence

- Input: `reports/dpo_utility_calibration_v14/blocker_retry/real_energy_calibration4_cuda_runtime_limit2/shard_00_of_01.csv`
- OK rows: `4`
- Delta_ref values: `[0.02072979509830475, 0.00031509879045188427, -8.203089237213135e-05, 0.008667878806591034]`
- Positive / negative Delta_ref counts: `3` / `1`
- Median |Delta_ref|: `0.004491488798521459`
- Min / max |Delta_ref|: `8.203089237213135e-05` / `0.02072979509830475`

## Beta Interpretation

- Because policy and reference are identical at calibration init, `reference_relative_margin = Delta_policy - Delta_ref = 0` for all rows.
- Therefore the beta sweep now correctly reports `NONE_ZERO_UTILITY`; no beta can turn zero utility into DPO signal.
- If training produces `u ~= 1e-4`, beta must be roughly `1000` just to reach `beta*u ~= 0.1`.
- Pair energy margins vary by orders of magnitude and include one negative margin, so raw full-future reduction is not stable enough by itself.

## Consequence

Next objective search should use per-pair/sigma normalization and should gate on real rollout videos; this evidence does not permit S16/S32/train400 scale.
