# Beta Loss Response Summary

Recommended utility: `u_log`
Recommended beta: `1000`

This sweep used v13b real training CSVs. The v14 all500 real-energy calibration is still blocked by LingBot runtime initialization timeout.

## Why beta=0.1 failed

- `u_log` median |u| is 0.00020455321269580986; at beta=0.1, median |beta*u| is 2.0455321269580986e-05.
- Near-zero ratio at beta=0.1 is 1.0 for `u_log`, so DPO loss stays around 0.6931430251952352.
- `u_raw` shows the same issue: median |beta*u| 1.5062093734741212e-05 and near-zero ratio 1.0.

## What scale is needed

- With beta=1000, `u_log` median |beta*u| becomes 0.20455321269580987 and effective ratio becomes 0.888663967611336.
- With beta=1000, `u_raw` median |beta*u| becomes 0.1506209373474121 and effective ratio becomes 0.8562753036437247.

## Recommendation

Use log-normalized utility first (`u_log`) with a calibrated beta around 1000 only in a guarded tiny run. Keep loser detached or clipped, preserve the explicit winner anchor, and require video/metric audit before any scale.
