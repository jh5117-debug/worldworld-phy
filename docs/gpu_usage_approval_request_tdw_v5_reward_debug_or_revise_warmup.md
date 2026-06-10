# GPU Usage Approval Request: TDW v5 Reward Debug Or Revise Warmup

Date: 2026-06-10

The 4-condition reward gate failed for pair construction.

Failure reason:

- generated reward confidence avg: `0.463235 < 0.5`;
- generated real-backend confidence avg: `0.411765 < 0.5`;
- `R_reobs` missing for all rows;
- adapter-vs-base reward margins near zero;
- pair construction blocked.

Options:

1. Human review only.
   - Inspect the existing 4-condition gallery.
   - No further compute.

2. Reward debug.
   - Improve missing/fallback-heavy reward backend reporting, especially reobserve and generated-video physics/freeze confidence.
   - No reward calibration or weight changes unless separately approved.

3. Expand rollout manually after approval.
   - 12 conditions, 3 per template, base plus adapter = 24 videos.
   - Then rerun reward scoring.

4. Revise warmup / adapter scope.
   - Only if human review shows Stage A adapter is not improving camera behavior.

DPO remains disallowed until reward confidence and pair diagnostics pass.
