"""Build concise template-aware + object-consistency prompts for TDW LingBot manifests."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TEMPLATE_EVENTS = {
    "drop": "A rigid object falls under gravity in a synthetic TDW physical scene.",
    "collision": "A moving rigid object collides with another rigid object in a synthetic TDW physical scene.",
    "roll": "A rigid object rolls across the surface in a synthetic TDW physical scene.",
    "containment": "Rigid objects interact with a container in a synthetic TDW physical scene.",
}

GENERIC_CAMERA = "Follow the provided camera trajectory from the first frame."
GENERIC_OBJECTS = "Preserve the initially visible foreground objects, object count, colors, and rigid shapes."
GENERIC_NEGATIVE = "Do not add, remove, duplicate, recolor, melt, or morph objects. Keep the background geometrically stable under camera motion."
VISIBLE_OBJECTS = "The scene contains only the foreground objects visible in the first frame. Do not create any additional objects."


def _load_json(path: str | None) -> Any:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def _walk_object_inventory(obj: Any, out: list[str]) -> None:
    if isinstance(obj, dict):
        name = obj.get("name") or obj.get("model_name") or obj.get("category") or obj.get("type")
        color = obj.get("color") or obj.get("colour")
        shape = obj.get("shape")
        parts = []
        if color and isinstance(color, str):
            parts.append(color)
        if shape and isinstance(shape, str):
            parts.append(shape)
        if name and isinstance(name, str):
            parts.append(name)
        if parts:
            text = " ".join(parts)
            text = re.sub(r"[^A-Za-z0-9_ .-]", "", text).strip()
            if text and text.lower() not in {"object", "objects", "unknown"}:
                out.append(text)
        for v in obj.values():
            _walk_object_inventory(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk_object_inventory(v, out)


def extract_inventory(row: dict[str, Any]) -> str | None:
    metadata = _load_json(row.get("metadata_path"))
    candidates: list[str] = []
    _walk_object_inventory(metadata, candidates)
    dedup: list[str] = []
    seen = set()
    for c in candidates:
        key = c.lower()
        if key not in seen and len(c) <= 60:
            seen.add(key)
            dedup.append(c)
    if not dedup:
        return None
    # Keep it short; long enumerations make Wan hallucinate categories.
    return "The scene contains " + ", ".join(dedup[:6]) + ". Do not create any additional objects."


def build_prompt(row: dict[str, Any], use_inventory: bool) -> tuple[str, str]:
    template = str(row.get("template") or "").lower()
    event = TEMPLATE_EVENTS.get(template, "A synthetic TDW physical scene shows rigid objects moving under physical dynamics.")
    inventory = extract_inventory(row) if use_inventory else None
    object_phrase = inventory or VISIBLE_OBJECTS
    prompt = " ".join([event, GENERIC_CAMERA, object_phrase, GENERIC_OBJECTS, GENERIC_NEGATIVE])
    source = "metadata_inventory" if inventory else "first_frame_visible_objects_fallback"
    return prompt, source


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out_manifest", required=True)
    ap.add_argument("--out_prompt_root", required=True)
    ap.add_argument("--prompt_variant", default="combined_v2")
    ap.add_argument("--use_object_inventory_if_available", default="true")
    ap.add_argument("--do_not_overwrite_original", default="true")
    args = ap.parse_args()

    use_inventory = str(args.use_object_inventory_if_available).lower() in {"1", "true", "yes"}
    out_manifest = Path(args.out_manifest)
    prompt_root = Path(args.out_prompt_root)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    prompt_root.mkdir(parents=True, exist_ok=True)

    count = 0
    by_template: dict[str, int] = {}
    by_source: dict[str, int] = {}
    examples: dict[str, str] = {}
    with Path(args.manifest).open() as f, out_manifest.open("w") as out:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            prompt, source = build_prompt(row, use_inventory=use_inventory)
            sid = row.get("sample_id") or f"sample_{count:06d}"
            p = prompt_root / f"{sid}.txt"
            p.write_text(prompt + "\n")
            if args.do_not_overwrite_original:
                row["original_prompt_path"] = row.get("prompt_path")
            row["prompt_path"] = str(p)
            row["prompt_variant"] = args.prompt_variant
            row["prompt_inventory_source"] = source
            out.write(json.dumps(row) + "\n")
            count += 1
            t = str(row.get("template"))
            by_template[t] = by_template.get(t, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1
            examples.setdefault(t, prompt)
    summary = {
        "input_manifest": args.manifest,
        "out_manifest": str(out_manifest),
        "out_prompt_root": str(prompt_root),
        "count": count,
        "prompt_variant": args.prompt_variant,
        "template_distribution": by_template,
        "inventory_source_distribution": by_source,
        "examples": examples,
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
