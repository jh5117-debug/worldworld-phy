# Stage2 VideoGPA DPO Plan

Do not train yet. This project remains Physion-only, Fast-first, camera-conditioned, and no-action except for dummy compatibility files.

## Current Gate State

- Gate A: LingBot-Fast 1-sample actual inference passed.
- Gate B: 3-10 Fast rollout smoke is being validated by the rollout/reward autoloop.
- Gate C: camera condition ablation is being validated with correct/frozen/reversed poses.
- Gate D: reward-on-real-Fast-rollout is being validated after the small rollout set exists.
- Gate E: VideoGPA encode smoke is not allowed in the current phase.
- Gate F: LingBotFastVideoGPAAdapter winner/loser batch shape dry-run is not allowed in the current phase.
- Gate G: real DPO energy/logprob adapter is not wired and remains blocked.

## Why DPO Training Is Still Blocked

1. Small Fast rollout quality and failure modes must be inspected before pair generation grows.
2. Camera ablation must show whether poses/intrinsics materially affect generation. If correct/frozen/reversed look the same, the camera adapter must be fixed first.
3. Reward must separate clean GT from real Fast rollout failures, not only artificial corrupted negatives.
4. Feature backends must be reported honestly: DINO/V-JEPA/VideoMAE/flow may still be proxy or fallback in parts of the current reward path.
5. VideoGPA encode has not been run in this phase and should wait until Gates B-D are understood.
6. `LingBotFastVideoGPAAdapter.compute_dpo_energy_or_logprob` must not be faked.

Only after Gates B, C, and D are reasonably passed should a future round attempt VideoGPA encode smoke. DPO training remains disallowed until all gates A-G pass.

## Camera / Reward Debug Update

- Gate A: passed.
- Gate B: passed at small-smoke level with 3 Fast rollouts.
- Gate C: not proven. Camera tensors reach `WanI2VFast.generate` through `action_path`, and LingBot-Fast source builds `c2ws_plucker_emb`, but strong ablation did not produce enough successful variants to show output differences above stochastic baseline.
- Gate D: failed / not reliable. Raw reward still ranks Fast above clean GT. Confidence-aware aggregation lowers absolute scores and marks rows provisional, but it still wins only 1/3 pairs.
- Gate E: VideoGPA encode remains not allowed.
- Gate F: adapter batch shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next gate is not VideoGPA. The next minimal work is camera embedding instrumentation plus reward backend repair.

## Plucker / Reward Backend Debug Update

- Gate A: passed.
- Gate B: passed at 3-rollout smoke level.
- Gate C: partial. Direct probe of LingBot's actual `get_plucker_embeddings` path shows correct/frozen/reversed/exaggerated camera variants produce different `c2ws_plucker_emb` control tensors. This proves camera condition reaches the model-side embedding. Video-level effect is still not proven because the same-seed ablation set did not complete.
- Gate D: failed / not reliable. V2 reward aggregation now marks all proxy/missing components as low confidence and adds real-backend-only totals, but no real backend is active for clean or Fast in the rollout scorer. Raw and proxy totals still rank Fast above clean.
- Gate E: VideoGPA encode remains not allowed.
- Gate F: adapter batch-shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next minimal work before VideoGPA is either: finish a small video-level camera ablation after GPU 6/7 are free, or wire real reward backends for clean GT depth/ID/camera/object-state and generated rollout feature/flow.

## Camera Effect / Reward Real Backend Update

- Gate A: passed.
- Gate B: passed with 3 Fast rollout smoke videos.
- Gate C: partial. Camera/control tensors differ across camera variants and source-level DiT camera scale/shift injection is present. Runtime full-DiT scale/shift tensors were not captured, and video-level effect is still not proven because the 4-frame ablation is invalid for the current LingBot-Fast temporal latent path.
- Gate D: partial. Clean GT real metadata backend is active for depth, ID mask, camera, intrinsics, and object-state metadata. Reward v3 ranks clean above Fast on 3/3 pairs, but Fast rollout scoring remains fallback/proxy because generated-video DINO/flow/depth are not real yet.
- Gate E: VideoGPA encode remains not allowed.
- Gate F: LingBotFastVideoGPAAdapter batch shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next minimal work remains outside VideoGPA: run a valid 8-frame video-level camera ablation, wire real optical-flow forward from local RAFT assets, and add DINOv2-small only after user approval.

## Video Camera / Flow / DINO Smoke Update

- Gate A: passed.
- Gate B: passed with 3 Fast rollout smoke videos.
- Gate C: partial/pass. Embedding-level and DiT camera path remain confirmed. The valid 8-frame ablation completed at 256x448: same-seed repeat difference was `0.0`, frozen matched correct, and exaggerated-yaw produced nonzero output difference (`pixel_l1=0.02547`). This proves a strong camera perturbation can affect video output, but ordinary camera sensitivity still needs stronger/longer validation.
- Gate D: partial. Clean GT real backend remains active. RAFT-small real optical-flow forward now works and contributes to Fast rollout `bg`/`cam` real components. DINOv2-small is still missing, so `fg`/`reobs` feature terms remain proxy/fallback and reward is not DPO-ready.
- Gate E: VideoGPA encode remains not allowed until camera video effect and reward backends are both reliable.
- Gate F: LingBotFastVideoGPAAdapter batch-shape work remains deferred.
- Gate G: real DPO energy/logprob remains unimplemented.

Next minimal work is still not VideoGPA: add DINOv2-small after approval and re-run reward-on-rollout with both real flow and real feature backends.

## DINO Reward V5 / Camera Stress Update

