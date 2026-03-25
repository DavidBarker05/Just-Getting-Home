from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import TILE_SIZE


@dataclass
class LevelDef:
    name: str
    palette_bg: tuple[int, int, int]
    tile_size: int
    width_tiles: int
    height_tiles: int
    objects: list[dict[str, Any]]


_LEVEL_CACHE: dict[str, LevelDef] = {}


def _assets_levels_dir() -> Path:
    # repo_root/assets/levels
    return Path(__file__).resolve().parent.parent / "assets" / "levels"


def _load_level_file(path: Path) -> LevelDef:
    data = json.loads(path.read_text(encoding="utf-8"))

    name = str(data.get("name") or path.stem).lower().strip()
    palette_bg_raw = data["palette_bg"]
    palette_bg = (int(palette_bg_raw[0]), int(palette_bg_raw[1]), int(palette_bg_raw[2]))

    tile_size = int(data.get("tile_size") or TILE_SIZE)
    width_tiles = int(data["width_tiles"])
    height_tiles = int(data["height_tiles"])
    objects = list(data.get("objects") or [])

    return LevelDef(
        name=name,
        palette_bg=palette_bg,
        tile_size=tile_size,
        width_tiles=width_tiles,
        height_tiles=height_tiles,
        objects=objects,
    )


def _load_all_levels() -> None:
    if _LEVEL_CACHE:
        return

    levels_dir = _assets_levels_dir()
    if not levels_dir.exists():
        raise FileNotFoundError(f"Missing levels directory: {levels_dir}")

    for path in sorted(levels_dir.glob("*.json")):
        level = _load_level_file(path)
        _LEVEL_CACHE[level.name] = level


def get_level(name: str) -> LevelDef:
    _load_all_levels()
    key = name.lower().strip()
    if key not in _LEVEL_CACHE:
        raise KeyError(f"Unknown level: {name}. Available: {', '.join(sorted(_LEVEL_CACHE))}")
    return _LEVEL_CACHE[key]

