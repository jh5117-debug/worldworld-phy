
from cam_physgeo.dpo.pair_factory_condition_inventory import normalize_row, looks_like_path


def test_looks_like_path_detects_files():
    assert looks_like_path('/tmp/prompt.txt')
    assert not looks_like_path('a plain text prompt')


def test_normalize_quant_condition():
    row = {
        'sample_id': '01002_drop_orbit_left_72_seed40002',
        'template': 'drop',
        'camera_variant': 'orbit_left_72',
        'image': '/x/image.jpg',
        'target_video': '/x/video.mp4',
        'prompt': '/x/prompt.txt',
        'poses': '/x/poses.npy',
        'intrinsics': '/x/intrinsics.npy',
    }
    out = normalize_row(row, 'manifest.jsonl')
    assert out is not None
    assert out['prefix_len'] == 5
    assert out['prediction_start_frame'] == 5
    assert out['template'] == 'drop'
    assert out['gt_full_video_path'] == '/x/video.mp4'