- Gate A: passed.
- Gate B: passed.
- Gate C: pass/partial. A high-yaw stress sample was selected (`physion_movingcam_13db379640ce`). The 8-frame 480x832 stress ablation generated all six variants. Same-seed repeat stayed `0.0`; reversed, exaggerated-yaw, and exaggerated-translation diverged from repeat baseline. Frozen still matched correct.
- Gate D: partial/pass for smoke. DINOv2-small was downloaded to `local_assets/weights/dinov2/dinov2_vits14/` and forwards successfully. Reward v5 uses clean GT metadata, RAFT real flow, and DINO real features; clean > Fast remains `3/3`.
- Gate E: VideoGPA encode smoke may be considered next, but only encode smoke. Do not train.
- Gate F: DPO remains not allowed.
- Gate G: real DPO energy/logprob remains unimplemented.

Next permitted step is VideoGPA encode smoke only. DPO training is still blocked.

## VideoGPA Encode Smoke Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass. Stress camera perturbations have video-level effect, but ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke. Reward v5 provides a usable smoke-level clean > Fast signal with RAFT and DINO active, but generated depth/mask/physics are still not complete.
- Gate E: partial. VideoGPA pair export and encode-readiness smoke passed for `gt_vs_fast` metadata/video readability, and camera sidecars were preserved. Native latent encode did not run because LingBot-Fast VAE/condition encoding is not wired into VideoGPA.
- Gate F: still no. DPO remains blocked.
- Gate G: still no. `compute_dpo_energy_or_logprob` is intentionally `NotImplementedError`.

Next minimal step is not training. It is a LingBot-Fast VideoGPA adapter dry-run that implements real LingBot VAE latent encode, same-noise/same-timestep batch collation, and a non-fake energy/logprob path.

## LingBot VAE / Energy Dry-Run Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass. Camera stress perturbations have video-level effect, but ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke. Reward v5 has clean > Fast on the 3-sample smoke with RAFT and DINO active, but generated depth/mask/physics are still incomplete.
- Gate E: partial/pass for latent/condition/batch plumbing. LingBot `Wan2_1_VAE` loads, winner/loser videos encode to LingBot-compatible latents, camera condition packs into a nonzero Plucker/control tensor, and a same-noise/same-timestep 1-pair batch shape dry-run passes.
- Gate F: still no. Energy/logprob remains `NotImplementedError`; no DPO loss, backward, optimizer, LoRA save, or model update was run.
- Gate G: still no. Real DPO training remains blocked.

Next minimal step is to wire the real LingBot-Fast denoising/velocity forward target for `compute_dpo_energy_or_logprob`. Only after that may a future round consider a 1-pair DPO scalar-loss dry-run, still without real training unless explicitly approved.

## LingBot Energy Forward Debug Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass. Camera stress perturbations have video-level effect, while ordinary frozen/correct remains weak.
- Gate D: partial/pass for smoke. Reward v5 has clean > Fast on the 3-sample smoke with RAFT and DINO active, but generated depth/mask/physics are still incomplete.
- Gate E: passed for 1-pair plumbing smoke. VideoGPA pair/metadata, LingBot latent encode, condition encode, same-noise/same-timestep batch, real LingBot model forward, and policy energy dry-run all pass.
- Gate F: no. DPO training remains disallowed.
- Gate G: partial. Real policy energy is wired with a code-backed flow target (`noise - x0`), but frozen reference energy and scalar DPO loss have not been run.

Energy dry-run details:

- Policy model: `WanModelFast` through `WanI2VFast`.
- Target: flow velocity `noise - x0`.
- Winner energy: `0.8652140498161316`.
- Loser energy: `0.8322668075561523`.
- Reference: deferred, not faked.
- Backward / optimizer / LoRA / checkpoint save: none.

Next permitted step is only a user-confirmed 1-pair scalar DPO loss dry-run
with a real frozen reference, no optimizer, and preferably no backward. Real
DPO training remains blocked.

## Reference Energy / Scalar Loss Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: passed for 1-pair no-backward DPO plumbing. VideoGPA pair/metadata,
  LingBot latent encode, condition encode, batch shape, policy energy,
  reference energy, and scalar DPO loss dry-run all pass.
- Gate F: no. DPO training remains disallowed.

Reference/scalar details:

- Reference model: same frozen LingBot-Fast checkpoint as policy base.
- Reference load: passed sequentially under `torch.no_grad()`.
- Reference energy: `E_ref_winner=0.8652140498161316`,
  `E_ref_loser=0.8322668075561523`.
- Policy energy: `E_policy_winner=0.8652140498161316`,
  `E_policy_loser=0.8322668075561523`.
- Beta: `0.1`.
- Scalar loss: `L_DPO=0.6931471824645996`.
- Backward / optimizer / LoRA / checkpoint save: none.

Because policy and reference are identical frozen weights in this smoke,
`Delta_policy == Delta_ref` and the scalar loss is `log(2)`. This validates the
formula and tensor plumbing, not preference learning. The next permitted step is
only a user-confirmed 1-pair backward-only dry-run with no optimizer and no
saved weights. Real DPO training remains blocked.

## DPO Backward-Only Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: passed for 1-pair backward-only plumbing with fallback
  `tiny_subset`.
- Gate F: no. Real DPO training remains disallowed.

Backward-only details:

- Reference energy: passed with frozen same LingBot-Fast checkpoint.
- Scalar DPO loss: passed.
- Primary `camera_adapter` gradient scope: failed with CUDA OOM at the current
  8-frame 480x832 latent size.
- Fallback `tiny_subset`: passed.
- Trainable fallback params: `head.head.bias`, `head.head.weight`.
- Trainable param count: `327,744`.
- Params with grad: `2`.
- Reference params with grad: `0`.
- Optimizer / optimizer step / checkpoint / LoRA save: none.

