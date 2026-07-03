# v8l Objective Preflight

Status: BLOCKED

## Cache Evidence
- cache index: `local_assets/dpo_objective_cache_v8j/gt_c_10_window49/cache_index.jsonl`
- rows: 10
- PASS rows: 10
- rows with explicit loser key fields: 0
- rows missing loser energy fields: 10
- rows missing loser tensor/path fields: 10

The cache includes winner fields such as `cached_winner_latent_tensor_path`, `future_loss_mask_tensor_path`, and `E_ref_winner_cached`. It does not include loser latent tensors or `E_ref_loser`.

## Objective Code Evidence
Relevant objective code references:

```text
41: "strict_sdpo_anchor",
42: "linear_dpo_anchor",
43: "safe_linear_dpo",
341: if objective == "strict_sdpo_anchor":
365: if objective == "linear_dpo_anchor":
379: if objective == "safe_linear_dpo":
545: "E_policy_loser": _scalar(pl.detach()),
546: "E_ref_loser": _scalar(rl.detach()),
657: "E_ref_loser",
659: "E_policy_loser",
699: "E_ref_loser": _scalar(rl.detach()),
701: "E_policy_loser": _scalar(pl.detach()),
721: "E_ref_loser": "",
723: "E_policy_loser": "",
879: "E_policy_loser": _scalar(policy_loser.detach()),
880: "E_ref_loser": _scalar(ref_loser.detach()),
```

## Decision
`PAIR_CACHE_WITH_LOSER_MISSING`

## Consequence
Do not run Strict SDPO, Linear-DPO, or safe-linear from this winner-only cache. The correct next step is a reviewed pair cache with both branches.
