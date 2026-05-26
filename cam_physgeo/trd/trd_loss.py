from cam_physgeo.trd.relation_utils import cosine_relation_matrix
def trd_loss(student_tokens, teacher_tokens, temporal_weight: float=1.0, spatial_weight: float=1.0):
    try:
        import torch
    except Exception as exc: raise RuntimeError('trd_loss requires torch') from exc
    sr=cosine_relation_matrix(student_tokens); tr=cosine_relation_matrix(teacher_tokens).detach()
    return torch.nn.functional.mse_loss(sr, tr) * float(temporal_weight + spatial_weight) / 2.0
