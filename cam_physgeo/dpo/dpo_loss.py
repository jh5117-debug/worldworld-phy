def dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta: float=0.1):
    try:
        import torch
    except Exception as exc:
        raise RuntimeError('dpo_loss requires torch') from exc
    logits=beta*((policy_chosen-policy_rejected)-(ref_chosen-ref_rejected))
    return -torch.nn.functional.logsigmoid(logits).mean()
