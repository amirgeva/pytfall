"""Player movement: walking, jumping, falling, ladders and rope swinging.

Position is (x, y) = (horizontal center, feet).
"""

from __future__ import annotations

from enum import Enum, auto

from ..ui import Display, InputState, Key
from .geometry import Rect
from .world import Ladder, Platform, Room, Rope

WALK_SPEED = 60.0
JUMP_SPEED = 200.0
GRAVITY = 600.0
MAX_FALL = 300.0
AIR_ACCEL = 300.0
CLIMB_SPEED = 40.0
HALF_W = 5
HEIGHT = 20
RESPAWN_INVULN = 2.0
DEATH_TIME = 1.5


class PState(Enum):
    GROUND = auto()
    AIR = auto()
    CLIMB = auto()
    SWING = auto()
    DEAD = auto()


class Player:
    def __init__(self, x: float, y: float):
        self.spawn(x, y)

    def spawn(self, x: float, y: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.state = PState.GROUND
        self.ladder: Ladder | None = None
        self.rope: Rope | None = None
        self.rope_d = 0.0
        self.grab_cooldown = 0.0
        self.invuln = RESPAWN_INVULN
        self.dead_timer = 0.0
        self.walk_t = 0.0
        self.moving = False

    @property
    def alive(self) -> bool:
        return self.state is not PState.DEAD

    def hitbox(self) -> Rect:
        return Rect(self.x - HALF_W, self.y - HEIGHT, 2 * HALF_W, HEIGHT)

    def kill(self) -> None:
        self.state = PState.DEAD
        self.dead_timer = DEATH_TIME
        self.vx = self.vy = 0.0
        self.ladder = None
        self.rope = None

    # ------------------------------------------------------------ update

    def update(self, dt: float, inp: InputState, room: Room, t: float) -> None:
        self.grab_cooldown = max(0.0, self.grab_cooldown - dt)
        self.invuln = max(0.0, self.invuln - dt)
        if self.state is PState.DEAD:
            self.dead_timer -= dt
            return

        dx = int(inp.held(Key.RIGHT)) - int(inp.held(Key.LEFT))
        if dx:
            self.facing = dx
        self.moving = False

        if self.state is PState.GROUND:
            self._update_ground(dt, inp, room, dx)
        elif self.state is PState.AIR:
            self._update_air(dt, inp, room, dx, t)
        elif self.state is PState.CLIMB:
            self._update_climb(dt, inp, dx)
        elif self.state is PState.SWING:
            self._update_swing(inp, dx, t)

        if self.moving:
            self.walk_t += dt

    def _update_ground(self, dt, inp, room, dx):
        ladder = self._ladder_at(room)
        if ladder is not None:
            at_top = self.y <= ladder.top + 0.5
            if (inp.held(Key.UP) and not at_top) or (inp.held(Key.DOWN) and at_top):
                self._start_climb(ladder)
                return

        if inp.pressed(Key.JUMP):
            self.state = PState.AIR
            self.vx = dx * WALK_SPEED
            self.vy = -JUMP_SPEED
            return

        self.vx = dx * WALK_SPEED
        self.x += self.vx * dt
        self.moving = dx != 0
        if self._support(room) is None:
            self.state = PState.AIR
            self.vy = 0.0

    def _update_air(self, dt, inp, room, dx, t):
        if dx:
            target = dx * WALK_SPEED
            step = AIR_ACCEL * dt
            self.vx = min(target, self.vx + step) if self.vx < target else max(target, self.vx - step)
        self.vy = min(MAX_FALL, self.vy + GRAVITY * dt)

        prev_y = self.y
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.vy >= 0:
            landing = None
            for p in room.platforms:
                if self._overlaps_x(p) and prev_y <= p.y <= self.y:
                    if landing is None or p.y < landing.y:
                        landing = p
            if landing is not None:
                self.y = landing.y
                self.vy = 0.0
                self.state = PState.GROUND
                return

        if self.grab_cooldown > 0:
            return
        if inp.held(Key.UP) or inp.held(Key.DOWN):
            ladder = self._ladder_at(room)
            if ladder is not None and ladder.top < self.y < ladder.bottom:
                self._start_climb(ladder)
                return
        for rope in room.ropes:
            d = self._rope_grab_distance(rope, t)
            if d is not None:
                self.state = PState.SWING
                self.rope = rope
                self.rope_d = d
                self.vx = self.vy = 0.0
                return

    def _update_climb(self, dt, inp, dx):
        ladder = self.ladder
        if inp.pressed(Key.JUMP) and dx:
            self.state = PState.AIR
            self.ladder = None
            self.vx = dx * WALK_SPEED
            self.vy = -JUMP_SPEED * 0.5
            self.grab_cooldown = 0.3
            return

        dy = int(inp.held(Key.DOWN)) - int(inp.held(Key.UP))
        self.moving = dy != 0
        self.y += dy * CLIMB_SPEED * dt
        if self.y <= ladder.top:
            self.y = ladder.top
            self.state = PState.GROUND
            self.ladder = None
        elif self.y >= ladder.bottom:
            self.y = ladder.bottom
            self.state = PState.GROUND
            self.ladder = None

    def _update_swing(self, inp, dx, t):
        rope = self.rope
        px, py = rope.point(t, self.rope_d)
        self.x = px
        self.y = py + HEIGHT
        if inp.pressed(Key.JUMP) or inp.pressed(Key.DOWN):
            rvx, rvy = rope.velocity(t, self.rope_d)
            self.vx = rvx + dx * WALK_SPEED * 0.7
            self.vy = min(rvy, 0.0) - 110.0
            self.state = PState.AIR
            self.rope = None
            self.grab_cooldown = 0.5

    # ------------------------------------------------------------ helpers

    def _overlaps_x(self, p: Platform) -> bool:
        return self.x + HALF_W > p.x and self.x - HALF_W < p.x + p.w

    def _support(self, room: Room) -> Platform | None:
        for p in room.platforms:
            if abs(self.y - p.y) < 0.5 and self._overlaps_x(p):
                return p
        return None

    def _ladder_at(self, room: Room) -> Ladder | None:
        for ladder in room.ladders:
            if abs(self.x - ladder.cx) <= 6 and ladder.top - 1 <= self.y <= ladder.bottom + 1:
                return ladder
        return None

    def _start_climb(self, ladder: Ladder) -> None:
        self.state = PState.CLIMB
        self.ladder = ladder
        self.x = float(ladder.cx)
        self.vx = self.vy = 0.0
        if self.y <= ladder.top + 0.5:
            self.y = ladder.top + 1.0

    def _rope_grab_distance(self, rope: Rope, t: float) -> float | None:
        """Distance along the rope within reach of the player's hands, if any."""
        d = rope.length
        while d >= rope.length * 0.4:
            px, py = rope.point(t, d)
            if abs(px - self.x) <= 6 and self.y - 24 <= py <= self.y - 12:
                return d
            d -= 3
        return None

    # ------------------------------------------------------------ drawing

    def sprite_id(self) -> str:
        if self.state is PState.DEAD:
            return "player/dead"
        if self.state is PState.CLIMB:
            return f"player/climb_{int(self.walk_t * 6) % 2}"
        if self.state is PState.SWING:
            return "player/swing"
        if self.state is PState.AIR:
            return "player/jump"
        if self.moving:
            return f"player/run_{int(self.walk_t * 10) % 4}"
        return "player/idle"

    def draw(self, display: Display, t: float) -> None:
        if self.invuln > 0 and self.alive and int(t * 10) % 2:
            return  # blink while invulnerable
        x, y = round(self.x), round(self.y)
        if self.state is PState.DEAD:
            display.draw_sprite("player/dead", x - 10, y - 12, flip_x=self.facing < 0)
        else:
            flip = self.facing < 0 and self.state is not PState.CLIMB
            display.draw_sprite(self.sprite_id(), x - 6, y - HEIGHT, flip_x=flip)
