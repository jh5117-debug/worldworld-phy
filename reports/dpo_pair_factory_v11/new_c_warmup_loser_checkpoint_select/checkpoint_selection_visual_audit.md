# Full-data Warmup Checkpoint Selection Visual Audit

Updated: 2026-07-06 10:26 CST

## Scope

Compared intermediate `fulldata-lingbotfast-warmup-weights` checkpoints against the old C loser source on the first v6b smoke condition.

Checkpoints launched on H20 GPU4-7:

- `step_000103` on GPU4
- `step_000206` on GPU5
- `step_000309` on GPU6
- `step_000412` on GPU7

Each command used the safe `WanModelFast.from_pretrained` loader and the same first two conditions from `manifests/targeted_BC_loser_mining_v6b_conditions.jsonl`.

## Runtime Outcome

- Produced future videos/contact sheets for `01002_drop_orbit_left_72_seed40002`: 4/4 checkpoints.
- Did not complete the second selected condition `01008_drop_orbit_left_72_seed40008` before the processes stalled in post-generation / decode-write cleanup.
- The four launched Python processes were our own checkpoint-selection smoke jobs. They were terminated with SIGTERM after visual gate failed and to release GPU4-7.
- GPU4-7 were confirmed free after termination; no GPU0-3 jobs were used or killed.

## Codex Visual Review

### `01002_drop_orbit_left_72_seed40002`

All four intermediate checkpoints (`step_000103`, `step_000206`, `step_000309`, `step_000412`) show the same qualitative pattern as the old C and final full-data checkpoint:

- The video remains decodable and visually readable.
- The red/green sphere physical contact event is not reproduced.
- The green sphere remains mostly static instead of responding physically.
- The red sphere drifts to the side / boundary.
- Late frames show duplicated red/blue/purple fragments or object residues.

This is visible as a failure, but it is not a better medium-hard loser source than old C. The failure shifts toward artifact fragments rather than clean physical/geometric mismatch.

## Decision

`FULLDATA_WARMUP_CHECKPOINT_SELECT_NO_GO_FOR_500`

Do not launch 500-video DPO loser generation from the full-data warmup checkpoints in this state.

Reason:

- The final adapter already failed the 2-condition visual gate.
- Intermediate checkpoints did not improve the available reviewed sample.
- The smoke runner did not complete the second condition cleanly.
- Scaling to 500 would likely waste GPU and storage while producing losers no better than old C.

## Next Recommendation

Use old C or the already-reviewed synthetic/controlled pair factory path for immediate DPO data. If real rollout loser expansion is still required, first fix the V2V-5 runner post-generation loop so multi-condition smoke completes reliably, then rerun an 8/16-condition checkpoint selection before any 500-scale rollout.
