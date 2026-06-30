# Small-LoRA Sweep Loser Source Decision

Current Status: MIXED / DIAGNOSTIC_ONLY

## Evidence Read This Round

- Existing video audit: `reports/candidate_generator_v2/video_audit.csv`
- Run inventory: `reports/candidate_generator_v2/run_inventory.csv`
- Codex-inspected overview contact sheets:
  - `reports/candidate_generator_v2/visual_overviews/A_step050_overview.jpg`
  - `reports/candidate_generator_v2/visual_overviews/B_step050_overview.jpg`
  - `reports/candidate_generator_v2/visual_overviews/C_step050_overview.jpg`
  - `reports/candidate_generator_v2/visual_overviews/D_step050_overview.jpg`

Recovered audit rows: **208**. Existing TypeB quality-gate pass count: **0**.

## Visual Judgment

- **A camera-only rank4**: clear and stable, but too conservative. It is too close to the winner/GT for a useful loser source.
- **B camera-only rank8**: clearest and most stable candidate generator. It is the best fallback generator/control baseline, but too mild as the primary loser source.
- **C camera + limited self/temporal attention rank4**: best exploratory loser source. It remains readable while showing more foreground identity / object deformation / weak physical-event failures.
- **D camera + limited cross-attention rank4**: runner-up diagnostic loser source. Some failures are more visible, but artifacts are less stable and more cross-attention-like.

## Decision

Saved A/B/C/D sweep videos should **not** be used directly as DPO-ready TypeB losers. The recovered candidate-generator audit already marked all of them as failing TypeB quality/usability gates.

For the next loser-source mining pass:

1. Use **B camera-only rank8** as the stable candidate generator / control baseline.
2. Use **C camera + limited self/temporal rank4** as the first exploratory medium-hard loser-source scope.
3. Keep **D camera + limited cross-attention rank4** as a diagnostic runner-up only.
4. Do not use **A camera-only rank4** as the main loser source; it is too similar to the winner.

## Next Check Before TypeB DPO Pair Construction

Run a targeted full80/quant80 rerollout from B and C, then apply sharpness, reward, visual, and subreward-alignment gates. Do not mark any TypeB pair DPO-ready until a human-visible medium-hard failure passes those gates.
