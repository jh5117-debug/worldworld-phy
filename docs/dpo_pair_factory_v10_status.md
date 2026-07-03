Current Status:
DPO_PAIR_FACTORY_V10_PRD_READY

# DPO Pair Factory v10 Status

Updated: 2026-07-03 16:15 CST

The active H20-2 priority has changed from DPO objective diagnosis to DPO preference-pair data construction. v7/v8 objective work remains diagnostic only and must not drive the next experiment. The immediate blocker is pair data volume and label purity, not optimizer plumbing.

Known data state at v10 start:

- v6 targeted B/C loser mining recovered only 5 runnable prefix5 conditions and 4 DPO-ready GT>C pairs, which is insufficient.
- v6b recovered 32 runnable prefix5 conditions, ran B/C rollout, selected 16 C medium-hard candidates, and produced 15 DPO-ready GT>C pairs.
- Protocol v1 contains 66 historical pairs, but its gates were broad and all old pairs require strict re-audit before use.
- Protocol v4 produced 42 reward-selected pairs, but strict visual alignment found only 3 human-visible/ready pairs and 39 too-subtle pairs.
- v8m/v8n cache/objective outputs are not the current focus; they prove training is still blocked and do not expand pair data.

v10 objective:

- Recover all runnable prefix5/V2V-5 conditions.
- Re-audit all old pairs under strict visual gates.
- Reuse or generate rollout candidates from Original Fast, B camera-r8, and C camera+self-temporal-r4.
- Construct GT>C, GT>controlled-corruption, B>C, teacher/failure, and diagnostic-only self-rollout candidates where valid.
- Require reward/metrics/quality checks plus Codex visual review for every DPO-ready loser.
- Produce at least 50 reviewed DPO-ready pairs, with 100 as stretch.

Current decision:

- Do not run DPO, SDPO, Linear-DPO, Safe-linear, winner-anchor, StageA, StageB, GRPO, or broad-LoRA in this experiment.
- DPO training remains blocked until the pair factory produces a clean reviewed dataset.
