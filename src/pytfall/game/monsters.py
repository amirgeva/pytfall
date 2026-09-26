"""Monsters. Each one is positioned by its horizontal center (x) and feet (y)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ..ui import Display
from .geometry import Rect

if TYPE_CHECKING:
    from .player import Player


class Monster:
    sprite_base = ""
    sprite_w = 16
    sprite_h = 10
    anim_period = 0.2

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.facing = 1

    def update(self, dt: float, t: float, player: Player) -> None:
        pass

    def hitbox(self) -> Rect:
        raise NotImplementedError

    def draw(self, display: Display, t: float) -> None:
        frame = int(t / self.anim_period) % 2
        display.draw_sprite(
            f"{self.sprite_base}_{frame}",
            round(self.x) - self.sprite_w // 2,
            round(self.y) - self.sprite_h,
            flip_x=self.facing < 0,
        )


class Scorpion(Monster):
    """Patrols a floor segment and crawls toward the player when on its level."""

    sprite_base = "monsters/scorpion"
    sprite_h = 10
    speed = 18.0

    def __init__(self, x: float, y: float, x_min: float, x_max: float):
        super().__init__(x, y)
        self.x_min = x_min
        self.x_max = x_max

    def update(self, dt, t, player):
        if player.alive and abs(player.y - self.y) < 2 and abs(player.x - self.x) > 2:
            self.facing = 1 if player.x > self.x else -1
        elif self.x <= self.x_min:
            self.facing = 1
        elif self.x >= self.x_max:
            self.facing = -1
        self.x = min(self.x_max, max(self.x_min, self.x + self.facing * self.speed * dt))

    def hitbox(self):
        return Rect(self.x - 7, self.y - 7, 14, 7)


class Snake(Monster):
    """Stationary coiled snake that turns to face the player."""

    sprite_base = "monsters/snake"
    sprite_h = 11  # the sprite has an empty bottom row
    anim_period = 0.35

    def update(self, dt, t, player):
        self.facing = 1 if player.x >= self.x else -1

    def hitbox(self):
        return Rect(self.x - 6, self.y - 8, 12, 8)


class Bat(Monster):
    """Flies back and forth on a sine path around (cx, cy)."""

    sprite_base = "monsters/bat"
    sprite_h = 5  # drawn centered vertically on y
    anim_period = 0.12

    def __init__(self, cx: float, cy: float, span: float, phase: float = 0.0):
        super().__init__(cx, cy)
        self.cx, self.cy, self.span, self.phase = cx, cy, span, phase

    def update(self, dt, t, player):
        a = 0.9 * t + self.phase
        self.x = self.cx + self.span * math.sin(a)
        self.y = self.cy + 6 * math.sin(4 * t)
        self.facing = 1 if math.cos(a) >= 0 else -1

    def hitbox(self):
        return Rect(self.x - 6, self.y - 3, 12, 6)
