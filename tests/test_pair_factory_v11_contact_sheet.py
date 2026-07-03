import numpy as np
from cam_physgeo.dpo.pair_factory_v11_contact_sheet import thumb_row

def test_thumb_row_shape():
    frames=[np.zeros((20,30,3), dtype=np.uint8) for _ in range(3)]
    row=thumb_row(frames,width=10,height=8)
    assert row.shape == (8,30,3)
