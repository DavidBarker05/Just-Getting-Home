from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pygame

from .config import FIRE_H, FIRE_W, PLAYER_H, PLAYER_W, TILE_SIZE


@dataclass
class MarkerSpawns:
    player_spawn: tuple[int, int]
    exit_spawn: tuple[int, int]
    hero_spawn: tuple[int, int]
    enemy_spawn: tuple[int, int]
    hazard_spawns: list[tuple[int, int]]  # (grid_x, grid_y) where cell is empty above floor


class TileMap:
    def __init__(self, ascii_map: Iterable[str], tile_size: int = TILE_SIZE) -> None:
        self.tile_size = tile_size
        self.ascii_map = tuple(ascii_map)
        self.height_tiles = len(self.ascii_map)
        self.width_tiles = len(self.ascii_map[0]) if self.height_tiles else 0

        self.solid_tiles: set[tuple[int, int]] = set()
        self.breakable_tiles: set[tuple[int, int]] = set()

        self.spawns: MarkerSpawns = self._parse_markers()

        # Fire hazard spawn cells (empty cell above floor). These correspond to map 'f'.
        self.hazard_spawns = self.spawns.hazard_spawns

    def _parse_markers(self) -> MarkerSpawns:
        player_spawn: tuple[int, int] | None = None
        exit_spawn: tuple[int, int] | None = None
        hero_spawn: tuple[int, int] | None = None
        enemy_spawn: tuple[int, int] | None = None
        hazard_spawns: list[tuple[int, int]] = []

        for gy, line in enumerate(self.ascii_map):
            for gx, ch in enumerate(line):
                if ch == "#":
                    self.solid_tiles.add((gx, gy))
                elif ch == "X":
                    # Breakable floor: solid until destroyed.
                    self.solid_tiles.add((gx, gy))
                    self.breakable_tiles.add((gx, gy))
                elif ch == "S":
                    player_spawn = self._player_spawn_from_cell(gx, gy)
                elif ch == "E":
                    exit_spawn = self._exit_spawn_from_cell(gx, gy)
                elif ch == "A":
                    hero_spawn = self._actor_spawn_from_cell(gx, gy)
                elif ch == "V":
                    enemy_spawn = self._actor_spawn_from_cell(gx, gy)
                elif ch == "f":
                    hazard_spawns.append((gx, gy))

        if player_spawn is None or exit_spawn is None or hero_spawn is None or enemy_spawn is None:
            missing = []
            if player_spawn is None:
                missing.append("S")
            if exit_spawn is None:
                missing.append("E")
            if hero_spawn is None:
                missing.append("A")
            if enemy_spawn is None:
                missing.append("V")
            raise ValueError(f"Missing required markers: {', '.join(missing)}")

        return MarkerSpawns(
            player_spawn=player_spawn,
            exit_spawn=exit_spawn,
            hero_spawn=hero_spawn,
            enemy_spawn=enemy_spawn,
            hazard_spawns=hazard_spawns,
        )

    def grid_to_pixel_bottomleft(self, grid_x: int, grid_y: int) -> tuple[int, int]:
        x = grid_x * self.tile_size
        y = grid_y * self.tile_size
        return x, y

    def _player_spawn_from_cell(self, cell_x: int, cell_y: int) -> tuple[int, int]:
        # Player spawn markers are placed in an empty cell directly above the floor.
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

    def width_px(self) -> int:
        return self.width_tiles * self.tile_size

    def height_px(self) -> int:
        return self.height_tiles * self.tile_size

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
        rects: list[pygame.Rect] = []
        for gx, gy in self.hazard_spawns:
            # Hazard cell marker is empty above the floor at (gx, gy+1).
            x = gx * self.tile_size + (self.tile_size - FIRE_W) // 2
            y = (gy + 1) * self.tile_size - FIRE_H
            rects.append(pygame.Rect(x, y, FIRE_W, FIRE_H))
        return rects

