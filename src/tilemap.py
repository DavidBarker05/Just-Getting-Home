from __future__ import annotations

from typing import Any

import pygame

from .config import FIRE_H, FIRE_W, PLAYER_H, PLAYER_W, TILE_SIZE
from .levels import LevelDef


class TileMap:
    def __init__(self, level_def: LevelDef) -> None:
        self.level_def = level_def
        self.tile_size = level_def.tile_size or TILE_SIZE
        self.width_tiles = level_def.width_tiles
        self.height_tiles = level_def.height_tiles

        self.solid_tiles: set[tuple[int, int]] = set()
        self.breakable_tiles: set[tuple[int, int]] = set()
        self.fire_cells: set[tuple[int, int]] = set()  # fire marker cells (empty cell above a floor tile)

        self.spawns = self._parse_objects(level_def.objects)

    def width_px(self) -> int:
        return self.width_tiles * self.tile_size

    def height_px(self) -> int:
        return self.height_tiles * self.tile_size

    def _player_spawn_from_cell(self, cell_x: int, cell_y: int) -> tuple[int, int]:
        # Spawn marker is conceptually placed in an empty cell directly above the floor.
        x = cell_x * self.tile_size + (self.tile_size - PLAYER_W) // 2
        y = (cell_y + 1) * self.tile_size - PLAYER_H
        return x, y

    def _exit_spawn_from_cell(self, cell_x: int, cell_y: int) -> tuple[int, int]:
        x = cell_x * self.tile_size + (self.tile_size - PLAYER_W) // 2
        y = (cell_y + 1) * self.tile_size - (PLAYER_H // 2)
        return x, y

    def _actor_spawn_from_cell(self, cell_x: int, cell_y: int) -> tuple[int, int]:
        w = 18
        h = 30
        x = cell_x * self.tile_size + (self.tile_size - w) // 2
        y = (cell_y + 1) * self.tile_size - h
        return x, y

    def _fire_spawn_rect_from_cell(self, cell_x: int, cell_y: int) -> pygame.Rect:
        x = cell_x * self.tile_size + (self.tile_size - FIRE_W) // 2
        y = (cell_y + 1) * self.tile_size - FIRE_H
        return pygame.Rect(x, y, FIRE_W, FIRE_H)

    def _parse_objects(self, objects: list[dict[str, Any]]) -> Any:
        required = {
            "player_spawn": None,
            "exit_spawn": None,
            "hero_spawn": None,
            "enemy_spawn": None,
        }

        # JSON schema (bottom-left origin):
        # - floor/breakable_floor: x/y are *tile coords* of the floor tiles themselves,
        #   where y=0 is the bottom row of the level.
        # - spawn/hazard markers: x/y are the marker *cell* directly above the floor,
        #   also using bottom-left origin semantics.
        for obj in objects:
            kind = str(obj.get("kind") or "").strip().lower()
            if not kind:
                continue

            if kind in ("floor", "breakable_floor"):
                x_tile = int(obj["x"])
                y_tile = int(obj["y"])
                w_tiles = int(obj["w_tiles"])
                h_tiles = int(obj["h_tiles"])

                # Convert from JSON bottom-left coords to internal top-left tile coords.
                for gy_input in range(y_tile, y_tile + h_tiles):
                    gy_internal = (self.height_tiles - 1) - gy_input
                    for gx in range(x_tile, x_tile + w_tiles):
                        self.solid_tiles.add((gx, gy_internal))
                        if kind == "breakable_floor":
                            self.breakable_tiles.add((gx, gy_internal))

            elif kind in required:
                cell_x = int(obj["x"])
                cell_y_input = int(obj["y"])
                cell_y_internal = (self.height_tiles - 1) - cell_y_input
                if kind == "player_spawn":
                    required[kind] = self._player_spawn_from_cell(cell_x, cell_y_internal)
                elif kind == "exit_spawn":
                    required[kind] = self._exit_spawn_from_cell(cell_x, cell_y_internal)
                elif kind == "hero_spawn":
                    required[kind] = self._actor_spawn_from_cell(cell_x, cell_y_internal)
                elif kind == "enemy_spawn":
                    required[kind] = self._actor_spawn_from_cell(cell_x, cell_y_internal)
            elif kind == "fire_spawn":
                cell_x = int(obj["x"])
                cell_y_input = int(obj["y"])
                cell_y_internal = (self.height_tiles - 1) - cell_y_input
                # Fire spawns are stored as marker cells. We'll spawn permanent fire
                # when the hero walks over the floor tile underneath them.
                self.fire_cells.add((cell_x, cell_y_internal))

        missing = [k for k, v in required.items() if v is None]
        if missing:
            raise ValueError(f"Missing required spawn objects: {', '.join(missing)}")

        # A tiny anonymous struct: avoids threading MarkerSpawns through all call sites.
        return type(
            "Spawns",
            (),
            {
                "player_spawn": required["player_spawn"],
                "exit_spawn": required["exit_spawn"],
                "hero_spawn": required["hero_spawn"],
                "enemy_spawn": required["enemy_spawn"],
            },
        )()

    def solid_rects(self) -> list[pygame.Rect]:
        rects: list[pygame.Rect] = []
        for gx, gy in self.solid_tiles:
            rects.append(pygame.Rect(gx * self.tile_size, gy * self.tile_size, self.tile_size, self.tile_size))
        return rects

    def destroy_breakables(self, center_px: tuple[int, int], radius_tiles: float = 2.0) -> list[tuple[int, int]]:
        cx, cy = center_px
        removed: list[tuple[int, int]] = []
        for gx, gy in list(self.breakable_tiles):
            tx = gx * self.tile_size + self.tile_size / 2
            ty = gy * self.tile_size + self.tile_size / 2
            dx = (tx - cx) / self.tile_size
            dy = (ty - cy) / self.tile_size
            if dx * dx + dy * dy <= radius_tiles * radius_tiles:
                self.breakable_tiles.remove((gx, gy))
                if (gx, gy) in self.solid_tiles:
                    self.solid_tiles.remove((gx, gy))
                removed.append((gx, gy))
        return removed

    def hazard_rects(self) -> list[pygame.Rect]:
        # Compatibility shim: build rects for all fire marker cells.
        return [self._fire_spawn_rect_from_cell(x, y) for (x, y) in self.fire_cells]

    def fire_rect_from_cell(self, cell_x: int, cell_y: int) -> pygame.Rect:
        return self._fire_spawn_rect_from_cell(cell_x, cell_y)

    def destroy_breakable_tile(self, tile_x: int, tile_y: int) -> bool:
        tile = (tile_x, tile_y)
        if tile not in self.breakable_tiles:
            return False
        self.breakable_tiles.remove(tile)
        if tile in self.solid_tiles:
            self.solid_tiles.remove(tile)
        return True

