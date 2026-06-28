# Beta / Utility Scale Summary

- beta=0.05: mean_u=0, mean_grad_scale=0.025, near_zero_ratio=1.000, saturation_ratio=0.000
- beta=0.1: mean_u=0, mean_grad_scale=0.05, near_zero_ratio=1.000, saturation_ratio=0.000
- beta=0.2: mean_u=0, mean_grad_scale=0.1, near_zero_ratio=1.000, saturation_ratio=0.000
- beta=0.5: mean_u=0, mean_grad_scale=0.25, near_zero_ratio=1.000, saturation_ratio=0.000
- beta=1.0: mean_u=0, mean_grad_scale=0.5, near_zero_ratio=1.000, saturation_ratio=0.000
- beta=2.0: mean_u=0, mean_grad_scale=1, near_zero_ratio=1.000, saturation_ratio=0.000
- beta=5.0: mean_u=0, mean_grad_scale=2.5, near_zero_ratio=1.000, saturation_ratio=0.000
- beta=10.0: mean_u=0, mean_grad_scale=5, near_zero_ratio=1.000, saturation_ratio=0.000

At initialization/policy-reference equality, u is effectively zero for all rows, so sigmoid DPO sits at the 0.693 no-margin point. Larger beta increases local gradient scale but does not create a winner-improving direction by itself.