Next permitted step is not real training. If the user confirms, the next round
may do only a 1-pair optimizer-step dry-run, preferably after adding a smaller
LoRA/camera-adapter trainable scope. Large/multi-pair DPO training remains no.

## DPO Trainable Scope Sweep Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: partial/pass. VideoGPA pair/metadata, LingBot latent encode,
  condition encode, batch shape, policy energy, reference energy, scalar loss,
  and backward-only have all passed for plumbing scopes. A camera-aware scope
  sweep has now been attempted.
- Gate F: no. Real DPO training remains disallowed.

Scope sweep details:

- `tiny_subset`: passed, `327,744` trainable params.
- `head_only`: passed, `337,984` trainable params.
- `plucker_projection_only`: OOM, peak about `100.44 GB`.
- `action_scale_shift_tiny`: OOM, peak about `100.48 GB`.
- `camera_lora_tiny`: skipped because no existing LoRA params were injected.

Conclusion: the only passing scopes are still output-head plumbing scopes.
Existing camera bias scopes are semantically better but still retain too much
autograd graph at the current 8-frame 480x832 latent size. The next permitted
step is only to implement a tiny real LoRA/camera adapter injection path and
rerun backward-only. Do not run optimizer step yet. Real DPO training remains
blocked.

## Tiny LoRA Camera-Control Backward Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: pass/partial. VideoGPA pair/metadata, LingBot latent encode,
  condition encode, batch shape, policy energy, reference energy, scalar loss,
  and backward-only all pass. A meaningful runtime camera-control LoRA scope now
  also passes backward-only.
- Gate F: no. Real DPO training remains disallowed.

LoRA backward-only details:

- Scope: `camera_control_lora_tiny`.
- Runtime target modules:
  `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Rank/alpha: `2` / `4.0`.
- Trainable params: `40,960`.
- Loss: `0.6931474208831787`.
- LoRA params with grad: `4`.
- Base params with grad: `0`.
- Reference params with grad: `0`.
- NaN/Inf gradients: no.
- Optimizer / optimizer step / LoRA save / checkpoint save: none.

Next permitted step is only a user-confirmed 1-pair optimizer-step dry-run on
this LoRA scope, with no save and explicit before/after parameter checks. Real
DPO training and multi-pair training remain blocked.

## LoRA Optimizer-Step Dry-Run Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: pass/partial. VideoGPA pair/metadata, LingBot latent encode,
  condition encode, batch shape, policy energy, reference energy, scalar loss,
  backward-only, and tiny camera-control LoRA backward-only all pass. A 1-pair
  / 1-step optimizer-step dry-run on the same LoRA scope also passed.
- Gate F: no. Real DPO training remains disallowed.

Optimizer-step dry-run details:

- Scope: `camera_control_lora_tiny`.
- Runtime target modules:
  `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Rank/alpha: `2` / `4.0`.
- Optimizer: `AdamW`, lr `1e-5`, one param group, LoRA params only.
- Trainable params: `40,960`.
- Step count: `1`.
- `L_DPO_before`: `0.6931473016738892`.
- LoRA params changed: yes, max abs diff `9.981580660678446e-06`.
- Base sample params changed: no, max abs diff `0.0`.
- Reference sample params changed: no, max abs diff `0.0`.
- NaN/Inf gradients: no.
- LoRA save / checkpoint save: none.
- `restore_after_step`: passed; runtime LoRA params were restored in memory.

Next permitted step is not real training. If the user explicitly confirms, the
next round may do only a 1-pair overfit mini-loop such as 5 optimizer steps on
the same pair, no checkpoint, no LoRA save, and no multi-pair training.

## DPO 1-Pair Overfit Mini-Loop Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: pass/partial. VideoGPA pair/metadata, LingBot latent encode,
  condition encode, batch shape, policy energy, reference energy, scalar loss,
  backward-only, tiny camera-control LoRA backward-only, and 1-pair
  optimizer-step dry-run all pass. A bounded 1-pair / 5-step runtime LoRA
  mini-loop also passed.
- Gate F: no. Real DPO training remains disallowed.

Mini-loop details:

