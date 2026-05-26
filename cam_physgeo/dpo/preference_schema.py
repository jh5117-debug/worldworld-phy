REQUIRED_PAIR_FIELDS=['pair_id','condition','winner','loser','pair_type','margin','quality_flags']
def validate_pair(pair: dict) -> list[str]:
    errors=[f'missing:{k}' for k in REQUIRED_PAIR_FIELDS if k not in pair]
    for side in ['winner','loser']:
        if side in pair and 'video' not in pair[side]: errors.append(f'missing:{side}.video')
    return errors
