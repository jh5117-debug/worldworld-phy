

## Targeted B/C Loser Mining v6 Update - 2026-06-30

Current Status: BLOCKED_BY_GPU_OR_RUNNER_DISCOVERY

B and C checkpoints were found. B camera-r8 remains the stable candidate generator/control baseline; C camera+self/temporal-r4 remains the intended loser mining scope. New rollout did not start because GPU/process queries were unsafe/hung under high GPU occupancy. No DPO-ready TypeB-C pairs were produced, and no saved sweep video was promoted to DPO-ready.

# Small-LoRA Sweep Loser Source Audit

Current Status: MIXED / DIAGNOSTIC_ONLY

## Scope

This audit recovered the saved A/B/C/D small-LoRA sweep artifacts and rechecked them as potential DPO loser sources. No training, DPO, StageB, GRPO, checkpoint edits, or data deletion were performed.

## Recovered Artifacts

- Video rows recovered from `reports/candidate_generator_v2/video_audit.csv`: **208**
- Contact sheet rows recovered: **212** including four overview sheets opened by Codex this round.
- A/B/C/D rollout rows: A=48, B=48, C=48, D=48.
- Original Fast baseline rows: 16.

## Codex Visual Audit

- A camera-only rank4: clear/stable but too similar to the winner; not a primary loser source.
- B camera-only rank8: best stable candidate generator/control baseline; not enough visible loser failure by itself.
- C camera+self/temporal rank4: best exploratory loser-source scope; most suitable for future medium-hard mining diagnostics.
- D camera+cross rank4: runner-up diagnostic scope; more visible local artifacts but less stable.

## Existing Gate Result

The recovered candidate-generator audit has **0 TypeB quality-gate passes** across the saved sweep rows. Therefore these videos are not DPO-ready TypeB losers as-is.

## Recommendation

Use B as the stable generator/control and C as the first medium-hard loser-source scope for a future targeted rerollout. Re-run full80/quant80 and apply sharpness, reward, human-visible, and subreward-alignment gates before building TypeB pairs.

## Output Paths

- `reports/small_lora_sweep_visual_audit/model_summary.csv`
- `reports/small_lora_sweep_visual_audit/best_loser_source_decision.md`
- `reports/ppt_winlose_showcase_latest/small_lora_sweep_loser_source_showcase.mp4`
