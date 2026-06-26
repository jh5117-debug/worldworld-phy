from __future__ import annotations


def test_same_noise_timestep_pairs_are_identical():
    import torch

    from cam_physgeo.training.train_stage2_anchored_dpo import same_noise_timestep

    batch = same_noise_timestep(batch_size=3, latent_shape=(2, 3), seed=11, timestep=412)

    assert torch.equal(batch["winner_noise"], batch["loser_noise"])
    assert torch.equal(batch["winner_timestep"], batch["loser_timestep"])
    assert batch["winner_noise"].shape == (3, 2, 3)
    assert batch["winner_timestep"].tolist() == [412, 412, 412]


def test_same_noise_timestep_is_seeded():
    import torch

    from cam_physgeo.training.train_stage2_anchored_dpo import same_noise_timestep

    a = same_noise_timestep(batch_size=1, latent_shape=(2, 2), seed=7)
    b = same_noise_timestep(batch_size=1, latent_shape=(2, 2), seed=7)
    c = same_noise_timestep(batch_size=1, latent_shape=(2, 2), seed=8)

    assert torch.equal(a["winner_noise"], b["winner_noise"])
    assert not torch.equal(a["winner_noise"], c["winner_noise"])
