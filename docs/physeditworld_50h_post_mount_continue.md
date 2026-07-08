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
4. Smoke LingBot manifest validation.
5. Backend readiness check before any baseline/warm-up command is considered.
6. Pipeline gate collector.
7. Requirement matrix refresh.

By default the conversion smoke writes only the non-canonical smoke manifest:

```text
manifests/physeditworld_50h_lingbot_smoke_train.jsonl
```

The canonical LingBot manifests remain empty placeholders until the smoke passes and full conversion is explicitly requested:

```bash
RUN_FULL_CONVERSION=1 PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h bash scripts/continue_physeditworld_after_mount.sh
```

The default report records this as `POST_MOUNT_CANONICAL_CONVERSION_DEFERRED`; it should not be treated as a failed smoke conversion.

It does not start warm-up training, checkpoint rollout, DPO, StageB, GRPO, broad-LoRA, deletion, or large file push.

If no root is provided, the expected decision is:

```text
POST_MOUNT_BLOCKED_AT_ROOT_INPUT
```

Outputs:

- `reports/physeditworld_50h/post_mount/post_mount_status.csv`
- `reports/physeditworld_50h/post_mount/post_mount_status.json`
- `reports/physeditworld_50h/post_mount/post_mount_summary.md`
