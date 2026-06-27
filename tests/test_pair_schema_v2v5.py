from cam_physgeo.dpo.preference_protocol_v1 import FUTURE_FRAME_INDICES, PREFIX_FRAME_INDICES

def test_v2v5_schema_constants():
    assert PREFIX_FRAME_INDICES == [0,1,2,3,4]
    assert FUTURE_FRAME_INDICES == list(range(5,81))
