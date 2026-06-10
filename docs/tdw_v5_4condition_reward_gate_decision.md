# TDW v5 4-Condition Reward Gate Decision

Date: 2026-06-10

Decision: reward gate failed for pair construction.

Completed:

- GT/Base/Adapter reward scoring completed.
- RAFT/DINO backends were requested and reward v5 ran.
- GT > Base and GT > Adapter for all four conditions.

Gate failure reason:

- generated reward confidence avg = `0.463235`, below `0.5`;
- generated real-backend confidence avg = `0.411765`, below `0.5`;
- `R_reobs` is missing for all rows;
- generated `phys`, `quality`, and `freeze` remain fallback-heavy;
- adapter-vs-base margins are near zero.

Therefore no winner/loser pairs were built.

Next action:

- human review the 4-condition rollout;
- debug reward confidence / missing reobserve backend;
- or request a 12-condition rollout+reward pass after approval.

DPO remains blocked.
