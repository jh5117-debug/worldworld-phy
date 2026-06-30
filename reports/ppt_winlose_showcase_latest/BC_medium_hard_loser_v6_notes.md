# BC Medium-Hard Loser v6 Notes

Current Status: BLOCKED_BY_GPU_OR_RUNNER_DISCOVERY

No v6 all-in-one PPT showcase was generated because no new B/C targeted rollout videos were produced. Existing saved sweep videos remain diagnostic only and had 0 / 208 TypeB quality-gate passes.

Checkpoint inventory did pass:

- B camera-only rank8 step200 found; stable candidate generator / control baseline.
- C camera+self/temporal rank4 step200 found; intended loser mining scope.

Next action: rerun this experiment when a safe GPU slot and the rollout runner are available, starting with 32 locked conditions and seeds=2.