- Scope: `camera_control_lora_tiny`.
- Runtime target modules:
  `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Rank/alpha: `2` / `4.0`.
- Optimizer: `AdamW`, lr `1e-5`, LoRA params only.
- Steps: `5` on the same pair.
- Noise/timestep: resampled each step, but shared between winner and loser
  within each step.
- Loss values: `[0.6931473016738892, 0.6931471228599548,
  0.6931470632553101, 0.6931471228599548, 0.6931472420692444]`.
- LoRA params changed: yes, max abs diff `4.924208769807592e-05`.
- Base sample params changed: no, max abs diff `0.0`.
- Reference sample params changed: no, max abs diff `0.0`.
- LoRA params with grad: `4` each step.
- Base params with grad: `0` each step.
- NaN/Inf gradients: no.
- OOM: no.
- LoRA save / checkpoint save: none.
- `restore_after_loop`: passed; runtime LoRA params were restored in memory.

Because noise and timestep were resampled each step and the policy starts from
the same checkpoint as the reference, monotonic loss decrease is not expected in
this smoke. The run confirms finite repeated steps, stable gradients, LoRA-only
updates, and base/reference immutability.

Next permitted step is not real training. If the user explicitly confirms, a
future round may do only a tiny 5-pair or 10-pair overfit smoke, or a fixed
noise/timestep 1-pair diagnostic. Saved LoRA remains disabled by default, and
multi-pair real DPO training remains blocked.

## Fixed-Noise DPO Diagnostic Update

- Gate A: passed.
- Gate B: passed.
- Gate C: partial/pass.
- Gate D: partial/pass for smoke.
- Gate E: pass/partial. VideoGPA pair/metadata, LingBot latent encode,
  condition encode, batch shape, policy energy, reference energy, scalar loss,
  backward-only, tiny camera-control LoRA backward-only, 1-pair optimizer-step,
  1-pair 5-step resampled mini-loop, and a fixed-noise/fixed-timestep
  diagnostic all pass at the plumbing/safety level.
- Gate F: no. Real DPO training remains disallowed.

Fixed diagnostic details:

- Scope: `camera_control_lora_tiny`.
- Runtime target modules:
  `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`.
- Rank/alpha: `2` / `4.0`.
- Optimizer: `AdamW`, lr `1e-5`, LoRA params only.
- Steps: `10` on the same pair.
- Fixed noise seed: `123`.
- Fixed timestep: `579`.
- Loss values: `[0.6931471228599548, 0.6931471824645996,
  0.6931471824645996, 0.6931471824645996, 0.6931472420692444,
  0.6931471824645996, 0.6931472420692444, 0.6931472420692444,
  0.6931471824645996, 0.6931471824645996]`.
- Loss monotonic: no.
- Loss delta: `+5.960464477539063e-08`.
- Preference logits stayed near zero, around `1e-7`.
- LoRA params changed: yes, max abs diff `0.0001006147067528218`.
- Base sample params changed: no, max abs diff `0.0`.
- Reference sample params changed: no, max abs diff `0.0`.
- NaN/Inf gradients: no.
- OOM: no.
- LoRA save / checkpoint save: none.
- `restore_after_loop`: passed.

Interpretation: fixed-noise plumbing and safety passed, but the overfit signal
is weak and not monotonic at rank 2 / lr `1e-5`. The sign convention is still
consistent: larger positive preference logit lowers DPO loss, but the observed
logits are extremely small. This is not a reason to launch real training.

Next permitted step is not real training. If the user explicitly confirms, the
next round may do either a stronger fixed-noise sensitivity diagnostic, or a
very small 5-pair/10-pair overfit smoke with saved LoRA disabled. Full DPO
training remains blocked.

## GitHub Remote Integrity Gate

Future push steps must target the user-visible repository:

- Correct repo: `jh5117-debug/worldworld-phy`
- Fixed remote:
  `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Old incorrect remote: `world_model_phys.git`

Before pushing any branch, run:

```bash
git remote -v
git ls-remote --heads origin
```

The push is allowed only if `origin` fetch and push URLs both match the fixed
remote above. Do not push code, docs, or reports to a remote containing
`world_model_phys.git`. The helper script
`scripts/check_github_remote_integrity.sh` performs this check and should be
used before future push operations.


## Current DPO Status Before TDW Generation v2

DPO engineering gates are mostly passed for smoke: VideoGPA pair/metadata dry-run, LingBot latent encode, condition encode, same-noise/same-timestep batch, policy energy, reference energy, scalar DPO loss, LoRA backward, optimizer-step dry-run, and 1-pair mini-loop have all been validated. However, signal sensitivity remains weak, the 5-pair tiny overfit was skipped, and real DPO training is still not allowed.

Before any real training, we need stronger signal through a fixed-noise LR/scope sweep and a better data pool. TDW / Physion-style moving-camera v2 generation is therefore needed for camera-conditioned warmup and later reward-selected top/bottom winner-loser pairs. No VideoGPA 03_train, no Stage1, and no real DPO training should run at this stage.

## TDW Generation v2 Mild-Smoke Gate

The TDW / Physion-style generation v2 wrapper now has an explicit
`warmup_mild` camera set. The plan-level blocker that allowed possible
stress/reobserve leakage is fixed:

- allowed mild variants: `orbit_left_12`, `orbit_right_12`,
  `strafe_left_025`, `strafe_right_025`, `dolly_in_010`, `dolly_out_010`;
- banned warmup terms: lookaway, offscreen, reobserve, relative-yaw-180,
  occluder, extreme;
- 10-trial dry-run plan check: `bad_count=0`.

Actual TDW generation is still gated by display/GPU routing. The observed TDW
display `:8` appears to be configured on GPU0, while the current task only
allows GPU6/7. Therefore 1-sample actual TDW generation must wait for either a
GPU6/7 TDW display or explicit user approval. This does not change DPO gates:
real DPO training remains `no`.

## Accelerated TDW / DPO Gate Update

After explicit one-sample approval for GPU0-bound `DISPLAY=:8`, one
`warmup_mild` TDW sample was generated and validated:

- HDF5: `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_1samples/00000_drop_orbit_left_12_seed10000/0000.hdf5`
- template / camera: `drop` / `orbit_left_12`
- frame count: `83`
- target visible ratio: `1.0`
- max invisible frames: `0`
- camera path length: `0.5927`
- RGB/depth/id/camera/object state: present
- suitable for warmup: yes

LingBot camera arrays converted with `use_action=false` and dummy action, but
the converted `target.mp4` still needs a probe-confirmed writer fix. Therefore:

| Gate | Status |
|---|---|
| TDW 1-sample HDF5 | passed |
| TDW 1-sample validation | passed |
| TDW LingBot conversion | partial |
| TDW 10-sample smoke | not run; GPU0 approval required |
| TDW 50-sample validation | not run |
| DPO fast signal sweep | implemented, not completed on GPU |
| 5-pair tiny overfit | no-go |
| real DPO training | no |

The new `dpo_signal_sensitivity_fast` mode reuses policy/reference model loads
for fixed-noise LR sweeps, but the GPU run did not complete in this pass due
remote access instability. Pair-count expansion remains blocked until the signal
gate is actually measured.
## 2026-06-04 Gate Update: TDW Conversion + DPO Signal

