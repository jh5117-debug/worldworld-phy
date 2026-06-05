# Current State Before Visible-Motion v2

Date: 2026-06-05

## v1 Result

`warmup_visible_motion` v1 was a partial pass:

- generated HDF5: 10 / 10;
- validation OK: 10 / 10;
- suitable for warmup: 10 / 10;
- suitable for visible motion: 5 / 10;
- converted to LingBot cam-only: 5 / 10.

## Accepted v1 Samples

- `drop + orbit_left_24`
- `drop + orbit_right_24`
- `drop + orbit_left_28`
- `collision + strafe_left_050`
- `collision + strafe_right_050`

These samples showed visibly stronger camera / background motion than the earlier `warmup_mild` 50-sample validation batch.

## Rejected v1 Samples

| Template | Camera | Reason |
|---|---|---|
| collision | `orbit_right_28` | too extreme; camera path 1.5903 > 1.50 |
| roll | `dolly_in_025` | too static; path 0.2518 < 0.45 |
| roll | `dolly_out_025` | too static; path 0.2518 < 0.45 and background motion too low |
| containment | `orbit_left_24` | too extreme; path 1.7776 > 1.50 |
| containment | `orbit_right_24` | too extreme; path 1.7776 > 1.50 |

## Template Problems

- `drop`: orbit 24/28 works well.
- `collision`: strafe 0.50 works; orbit 28 is too strong.
- `roll`: dolly 0.25 is still too weak; use strafe/orbit instead.
- `containment`: orbit 24/28 is too strong; use smaller orbit 18/20 or strafe.

## Why Not Directly Run 50

The v1 acceptance rate is only 5/10, and two templates have systematic failures. Running 50 now would waste GPU and storage on predictable rejections.

## v2 Direction

`warmup_visible_motion_v2` should be template-aware:

- per-template camera variant lists;
- avoid dolly for roll;
- avoid orbit 28 for collision;
- avoid orbit 24/28 for containment;
- keep the same visible-motion validator thresholds.
