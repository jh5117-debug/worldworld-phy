# Final Report: Accelerated TDW and DPO Gate Smoke Checks

## Current Status

| Item | Status |
|---|---|
| Worktree used for code/docs | `/tmp/worldworld_phy_push_tdw_prd` |
| Remote execution worktree | `/home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_fixed_noise_diagnostic_work/world_model_phys_tdw_generation_v2_prd_work/world_model_phys_tdw_generation_v2_mild_smoke_work` |
| Branch | `physion-accelerated-gates-tdw-dpo` |
| Remote | `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git` |
| `local_assets` | symlinked shared asset tree on remote |
| Training | no |
| VideoGPA `03_train.py` | no |
| Stage1 | no |
| LoRA/checkpoint save | no |
| `local_assets` commit | no |

## Gate Board Final

| Gate | Status | Notes |
|---|---|---|
| TDW warmup_mild plan | passed | no stress/reobserve variants; `bad_count=0` |
| TDW 1-sample actual | passed | one user-approved GPU0-bound `DISPLAY=:8` sample |
| TDW 1-sample validation | passed | HDF5 complete and target visible |
| TDW LingBot conversion | partial | camera arrays/action/metadata converted; target MP4 probe still blocked |
| TDW 10-sample smoke | not run | GPU0 approval required; conversion not fully complete |
| TDW 50-sample validation | not run | requires 10-sample pass |
| DPO signal fast runner | implemented | `dpo_signal_sensitivity_fast` added |
| DPO signal GPU run | not completed | remote SSH instability prevented safe launch |
| 5-pair tiny overfit | no-go | signal gate incomplete |
| full TDW generation | no | staged validation incomplete |
| real DPO training | no | still disallowed |

## TDW 1-Sample Result

| Metric | Value |
|---|---|
| Generated count | 1 |
| Success count | 1 HDF5 |
| Rejected count | 0 at HDF5 validation |
| Profile | `warmup_mild` |
| Template | `drop` |
| Camera variant | `orbit_left_12` |
| Display / GPU | `DISPLAY=:8`, GPU0, explicitly approved for this one sample |
| HDF5 | `local_assets/data/physion/generated_v2/raw_hdf5/warmup_mild_1samples/00000_drop_orbit_left_12_seed10000/0000.hdf5` |
| Frame count | 83 |
| RGB/depth/id | present |
| camera pose / position / aim | present |
| projection / camera matrix | present |
| object state | present |
| target visible ratio | 1.0 |
| max invisible frames | 0 |
| camera path length | 0.5927 |
| contact sheet | `local_assets/data/physion/generated_v2/reports/contact_sheets/00000_drop_orbit_left_12_seed10000_0000_contact_sheet.jpg` |
| suitable for warmup | yes, at HDF5 level |

The original system Python lacked `h5py`, so validation was rerun with the TDW
environment Python.

## LingBot Conversion

Converted assets:

- `poses.npy`: `(81, 4, 4)`;
- `intrinsics.npy`: `(81, 4, 4)` projection matrices, runtime-convertible to
  LingBot `(81, 4)`;
- `action.npy`: dummy zero `(81, 4)`;
- `metadata.json`: `use_action=false`;
- `depth.npy` and `id_mask.npy`;
- `image.jpg` via direct first-frame fallback.

Blocked / partial:

- `target.mp4` was emitted, but remote `probe_video` did not validate it.
- The conversion code was updated with stricter video writer fallbacks, but SSH
  instability prevented one final probe-confirmed rerun on the remote machine.

Because MP4 probing is not yet green, 10-sample generation was not run.

## DPO Signal

Implemented:

- New mode: `dpo_signal_sensitivity_fast`.
- Reuses one reference load and one policy load across LR settings.
- Restores runtime LoRA params before each LR.
- Caches reference metrics for fixed-noise/fixed-timestep steps.
- Keeps no-save/no-checkpoint/no-real-training constraints.

Run status:

- First remote attempt exited before model load because the shell had no
  `python` command.
- Restart with the LingBot env Python was blocked by repeated SSH reset/timeout.
- No GPU6/7 DPO fast sweep completed.

Gate decision:

- Signal gate remains incomplete.
- 5-pair tiny overfit remains no-go.

## Safety

- No real training.
- No VideoGPA `03_train.py`.
- No Stage1.
- No LingBot rollout.
- No reward calibration.
- No LoRA or checkpoint saved.
- No 10/50/200/1k TDW generation.
- No generated HDF5/MP4/NPY/local_assets outputs committed.
- GPU0 was used only for the approved one-sample TDW smoke; later GPU0
  multi-sample use requires approval.

## Next Actions

1. Finish the probe-confirmed `target.mp4` writer rerun for the accepted
   1-sample, using the patched fallback code.
2. Ask the user before any GPU0-bound 10-sample TDW smoke, or configure a GPU6/7
   TDW display.
3. Run `dpo_signal_sensitivity_fast` on GPU6/7 when SSH is stable.
4. Keep 5-pair tiny overfit blocked until the signal sweep completes and shows
   stable nonzero `Delta_policy` movement.
5. Full TDW generation and real DPO training remain blocked until staged gates
   pass and the user explicitly approves.