Gate A: passed.

Gate B: passed.

Gate C: partial/pass.

Gate D: partial/pass.

Gate E:

| Component | Status |
|---|---|
| VideoGPA pair/metadata dry-run | passed |
| LingBot latent encode | passed |
| Condition encode | passed |
| Batch shape | passed |
| Policy energy | passed |
| Reference energy | passed |
| DPO scalar loss | passed |
| Backward-only | passed |
| Tiny camera-control LoRA backward-only | passed |
| 1-pair optimizer-step dry-run | passed |
| 1-pair mini-loop | passed |
| Fixed-noise diagnostic | stable but weak |
| `dpo_signal_sensitivity_fast` | runtime blocker; no completed LR summary |
| 5-pair tiny overfit | no-go |

Gate F:

Real DPO training: still no.

Next allowed DPO action: fix signal runner/runtime or target scope. Do not run 5-pair, 10-pair, or real training until signal gate passes.

## 2026-06-04 TDW 10-Sample Data Gate Update

TDW generation side:

| Gate | Status |
|---|---|
| warmup_mild plan | passed; bad_count 0 |
| 1-sample actual | passed |
| 1-sample LingBot conversion | passed |
| 10-sample actual | passed |
| 10-sample validation | passed |
| 10-sample LingBot conversion | passed |
| 50-sample | not run; approval required |
| 200 / 1k+ | no |

DPO side is unchanged:

- `dpo_signal_sensitivity_fast` remains runtime-blocked / incomplete;
- 5-pair tiny overfit remains no-go;
- real DPO training remains no.

Data caveat: the 10-sample run generated only `drop` scenes. Template-diverse generation should be fixed or explicitly waived before 50-sample validation.

## 2026-06-03 Template-Diverse TDW + DPO Signal Gate Update

TDW data side:

| Gate | Status |
|---|---|
| drop-only 10-sample smoke | passed |
| template coverage audit | completed |
| template-diverse plan | passed |
| template-diverse actual 10-sample | not run; GPU0 approval required |
| 50-sample validation | no-go until template-diverse 10 passes |

The new plan distribution is `drop:3`, `collision:3`, `roll:2`, `containment:2`, with no stress/reobserve camera variants.

DPO side:

| Gate | Status |
|---|---|
| scalar loss / backward / LoRA / optimizer plumbing | passed |
| fixed-noise diagnostic | stable but weak |
| `dpo_signal_sensitivity_fast` | no usable new multi-LR summary |
| 5-pair tiny overfit | no-go |
| real DPO training | no |

Next allowed DPO action remains signal/scope debugging only. Do not run 5-pair, 10-pair, or real DPO training until the signal gate passes.

## 2026-06-04 Template-Diverse Actual + DPO Signal Run

TDW data side:

| Gate | Status |
|---|---|
| template-diverse plan | passed |
| template-diverse actual 10-sample | failed |
| template-diverse validation | 0 accepted |
| template-diverse LingBot conversion | skipped |
| 50-sample validation | no-go |

The actual run failed because non-drop templates received drop-only upstream arguments. The wrapper now only appends those arguments for `template == "drop"`. A second actual run requires fresh user approval.

DPO side:

| Gate | Status |
|---|---|
| `dpo_signal_sensitivity_fast` | partial |
| LR settings completed | only partial `1e-5`, 3 steps |
| signal gate | no-go |
| 5-pair tiny overfit | no-go |
| real DPO training | no |

The observed `1e-5` steps were finite and had no NaN/Inf, but the multi-LR gate did not pass.

## 2026-06-04 Non-Drop Template Retry + DPO Signal Retry

TDW data side:

| Gate | Status |
|---|---|
| drop-only 10-sample smoke | passed |
| template-diverse plan | passed |
| non-drop command dry-run | passed |
| non-drop actual validation | failed: no HDF5 |
| template-diverse 10 retry | skipped |
| 50-sample validation | no-go |

The previous drop-only-args blocker is fixed: `collision`, `roll`, and `containment` no longer receive `--drop`, `--ymin`, `--ymax`, or `--dscale`. The new exact blocker is that the wrapper omitted upstream `--run 1`, so TDW returned successfully without writing HDF5. The wrapper now includes `--run 1`, but actual generation needs fresh user approval before rerun.

DPO side:

| Gate | Status |
|---|---|
| short `dpo_signal_sensitivity_fast` retry | incomplete |
| usable two-LR summary | no |
| 5-pair tiny overfit | no-go |
| real DPO training | no-go |

Next allowed actions:

1. request approval to rerun fixed non-drop 3-sample smoke, then template-diverse 10 only if non-drop validates;
2. make DPO signal runner faster or test a stronger LoRA target/scope;
3. keep 5-pair, 10-pair, VideoGPA `03_train.py`, and real DPO training disabled.

## 2026-06-04 Non-Drop `--run 1` Retry Gate

TDW side:

| Gate | Status |
|---|---|
| non-drop command dry-run with `--run 1` | passed |
| non-drop actual command return | 3/3 returned 0 |
| non-drop HDF5 validation | failed; 0/3 accepted |
| template-diverse 10 `run1` | skipped |
| 50-sample validation | no-go |

The commands now include `--run 1` and exclude drop-only arguments for non-drop templates. The remaining blocker is upstream non-drop template generation writing no HDF5 despite successful exit. Do not run template-diverse 10 or 50 until non-drop HDF5 generation works.

DPO side remains unchanged in this round: no DPO signal sweep was run, 5-pair remains no-go, and real DPO training remains no.

## 2026-06-04 TDW Template-Diverse Data Gate Update

