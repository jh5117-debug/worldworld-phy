# DPO Protocol Literature Design

Updated: 2026-06-28T00:20:04

## Protocol v1 Goal

Build stable V2V-5 preference pairs before another DPO training attempt. This round does not train DPO.

## LocalDPO-Inspired Type A

Type A uses:

- winner = clean GT future frames 5-80
- loser = locally corrupted GT future frames 5-80
- prefix frames 0-4 unchanged
- affected region/time/mask saved

This gives DPO a localized and explainable failure rather than asking it to rank two arbitrary generated clips.

## SDPO-Inspired Safety Rules

Future training should monitor:

- winner improvement
- loser degradation
- reference-relative margin
- winner contribution to margin
- video quality before and after update

If margin comes mainly from loser degradation, the run should fail. A later trainer should implement SDPO-style safe-lambda or loser-gradient scaling.

## Linear-DPO-Inspired Future Objective

Protocol v1 stores continuous reward margins and reward vectors. This is intended to support Linear-DPO or flow-matching-specific DPO later, because the previous sigmoid DPO probe produced weak signal near 0.693.

## Current Pair Mix

- Type A local corruption: 50
- Type B GT vs medium-hard rollout: 16
- Type C teacher vs rollout: 0

Recommended first DPO subset: Type A only, then add Type B after full real-energy audit.
