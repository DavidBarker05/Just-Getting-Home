from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .config import TILE_SIZE, PLAYER_H, PLAYER_W


@dataclass(frozen=True)
class LevelDef:
    name: str
    ascii_map: tuple[str, ...]
    palette_bg: tuple[int, int, int]
    # Markers:
    #  - `S`: player spawn cell (empty cell directly above floor)
    #  - `E`: exit cell (empty cell directly above floor)
    #  - `A`: hero spawn cell
    #  - `V`: enemy spawn cell
    #  - `X`: breakable floor tile (solid until destroyed)
    #  - `f`: fire hazard spawn cell (empty cell above floor)
    #  - `#`: solid floor tile


def _validate_map(ascii_map: Iterable[str], expected_width: int) -> tuple[str, ...]:
    lines = tuple(ascii_map)
    if not lines:
        raise ValueError("Level map cannot be empty")
    for i, line in enumerate(lines):
        if len(line) != expected_width:
            raise ValueError(f"Level map line {i} has width {len(line)}; expected {expected_width}")
    return lines


def _map_width_from_config() -> int:
    # Screen width is 960 by default; we keep maps at 30 tiles wide.
    return 30


LEVELS: dict[str, LevelDef] = {}


def _register(level: LevelDef) -> None:
    if level.name in LEVELS:
        raise ValueError(f"Duplicate level name: {level.name}")
    LEVELS[level.name] = level


_W = _map_width_from_config()

# Market: hero fight breaks a gap where the player must jump over hazards.
_market_map = _validate_map(
    (
        "..............................",  # 0
        "..............................",  # 1
        "..............................",  # 2
        "..............................",  # 3
        "..............................",  # 4
        "..............................",  # 5
        "..............................",  # 6
        "..............................",  # 7
        "..............................",  # 8
        "..............................",  # 9
        "..............................",  # 10
        "..............................",  # 11
        "..............................",  # 12
        "..............................",  # 13
        "..............................",  # 14
        "...S..........Aff.V.......E...",  # 15 (S/A/V/f/E)
        "#############XXXX#############",  # 16 (floor/breakables)
    ),
    expected_width=_W,
)

_register(
    LevelDef(
        name="market",
        ascii_map=_market_map,
        palette_bg=(30, 35, 25),
    )
)


# Bridge: similar structure, tuned palette; hero destroys bridge tiles in the center.
_bridge_map = _validate_map(
    (
        "..............................",  # 0
        "..............................",  # 1
        "..............................",  # 2
        "..............................",  # 3
        "..............................",  # 4
        "..............................",  # 5
        "..............................",  # 6
        "..............................",  # 7
        "..............................",  # 8
        "..............................",  # 9
        "..............................",  # 10
        "..............................",  # 11
        "..............................",  # 12
        "..............................",  # 13
        "..............................",  # 14
        "...S........A.ff.V........E...",  # 15
        "#############XXXX#############",  # 16
    ),
    expected_width=_W,
)

_register(
    LevelDef(
        name="bridge",
        ascii_map=_bridge_map,
        palette_bg=(20, 30, 40),
    )
)


# Forest choke point: breaks into a more dangerous path.
_forest_map = _validate_map(
    (
        "..............................",  # 0
        "..............................",  # 1
        "..............................",  # 2
        "..............................",  # 3
        "..............................",  # 4
        "..............................",  # 5
        "..............................",  # 6
        "..............................",  # 7
        "..............................",  # 8
        "..............................",  # 9
        "..............................",  # 10
        "..............................",  # 11
        "..............................",  # 12
        "..............................",  # 13
        "..............................",  # 14
        "...S.........A.ff.V......E....",  # 15 (S/A/V/f/E)
        "############XXXXXX############",  # 16 (floor/breakables)
    ),
    expected_width=_W,
)

_register(
    LevelDef(
        name="forestchokepoint",
        ascii_map=_forest_map,
        palette_bg=(28, 45, 30),
    )
)


# Homecoming aftermath: more breakables and fire across the “safe” route.
_burning_map = _validate_map(
    (
        "..............................",  # 0
        "..............................",  # 1
        "..............................",  # 2
        "..............................",  # 3
        "..............................",  # 4
        "..............................",  # 5
        "..............................",  # 6
        "..............................",  # 7
        "..............................",  # 8
        "..............................",  # 9
        "..............................",  # 10
        "..............................",  # 11
        "..............................",  # 12
        "..............................",  # 13
        "..............................",  # 14
        "...S......A.ff.V....f....E....",  # 15 (S/A/V/f/E)
        "########XXXXXXXXXX############",  # 16 (floor/breakables)
    ),
    expected_width=_W,
)

_register(
    LevelDef(
        name="burninghearthrun",
        ascii_map=_burning_map,
        palette_bg=(30, 20, 15),
    )
)


def get_level(name: str) -> LevelDef:
    key = name.lower().strip()
    if key not in LEVELS:
        raise KeyError(f"Unknown level: {name}. Available: {', '.join(sorted(LEVELS))}")
    return LEVELS[key]

