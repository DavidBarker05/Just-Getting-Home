from __future__ import annotations

from dataclasses import dataclass

import pygame

from .config import PLAYER_H, PLAYER_W, SCREEN_FPS
from .entities import Actor, FirePatch, InputState, Player
from .levels import LevelDef, get_level
from .tilemap import TileMap

LEVEL_SEQUENCE = ["market", "bridge", "forestchokepoint", "burninghearthrun"]


@dataclass
class GamePhase:
    hero_left: bool = False
    won: bool = False
    lost: bool = False
    enemy_dead: bool = False


class GameApp:
    def __init__(self, width: int, height: int, level_name: str, smoke_test: bool) -> None:
        self.width = width
        self.height = height
        self.smoke_test = smoke_test

        normalized = level_name.lower().strip()
        if normalized not in LEVEL_SEQUENCE:
            raise ValueError(f"Unknown/unsupported level '{level_name}'. Start one of: {', '.join(LEVEL_SEQUENCE)}")

        self.level_order = LEVEL_SEQUENCE
        self.level_index = self.level_order.index(normalized)
        self.level_name = self.level_order[self.level_index]

        pygame.init()
        pygame.display.set_caption("Just Getting Home")
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 26)

        self.level_def: LevelDef = get_level(self.level_name)
        self._load_level()

    def _load_level(self) -> None:
        self.tilemap = TileMap(self.level_def)
        self.phase = GamePhase()

        psx, psy = self.tilemap.spawns.player_spawn
        self.player = Player(psx, psy)

        ex, ey = self.tilemap.spawns.exit_spawn
        self.exit_rect = pygame.Rect(int(ex), int(ey), PLAYER_W, PLAYER_H)

        # Permanent hazards.
        self.fire_patches: list[FirePatch] = []
        self.activated_fire_cells: set[tuple[int, int]] = set()

        # Route-based traversal:
        # - hero/enemy walk along ordered floor tiles
        # - breakable tiles are destroyed after hero leaves them
        # - fire appears on fire-marked cells after hero leaves the tile beneath them
        if not self.level_def.route:
            raise ValueError(f"Level '{self.level_name}' is missing 'route' in JSON.")

        self.hero_step_interval_s = max(0.05, float(self.level_def.hero_step_interval_s))
        self.enemy_gap_steps = max(0, int(self.level_def.enemy_gap_steps))

        # Convert route points (JSON bottom-left origin) to internal top-left tile coords.
        self.route_internal: list[tuple[int, int]] = [
            (int(x), (self.tilemap.height_tiles - 1) - int(y)) for (x, y) in self.level_def.route
        ]
        if not self.route_internal:
            raise ValueError(f"Level '{self.level_name}' route is empty.")

        self.hero_last_step_index = 0
        self.start_time = pygame.time.get_ticks() / 1000.0

        # Combat tuning (prototype feel).
        self.ATTACK_INTERVAL = 0.6
        self.DAMAGE = 25
        self.next_attack_at = self.start_time + 0.2

        # Actor dimensions are fixed in `Actor` (18x30), but we keep them explicit.
        actor_w = 18
        actor_h = 30

        def tile_to_actor_pos(tile_x: int, tile_y: int) -> tuple[int, int]:
            x = tile_x * self.tilemap.tile_size + (self.tilemap.tile_size - actor_w) // 2
            # Actors "stand" with their feet on the top edge of the floor tile.
            y = tile_y * self.tilemap.tile_size - actor_h
            return x, y

        # Start both at route[0]. Enemy will lag behind by `enemy_gap_steps`.
        hero_tile = self.route_internal[0]
        hero_x, hero_y = tile_to_actor_pos(hero_tile[0], hero_tile[1])
        self.hero = Actor(hero_x, hero_y, color_idle=(170, 60, 60), color_attack=(255, 110, 110))

        enemy_x, enemy_y = tile_to_actor_pos(hero_tile[0], hero_tile[1])
        self.enemy = Actor(enemy_x, enemy_y, color_idle=(60, 60, 60), color_attack=(110, 110, 110))

    def _reset_level(self) -> None:
        self._load_level()

    def _handle_input(self) -> InputState:
        keys = pygame.key.get_pressed()
        left = bool(keys[pygame.K_LEFT] or keys[pygame.K_a])
        right = bool(keys[pygame.K_RIGHT] or keys[pygame.K_d])
        return InputState(left=left, right=right, jump_pressed=self._jump_pressed)

    def _process_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                self._jump_pressed = True
        return True

    def _set_actor_to_tile(self, actor: Actor, tile_x: int, tile_y: int) -> None:
        # Actor stands on top of the floor tile.
        actor_w = actor.rect.width
        actor_h = actor.rect.height
        actor.rect.x = tile_x * self.tilemap.tile_size + (self.tilemap.tile_size - actor_w) // 2
        actor.rect.y = tile_y * self.tilemap.tile_size - actor_h

    def _destroy_and_spawn_from_tile(self, prev_tile_x: int, prev_tile_y: int, now: float) -> None:
        # Break tiles.
        self.tilemap.destroy_breakable_tile(prev_tile_x, prev_tile_y)

        # Fire: `fire_spawn` markers are stored as cells above a floor tile.
        # Because internal coords use top-left origin, the "cell above" is at y-1.
        fire_cell = (prev_tile_x, prev_tile_y - 1)
        if fire_cell[1] < 0:
            return
        if fire_cell not in self.tilemap.fire_cells:
            return
        if fire_cell in self.activated_fire_cells:
            return

        rect = self.tilemap.fire_rect_from_cell(fire_cell[0], fire_cell[1])
        patch = FirePatch(rect.x, rect.y, w=rect.width, h=rect.height, duration=None)
        patch.start(now)
        self.fire_patches.append(patch)
        self.activated_fire_cells.add(fire_cell)

    def _update_fight(self, now: float, dt: float) -> None:
        if self.phase.won or self.phase.lost or self.phase.hero_left:
            return

        end_index = len(self.route_internal) - 1
        t = now - self.start_time

        hero_step_index = min(int(t / self.hero_step_interval_s), end_index)

        # Enemy follows the same path but lags behind until the hero reaches the end.
        if hero_step_index < end_index:
            enemy_step_index = max(0, hero_step_index - self.enemy_gap_steps)
        else:
            enemy_step_index = end_index

        # Apply tile-by-tile destruction/fire when hero advances.
        if hero_step_index > self.hero_last_step_index:
            for passed_index in range(self.hero_last_step_index, hero_step_index):
                prev_tile_x, prev_tile_y = self.route_internal[passed_index]
                self._destroy_and_spawn_from_tile(prev_tile_x, prev_tile_y, now)
            self.hero_last_step_index = hero_step_index

        # Move actors (collisionless) to their current tiles.
        hero_tile_x, hero_tile_y = self.route_internal[hero_step_index]
        self._set_actor_to_tile(self.hero, hero_tile_x, hero_tile_y)
        enemy_tile_x, enemy_tile_y = self.route_internal[enemy_step_index]
        self._set_actor_to_tile(self.enemy, enemy_tile_x, enemy_tile_y)

        # Combat only happens at the end-of-route (the "exit" for the hero).
        if hero_step_index == end_index and not self.phase.enemy_dead:
            if self.enemy.alive and now >= self.next_attack_at:
                self.hero.attacking_until = now + 0.15
                self.enemy.take_damage(self.DAMAGE)
                self.next_attack_at = now + self.ATTACK_INTERVAL

            if not self.enemy.alive:
                self.phase.enemy_dead = True

        # After defeating the enemy, the hero retreats off-screen.
        if self.phase.enemy_dead and not self.phase.hero_left:
            self.hero.rect.x += int(520 * dt)
            if self.hero.rect.left > self.tilemap.width_px() + 80:
                self.phase.hero_left = True

    def _update_player(self, inp: InputState, dt: float) -> None:
        solids = self.tilemap.solid_rects()

        # Lock player controls until the hero is fully off-screen.
        if not self.phase.hero_left:
            inp = InputState(left=False, right=False, jump_pressed=False)

        self.player.update(inp, solids, dt)

        # Permanent hazard collision: restart level.
        for patch in self.fire_patches:
            if patch.active and self.player.rect.colliderect(patch.rect):
                self.phase.lost = True
                self._reset_level()
                return

        # Win condition: exit is only safe after hero leaves.
        if self.phase.hero_left and self.player.rect.colliderect(self.exit_rect):
            if self.level_index < len(self.level_order) - 1:
                self.level_index += 1
                self.level_name = self.level_order[self.level_index]
                self.level_def = get_level(self.level_name)
                self._load_level()
                return

            self.phase.won = True

    def _render(self, now: float) -> None:
        self.screen.fill(self.level_def.palette_bg)

        ground_color = (140, 120, 90)
        break_color = (110, 90, 70)
        for gx, gy in self.tilemap.solid_tiles:
            r = pygame.Rect(
                gx * self.tilemap.tile_size,
                gy * self.tilemap.tile_size,
                self.tilemap.tile_size,
                self.tilemap.tile_size,
            )
            is_breakable = (gx, gy) in self.tilemap.breakable_tiles
            pygame.draw.rect(self.screen, break_color if is_breakable else ground_color, r)
            pygame.draw.rect(self.screen, (70, 55, 40), r, width=1)

        pygame.draw.rect(self.screen, (80, 200, 90), self.exit_rect, border_radius=4)
        pygame.draw.rect(self.screen, (20, 100, 35), self.exit_rect, width=2, border_radius=4)

        for patch in self.fire_patches:
            patch.draw(self.screen)

        self.hero.draw(self.screen, now)
        self.enemy.draw(self.screen, now)
        pygame.draw.rect(self.screen, (90, 170, 240), self.player.rect, border_radius=3)
        pygame.draw.rect(self.screen, (30, 80, 140), self.player.rect, width=2, border_radius=3)

        if not self.phase.won:
            if not self.phase.hero_left:
                msg = "You are not the hero. Wait for him to leave the route."
            else:
                msg = "Hero left. Get to the exit!"
            self._draw_text(msg, 18, 16)
        else:
            self._draw_text("You made it home!", 38, 24)

        pygame.display.flip()

    def _draw_text(self, text: str, y: int, scale: int) -> None:
        surf = self.font.render(text, True, (230, 230, 220))
        self.screen.blit(surf, (16, y))

    def run(self) -> int:
        running = True
        smoke_start = pygame.time.get_ticks() / 1000.0

        while running:
            dt = min(1.0 / 30.0, self.clock.tick(SCREEN_FPS) / 1000.0)
            now = pygame.time.get_ticks() / 1000.0

            self._jump_pressed = False
            running = self._process_events()
            if not running:
                break

            inp = self._handle_input()

            if self.phase.won:
                self._render(now)
            else:
                self._update_fight(now, dt)
                self._update_player(inp, dt)
                self._render(now)

            if self.smoke_test and now - smoke_start >= 1.5:
                running = False

        pygame.quit()
        return 0