TDW generation v2 data gate is now advanced past the non-drop/template-diverse smoke:

| Gate | Status |
|---|---|
| non-drop upstream wrapper fix | passed |
| non-drop 3-sample validation | passed, 3/3 |
| template-diverse 10 validation | passed, 10/10 |
| template distribution | drop 3 / collision 3 / roll 2 / containment 2 |
| LingBot cam-only conversion | passed, 10/10 |
| TDW 50-sample validation | not run; approval required |

This does not change DPO readiness:

- DPO signal-sensitivity remains no-go;
- 5-pair tiny overfit remains no-go until DPO signal improves;
- real DPO training remains no;
- VideoGPA `03_train.py` remains disallowed.

## TDW 50-Sample Data Gate Update

The TDW / Physion-style data gate has progressed independently of DPO training.
This does not permit DPO training yet.

Current TDW v2 status:

- `warmup_mild` camera set: passed.
- non-drop templates: passed after the absolute-output-path wrapper fix.
- template-diverse 10-sample smoke: passed.
- template-diverse 50-sample validation: passed.
- 50 planned distribution: `drop:15`, `collision:15`, `roll:10`, `containment:10`.
- 50 validation: `50/50` HDF5 complete, `50/50` suitable for warmup.
- LingBot cam-only conversion: `50/50`, with `use_action=false` and dummy zero `action.npy`.

DPO status is unchanged:

- signal-sensitivity remains weak / incomplete;
- 5-pair tiny overfit remains no-go;
- real DPO training remains no;
- VideoGPA `03_train.py` remains disallowed.

The data gate is now ready for a user-approved 200-sample TDW pilot, but that does not replace the DPO signal gate. Before any 5-pair or real DPO work, the fixed-noise signal sweep still needs a clear nonzero policy movement and a go/no-go report.

## Visible-Motion Data Gate Update

The previous TDW 50-sample gate should now be interpreted as a pipeline validation pass, not a final warmup-data-quality pass.

Reason:

- camera motion in `warmup_mild` is visually too weak;
- the batch is too close to ordinary I2V generation;
- it does not sufficiently stress whether LingBot follows poses/intrinsics.

New data gate:

`warmup_visible_motion`

The profile and validator have been added, but actual 10-sample generation is blocked until a GPU6/7 TDW display exists. GPU0-bound `DISPLAY=:8` is forbidden for this turn and was not used.

DPO status remains unchanged:

- no DPO training;
- no 5-pair;
- no VideoGPA `03_train.py`;
- signal-sensitivity remains a separate no-go gate.
## 2026-06-05 TDW visible-motion data gate status

No DPO training was run.

TDW data gate update:

- `warmup_mild` template-diverse 50 remains pipeline-valid but too static for final warmup main data.
- `warmup_visible_motion` 1-sample passed.
- `warmup_visible_motion` 10-sample generated 10 / 10 HDF5.
- Visible-motion quality accepted 5 / 10 samples.
- Only the 5 `suitable_for_visible_motion=true` samples were converted to LingBot cam-only inputs.

DPO remains gated separately:

- signal-sensitivity remains no-go from prior reports;
- 5-pair tiny overfit remains no-go;
- real DPO training remains no.

Next DPO step should wait until the signal runner is fixed and the visible-motion data profile is tuned.

## 2026-06-05 TDW visible-motion v2 gate status

No DPO training was run.

Data-side update:

- `warmup_visible_motion_v2` profile added;
- v2 plan dry-run passed locally;
- v2 actual generation later passed 10 / 10 on approved GPU0-bound `DISPLAY=:8`;
- v2 visible-motion acceptance passed 10 / 10;
- v2 LingBot cam-only conversion passed 10 / 10;
- no 50 / 200 / 1k run.

DPO remains no-go until both the data gate and signal gate are ready.

The data gate is now ready to ask for a 50-sample `warmup_visible_motion_v2` validation, but this does not change the DPO gate. No DPO training, 5-pair tiny overfit, or VideoGPA `03_train` should run until the signal gate is separately resolved and approved.

## 2026-06-06 TDW visible-motion v2 50-sample data gate status

No DPO training was run.

Data-side update:

- `warmup_mild` 50 remains pipeline-valid but too weak for final camera-conditioned warmup data.
- `warmup_visible_motion_v2` 10-sample smoke passed 10 / 10.
- `warmup_visible_motion_v2` 50-sample validation passed 50 / 50.
- Per-template accepted counts: drop 15, collision 15, roll 10, containment 10.
- LingBot cam-only conversion passed 50 / 50 with `use_action=false` and dummy zero `action.npy`.

Motion-quality summary:

- camera path length min/avg/max: `0.5016 / 1.0778 / 1.4814`;
- background motion proxy min/avg/max: `0.0121 / 0.0211 / 0.0332`;
- `too_static`: `0 / 50`;
- `too_extreme`: `0 / 50`.

DPO remains gated separately:

- signal-sensitivity remains no-go from prior reports;
- 5-pair tiny overfit remains no-go;
- real DPO training remains no;
- VideoGPA `03_train.py` remains disallowed.

The data gate is ready for a user-approved 200-sample visible-motion pilot. It does not authorize DPO training or any 200 / 1k generation automatically.

## 2026-06-06 TDW visible-motion v3 review status

No DPO training was run.

Data-side update:

- manual review rejected the v2 50-sample set as final warmup data despite numeric validation pass;
- `warmup_visible_motion_v3_start0_scene_diverse` was added and tested as a 50-sample review set;
- generated HDF5: `50 / 50`;
- validation OK: `50 / 50`;
- unique scene hashes: `50 / 50`;
- accepted for visible-motion v3: `28 / 50`;
- converted accepted samples: `28 / 28`;
- rejected samples: `22 / 50`, all caused by strafe variants failing `too_static` / `delayed_camera_motion`.

