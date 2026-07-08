# PhysEditWorld 50h Post-Mount Continuation

When the selected PhysEditWorld 50h root becomes visible on H20 or PAI, set `PHYS_EDITWORLD_ROOTS` and run:

```bash
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h \
bash scripts/continue_physeditworld_after_mount.sh
```

The command performs only safe CPU/IO preparation and gate collection:

1. Phase 1 manifest audit.
2. Replay-group-safe split.
3. Prompt-only LingBot conversion smoke, limit 32.
4. Pipeline gate collector.
5. Requirement matrix refresh.

It does not start warm-up training, checkpoint rollout, DPO, StageB, GRPO, broad-LoRA, deletion, or large file push.

If no root is provided, the expected decision is:

```text
POST_MOUNT_BLOCKED_AT_ROOT_INPUT
```

Outputs:

- `reports/physeditworld_50h/post_mount/post_mount_status.csv`
- `reports/physeditworld_50h/post_mount/post_mount_status.json`
- `reports/physeditworld_50h/post_mount/post_mount_summary.md`
