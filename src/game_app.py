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
    fight_active: bool = True
    hero_left: bool = False
    won: bool = False
    lost: bool = False


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
        psx, psy = self.tilemap.spawns.player_spawn
        self.player = Player(psx, psy)

        hsx, hsy = self.tilemap.spawns.hero_spawn
        esx, esy = self.tilemap.spawns.enemy_spawn
        # Hero: red-ish. Enemy: dark.
        self.hero = Actor(hsx, hsy, color_idle=(170, 60, 60), color_attack=(255, 110, 110))
        self.enemy = Actor(esx, esy, color_idle=(60, 60, 60), color_attack=(110, 110, 110))

        ex, ey = self.tilemap.spawns.exit_spawn
        self.exit_rect = pygame.Rect(int(ex), int(ey), PLAYER_W, PLAYER_H)

        self.fire_patches: list[FirePatch] = []

        # Fight timeline.
        self.phase = GamePhase()
        self.start_time = pygame.time.get_ticks() / 1000.0
        self.destroyed = False
        self.enemy_dead = False
        self.hero_left_started = False
        self.next_attack_at = self.start_time + 0.5

        self.fight_center = (
            (self.hero.rect.centerx + self.enemy.rect.centerx) / 2,
            (self.hero.rect.centery + self.enemy.rect.centery) / 2,
        )

    def _reset_level(self) -> None:
        # Recreate the tilemap so breakables/solids go back to the initial state.
        self._load_level()

    def _handle_input(self) -> InputState:
        keys = pygame.key.get_pressed()
        left = bool(keys[pygame.K_LEFT] or keys[pygame.K_a])
        right = bool(keys[pygame.K_RIGHT] or keys[pygame.K_d])
        return InputState(left=left, right=right, jump_pressed=self._jump_pressed)

    def _process_events(self) -> bool:
        # Returns False if we should exit.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                self._jump_pressed = True
        return True

    def _update_fight(self, now: float, dt: float) -> None:
        if self.phase.won or self.phase.lost:
            return

        t = now - self.start_time

        # Tuned for “prototype feel”, not perfect combat.
        ATTACK_INTERVAL = 0.6
        DAMAGE = 25
        DESTROY_AT = 2.4
        LEAVE_AFTER = 1.3  # seconds after enemy death
        MAX_FIGHT_TIME = 8.0

        if self.phase.fight_active:
            # Enemy gets attacked on a timer.
            if self.enemy.alive and now >= self.next_attack_at:
                self.hero.attacking_until = now + 0.15
                self.enemy.take_damage(DAMAGE)
                self.next_attack_at = now + ATTACK_INTERVAL

            if not self.destroyed and t >= DESTROY_AT:
                # Break central floor tiles in a radius, making hazards relevant.
                self.tilemap.destroy_breakables(self.fight_center, radius_tiles=2.2)

                # Spawn hazard patches at pre-marked cells.
                self.fire_patches = []
                for rect in self.tilemap.hazard_rects():
                    patch = FirePatch(rect.x, rect.y, w=rect.width, h=rect.height, duration=3.0)
                    patch.start(now)
                    self.fire_patches.append(patch)
                self.destroyed = True

            if self.enemy.alive is False:
                self.enemy_dead = True
                self.phase.fight_active = False

            # Safety cutoff so the phase always ends even if something changes.
            if t >= MAX_FIGHT_TIME:
                self.phase.fight_active = False
                self.enemy_dead = not self.enemy.alive

        # After enemy is dead, the hero retreats off-screen.
        if self.enemy_dead and not self.phase.hero_left:
            if not self.hero_left_started:
                self.hero_left_started = True
                self.hero_left_at = now

            if now - self.hero_left_at >= 0.15:
                self.hero.rect.x += int(520 * dt)
                if self.hero.rect.left > self.tilemap.width_px() + 80:
                    self.phase.hero_left = True

        # If the fight never spawned an enemy death, leave anyway at end.
        if not self.phase.hero_left and t >= MAX_FIGHT_TIME:
            self.phase.hero_left = True

    def _update_player(self, inp: InputState, dt: float) -> None:
        solids = self.tilemap.solid_rects()

        self.player.update(inp, solids, dt)

        # Hazard collision: restart level.
        for patch in self.fire_patches:
            if patch.active and self.player.rect.colliderect(patch.rect):
                self.phase.lost = True
                self._reset_level()
                return

        # Win condition: exit is only “safe” after hero leaves.
        if self.phase.hero_left and self.player.rect.colliderect(self.exit_rect):
            # Not final: immediately load the next level.
            if self.level_index < len(self.level_order) - 1:
                self.level_index += 1
                self.level_name = self.level_order[self.level_index]
                self.level_def = get_level(self.level_name)
                self._load_level()
                return

            # Final level: show win message and stop advancing.
            self.phase.won = True

    def _render(self, now: float) -> None:
        # Background
        self.screen.fill(self.level_def.palette_bg)

        # Tiles: draw floor + breakable floor with different tones.
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
            # subtle edge for pixel look
            pygame.draw.rect(self.screen, (70, 55, 40), r, width=1)

        # Exit
        pygame.draw.rect(self.screen, (80, 200, 90), self.exit_rect, border_radius=4)
        pygame.draw.rect(self.screen, (20, 100, 35), self.exit_rect, width=2, border_radius=4)

        # Hazards
        for patch in self.fire_patches:
            patch.update(now)
            patch.draw(self.screen)

        # Actors
        self.hero.draw(self.screen, now)
        self.enemy.draw(self.screen, now)
        pygame.draw.rect(self.screen, (90, 170, 240), self.player.rect, border_radius=3)
        pygame.draw.rect(self.screen, (30, 80, 140), self.player.rect, width=2, border_radius=3)

        # HUD / status text
        if not self.phase.won:
            if not self.phase.hero_left:
                msg = "Hero fighting... avoid hazards (jump over the danger)"
            else:
                msg = "Hero left. Get to the exit!"
            self._draw_text(msg, 18, 16)
        else:
            self._draw_text("You made it home!", 38, 24)

        pygame.display.flip()

    def _draw_text(self, text: str, y: int, scale: int) -> None:
        # keep it simple: scale is unused for now, but leaves room for later.
        surf = self.font.render(text, True, (230, 230, 220))
        self.screen.blit(surf, (16, y))

    def run(self) -> int:
        running = True
        smoke_start = pygame.time.get_ticks() / 1000.0

        while running:
            # cap dt to reduce tunneling/jitter in collisions
            dt = min(1.0 / 30.0, self.clock.tick(SCREEN_FPS) / 1000.0)
            now = pygame.time.get_ticks() / 1000.0

            self._jump_pressed = False
            running = self._process_events()
            if not running:
                break

            inp = self._handle_input()

            if self.phase.won:
                # Still render; but keep updating events.
                self._render(now)
            else:
                self._update_fight(now, dt)
                self._update_player(inp, dt)
                self._render(now)

            if self.smoke_test and now - smoke_start >= 1.5:
                running = False

        pygame.quit()
        return 0

