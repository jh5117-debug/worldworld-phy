# v14 Gap Scale Root Cause

## Decision

The v13b failure is consistent with a preference utility scale problem. The DPO branch operated in the near-zero logit regime, so `-logsigmoid(beta*u)` stayed near `0.693` even when winner-anchor energy moved.

## Evidence From v13b Real Training CSVs

- Recommended utility: `u_log`
- Recommended beta: `1000`
- Recommended median |beta*u|: `0.20455321269580987`

At beta=0.1:
- `u_log` median |u| = 0.00020455321269580986; median |beta*u| = 2.0455321269580986e-05; near-zero ratio = 1.0; effective ratio = 0.0; mean loss = 0.6931430251952352.
- `u_raw` median |u| = 0.0001506209373474121; median |beta*u| = 1.5062093734741212e-05; near-zero ratio = 1.0; effective ratio = 0.0; mean loss = 0.6931442316728934.

At beta=1000:
- `u_log` median |beta*u| = 0.20455321269580987; near-zero ratio = 0.018218623481781375; effective ratio = 0.888663967611336; mean loss = 0.6591367960510969.
- `u_raw` median |beta*u| = 0.1506209373474121; near-zero ratio = 0.02631578947368421; effective ratio = 0.8562753036437247; mean loss = 0.6677152698414787.

## Interpretation

For utilities around `1e-4` to `2e-4`, beta=0.1 gives logits around `1e-5`. A calibrated beta in the hundreds to low thousands is required if this utility definition is retained.

This does not prove beta=1000 is safe for training. It only proves beta=0.1 was far too small for the observed v13b utility scale. Any v14 training still needs winner protection, loser-dominance guards, checkpoint video, metrics, and Codex visual audit.

## Real Energy Calibration Blocker

A one-pair real LingBot energy smoke on `s_pass` was attempted with `CUDA_VISIBLE_DEVICES=4` and timed out after 300 seconds before writing a pair row. The v14 all500 `energy_utility_*.csv` files therefore document `MISSING_REAL_ENERGY`; they are not final all500 real-energy calibration.

Exact blocker: LingBot-Fast runtime/model initialization is still too slow for direct all500 offline energy calibration.
