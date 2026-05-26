def mask_available(sample: dict, key: str='id_path') -> bool:
    return bool(sample.get(key))
def default_background_mask_note(sample: dict) -> str:
    return 'simulator_id_mask' if mask_available(sample) else 'fallback_required_sam_or_flow_propagation'
