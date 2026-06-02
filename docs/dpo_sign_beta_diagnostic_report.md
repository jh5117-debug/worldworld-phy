# DPO Sign / Beta Diagnostic Report

## Inputs

The sign/beta check used the fallback fixed-noise `lr=1e-4` 1-step values:

- `Delta_policy = -0.0061973780`
- `Delta_ref = -0.0061976612`
- `Delta_policy - Delta_ref = 2.831e-07`

## Sign Convention

The adapter uses:

```text
Delta = E_loser - E_winner
L_DPO = -log sigmoid(beta * (Delta_policy - Delta_ref))
```

Lower energy means higher compatibility. Therefore, increasing
`Delta_policy - Delta_ref` should lower the DPO loss. This sign convention is
still consistent.

## Beta Scaling

Approximate logits:

| beta | preference logit |
| ---: | ---: |
| 0.05 | 1.416e-08 |
| 0.10 | 2.831e-08 |
| 0.50 | 1.416e-07 |

The scalar remains extremely close to `log(2)` for all three beta values because
the underlying delta gap is tiny. Raising beta alone would make the number more
visible but would not fix the weak policy energy movement.

## Recommendation

Keep `beta=0.1` for bounded smoke unless a later optimized sensitivity run shows
a larger, stable `Delta_policy` movement. The immediate blocker is not the sign;
it is weak LoRA-induced energy movement and/or too narrow a target scope.
