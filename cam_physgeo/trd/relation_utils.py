def cosine_relation_matrix(x):
    try:
        import torch
    except Exception as exc: raise RuntimeError('TRD relation utilities require torch') from exc
    x=torch.nn.functional.normalize(x, dim=-1)
    return x @ x.transpose(-1,-2)
