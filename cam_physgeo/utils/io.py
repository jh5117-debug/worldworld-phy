from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Iterable, Iterator

def ensure_dir(path: str|Path) -> Path:
    p=Path(path); p.mkdir(parents=True, exist_ok=True); return p

def read_jsonl(path: str|Path) -> Iterator[dict[str, Any]]:
    with Path(path).open('r', encoding='utf-8') as f:
        for n,line in enumerate(f,1):
            line=line.strip()
            if line:
                try: yield json.loads(line)
                except json.JSONDecodeError as e: raise ValueError(f'{path}:{n}: {e}') from e

def write_jsonl(records: Iterable[dict[str, Any]], path: str|Path) -> int:
    p=Path(path); ensure_dir(p.parent); c=0
    with p.open('w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True)+'\n'); c+=1
    return c

def write_json(payload: Any, path: str|Path) -> None:
    p=Path(path); ensure_dir(p.parent); p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')

def read_json(path: str|Path, default: Any=None) -> Any:
    p=Path(path)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def load_yaml(path: str|Path) -> dict[str, Any]:
    p=Path(path)
    if not p.exists(): return {}
    text=p.read_text(encoding='utf-8')
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        data={}
        for raw in text.splitlines():
            s=raw.strip()
            if not s or s.startswith('#') or ':' not in s or raw.startswith(' '): continue
            k,v=s.split(':',1); v=v.strip().strip('"\'')
            data[k]=None if v in {'','null','None','~'} else v
        return data
