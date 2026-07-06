# v14 Normalization And Regularization Design

## Energy Reduction Normalization

- Prefer per-token or per-latent mean over full future sum when comparing pairs.
- For controlled local failures, report both full-future utility and local/time-mask utility.
- Normalize by sigma/timestep bin before mixing bins.
- Store raw, log-ratio, z-score, and robust MAD versions.

## Gap Normalization

- Primary candidate: `u_log = log(m_l / m_l_ref) - log(m_w / m_w_ref)`.
- Secondary: sigma-bin z-score utility `u_z` once enough real-energy rows exist.
- Split summaries by source: rollout-derived vs synthetic controlled.

## Beta Calibration

- Choose beta from empirical utility distribution so median `|beta*u|` is roughly `0.1..1.0`.
- v13b evidence indicates beta=0.1 is far too small; beta around 1000 is required for observed `u_log`/`u_raw` scales.
- High beta is not automatically safe; it must be paired with winner protection and early-stop gates.

## Loser Regularization

- Start with loser detached or alpha_loser <= 0.02.
- Clip loser normalized gap before it enters utility.
- Keep `lambda_loser = 0` until winner improvement is positive for multiple eval windows.
- Stop if winner contribution ratio falls below 0.30 or loser dominance exceeds 0.70.

## Winner Protection

- Always include explicit winner energy anchor.
- Add a winner-worse penalty such as `ReLU(g_w_z)` when using normalized gaps.
- Select best checkpoint by validation/video metrics, not final step by default.

## Local DPO

- If `affected_time_span` exists, compute time-local utility and compare with full-future utility.
- If spatial region/mask exists, use region-normalized local utility.
- Do not claim full LocalDPO unless spatial masks are present and verified.

## Latent Monitor

- v14 latent monitor found local backend candidates but did not produce TRD/VJEPA scores yet.
- V-JEPA/VideoREPA/TRD remain monitor-first; no auxiliary training loss should be added until monitor discrimination is proven.

## Next Safe Objective Family

Recommended first calibrated scheme:

- objective: calibrated_winner_detached_log
- utility: u_log
- beta: 1000
- lambda_pref: 0.005
- lambda_winner: 1.0
- lambda_loser: 0.0
- loser_gradient: detached
- scope: L0_camera_r4
- max_steps: 200
- required_eval: video_metrics_codex_audit

Do not run train400, S32, S64, or large DPO until a tiny calibrated scheme passes training signal, checkpoint videos, metrics, and Codex audit.
