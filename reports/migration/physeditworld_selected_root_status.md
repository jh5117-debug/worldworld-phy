# PhysEditWorld Selected Root Status

Decision: `PHYS_EDITWORLD_ROOT_SELECTION_BLOCKED_NO_ROOT`

## Roots

- `BLOCKED`
  - score: 0
  - exists/is_dir: False/False
  - signals: none
  - blocker: PHYS_EDITWORLD_ROOTS is empty
  - next: set PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h

## Lock

- lock path: `reports/migration/physeditworld_selected_root.lock.json`
- lock written: no

## Next Commands

```bash
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h bash scripts/migration/select_physeditworld_root.sh
PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h bash scripts/continue_physeditworld_after_mount.sh
```

## Safety

This selector is CPU/IO only. It does not copy data, delete files, train, rollout, run DPO, use GPUs, or push large artifacts.
