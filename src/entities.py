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
    def __init__(self, x: float, y: float, w: int = PLAYER_W, h: int = PLAYER_H) -> None:
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False

    def reset(self, x: float, y: float) -> None:
        self.rect.topleft = (int(x), int(y))
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False

    def handle_movement(self, inp: InputState, dt: float) -> None:
        self.vel_x = 0.0
        if inp.left:
            self.vel_x = -PLAYER_SPEED
        if inp.right:
            self.vel_x = PLAYER_SPEED

        if inp.jump_pressed and self.on_ground:
            self.vel_y = JUMP_VELOCITY
            self.on_ground = False

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
                elif self.vel_y < 0:
                    self.rect.top = tile.bottom
                    self.vel_y = 0.0

    def update(self, inp: InputState, solids: list[pygame.Rect], dt: float) -> None:
        self.handle_movement(inp, dt)
        self.apply_gravity(dt)
        self.move_and_collide(solids, dt)


class Actor:
    def __init__(self, x: float, y: float, color_idle: tuple[int, int, int], color_attack: tuple[int, int, int]) -> None:
        w = 18
        h = 30
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self.color_idle = color_idle
        self.color_attack = color_attack
        self.hp = 100
        self.attacking_until = 0.0

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def draw(self, screen: pygame.Surface, now: float) -> None:
        color = self.color_idle
        if now < self.attacking_until:
            color = self.color_attack
        pygame.draw.rect(screen, color, self.rect)


class FirePatch:
    def __init__(self, x: float, y: float, w: int = FIRE_W, h: int = FIRE_H, duration: float = 3.0) -> None:
        self.rect = pygame.Rect(int(x), int(y), w, h)
        self.expires_at = 0.0
        self.duration = duration
        self.active = True

    def start(self, now: float) -> None:
        self.expires_at = now + self.duration
        self.active = True

    def update(self, now: float) -> None:
        if self.active and now >= self.expires_at:
            self.active = False

    @property
    def expired(self) -> bool:
        return not self.active

    def draw(self, screen: pygame.Surface) -> None:
        if self.active:
            pygame.draw.rect(screen, (235, 120, 40), self.rect, border_radius=2)
            pygame.draw.rect(screen, (255, 180, 70), self.rect, width=2, border_radius=2)

