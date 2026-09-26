"""Room layout: platforms, pits, ladders, ropes, water and monster placement.

The world is an endless strip of screens ("rooms"), each generated
deterministically from (seed, index). Every room has a jungle surface and an
underground tunnel below it. All geometry is aligned to 8px tiles.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from ..config import SCREEN_W
from .geometry import Rect
from .monsters import Bat, Monster, Scorpion, Snake

TILE = 8
TILES_X = SCREEN_W // TILE

HUD_H = 16
SURFACE_Y = 120  # top of the jungle floor
FLOOR_Y = 184    # top of the tunnel floor
LOG_Y = 100      # floating log platforms
# Generation keeps the outer ~6 tile columns of the surface solid so that
# entering a room or respawning at its left edge is always safe.


@dataclass
class Platform:
    """One-way platform: solid when landing from above, passable from below."""

    x: int
    y: int
    w: int


@dataclass
class Ladder:
    x: int  # left edge; ladders are 16px wide
    top: int
    bottom: int

    @property
    def cx(self) -> int:
        return self.x + 8


@dataclass
class Rope:
    """Pendulum rope. Its angle is driven (not simulated) so timing is learnable."""

    ax: float
    ay: float
    length: float
    amplitude: float = 0.6
    period: float = 3.0
    phase: float = 0.0

    def _phase(self, t: float) -> float:
        return 2 * math.pi * t / self.period + self.phase

    def angle(self, t: float) -> float:
        return self.amplitude * math.sin(self._phase(t))

    def point(self, t: float, d: float) -> tuple[float, float]:
        a = self.angle(t)
        return self.ax + d * math.sin(a), self.ay + d * math.cos(a)

    def velocity(self, t: float, d: float) -> tuple[float, float]:
        a = self.angle(t)
        w = self.amplitude * 2 * math.pi / self.period * math.cos(self._phase(t))
        return d * w * math.cos(a), -d * w * math.sin(a)


@dataclass
class Water:
    x: int
    w: int

    @property
    def hazard(self) -> Rect:
        return Rect(self.x, SURFACE_Y + 6, self.w, 10)


@dataclass
class Treasure:
    x: int  # center
    y: int  # resting surface
    value: int = 500

    @property
    def rect(self) -> Rect:
        return Rect(self.x - 6, self.y - 8, 12, 8)


@dataclass
class Room:
    index: int
    kind: str
    platforms: list[Platform] = field(default_factory=list)
    ladders: list[Ladder] = field(default_factory=list)
    ropes: list[Rope] = field(default_factory=list)
    waters: list[Water] = field(default_factory=list)
    monsters: list[Monster] = field(default_factory=list)
    treasure: Treasure | None = None
    # Static draw list: (sprite_id, x, y)
    tiles: list[tuple[str, int, int]] = field(default_factory=list)


ROOM_KINDS = ["ladder", "pits", "logs", "swamp", "snake"]


def generate_room(index: int, seed: int) -> Room:
    rng = random.Random(seed * 1_000_003 + index)
    kind = "ladder" if index == 0 else rng.choice(ROOM_KINDS)
    room = Room(index, kind)
    holes: list[tuple[int, int]] = []  # (first tile, tile count)

    def add_ladder(tx: int) -> None:
        room.ladders.append(Ladder(tx * TILE, SURFACE_Y, FLOOR_Y))

    def add_scorpion() -> None:
        x = rng.randint(60, SCREEN_W - 60)
        room.monsters.append(Scorpion(x, FLOOR_Y, 12, SCREEN_W - 12))

    def maybe_treasure(y: int, avoid: list[tuple[int, int]] = ()) -> None:
        if rng.random() < 0.5:
            return
        for _ in range(20):
            x = rng.randint(64, SCREEN_W - 64)
            if all(not (a - 8 <= x <= b + 8) for a, b in avoid):
                room.treasure = Treasure(x, y)
                return

    if kind == "ladder":
        tx = rng.randint(14, 22)
        add_ladder(tx)
        add_scorpion()
        maybe_treasure(FLOOR_Y, [(tx * TILE, tx * TILE + 16)])

    elif kind == "pits":
        holes.append((rng.randint(8, 13), rng.randint(3, 4)))
        holes.append((rng.randint(26, 30), rng.randint(3, 4)))
        add_ladder(rng.randint(18, 21))
        room.monsters.append(Bat(SCREEN_W / 2, 72, 90, rng.uniform(0, math.tau)))
        maybe_treasure(FLOOR_Y)

    elif kind == "logs":
        holes.append((14, 12))
        for tx in (15, 19, 23):
            room.platforms.append(Platform(tx * TILE, LOG_Y, 2 * TILE))
        add_ladder(rng.randint(29, 31))
        add_scorpion()
        if rng.random() < 0.5:
            room.treasure = Treasure(19 * TILE + TILE, LOG_Y)

    elif kind == "swamp":
        room.waters.append(Water(15 * TILE, 10 * TILE))
        room.ropes.append(Rope(SCREEN_W / 2, HUD_H + 8, 68, phase=rng.uniform(0, math.tau)))
        if rng.random() < 0.5:
            room.monsters.append(Snake(rng.randint(28, 32) * TILE, SURFACE_Y))
        maybe_treasure(FLOOR_Y)

    elif kind == "snake":
        holes.append((rng.randint(8, 10), 3))
        room.monsters.append(Snake(rng.randint(16, 23) * TILE, SURFACE_Y))
        add_ladder(rng.randint(27, 31))
        add_scorpion()
        maybe_treasure(SURFACE_Y, [(15 * TILE, 24 * TILE)])

    # Surface platforms are the jungle floor minus holes and water.
    gaps = sorted(holes + [(w.x // TILE, w.w // TILE) for w in room.waters])
    tx = 0
    for g_start, g_len in gaps + [(TILES_X, 0)]:
        if g_start > tx:
            room.platforms.append(Platform(tx * TILE, SURFACE_Y, (g_start - tx) * TILE))
        tx = g_start + g_len
    room.platforms.append(Platform(0, FLOOR_Y, SCREEN_W))

    _build_tiles(room)
    return room


def _build_tiles(room: Room) -> None:
    tiles = room.tiles
    for p in room.platforms:
        for x in range(p.x, p.x + p.w, TILE):
            if p.y == SURFACE_Y:
                tiles.append(("platforms/grass", x, p.y))
                tiles.append(("platforms/dirt", x, p.y + TILE))
            elif p.y == FLOOR_Y:
                tiles.append(("platforms/brick", x, p.y))
                tiles.append(("platforms/brick", x, p.y + TILE))
            else:
                tiles.append(("platforms/log", x, p.y))
    for lad in room.ladders:
        for y in range(lad.top - TILE, lad.bottom, TILE):
            tiles.append(("props/ladder", lad.x, y))
    for rope in room.ropes:
        tiles.append(("props/anchor", int(rope.ax) - 5, int(rope.ay) - 2))
