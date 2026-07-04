Current Status: SCOPE_PASS

# v12 LoRA Scope Winner-Anchor Sanity

## L0_camera_r4

- Status: `WINNER_ANCHOR_REPEAT_PASS`
- Rows/pass: 5 / 5
- Mean winner improvement post: `3.560781478881836e-05`
- Final winner improvement post: `0.00015497207641601562`
- Mean loser degradation post: `-4.887580871582031e-06`
- Winner contribution ratio: `0.6911888598020337`

## L1_camera_r8

- Status: `WINNER_ANCHOR_REPEAT_FAIL`
- Rows/pass: 5 / 5
- Mean winner improvement post: `-4.541873931884766e-06`
- Final winner improvement post: `-0.00016415119171142578`
- Mean loser degradation post: `-6.37054443359375e-05`
- Winner contribution ratio: `0.6122246696035243`

## L2_camera_temporal_r4

- Status: `WINNER_ANCHOR_REPEAT_FAIL`
- Rows/pass: 5 / 5
- Mean winner improvement post: `2.429485321044922e-05`
- Final winner improvement post: `-1.1920928955078125e-07`
- Mean loser degradation post: `-5.754232406616211e-05`
- Winner contribution ratio: `0.4`

## L3_camera_cross_r4

- Status: `WINNER_ANCHOR_REPEAT_FAIL`
- Rows/pass: 5 / 5
- Mean winner improvement post: `-1.5294551849365236e-05`
- Final winner improvement post: `-0.00019311904907226562`
- Mean loser degradation post: `-1.6117095947265624e-05`
- Winner contribution ratio: `0.35832923832923835`

Decision: `SCOPE_PASS`; best scope: `L0_camera_r4`. DPO may run only if decision is SCOPE_PASS.
