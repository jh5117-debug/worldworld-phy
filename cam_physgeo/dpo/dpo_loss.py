def dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta: float=0.1):
    try:
        import torch
    except Exception as exc:
        raise RuntimeError('dpo_loss requires torch') from exc
    logits=beta*((policy_chosen-policy_rejected)-(ref_chosen-ref_rejected))
    return -torch.nn.functional.logsigmoid(logits).mean()

def diffusion_energy_dpo_loss(policy_winner_error, policy_loser_error, ref_winner_error, ref_loser_error, beta: float=0.1):
    """Energy-form DPO for diffusion/flow models.

    Lower denoising or velocity prediction error is preferred. The same noise
    and timestep must be used for winner and loser before calling this helper.
    """
    try:
        import torch
    except Exception as exc:
        raise RuntimeError('diffusion_energy_dpo_loss requires torch') from exc
    delta_policy = policy_loser_error - policy_winner_error
    delta_ref = ref_loser_error - ref_winner_error
    return -torch.nn.functional.logsigmoid(beta * (delta_policy - delta_ref)).mean()
