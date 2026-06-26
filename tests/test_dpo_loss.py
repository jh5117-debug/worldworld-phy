from __future__ import annotations


def test_energy_dpo_prefers_larger_policy_margin():
    import torch

    from cam_physgeo.dpo.dpo_loss import dpo_energy_diagnostics, dpo_loss

    ref_winner = torch.tensor([0.30])
    ref_loser = torch.tensor([0.50])
    weak_policy_winner = torch.tensor([0.30])
    weak_policy_loser = torch.tensor([0.50])
    strong_policy_winner = torch.tensor([0.20])
    strong_policy_loser = torch.tensor([0.70])

    weak = dpo_loss(weak_policy_winner, weak_policy_loser, ref_winner, ref_loser, beta=1.0)
    strong = dpo_loss(strong_policy_winner, strong_policy_loser, ref_winner, ref_loser, beta=1.0)

    assert strong.item() < weak.item()
    diag = dpo_energy_diagnostics(
        strong_policy_winner,
        strong_policy_loser,
        ref_winner,
        ref_loser,
        beta=1.0,
    )
    assert diag["delta_policy"] > diag["delta_ref"]
    assert diag["reference_relative_margin"] > 0


def test_energy_dpo_backward_has_nonzero_gradient():
    import torch

    from cam_physgeo.dpo.dpo_loss import dpo_loss

    margin_gain = torch.nn.Parameter(torch.tensor(0.0))
    ref_winner = torch.tensor(0.2)
    ref_loser = torch.tensor(0.6)
    policy_winner = ref_winner - 0.5 * margin_gain
    policy_loser = ref_loser + 0.5 * margin_gain
    loss = dpo_loss(policy_winner, policy_loser, ref_winner, ref_loser, beta=0.5)
    loss.backward()

    assert margin_gain.grad is not None
    assert abs(float(margin_gain.grad)) > 0
