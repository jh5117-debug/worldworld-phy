# PhysEditWorld Root Schema Probe

Decision: `PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT`

## Roots

- `BLOCKED` / `PHYS_EDITWORLD_SCHEMA_PROBE_WAITING_FOR_ROOT`
  - files/dirs scanned: 0/0
  - counts: video=0, action=0, camera=0, intrinsics=0, gravity=0, replay=0, manifest=0
  - layouts: none
  - signals: none
  - blockers: PHYS_EDITWORLD_ROOTS is empty
  - next: export PHYS_EDITWORLD_ROOTS=/path/to/physeditworld_selected_50h

## Safety

This probe is CPU/IO only. It scans bounded filenames and shallow layout evidence; it does not decode videos, copy files, delete files, use GPUs, train, rollout, or run DPO.
