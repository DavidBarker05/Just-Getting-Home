from __future__ import annotations

from dataclasses import dataclass

import pygame

from .config import FIRE_H, FIRE_W, GRAVITY, JUMP_VELOCITY, PLAYER_H, PLAYER_SPEED, PLAYER_W
from .utils import clamp


@dataclass
class InputState:
    left: bool
    right: bool
    jump_pressed: bool


class Player:
    def __init__(
        self,
        x: float,
        y: float,
        w: int = PLAYER_W,
        h: int = PLAYER_H,
        sprite_surface: pygame.Surface | None = None,
    ) -> None:
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        # If set, GameApp will render this surface instead of the default rect.
        self.sprite_surface = sprite_surface
        # Jump quality-of-life:
        # - jump_buffer: allows a jump press shortly before landing
        # - coyote_time: allows a jump shortly after leaving the ground
        self.jump_buffer_time = 0.12
        self.jump_buffer_timer = 0.0
        self.coyote_time = 0.08
        self.coyote_timer = 0.0

    def reset(self, x: float, y: float) -> None:
        self.rect.topleft = (int(x), int(y))
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0

    def handle_movement(self, inp: InputState, dt: float) -> None:
        # Update timers first so input registered this frame uses a fresh budget.
        if self.jump_buffer_timer > 0.0:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        if self.coyote_timer > 0.0:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        if inp.jump_pressed:
            self.jump_buffer_timer = self.jump_buffer_time

        self.vel_x = 0.0
        if inp.left:
            self.vel_x = -PLAYER_SPEED
        if inp.right:
            self.vel_x = PLAYER_SPEED

        # Use buffered jump with either grounded state or coyote window.
        if self.jump_buffer_timer > 0.0 and (self.on_ground or self.coyote_timer > 0.0):
            self.vel_y = JUMP_VELOCITY
            self.on_ground = False
            self.jump_buffer_timer = 0.0
            self.coyote_timer = 0.0

    def apply_gravity(self, dt: float) -> None:
        self.vel_y += GRAVITY * dt

    def move_and_collide(self, solids: list[pygame.Rect], dt: float) -> None:
        # X axis
        self.rect.x += int(self.vel_x * dt)
        for tile in solids:
            if self.rect.colliderect(tile):
                if self.vel_x > 0:
                    self.rect.right = tile.left
                elif self.vel_x < 0:
                    self.rect.left = tile.right

        # Y axis
        self.on_ground = False
        self.rect.y += int(self.vel_y * dt)
        for tile in solids:
            if self.rect.colliderect(tile):
                if self.vel_y > 0:
                    self.rect.bottom = tile.top
                    self.vel_y = 0.0
                    self.on_ground = True
                    self.coyote_timer = self.coyote_time
                elif self.vel_y < 0:
                    self.rect.top = tile.bottom
                    self.vel_y = 0.0

    def update(self, inp: InputState, solids: list[pygame.Rect], dt: float) -> None:
        self.handle_movement(inp, dt)
        self.apply_gravity(dt)
        self.move_and_collide(solids, dt)


class Actor:
    def __init__(
        self,
        x: float,
        y: float,
        color_idle: tuple[int, int, int],
        color_attack: tuple[int, int, int],
        sprite_surface: pygame.Surface | None = None,
    ) -> None:
        w = 18
        h = 30
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self.color_idle = color_idle
        self.color_attack = color_attack
        self.sprite_surface = sprite_surface
        self.hp = 100
        self.attacking_until = 0.0

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def draw(self, screen: pygame.Surface, now: float) -> None:
        if self.sprite_surface is not None:
            # Draw the sprite scaled to the actor rect, then tint during attack.
            screen.blit(pygame.transform.smoothscale(self.sprite_surface, self.rect.size), self.rect.topleft)
            if now < self.attacking_until:
                overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
                # Semi-transparent tint so the sprite still reads through.
                overlay.fill((*self.color_attack, 120))
                screen.blit(overlay, self.rect.topleft)
            return

        color = self.color_idle
        if now < self.attacking_until:
            color = self.color_attack
        pygame.draw.rect(screen, color, self.rect)


class FirePatch:
    def __init__(
        self,
        x: float,
        y: float,
        w: int = FIRE_W,
        h: int = FIRE_H,
        duration: float | None = None,
        sprite_surface: pygame.Surface | None = None,
    ) -> None:
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self.duration = duration
        self.active = True
        self.sprite_surface = sprite_surface
        # If duration is None, the hazard is permanent.
        self.expires_at: float | None = None

    def start(self, now: float) -> None:
        if self.duration is None:
            self.expires_at = None
        else:
            self.expires_at = now + self.duration
        self.active = True

    def update(self, now: float) -> None:
        if not self.active:
            return
        if self.expires_at is None:
            return  # permanent hazard
        if now >= self.expires_at:
            self.active = False

    @property
    def expired(self) -> bool:
        return not self.active

    def draw(self, screen: pygame.Surface) -> None:
        if self.active:
            if self.sprite_surface is not None:
                screen.blit(pygame.transform.smoothscale(self.sprite_surface, self.rect.size), self.rect.topleft)
                return

            pygame.draw.rect(screen, (235, 120, 40), self.rect, border_radius=2)
            pygame.draw.rect(screen, (255, 180, 70), self.rect, width=2, border_radius=2)