DPO remains gated separately:

- signal-sensitivity remains no-go from prior reports;
- 5-pair tiny overfit remains no-go;
- real DPO training remains no;
- VideoGPA `03_train.py` remains disallowed.

The data gate is not ready for 200 from this v3 revision. Tune the TDW camera profile first, then rerun a small smoke. No training or DPO should start from this dataset state.

### Human-review update

The user manually reviewed the v3 50 videos and confirmed that all 50 are usable. The data-side status is therefore updated to:

- v3 human review accepted: `50 / 50`;
- all-50 LingBot cam-only conversion: `50 / 50`;
- old generated_v2 waste assets cleaned up;
- a v3 200-sample pilot can be requested, but not run without explicit approval.

DPO remains unchanged: signal-sensitivity and 5-pair are still separate no-go gates, and no DPO training is approved.

## 2026-06-07 TDW v3 200 pilot status

No DPO training was run.

The TDW data-side 200 pilot completed:

- profile: `warmup_visible_motion_v3_start0_scene_diverse`;
- HDF5 generation: `200 / 200`;
- validation OK: `200 / 200`;
- scene diversity: `200 / 200` unique scene hashes;
- LingBot cam-only conversion: `200 / 200`;
- `use_action=false`: `200 / 200`;
- dummy `action.npy`: `200 / 200`.

The data is ready for human review and possible warmup indexing after review. DPO remains gated separately; signal-sensitivity and 5-pair are still no-go unless explicitly revisited.

## 2026-06-07 TDW v4 stronger smoke status

No DPO training was run.

A stronger visible-motion TDW smoke was generated for data review:

- profile: `warmup_visible_motion_v4_stronger_start0_review`;
- generated / validated / converted: `16 / 16 / 16`;
- suitable visible motion: `16 / 16`;
- too_static / too_extreme / delayed: `0 / 0 / 0`;
- `use_action=false` and dummy `action.npy` remain in the converted LingBot cam-only inputs.

This is data-side preparation only. DPO signal-sensitivity and 5-pair tiny overfit remain separate gates and were not run in this step.
## 2026-06-09 Pre-DPO Warmup Dataset Gate

TDW v5 aggressive 2x 200 is now registered as the current human-approved warmup candidate, but this remains pre-DPO.

- Dataset manifest/audit/split: passed.
- LingBot dataloader smoke: passed.
- Full LingBot-Fast model-load forward-loss: not yet passed.
- Placeholder no-model-load forward smoke: passed on GPU7 with no backward, no optimizer, and no checkpoint.
- `dpo_diag`: `not_applicable_pre_dpo`.

DPO training remains disallowed. Future DPO work should only resume after a warmup pilot produces usable camera-conditioned behavior and after reward-based winner/loser pair selection is rebuilt for the accepted TDW data.

## 2026-06-09 True LingBot-Fast Forward-Loss / MoE-Aware Gate

No DPO training was run.

The TDW v5 200 warmup candidate has now passed the real model-load forward-loss gate:

- real component load: `WanI2VFast` / `WanModelFast` / `Wan2_1_VAE` / `T5TokenizerFast`;
- scheduler: `FlowUniPCMultistepScheduler`;
- `num_train_timesteps`: `1000`;
- camera condition tensor: `[1, 384, 2, 60, 104]`;
- target video latent: `[16, 2, 60, 104]`;
- flow target: `noise - x0`;
- no backward, no optimizer, no checkpoint.

MoE/timestep conclusion:

- LingBot Base has high-noise / low-noise checkpoint branches;
- LingBot-Fast loaded in this runtime does not expose explicit expert routing;
- high/low losses are therefore scheduler-quantile diagnostics, not exact expert-boundary measurements.

Forward-loss result:

| Band | Timestep | Sigma | Loss | Finite |
|---|---:|---:|---:|---|
| diagnostic high-noise | 799 | 0.7990 | 0.046257 | yes |
| diagnostic low-noise | 200 | 0.2000 | 0.895799 | yes |
| random | 412 | 0.4120 | 0.437084 | yes |

Next step is not DPO. The next allowed action, only after explicit user approval, is a staged warmup pilot:

1. Stage A: high-noise/global-camera, max 100 steps, batch size 1, camera adapter/LoRA only.
2. Stage B: mixed/low-noise detail refinement only if Stage A is stable.

DPO remains gated until after warmup and reward-based winner/loser pair selection. `dpo_diag` for this experiment is `not_applicable_pre_dpo`.

## 2026-06-09 Stage A Warmup Pilot Update

No DPO training was run.

The TDW v5 200 human-approved warmup candidate passed a small Stage A high-noise/global-camera warmup pilot:

- mode: `staged_warmup_pilot`;
- model: real LingBot-Fast runtime (`WanI2VFast` / `WanModelFast`);
- VAE: `Wan2_1_VAE`;
- scheduler: `FlowUniPCMultistepScheduler`;
- diagnostic timestep: 799, sigma 0.799;
- trainable scope: runtime `camera_control_lora_tiny`;
- trainable params: 40,960;
- LoRA targets: `blocks.39.cam_shift_layer`, `blocks.39.cam_scale_layer`;
- steps: 20;
- train loss: finite, min 0.030702, max 0.062314;
- val losses: 0.033537 and 0.034270;
- LoRA tensors changed: 4;
- sampled base tensors changed: 0;
- no checkpoint, LoRA, or optimizer state was saved.

