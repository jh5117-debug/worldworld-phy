# GPU8 Allocation and Cleanup Report

Updated: 2026-06-24 12:47:51 CST

## Permission State

User authorized physical GPU0-7 for evaluation, rollout, LoRA sweep, and DPO probe. Prior GPU0-only-for-TDW restriction is removed for this round.

## GPU Snapshot

```text
index, name, memory.total [MiB], memory.used [MiB], utilization.gpu [%]
0, NVIDIA H20, 97871 MiB, 28 MiB, 0 %
1, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
2, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
3, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
4, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
5, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
6, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
7, NVIDIA H20, 97871 MiB, 1 MiB, 0 %
```

## PMON

```text
# gpu         pid   type     sm    mem    enc    dec    jpg    ofa    command 
# Idx           #    C/G      %      %      %      %      %      %    name 
    0     883875     G      -      -      -      -      -      -    Xorg           
    1          -     -      -      -      -      -      -      -    -              
    2          -     -      -      -      -      -      -      -    -              
    3          -     -      -      -      -      -      -      -    -              
    4          -     -      -      -      -      -      -      -    -              
    5          -     -      -      -      -      -      -      -    -              
    6          -     -      -      -      -      -      -      -    -              
    7          -     -      -      -      -      -      -      -    -
```

## Tmux Snapshot

```text
15: 1 windows (created Tue Apr  7 12:45:47 2026)
21: 1 windows (created Wed Apr  8 08:01:54 2026)
22: 1 windows (created Wed Apr  8 15:31:21 2026)
27: 1 windows (created Tue Apr 21 02:25:13 2026)
29: 1 windows (created Wed Apr 22 18:47:08 2026)
30: 1 windows (created Wed Apr 22 18:48:12 2026)
88: 2 windows (created Wed May 13 14:22:34 2026)
89: 2 windows (created Fri May 15 00:27:39 2026)
arcc: 1 windows (created Mon Mar 23 07:22:24 2026)
arcc_gtr: 1 windows (created Tue Mar 24 10:53:14 2026)
chen_zhihong: 1 windows (created Mon Apr 20 10:03:48 2026)
compare_gpqa: 1 windows (created Tue Mar 24 07:45:08 2026)
copydata: 1 windows (created Tue Apr 21 04:58:56 2026)
dl_hm3d: 1 windows (created Mon May 11 09:35:47 2026)
down_tos: 1 windows (created Sat Apr 25 18:23:49 2026)
dpo_s1_resume: 1 windows (created Sat May  2 22:12:38 2026)
dpo_smoke: 1 windows (created Thu Apr 23 09:54:22 2026)
fast_stageA_high_only_formal_monitor_20260622_1948: 1 windows (created Mon Jun 22 19:45:41 2026)
fast_stageA_train_preflight_supervisor_20260623_014645: 1 windows (created Tue Jun 23 01:46:45 2026)
gpqa: 1 windows (created Sun Mar 22 04:43:52 2026)
gsm8k: 1 windows (created Mon Mar 30 02:18:57 2026)
habitat: 1 windows (created Mon Apr 20 10:07:43 2026)
humaneval: 1 windows (created Sat Mar 21 11:53:46 2026)
humaneval_gtr: 1 windows (created Tue Mar 24 12:09:31 2026)
lingbot_fast_monitor: 1 windows (created Wed Apr 29 18:15:38 2026)
log-14: 1 windows (created Thu Apr  2 13:07:37 2026) (group log)
math_eval: 1 windows (created Wed Mar 18 11:54:51 2026)
math_eval2: 1 windows (created Wed Mar 18 12:06:43 2026)
mmlu: 1 windows (created Sat Mar 21 11:02:11 2026)
mmlu_gtr: 1 windows (created Wed Mar 25 11:15:10 2026)
mmlupro: 1 windows (created Sun Mar 22 05:03:36 2026)
mmlupro_gtr: 1 windows (created Mon Mar 23 09:14:10 2026)
refusion: 1 windows (created Sun May 10 12:11:37 2026)
run_all_75: 1 windows (created Sat May  9 19:40:23 2026)
safe: 1 windows (created Wed Apr  1 10:16:26 2026)
skill-20: 1 windows (created Tue Apr  7 17:30:37 2026) (group skill)
tdw_v5_4000_monitor: 1 windows (created Wed Jun 17 14:44:35 2026)
wan_layers_late: 1 windows (created Tue May  5 01:05:01 2026)
wan_layers_mid: 1 windows (created Tue May  5 01:04:21 2026)
wan_ood: 1 windows (created Sat May  9 16:23:46 2026)
wan_top2: 1 windows (created Mon May  4 16:07:18 2026)
wan_top3: 1 windows (created Mon May  4 16:07:42 2026)
wan_top5: 1 windows (created Mon May  4 16:08:00 2026)
world_safe: 1 windows (created Tue Apr  7 15:15:03 2026) (group world_safe)
world_safe-18: 1 windows (created Tue Apr  7 17:03:04 2026) (group world_safe)
```

## Relevant Processes

```text
3708071 3707979 3707979       00:02 -                \_ /home/nvme03/workspace/lingbot-world/.conda_envs/lingbot-world-v2/bin/python -
 115577  288492  115577  1-17:02:10 -    \_ bash -c cd /home/nvme04/workspace/world_model_phys/PHYS/world_model_phys_stageA_v5_broad_lora_work && while true; do echo ==== \Mon Jun 22 19:45:41 CST 2026 ====; echo --sessions--; tmux has-session -t fast_stageA_high_only_formal_balanced_20260622_1925 2>/dev/null && echo train_running || echo train_ended; tmux has-session -t tdw_v5_4000_gpu0_scaleup 2>/dev/null && echo tdw_scaleup_alive || echo tdw_scaleup_missing; tmux has-session -t tdw_v5_4000_monitor 2>/dev/null && echo tdw_monitor_alive || echo tdw_monitor_missing; echo --gpu--; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; echo --metrics--; tail -n 3 local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/formal_fast_stageA_high_only_balanced_snapshot_20260622_1830_20260622_1925/checkpoints/fast_stageA_high_only_balanced_snapshot_20260622_1830/high_only_phase/metrics.jsonl 2>/dev/null || true; sleep 300; done >> local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/logs/formal_fast_stageA_high_only_monitor_20260622_1948.log 2>&1
3729144  288492 3729144  1-11:01:05 -    \_ bash -c bash 'local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/supervision_20260623_014645/supervise_training_and_preflight.sh' >> 'local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/logs/supervise_training_and_preflight_20260623_014645.log' 2>&1
3729147 3729144 3729144  1-11:01:05 -        \_ bash local_assets/experiments/fast_stageA_high_only_data_gate_20260622_135505/supervision_20260623_014645/supervise_training_and_preflight.sh
```

## Cleanup Decision

No process was killed for this PRD/checkpoint stage. Existing monitor/supervisor bash sessions do not occupy GPU memory and were left untouched. Xorg was not modified. No GPU reset, `pkill`, or `killall` was used.

## Planned GPU Mapping

- Small-LoRA A: GPU0,1
- Small-LoRA B: GPU2,3
- Small-LoRA C: GPU4,5
- Small-LoRA D: GPU6,7
- DPO BF16 preflight later: GPU7, then GPU6/7, then GPU0-7

All mappings must be revalidated immediately before launch.
