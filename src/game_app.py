from __future__ import annotations

from dataclasses import dataclass
import json
import sys
from pathlib import Path

import pygame

from .config import DEBUG_STEP_LARGE_S, DEBUG_STEP_MEDIUM_S, DEBUG_STEP_SMALL_S, PLAYER_H, PLAYER_W, SCREEN_FPS
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
        self._sprite_cache: dict[str, pygame.Surface | None] = {}
        # Single simulation clock used by gameplay and debug pause/step.
        self.sim_time = 0.0

        # Debug mode is only available when running from Python (not in a PyInstaller exe).
        self.debug_available = not bool(getattr(sys, "frozen", False))
        self.debug_enabled = False
        self.debug_show_fps = False
        self.debug_show_level_name = False
        self.debug_god_mode = False
        self.debug_paused = False
        self.debug_step_request_s: float = 0.0
        self._last_caption_update_at = 0.0

        # UI flow: menu -> controls -> game.
        # Smoke test skips menu so CI/sanity runs don't wait for clicks.
        self.ui_screen = "game" if smoke_test else "menu"
        self.story_key: str | None = None
        self.story_button_label = "Continue"
        self.story_data = self._load_story_data()

        self.level_def: LevelDef = get_level(self.level_name)
        self._load_level()

    def _load_level(self) -> None:
        self.tilemap = TileMap(self.level_def)
        self.phase = GamePhase()

        psx, psy = self.tilemap.spawns.player_spawn
        self.player_sprite_surface = self._sprite_surface_or_none(getattr(self.tilemap.spawns, "player_sprite", None))
        self.player = Player(psx, psy, sprite_surface=self.player_sprite_surface)

        ex, ey = self.tilemap.spawns.exit_spawn
        self.exit_rect = pygame.Rect(int(ex), int(ey), PLAYER_W, PLAYER_H)
        self.exit_sprite_surface = self._sprite_surface_or_none(getattr(self.tilemap.spawns, "exit_sprite", None))

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

        # Convert route points (JSON bottom-left origin) to internal top-left tile coords.
        self.route_internal: list[tuple[int, int]] = [
            (int(x), (self.tilemap.height_tiles - 1) - int(y)) for (x, y) in self.level_def.route
        ]
        if not self.route_internal:
            raise ValueError(f"Level '{self.level_name}' route is empty.")

        self.hero_last_step_index = 0
        self.end_tile_processed = False
        # IMPORTANT: route timing must use the same simulation clock as run().
        self.start_time = self.sim_time

        # Combat tuning (prototype feel).
        self.ATTACK_INTERVAL = 0.6
        self.DAMAGE = 25
        self.next_attack_at = self.start_time + 0.2

        # Actor dimensions are fixed in `Actor` (18x30), but we keep them explicit.
        actor_w = 18
        actor_h = 30

        def tile_to_actor_pos(tile_x: int, tile_y: int) -> tuple[int, int]:
            x = tile_x * self.tilemap.tile_size + (self.tilemap.tile_size - actor_w) // 2
            # Align actors to the route tile row (visually consistent with the JSON route).
            y = (tile_y + 1) * self.tilemap.tile_size - actor_h
            return x, y

        # Start both at route[0]. Hero will lag 1 behind enemy.
        hero_tile = self.route_internal[0]
        hero_x, hero_y = tile_to_actor_pos(hero_tile[0], hero_tile[1])
        self.hero_sprite_surface = self._sprite_surface_or_none(getattr(self.tilemap.spawns, "hero_sprite", None))
        self.hero = Actor(
            hero_x,
            hero_y,
            color_idle=(170, 60, 60),
            color_attack=(255, 110, 110),
            sprite_surface=self.hero_sprite_surface,
        )

        enemy_x, enemy_y = tile_to_actor_pos(hero_tile[0], hero_tile[1])
        self.enemy_sprite_surface = self._sprite_surface_or_none(getattr(self.tilemap.spawns, "enemy_sprite", None))
        self.enemy = Actor(
            enemy_x,
            enemy_y,
            color_idle=(60, 60, 60),
            color_attack=(110, 110, 110),
            sprite_surface=self.enemy_sprite_surface,
        )

    def _reset_level(self) -> None:
        self._load_level()

    def _restart_game(self) -> None:
        self.level_index = 0
        self.level_name = self.level_order[self.level_index]
        self.level_def = get_level(self.level_name)
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

            # Debug toggles (only when running from Python).
            if self.debug_available and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    self.debug_enabled = not self.debug_enabled
                if not self.debug_enabled:
                    continue

                if event.key == pygame.K_F2:
                    self.debug_show_fps = not self.debug_show_fps
                elif event.key == pygame.K_F3:
                    self.debug_show_level_name = not self.debug_show_level_name
                elif event.key == pygame.K_F4:
                    self.debug_god_mode = not self.debug_god_mode
                elif event.key == pygame.K_F5:
                    self._reset_level()
                elif event.key == pygame.K_F6:
                    self._restart_game()
                elif event.key == pygame.K_F7:
                    self.debug_paused = not self.debug_paused
                elif event.key == pygame.K_COMMA:
                    self.debug_step_request_s += DEBUG_STEP_SMALL_S
                elif event.key == pygame.K_PERIOD:
                    self.debug_step_request_s += DEBUG_STEP_MEDIUM_S
                elif event.key == pygame.K_SLASH:
                    self.debug_step_request_s += DEBUG_STEP_LARGE_S
        return True

    def _menu_button_rects(self) -> dict[str, pygame.Rect]:
        button_w = 300
        button_h = 56
        gap = 18
        total_h = button_h * 3 + gap * 2
        start_y = (self.height - total_h) // 2 + 36
        x = (self.width - button_w) // 2
        return {
            "start": pygame.Rect(x, start_y, button_w, button_h),
            "controls": pygame.Rect(x, start_y + button_h + gap, button_w, button_h),
            "quit": pygame.Rect(x, start_y + (button_h + gap) * 2, button_w, button_h),
        }

    def _process_menu_events(self) -> bool:
        buttons = self._menu_button_rects()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # ESC in menu/controls exits the game quickly.
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and self.ui_screen == "menu":
                self._restart_game()
                self._open_story_for_current_level(initial=True)
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                self.ui_screen = "controls"
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_b and self.ui_screen == "controls":
                self.ui_screen = "menu"
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and self.ui_screen == "story":
                self.ui_screen = "game"
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.ui_screen == "menu":
                if buttons["start"].collidepoint(event.pos):
                    self._restart_game()
                    self._open_story_for_current_level(initial=True)
                    return True
                if buttons["controls"].collidepoint(event.pos):
                    self.ui_screen = "controls"
                    return True
                if buttons["quit"].collidepoint(event.pos):
                    return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.ui_screen == "controls":
                self.ui_screen = "menu"
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.ui_screen == "story":
                if self._story_continue_button_rect().collidepoint(event.pos):
                    self.ui_screen = "game"
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.ui_screen == "ending":
                end_buttons = self._ending_button_rects()
                if end_buttons["menu"].collidepoint(event.pos):
                    self._restart_game()
                    self.ui_screen = "menu"
                    return True
                if end_buttons["quit"].collidepoint(event.pos):
                    return False
        return True

    def _set_actor_to_tile(self, actor: Actor, tile_x: int, tile_y: int) -> None:
        # Actor stands on top of the floor tile.
        actor_w = actor.rect.width
        actor_h = actor.rect.height
        actor.rect.x = tile_x * self.tilemap.tile_size + (self.tilemap.tile_size - actor_w) // 2
        actor.rect.y = (tile_y + 1) * self.tilemap.tile_size - actor_h

    def _sprite_surface_or_none(self, sprite_name: str | None) -> pygame.Surface | None:
        """Load a sprite from `assets/sprites/<name>.png` with caching.

        Empty/None sprite names mean "use the default shape rendering".
        """
        if not sprite_name:
            return None
        if sprite_name in self._sprite_cache:
            return self._sprite_cache[sprite_name]

        sprites_dir = Path(__file__).resolve().parent.parent / "assets" / "sprites"
        sprite_path = sprites_dir / f"{sprite_name}.png"
        try:
            if not sprite_path.exists():
                self._sprite_cache[sprite_name] = None
                return None
            surf = pygame.image.load(str(sprite_path)).convert_alpha()
        except Exception:
            self._sprite_cache[sprite_name] = None
            return None

        self._sprite_cache[sprite_name] = surf
        return surf

    def _destroy_and_spawn_from_tile(self, prev_tile_x: int, prev_tile_y: int, now: float) -> None:
        # Route points currently represent the actor's step row (one cell above floor),
        # so convert to the actual floor tile before applying break/fire logic.
        floor_tile_x = prev_tile_x
        floor_tile_y = prev_tile_y + 1

        # Break tiles.
        # Decide fire behavior based on whether the floor tile was breakable BEFORE destroying it.
        tile_was_breakable = (floor_tile_x, floor_tile_y) in self.tilemap.breakable_tiles
        self.tilemap.destroy_breakable_tile(floor_tile_x, floor_tile_y)

        # Fire markers live in the actor-step row, i.e. the route cell itself.
        fire_cell = (prev_tile_x, prev_tile_y)
        if tile_was_breakable:
            # Avoid fire spawning above destroyed breakable floors.
            return
        if fire_cell not in self.tilemap.fire_cells:
            return
        if fire_cell in self.activated_fire_cells:
            return

        rect = self.tilemap.fire_rect_from_cell(fire_cell[0], fire_cell[1])
        fire_sprite_name = self.tilemap.fire_sprites.get(fire_cell)
        fire_sprite_surface = self._sprite_surface_or_none(fire_sprite_name)
        patch = FirePatch(rect.x, rect.y, w=rect.width, h=rect.height, duration=None, sprite_surface=fire_sprite_surface)
        patch.start(now)
        self.fire_patches.append(patch)
        self.activated_fire_cells.add(fire_cell)

    def _update_fight(self, now: float, dt: float) -> None:
        if self.phase.won or self.phase.lost or self.phase.hero_left:
            return

        end_index = len(self.route_internal) - 1
        t = now - self.start_time

        # Enemy leads; hero follows.
        # With this prototype route stepping, the "one tile to the left" relationship
        # is represented as "hero is 1 route-step behind the enemy".
        hero_follow_gap_steps = 1
        enemy_step_index = min(int(t / self.hero_step_interval_s), end_index)
        hero_step_index = max(0, enemy_step_index - hero_follow_gap_steps)

        # Apply tile-by-tile destruction/fire when hero advances.
        if hero_step_index > self.hero_last_step_index:
            for passed_index in range(self.hero_last_step_index, hero_step_index):
                prev_tile_x, prev_tile_y = self.route_internal[passed_index]
                self._destroy_and_spawn_from_tile(prev_tile_x, prev_tile_y, now)
            self.hero_last_step_index = hero_step_index

        # Move actors along the route until the enemy is defeated.
        # Once defeated, the hero retreats off-screen and we must NOT keep
        # snapping the hero back onto the end tile each frame.
        if self.phase.enemy_dead:
            end_tile_x, end_tile_y = self.route_internal[end_index]
            self._set_actor_to_tile(self.enemy, end_tile_x, end_tile_y)
        else:
            hero_tile_x, hero_tile_y = self.route_internal[hero_step_index]
            self._set_actor_to_tile(self.hero, hero_tile_x, hero_tile_y)
            enemy_tile_x, enemy_tile_y = self.route_internal[enemy_step_index]
            self._set_actor_to_tile(self.enemy, enemy_tile_x, enemy_tile_y)

        # Combat only happens when the hero reaches its final tile (2 tiles left of the exit).
        hero_final_index = max(0, end_index - hero_follow_gap_steps)
        if hero_step_index == hero_final_index and not self.phase.enemy_dead:
            if self.enemy.alive and now >= self.next_attack_at:
                # Flash the enemy during the "proper fight" instead of the hero.
                self.enemy.attacking_until = now + 0.15
                self.enemy.take_damage(self.DAMAGE)
                self.next_attack_at = now + self.ATTACK_INTERVAL

            if not self.enemy.alive:
                self.phase.enemy_dead = True

        # After defeating the enemy, the hero retreats off-screen.
        if self.phase.enemy_dead and not self.phase.hero_left:
            # Process the end tile once when hero begins retreating.
            if not self.end_tile_processed:
                # Now that the hero follows after the enemy, we want to process the
                # tile the hero is standing on (its final tile), not the enemy's tile.
                hero_final_x, hero_final_y = self.route_internal[end_index - hero_follow_gap_steps]
                self._destroy_and_spawn_from_tile(hero_final_x, hero_final_y, now)
                self.end_tile_processed = True

            self.hero.rect.x += int(520 * dt)
            if self.hero.rect.left > self.tilemap.width_px() + 80:
                self.phase.hero_left = True

    def _update_player(self, inp: InputState, dt: float) -> None:
        solids = self.tilemap.solid_rects()

        # Lock player controls until the hero is fully off-screen.
        if not self.phase.hero_left:
            inp = InputState(left=False, right=False, jump_pressed=False)

        self.player.update(inp, solids, dt)

        # Prevent the player from leaving the visible screen horizontally.
        # (No side walls in the tilemap, so without clamping the player could drift off-screen.)
        if self.player.rect.left < 0:
            self.player.rect.left = 0
            self.player.vel_x = 0.0
        elif self.player.rect.right > self.width:
            self.player.rect.right = self.width
            self.player.vel_x = 0.0

        # Permanent hazard collision: restart level.
        if not self.debug_god_mode:
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
                self._open_story_for_current_level(initial=False)
                return

            self.phase.won = True
            self.story_key = "ending"
            self.ui_screen = "ending"

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
            sprite_name = self.tilemap.tile_sprites.get((gx, gy))
            if sprite_name:
                surf = self._sprite_surface_or_none(sprite_name)
                if surf is not None:
                    self.screen.blit(pygame.transform.smoothscale(surf, r.size), r.topleft)
                    continue

            is_breakable = (gx, gy) in self.tilemap.breakable_tiles
            pygame.draw.rect(self.screen, break_color if is_breakable else ground_color, r)
            pygame.draw.rect(self.screen, (70, 55, 40), r, width=1)

        if self.exit_sprite_surface is not None:
            self.screen.blit(
                pygame.transform.smoothscale(self.exit_sprite_surface, self.exit_rect.size),
                self.exit_rect.topleft,
            )
        else:
            pygame.draw.rect(self.screen, (80, 200, 90), self.exit_rect, border_radius=4)
            pygame.draw.rect(self.screen, (20, 100, 35), self.exit_rect, width=2, border_radius=4)

        for patch in self.fire_patches:
            patch.draw(self.screen)

        # Decorative props (e.g. house at the end).
        for prop in getattr(self.tilemap, "props", []):
            if prop.get("kind") != "house":
                continue
            rect = prop.get("rect")
            if rect is None:
                continue

            # On the final level, swap to the destroyed house sprite after the fight ends.
            is_final_level = self.level_index == (len(self.level_order) - 1)
            if is_final_level and self.phase.enemy_dead:
                sprite_name = prop.get("destroyed_sprite") or prop.get("sprite")
            else:
                sprite_name = prop.get("sprite")

            surf = self._sprite_surface_or_none(sprite_name)
            if surf is not None:
                self.screen.blit(pygame.transform.smoothscale(surf, rect.size), rect.topleft)
            else:
                # Fallback: simple placeholder rectangle if no sprite is provided.
                pygame.draw.rect(self.screen, (150, 110, 80), rect, border_radius=6)
                pygame.draw.rect(self.screen, (70, 50, 35), rect, width=2, border_radius=6)

        self.hero.draw(self.screen, now)
        if self.enemy.alive:
            self.enemy.draw(self.screen, now)
        if self.player.sprite_surface is not None:
            self.screen.blit(
                pygame.transform.smoothscale(self.player.sprite_surface, self.player.rect.size),
                self.player.rect.topleft,
            )
        else:
            pygame.draw.rect(self.screen, (90, 170, 240), self.player.rect, border_radius=3)
            pygame.draw.rect(self.screen, (30, 80, 140), self.player.rect, width=2, border_radius=3)

        if self.debug_enabled:
            self._render_debug_overlay()
            if self.debug_show_level_name:
                self._draw_text_centered(f"Level: {self.level_name}", y=8)

        if not self.phase.won:
            if not self.phase.hero_left:
                msg = "You are not the hero. Wait for him to leave the route."
            else:
                msg = "Hero left. Get to the exit!"
            self._draw_text(msg, 18, 16)
        else:
            self._draw_text("You made it home!", 38, 24)

        pygame.display.flip()

    def _draw_text_right(self, text: str, y: int) -> None:
        surf = self.font.render(text, True, (230, 230, 220))
        x = self.width - 12 - surf.get_width()
        self.screen.blit(surf, (x, y))

    def _draw_text_centered(self, text: str, y: int) -> None:
        surf = self.font.render(text, True, (230, 230, 220))
        x = (self.width - surf.get_width()) // 2
        self.screen.blit(surf, (x, y))

    def _render_debug_overlay(self) -> None:
        # Right-justified help text (top-right).
        lines = [
            "Debug (F1): toggle",
            "F2: FPS in title",
            "F3: level name",
            "F4: god mode",
            "F5: restart level",
            "F6: restart game",
            "F7: pause/unpause",
            f",: +{DEBUG_STEP_SMALL_S:.1f}s  .: +{DEBUG_STEP_MEDIUM_S:.1f}s  /: +{DEBUG_STEP_LARGE_S:.1f}s",
        ]

        y = 8
        for line in lines:
            self._draw_text_right(line, y)
            y += 18

    def _draw_menu_button(self, rect: pygame.Rect, label: str, hovered: bool) -> None:
        fill = (95, 120, 145) if hovered else (70, 92, 112)
        border = (28, 42, 56)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)
        surf = self.font.render(label, True, (240, 240, 235))
        x = rect.x + (rect.width - surf.get_width()) // 2
        y = rect.y + (rect.height - surf.get_height()) // 2
        self.screen.blit(surf, (x, y))

    def _story_panel_rect(self) -> pygame.Rect:
        panel_w = min(820, self.width - 80)
        panel_h = min(420, self.height - 120)
        return pygame.Rect((self.width - panel_w) // 2, (self.height - panel_h) // 2, panel_w, panel_h)

    def _story_continue_button_rect(self) -> pygame.Rect:
        panel = self._story_panel_rect()
        btn_w = 220
        btn_h = 52
        return pygame.Rect(panel.centerx - btn_w // 2, panel.bottom - btn_h - 22, btn_w, btn_h)

    def _ending_button_rects(self) -> dict[str, pygame.Rect]:
        panel = self._story_panel_rect()
        btn_w = 220
        btn_h = 52
        gap = 24
        total_w = btn_w * 2 + gap
        start_x = panel.centerx - total_w // 2
        y = panel.bottom - btn_h - 22
        return {
            "menu": pygame.Rect(start_x, y, btn_w, btn_h),
            "quit": pygame.Rect(start_x + btn_w + gap, y, btn_w, btn_h),
        }

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        wrapped: list[str] = []
        for paragraph in text.split("\n"):
            words = paragraph.split()
            if not words:
                wrapped.append("")
                continue
            line = words[0]
            for word in words[1:]:
                trial = f"{line} {word}"
                if self.font.size(trial)[0] <= max_width:
                    line = trial
                else:
                    wrapped.append(line)
                    line = word
            wrapped.append(line)
        return wrapped

    def _load_story_data(self) -> dict[str, str]:
        story_path = Path(__file__).resolve().parent.parent / "assets" / "story" / "story.json"
        defaults = {
            "before_market": "You set off from the market. Stay out of the hero's way and survive the chaos.",
            "before_bridge": "The bridge route is unstable after the last clash. Keep moving and avoid the flames.",
            "before_forestchokepoint": "The forest narrows ahead. The hero's path leaves danger behind for you.",
            "before_burninghearthrun": "Home is close now. One last battle stands between you and safety.",
            "ending": "You finally make it home... only to find the hero's final battle has destroyed it.",
        }
        try:
            if not story_path.exists():
                return defaults
            data = json.loads(story_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return defaults
            merged = defaults.copy()
            for key, value in data.items():
                if isinstance(value, str) and value.strip():
                    merged[str(key)] = value
            return merged
        except Exception:
            return defaults

    def _open_story_for_current_level(self, initial: bool) -> None:
        self.story_key = f"before_{self.level_name}"
        self.story_button_label = "Begin Level" if initial else "Continue"
        self.ui_screen = "story"

    def _render_menu(self) -> None:
        self.screen.fill((18, 22, 30))
        title_font = pygame.font.SysFont(None, 64)
        subtitle_font = pygame.font.SysFont(None, 28)
        title = title_font.render("Just Getting Home", True, (240, 236, 215))
        subtitle = subtitle_font.render("You are not the main character", True, (190, 196, 210))
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 70))
        self.screen.blit(subtitle, ((self.width - subtitle.get_width()) // 2, 132))

        mouse_pos = pygame.mouse.get_pos()
        buttons = self._menu_button_rects()
        self._draw_menu_button(buttons["start"], "Start Game", buttons["start"].collidepoint(mouse_pos))
        self._draw_menu_button(buttons["controls"], "Controls", buttons["controls"].collidepoint(mouse_pos))
        self._draw_menu_button(buttons["quit"], "Quit", buttons["quit"].collidepoint(mouse_pos))

        hint = self.font.render("Enter: Start   C: Controls   Esc: Quit", True, (178, 186, 200))
        self.screen.blit(hint, ((self.width - hint.get_width()) // 2, self.height - 44))
        pygame.display.flip()

    def _render_controls(self) -> None:
        self.screen.fill((18, 22, 30))
        title_font = pygame.font.SysFont(None, 52)
        title = title_font.render("Controls", True, (240, 236, 215))
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 56))

        lines = [
            "Move: A/D or Left/Right",
            "Jump: W / Up / Space",
        ]
        if self.debug_available:
            lines.append("Debug (Python only): F1-F7, , . /")
        lines.extend(["", "Click anywhere to return", "or press B for Back"])
        y = 150
        for line in lines:
            surf = self.font.render(line, True, (220, 224, 232))
            self.screen.blit(surf, ((self.width - surf.get_width()) // 2, y))
            y += 34
        pygame.display.flip()

    def _render_story(self, ending: bool = False) -> None:
        self.screen.fill((18, 22, 30))
        panel = self._story_panel_rect()
        pygame.draw.rect(self.screen, (42, 52, 68), panel, border_radius=10)
        pygame.draw.rect(self.screen, (20, 28, 40), panel, width=2, border_radius=10)

        title_font = pygame.font.SysFont(None, 50)
        title_text = "The End" if ending else "Story"
        title = title_font.render(title_text, True, (240, 236, 215))
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 18))

        story_text = self.story_data.get(self.story_key or "", "")
        text_x = panel.x + 26
        text_y = panel.y + 86
        text_max_w = panel.width - 52
        for line in self._wrap_text(story_text, text_max_w):
            surf = self.font.render(line, True, (230, 232, 238))
            self.screen.blit(surf, (text_x, text_y))
            text_y += 30

        mouse_pos = pygame.mouse.get_pos()
        if ending:
            btns = self._ending_button_rects()
            self._draw_menu_button(btns["menu"], "Return To Menu", btns["menu"].collidepoint(mouse_pos))
            self._draw_menu_button(btns["quit"], "Quit Game", btns["quit"].collidepoint(mouse_pos))
        else:
            continue_rect = self._story_continue_button_rect()
            self._draw_menu_button(
                continue_rect, self.story_button_label, continue_rect.collidepoint(mouse_pos)
            )

        pygame.display.flip()

    def _update_caption(self) -> None:
        if not (self.debug_enabled and self.debug_show_fps):
            pygame.display.set_caption("Just Getting Home")
            return

        now = pygame.time.get_ticks() / 1000.0
        if now - self._last_caption_update_at < 0.25:
            return
        self._last_caption_update_at = now
        fps = self.clock.get_fps()
        pygame.display.set_caption(f"Just Getting Home  |  FPS: {fps:.1f}")

    def _draw_text(self, text: str, y: int, scale: int) -> None:
        surf = self.font.render(text, True, (230, 230, 220))
        self.screen.blit(surf, (16, y))

    def run(self) -> int:
        running = True
        smoke_elapsed = 0.0

        while running:
            raw_dt = self.clock.tick(SCREEN_FPS) / 1000.0
            raw_dt = min(1.0 / 30.0, raw_dt)
            smoke_elapsed += raw_dt

            if self.ui_screen != "game":
                running = self._process_menu_events()
                if not running:
                    break
                if self.ui_screen == "controls":
                    self._render_controls()
                elif self.ui_screen == "story":
                    self._render_story(ending=False)
                elif self.ui_screen == "ending":
                    self._render_story(ending=True)
                else:
                    self._render_menu()
                # Keep simulation frozen while UI/story screens are open.
                # Gameplay time must not advance until "Begin Level"/"Continue" is pressed.
                if self.smoke_test and smoke_elapsed >= 1.5:
                    running = False
                continue

            self._jump_pressed = False
            running = self._process_events()
            if not running:
                break

            inp = self._handle_input()

            # Debug pause/step time handling.
            if self.debug_enabled and self.debug_paused:
                if self.debug_step_request_s > 0.0:
                    dt = min(1.0, self.debug_step_request_s)
                    self.debug_step_request_s = max(0.0, self.debug_step_request_s - dt)
                else:
                    dt = 0.0
            else:
                dt = raw_dt

            self.sim_time += dt
            now = self.sim_time

            if self.phase.won:
                self._render(now)
            else:
                self._update_fight(now, dt)
                self._update_player(inp, dt)
                self._render(now)

            self._update_caption()

            if self.smoke_test and smoke_elapsed >= 1.5:
                running = False

        pygame.quit()
        return 0

