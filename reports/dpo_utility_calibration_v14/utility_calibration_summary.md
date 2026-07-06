# Utility Calibration Real-Energy Status

Real LingBot energy was attempted with `s_pass` limit=1 on GPU4 and timed out after 300 seconds before writing a pair row. Therefore these v14 subset utility CSVs are coverage/blocker files, not real energy evidence.
- `energy_utility_all500.csv`: rows=500, status={'MISSING_REAL_ENERGY': 500}
- `energy_utility_local_mask.csv`: rows=485, status={'MISSING_REAL_ENERGY': 485}
- `energy_utility_rollout_only.csv`: rows=15, status={'MISSING_REAL_ENERGY': 15}
- `energy_utility_s_fail.csv`: rows=0, status={}
- `energy_utility_s_pass.csv`: rows=4, status={'MISSING_REAL_ENERGY': 4}
- `energy_utility_stratified100.csv`: rows=100, status={'MISSING_REAL_ENERGY': 100}
- `energy_utility_synthetic.csv`: rows=485, status={'MISSING_REAL_ENERGY': 485}
