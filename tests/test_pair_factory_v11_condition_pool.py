from cam_physgeo.dpo.pair_factory_v11_condition_pool import condition_from_row, runnable

def test_condition_from_plain_row():
    row={"sample_id":"s1","prefix_video_path":"p.mp4","gt_future_video_path":"f.mp4","poses":"poses.npy","intrinsics":"intr.npy","prompt":"hello"}
    c=condition_from_row(row,"manifest.jsonl")
    assert c["prefix_len"] == 5
    assert c["prediction_start_frame"] == 5
    assert c["sample_id"] == "s1"
