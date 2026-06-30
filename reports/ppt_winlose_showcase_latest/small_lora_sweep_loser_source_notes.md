# Small-LoRA Sweep Loser Source Showcase Notes

Current Status: DIAGNOSTIC_ONLY

This showcase summarizes the recovered A/B/C/D small-LoRA sweep visual overviews. It is **not** a DPO-ready pair video. Existing candidate-generator audit has 0 TypeB quality-gate passes across the recovered sweep rows.

Recommended reading for PPT:

- B camera-r8: best stable candidate generator / control baseline.
- C camera+self/temporal-r4: best next loser-source mining scope.
- D camera+cross-r4: diagnostic runner-up with more artifact risk.
- A camera-r4: stable but too similar to the winner.

Conclusion: use B/C for the next targeted TypeB rerollout and reapply visual + reward gates. Do not use the saved sweep outputs directly as DPO-ready TypeB losers.
