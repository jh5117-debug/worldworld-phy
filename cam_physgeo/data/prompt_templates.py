from __future__ import annotations

P0 = "A synthetic physical scene."

P1 = (
    "A synthetic indoor physical scene. The static background should remain "
    "geometrically stable. Foreground objects move under physical dynamics "
    "such as gravity, collision, rolling, containment, or support. The camera "
    "follows the provided camera trajectory."
)

P2_BY_TEMPLATE = {
    "drop": (
        "A synthetic physical scene with rigid objects. A target object falls "
        "under gravity and may contact another object or the floor. The static "
        "background should remain geometrically stable. The camera follows the "
        "provided camera trajectory."
    ),
    "collision": (
        "A synthetic physical scene where a moving object may collide with "
        "another object. The foreground objects should preserve their shape and "
        "identity while moving physically. The camera follows the provided "
        "trajectory."
    ),
    "containment": (
        "A synthetic physical scene involving an object and a container. The "
        "object-container spatial relationship should remain physically "
        "plausible. The camera follows the provided trajectory."
    ),
    "roll": (
        "A synthetic physical scene where an object rolls or slides along a "
        "surface. Its trajectory should be smooth and physically plausible. The "
        "camera follows the provided trajectory."
    ),
    "support": (
        "A synthetic physical scene with objects in a support relationship. "
        "Supported objects should remain stable unless the support is removed "
        "or becomes unstable. The camera follows the provided trajectory."
    ),
    "dominoes": (
        "A synthetic physical scene with multiple rigid objects arranged for "
        "chain-like contact. Objects should preserve shape and identity while "
        "the camera follows the provided trajectory."
    ),
    "drape": (
        "A synthetic physical scene involving deformable or cloth-like motion "
        "and rigid scene context. The static background should remain stable "
        "while the camera follows the provided trajectory."
    ),
    "link": (
        "A synthetic physical scene with linked or constrained objects. The "
        "object relationships should remain physically plausible while the "
        "camera follows the provided trajectory."
    ),
}


def build_prompt(sample: dict | None = None, level: str = "P1") -> str:
    sample = sample or {}
    level = (level or "P1").upper()
    if level == "P0":
        return P0
    if level == "P2":
        return build_metadata_prompt(sample)
    return P1


def build_metadata_prompt(sample: dict) -> str:
    template = str(sample.get("template") or "unknown").lower()
    base = P2_BY_TEMPLATE.get(template, P1)
    motion = str(sample.get("camera_motion") or "").lower()
    if any(key in motion for key in ["lookaway", "offscreen", "reobserve", "yaw"]):
        base += " The camera may temporarily look away or move around the scene, so persistent scene identity is important."
    elif motion and motion not in {"unknown", "static", "fixed"}:
        base += " The camera motion should be followed without changing object identity."
    return base
