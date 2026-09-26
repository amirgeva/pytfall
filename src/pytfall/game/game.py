"""Top-level game state: title, play and game-over, room transitions, rendering."""

from __future__ import annotations

from ..ui import Display, InputState, Key
from .player import Player
from .text import draw_text, draw_text_centered, text_width
from .world import FLOOR_Y, HUD_H, SURFACE_Y, TILE, Room, generate_room

START_LIVES = 3
SPAWN_X = 24


class Game:
    def __init__(self, width: int, height: int, seed: int = 1982):
        self.width = width
        self.height = height
        self.seed = seed
        self.t = 0.0
        self.mode = "title"
        self.quit_requested = False
        self._new_game()

    def _new_game(self) -> None:
        self.score = 0
        self.lives = START_LIVES
        self.collected: set[int] = set()
        self._load_room(0)
        self.player = Player(SPAWN_X, SURFACE_Y)

    def _load_room(self, index: int) -> None:
        self.room: Room = generate_room(index, self.seed)

    # ------------------------------------------------------------ update

    def update(self, dt: float, inp: InputState) -> None:
        self.t += dt
        if inp.pressed(Key.QUIT):
            self.quit_requested = True
            return

        if self.mode == "title":
            if inp.pressed(Key.START) or inp.pressed(Key.JUMP):
                self._new_game()
                self.mode = "play"
        elif self.mode == "gameover":
            if inp.pressed(Key.START):
                self.mode = "title"
        else:
            self._update_play(dt, inp)

    def _update_play(self, dt: float, inp: InputState) -> None:
        player = self.player
        for m in self.room.monsters:
            m.update(dt, self.t, player)
        player.update(dt, inp, self.room, self.t)

        if not player.alive:
            if player.dead_timer <= 0:
                if self.lives > 0:
                    player.spawn(SPAWN_X, SURFACE_Y)
                else:
                    self.mode = "gameover"
            return

        # Walking off a screen edge moves to the neighbouring room.
        if player.x < 0:
            self._load_room(self.room.index - 1)
            player.x += self.width
        elif player.x >= self.width:
            self._load_room(self.room.index + 1)
            player.x -= self.width

        box = player.hitbox()
        if any(box.intersects(w.hazard) for w in self.room.waters):
            self._kill_player()
            return
        if player.invuln <= 0 and any(box.intersects(m.hitbox()) for m in self.room.monsters):
            self._kill_player()
            return

        treasure = self.room.treasure
        if treasure and self.room.index not in self.collected and box.intersects(treasure.rect):
            self.collected.add(self.room.index)
            self.score += treasure.value

    def _kill_player(self) -> None:
        self.player.kill()
        self.lives -= 1

    # ------------------------------------------------------------ render

    def render(self, display: Display) -> None:
        display.draw_sprite("background/jungle", 0, HUD_H)
        display.draw_sprite("background/underground", 0, SURFACE_Y)
        for sprite_id, x, y in self.room.tiles:
            display.draw_sprite(sprite_id, x, y)

        water_frame = int(self.t * 3) % 2
        for w in self.room.waters:
            for x in range(w.x, w.x + w.w, TILE):
                display.draw_sprite(f"props/water_{water_frame}", x, SURFACE_Y + 2)

        for rope in self.room.ropes:
            d = 0.0
            while d <= rope.length:
                px, py = rope.point(self.t, d)
                display.draw_sprite("props/rope", round(px) - 1, round(py) - 1)
                d += 2.0

        treasure = self.room.treasure
        if treasure and self.room.index not in self.collected:
            display.draw_sprite("items/gold", treasure.x - 6, treasure.y - 8)

        for m in self.room.monsters:
            m.draw(display, self.t)

        if self.mode != "title":
            self.player.draw(display, self.t)

        self._render_hud(display)

    def _render_hud(self, display: Display) -> None:
        draw_text(display, f"SCORE {self.score:06d}", 4, 4)
        room_label = f"ROOM {self.room.index}"
        draw_text(display, room_label, (self.width - text_width(room_label)) // 2, 4)
        for i in range(self.lives):
            display.draw_sprite("hud/life", self.width - 12 - i * 10, 4)

        if self.mode == "title":
            draw_text_centered(display, "PYTFALL", 50)
            draw_text_centered(display, "PRESS ENTER TO START", 66)
            draw_text_centered(display, "ARROWS MOVE - SPACE JUMP", FLOOR_Y - 30)
        elif self.mode == "gameover":
            draw_text_centered(display, "GAME OVER", 56)
            draw_text_centered(display, "PRESS ENTER", 72)
