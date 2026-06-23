# Meeting StageA Qualitative Results

## Inputs

- Evaluation root: `local_assets/meeting_eval_20260624_011137`
- Samples reviewed: 8 total, 2 each for drop / collision / roll / containment.
- Compared models: M0 Original LingBot-Fast, M1 StageA step800 adapter, M2 StageA final883 adapter.
- All three use the same initial image, prompt, poses, intrinsics, seed, scheduler settings, 81 frames, and 480x832 resolution.
- Contact sheets: `local_assets/meeting_eval_20260624_011137/contact_sheets/`
- Score CSV: `reports/meeting_eval_20260624_011137/qualitative_scores.csv`

## Anonymous Scoring Setup

The visual pass was scored as anonymous A/B/C from the contact sheets, then deblinded:

- A = M0 Original LingBot-Fast
- B = M1 StageA step800
- C = M2 StageA final883

Each category uses 0/1/2, where 2 means good, 1 means partial, and 0 means failed.

## Aggregate Preliminary Scores

| Model | Average total / 16 |
|---|---:|
| M0_original_fast | 6.00 |
| M1_stageA_step800 | 3.25 |
| M2_stageA_final883 | 3.50 |

## Main Visual Findings

- Background geometry is often more persistent than foreground objects, but all variants still drift or hallucinate in some conditions.
- Camera-conditioned generation is not reliably strong; there is visible view change in several clips, but it is not enough to preserve scene identity.
- Foreground identity is the largest failure: objects disappear, duplicate, recolor, or become noisy fragments.
- Physical events are mostly not preserved; collision, rolling, and containment semantics are weak.
- StageA step800/final883 do not provide a reliable qualitative win over Original Fast on this 8-sample holdout.

## Status

StageA optimization: `PASS` based on fixed-val loss decrease and finite training.

StageA generation quality: `FAILED_OR_MIXED` because qualitative rollout still has severe foreground and physics failures.

DPO readiness: `NO`; these outputs are too poor to use as quality-bounded hard negatives without more data/prompt/scope work.

## Generated Video Geometry Diagnostics

| Model | Mean median Sampson ↓ | Mean C-SGC score ↑ | Epipolar confidence | C-SGC confidence |
|---|---:|---:|---:|---:|
| original_fast | 919.479 | 0.324 | 0.261 | 1.000 |
| stageA_final883 | 769.429 | 0.324 | 0.255 | 1.000 |
| stageA_step800 | 874.914 | 0.325 | 0.252 | 1.000 |

These diagnostics are preliminary and should be read together with the contact sheets. Lower Sampson error means better epipolar consistency; higher C-SGC means more camera-conditioned static-background consistency.
