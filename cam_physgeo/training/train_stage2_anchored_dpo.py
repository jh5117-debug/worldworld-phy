from __future__ import annotations
import argparse
from cam_physgeo.dpo.anchored_dataset import AnchoredPreferenceDataset
from cam_physgeo.training.train_utils import load_training_config, print_dry_run_plan

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--pair_manifest','--pairs',dest='pair_manifest',default=''); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--run',action='store_true'); ap.add_argument('--limit_pairs',type=int,default=0); ap.add_argument('--max_steps',type=int,default=0); a=ap.parse_args(argv)
    cfg=load_training_config(a.config); pair_manifest=a.pair_manifest or cfg.get('pair_manifest','manifests/cam_physgeo_dpo_pairs.jsonl')
    dataset_len=None; first_pair=None
    try:
        ds=AnchoredPreferenceDataset(pair_manifest,min_margin=float(cfg.get('min_margin',0.05) or 0.05))
        dataset_len=len(ds); first_pair=ds[0] if len(ds) else None
    except Exception as exc:
        first_pair={'error':repr(exc)}
    print_dry_run_plan('stage2_anchored_dpo', cfg, pair_manifest=pair_manifest, pairs=dataset_len, first_pair=first_pair, limit_pairs=a.limit_pairs, max_steps=a.max_steps, dpo_loss='E_theta(loser)-E_theta(winner) with same timestep/noise minus frozen reference delta', real_model_adapter='LingBot diffusion/flow energy adapter still guarded; no fake training success')
    if a.dry_run or not a.run:
        return 0
    raise RuntimeError('Stage2 real DPO training is guarded: build rollouts/logprob adapter before launching long training. Pair dataset and DPO loss are ready for integration.')
if __name__=='__main__': raise SystemExit(main())
