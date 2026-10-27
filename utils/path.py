from __future__ import annotations
from pathlib import Path


def resolve_path(base: str | Path, path: str | Path):
    path = Path(path)
    if path.is_absolute():
        return path.resolve();
    return Path(base).resolve() / path

def display_path_rel_to_cwd(path: str, cwd: Path | None = None)->str:
    try:
        p = Path(path)
    except Exception as e:
        return path
    if cwd:
        try:
            return p.relative_to(cwd)
        except:
            pass
    return str(p)

def is_binary_file(path: Path)-> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
            return f"\x00" in chunk
    except Exception as e:
        return False
