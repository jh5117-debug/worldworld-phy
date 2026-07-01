# BC Medium-Hard Loser v6b Notes

Current Status: READY_FOR_TINY_DPO_SMOKE_DATA

This v6b pass recovered 32 runnable prefix5 conditions and found enough C-scope medium-hard rollout losers for GT>C DPO smoke data. The preferred training-ready construction is clean GT future as WIN and C camera+self/temporal rank4 rollout as LOSE. B camera-r8 remains the stable candidate generator/control baseline, not the main loser source.

No DPO training was run. No StageB/GRPO/full-data StageA/broad-LoRA was run.
