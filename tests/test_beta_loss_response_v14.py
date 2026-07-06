
from cam_physgeo.dpo.beta_loss_response_v14 import sigmoid, softplus_neg

def test_beta_math():
    assert abs(sigmoid(0.0) - 0.5) < 1e-12
    assert softplus_neg(0.0) > 0.69 and softplus_neg(0.0) < 0.70
