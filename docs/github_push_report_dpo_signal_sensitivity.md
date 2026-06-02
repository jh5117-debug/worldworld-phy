# GitHub Push Report: DPO Signal Sensitivity

## Branch

- Branch: `physion-dpo-signal-sensitivity`
- Correct repo: `jh5117-debug/worldworld-phy`
- Remote: `ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git`
- Commit message: `Add DPO signal sensitivity summary reports`

## Scope

Committed lightweight documentation only:

- `docs/lora_functional_influence_probe_report.md`
- `docs/dpo_lr_sensitivity_sweep_report.md`
- `docs/dpo_scope_sensitivity_sweep_report.md`
- `docs/dpo_sign_beta_diagnostic_report.md`
- `docs/signal_sensitivity_summary.md`
- `docs/final_report_dpo_signal_sensitivity.md`
- `docs/github_push_report_dpo_signal_sensitivity.md`

Not committed:

- `local_assets/`
- optimizer outputs
- gradient tensors
- encoded latents
- generated videos
- energy tensors
- HDF5/MP4/NPY/NPZ/PT/PTH/safetensors
- saved LoRA weights
- checkpoints
- third-party raw repos

## Remote Integrity

Before push, verify:

```bash
git remote -v
git ls-remote --heads origin "$(git branch --show-current)"
```

The branch must be pushed only to `jh5117-debug/worldworld-phy`, never to
`world_model_phys.git`.
