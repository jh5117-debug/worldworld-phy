P0_SHORT='A synthetic physical scene.'
P1_STRUCTURED=('A synthetic indoor physical scene. The static background should remain geometrically stable. '
'Foreground objects move under physical dynamics such as gravity, collision, rolling, containment, or support. '
'The camera follows the provided camera trajectory.')
TEMPLATE_WORDS={'drop':'a gravity-driven drop event','collision':'a collision event with object response','roll':'a rolling or sliding event','containment':'a containment relation between an object and a container','support':'a support relation with possible support failure','unknown':'a physical event'}
CAMERA_WORDS={'lookaway_up_reobserve':'the camera looks away and later reobserves the scene','occluder_lookaway_reobserve':'the camera view is partially occluded before reobserving the scene','offscreen_z_reobserve':'the camera moves so the target leaves view and later returns','offscreen_x_reobserve':'the camera pans sideways so the target leaves view and later returns','relative_yaw_180_reobserve':'the camera yaws away and returns to reobserve the scene','reobserve':'the camera leaves and returns to the scene','orbit':'the camera orbits the scene','strafe':'the camera strafes across the scene','dolly':'the camera moves forward or backward','static':'the camera remains approximately static','unknown':'the camera follows the provided trajectory'}
def build_prompt(sample: dict|None=None, level: str='P1') -> str:
    sample=sample or {}; level=level.upper()
    if level=='P0': return P0_SHORT
    if level=='P1': return P1_STRUCTURED
    if level!='P2': raise ValueError(f'unknown prompt level: {level}')
    event=TEMPLATE_WORDS.get(str(sample.get('template') or 'unknown'), TEMPLATE_WORDS['unknown'])
    cam=CAMERA_WORDS.get(str(sample.get('camera_motion') or 'unknown'), CAMERA_WORDS['unknown'])
    return f'A synthetic indoor physical scene with {event}. The static background should remain the same 3D scene while {cam}. Foreground object color, shape, and identity should remain stable. The generated video must follow the provided camera poses and intrinsics.'