The first 100-step attempt was stopped after 3 steps because measured step time would likely exceed the timeout before writing a complete summary. The completed 20-step run satisfies the Stage A stability gate minimum.

Important limitation: the first 20 rows in the current train split were all `collision + orbit_right_64`. This pilot proves stability of the real warmup path, but not balanced template behavior. Future Stage A/B pilots should shuffle or balance the sampler.

Next allowed actions require explicit user approval:

1. Stage B mixed/low-noise pilot with shuffled/balanced sampler.
2. Rerun Stage A with approved LoRA/checkpoint save if rollout inspection is needed.
3. Pause and inspect metrics.

DPO remains later. Do not run reward calibration, winner/loser pair selection, VideoGPA `03_train`, or DPO training from this gate alone.

## 2026-06-09 Balanced Stage A Warmup Pilot Update

No DPO training was run.

The previous Stage A pilot was a minimal stability pass but had an unbalanced first-20 sample window (`collision + orbit_right_64` only). The balanced Stage A rerun fixes that issue.

Balanced Stage A result:

- sampler: `balanced`;
- balance keys: `template,camera_variant`;
- steps: `60`;
- first 20 templates: `drop:5`, `collision:5`, `roll:5`, `containment:5`;
- full 60 templates: `drop:15`, `collision:15`, `roll:15`, `containment:15`;
- camera variants in full run: `orbit_left_72`, `strafe_left_180`, `orbit_right_60`, `orbit_left_44`, `orbit_right_64`;
- train loss range: `0.033201` to `0.067220`;
- val losses: `0.037449`, `0.046542`, `0.057670`;
- timestep / sigma: `799 / 0.799`;
- trainable scope: `camera_control_lora_tiny`;
- trainable params: `40,960`;
- LoRA tensors changed: `4`;
- sampled frozen base tensors changed: `0`;
- no NaN/Inf or OOM.

Checkpoint status:

- one tiny adapter-only checkpoint was saved;
- path: `local_assets/experiments/exp_tdw_v5_200_stageA_balanced_warmup/checkpoint/stageA_balanced_camera_lora_final/adapter_state.pt`;
- size: `166,809` bytes;
- no full model checkpoint;
- no optimizer state.

Important note: validation sampling is still sequential and the three val probes were `collision + orbit_right_64`. This is sufficient for this train-sampler gate but future Stage B and rollout evaluation should use balanced validation / one-per-template rollout selection.

Next allowed action requires explicit user approval: tiny rollout smoke using the saved adapter. DPO, reward calibration, winner/loser pair selection, and VideoGPA `03_train` remain blocked.
## 2026-06-10 Scale-Up / Warmup / Reward-Pair Gate Update

TDW v5 aggressive 2x 200 is still the active camera-visible warmup dataset. Additional TDW scale-up is deferred until either GPU0 `DISPLAY=:8` is explicitly approved for TDW or a GPU4-7 TDW display is configured.

The existing balanced Stage A high-noise adapter checkpoint remains the next rollout candidate. A longer Stage A run is estimated to exceed 12 hours based on the 60-step runtime, so it requires explicit approval before execution.

New code now supports:

- loading the Stage A adapter into LingBot-Fast inference;
- selecting balanced rollout conditions from the TDW v5 manifest;
- scoring GT/base/adapter rollouts with reward v5 confidence reporting;
- constructing reward pairs only when confidence and margin pass.

DPO remains blocked. The next gate is a small base-vs-adapter rollout smoke, then reward scoring, then pair diagnostics.

## 2026-06-10 4-Condition Rollout Smoke Update

The bounded base-vs-Stage-A-adapter rollout smoke has passed:

- 4 conditions, one per template;
- base rollout: 4/4;
- Stage A adapter rollout: 4/4;
- adapter checkpoint load confirmed in runtime logs;
- GT/base/adapter video probe: 12/12;
- review gallery: `local_assets/reports/human_review/tdw_v5_stageA_4condition_base_vs_adapter/video_gallery.html`.

The first adapter attempt exposed a real runtime import bug: the generated LingBot runtime script did not include the project root in `sys.path`, so adapter LoRA injection could not import `cam_physgeo.dpo.lora_utils`. This is fixed in `run_inference.py` by passing `WORLD_MODEL_PHYS_ROOT` into the subprocess.

Reward scoring, reward-pair construction, DPO, rollout expansion, VideoGPA `03_train`, and Stage1 remain gated. The next decision should be human review first, then either reward scoring on these 4 conditions or a 12-condition rollout.

## 2026-06-10 4-Condition Reward / Pair Gate Update

No DPO training was run.

Reward v5 was run on the existing 4-condition rollout only; no new rollout, TDW generation, VideoGPA `03_train`, Stage1, reward calibration, or training was performed.

Reward results:

- rows scored: `12` (`GT:4`, `base:4`, `Stage A adapter:4`);
- GT avg: `0.492143`;
- Base avg: `0.294709`;
- Stage A adapter avg: `0.295647`;
- Adapter > Base: `2/4`, with very small margins;
- GT > Base and GT > Adapter: `4/4`.

Pair gate result: failed for DPO pair construction.

Reasons:

- generated reward confidence avg: `0.463235 < 0.5`;
- generated real-backend confidence avg: `0.411765 < 0.5`;
- `R_reobs` is unavailable for all rows;
- generated `phys`, `quality`, and `freeze` remain fallback-heavy;
- adapter/base margins are too small for robust preference labels.

No reward pairs were constructed. `dpo_diag` is now `reward_scored_pair_construction_blocked`, not DPO-ready.

Next allowed actions require explicit approval: human review, reward backend/debug work, or a 12-condition rollout+reward pass. DPO training remains blocked until reward confidence, margins, and pair coverage pass.
