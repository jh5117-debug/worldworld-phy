from __future__ import annotations

import re

FUTURE_LEAK_PATTERNS = [
    re.compile(r"\bfall[s]? faster\b", re.IGNORECASE),
    re.compile(r"\bland[s]? at frame\b", re.IGNORECASE),
    re.compile(r"\bjump[s]? higher\b", re.IGNORECASE),
    re.compile(r"\bwill land\b", re.IGNORECASE),
    re.compile(r"\bwill hit\b", re.IGNORECASE),
]


def format_gravity_value(value: object) -> str:
    val = float(value)
    if abs(val - round(val)) < 1e-8:
        return f"{val:.1f}g"
    return f"{val:g}g"


def build_prompt_gravity(value: object, style: str = "physeditworld_v0") -> str:
    if style != "physeditworld_v0":
        raise ValueError(f"unsupported gravity_prompt_style:{style}")
    gravity = format_gravity_value(value)
    return (
        "A first-person interactive world rollout.\n"
        "The character follows the given action sequence and camera trajectory.\n"
        f"The scene is rendered under gravity: {gravity}."
    )


def prompt_has_future_leak(prompt: str) -> bool:
    return any(pattern.search(prompt) for pattern in FUTURE_LEAK_PATTERNS)


def validate_prompt(prompt: str) -> list[str]:
    errors: list[str] = []
    if "gravity:" not in prompt.lower():
        errors.append("missing_gravity_token")
    if prompt_has_future_leak(prompt):
        errors.append("future_answer_leak")
    return errors
