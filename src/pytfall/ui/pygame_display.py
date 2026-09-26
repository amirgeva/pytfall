"""Local pygame implementation of ``Display``."""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

from .display import Display, EventType, InputEvent, Key

KEYMAP = {
    pygame.K_LEFT: Key.LEFT,
    pygame.K_a: Key.LEFT,
    pygame.K_RIGHT: Key.RIGHT,
    pygame.K_d: Key.RIGHT,
    pygame.K_UP: Key.UP,
    pygame.K_w: Key.UP,
    pygame.K_DOWN: Key.DOWN,
    pygame.K_s: Key.DOWN,
    pygame.K_SPACE: Key.JUMP,
    pygame.K_RETURN: Key.START,
    pygame.K_ESCAPE: Key.QUIT,
}


class PygameDisplay(Display):
    def __init__(self, width: int, height: int, scale: int, sprite_dir: Path, title: str = "PytFall"):
        super().__init__(width, height)
        pygame.init()
        self._window = pygame.display.set_mode((width * scale, height * scale))
        pygame.display.set_caption(title)
        self._canvas = pygame.Surface((width, height))
        self._sprites: dict[str, pygame.Surface] = {}
        self._flipped: dict[str, pygame.Surface] = {}
        self._missing: set[str] = set()
        self._load_sprites(sprite_dir)

    def _load_sprites(self, sprite_dir: Path) -> None:
        for path in sorted(sprite_dir.rglob("*.png")):
            sprite_id = path.relative_to(sprite_dir).with_suffix("").as_posix()
            self._sprites[sprite_id] = pygame.image.load(str(path)).convert_alpha()
        if not self._sprites:
            raise RuntimeError(f"No sprites found under {sprite_dir}; run src/tools/make_sprites.py first")

    def begin_frame(self, clear_color=(0, 0, 0)) -> None:
        self._canvas.fill(clear_color)

    def draw_sprite(self, sprite_id: str, x: int, y: int, flip_x: bool = False) -> None:
        surf = self._sprites.get(sprite_id)
        if surf is None:
            if sprite_id not in self._missing:
                self._missing.add(sprite_id)
                print(f"warning: missing sprite '{sprite_id}'", file=sys.stderr)
            self._canvas.fill((255, 0, 255), (x, y, 8, 8))
            return
        if flip_x:
            flipped = self._flipped.get(sprite_id)
            if flipped is None:
                flipped = self._flipped[sprite_id] = pygame.transform.flip(surf, True, False)
            surf = flipped
        self._canvas.blit(surf, (x, y))

    def end_frame(self) -> None:
        pygame.transform.scale(self._canvas, self._window.get_size(), self._window)
        pygame.display.flip()

    def poll_events(self) -> list[InputEvent]:
        events = []
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                events.append(InputEvent(EventType.QUIT))
            elif ev.type in (pygame.KEYDOWN, pygame.KEYUP):
                key = KEYMAP.get(ev.key)
                if key is not None:
                    kind = EventType.KEY_DOWN if ev.type == pygame.KEYDOWN else EventType.KEY_UP
                    events.append(InputEvent(kind, key))
        return events

    def save_screenshot(self, path: str | Path) -> None:
        pygame.image.save(self._canvas, str(path))

    def close(self) -> None:
        pygame.quit()
