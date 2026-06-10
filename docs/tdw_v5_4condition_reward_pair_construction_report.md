# TDW v5 4-Condition Reward Pair Construction Report

Date: 2026-06-10

Status: not run / blocked by reward gate.

Reason:

Reward scoring completed, but backend confidence did not pass the pair-construction gate:

- generated reward confidence avg: `0.463235`;
- generated real-backend confidence avg: `0.411765`;
- trustworthy for pairs: `false`.

Candidate margins:

- GT beats generated videos on all four conditions, but generated confidence is too low for DPO-ready pairs.
- Adapter vs Base margins are very small: about `+0.0028`, `+0.0021`, `-0.00024`, `-0.00084`.

Accepted pairs: `0`.

Rejected/blocked pairs: all diagnostic candidates.

Pair set DPO-ready: no.

No DPO training was run.
