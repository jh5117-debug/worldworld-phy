from __future__ import annotations


def dpo_energy_logits(
    policy_winner_energy,
    policy_loser_energy,
    ref_winner_energy,
    ref_loser_energy,
    *,
    beta: float = 0.1,
):
    """Return anchored DPO logits for energy-style video losses.

    Lower energy is better.  The preference signal is therefore the loser-minus-
    winner energy gap.  DPO should increase the policy gap relative to the
    frozen reference without merely changing the absolute energy scale.
    """

    try:
        import torch  # noqa: F401
    except Exception as exc:  # pragma: no cover - import environment guard
        raise RuntimeError("dpo_energy_logits requires torch") from exc

    delta_policy = policy_loser_energy - policy_winner_energy
    delta_ref = ref_loser_energy - ref_winner_energy
    return float(beta) * (delta_policy - delta_ref)


def dpo_loss(
    policy_chosen,
    policy_rejected,
    ref_chosen,
    ref_rejected,
    beta: float = 0.1,
    *,
    reduction: str = "mean",
):
    """Anchored DPO loss using winner/loser energies.

    The argument names keep compatibility with older callers where
    ``chosen == winner`` and ``rejected == loser``.  Values are energies, not
    log-probabilities.
    """

    try:
        import torch
    except Exception as exc:  # pragma: no cover - import environment guard
        raise RuntimeError("dpo_loss requires torch") from exc

    logits = dpo_energy_logits(
        policy_chosen,
        policy_rejected,
        ref_chosen,
        ref_rejected,
        beta=beta,
    )
    loss = -torch.nn.functional.logsigmoid(logits)
    if reduction == "mean":
        return loss.mean()
    if reduction == "sum":
        return loss.sum()
    if reduction == "none":
        return loss
    raise ValueError(f"unsupported reduction: {reduction}")


def dpo_energy_diagnostics(
    policy_winner_energy,
    policy_loser_energy,
    ref_winner_energy,
    ref_loser_energy,
    *,
    beta: float = 0.1,
) -> dict:
    """Return scalar diagnostics for anchored DPO monitoring."""

    logits = dpo_energy_logits(
        policy_winner_energy,
        policy_loser_energy,
        ref_winner_energy,
        ref_loser_energy,
        beta=beta,
    )
    loss = dpo_loss(
        policy_winner_energy,
        policy_loser_energy,
        ref_winner_energy,
        ref_loser_energy,
        beta=beta,
    )
    try:
        import torch

        implicit_accuracy = (logits > 0).to(torch.float32).mean()
        to_float = lambda x: float(x.detach().mean().cpu())
    except Exception:  # pragma: no cover - non-tensor fallback
        implicit_accuracy = 1.0 if float(logits) > 0 else 0.0
        to_float = float

    return {
        "dpo_loss": to_float(loss),
        "implicit_accuracy": to_float(implicit_accuracy),
        "policy_winner_energy": to_float(policy_winner_energy),
        "policy_loser_energy": to_float(policy_loser_energy),
        "ref_winner_energy": to_float(ref_winner_energy),
        "ref_loser_energy": to_float(ref_loser_energy),
        "delta_policy": to_float(policy_loser_energy - policy_winner_energy),
        "delta_ref": to_float(ref_loser_energy - ref_winner_energy),
        "reference_relative_margin": to_float(
            (policy_loser_energy - policy_winner_energy)
            - (ref_loser_energy - ref_winner_energy)
        ),
    }
