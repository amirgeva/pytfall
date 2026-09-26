"""Entry point and backend-independent main loop."""

from __future__ import annotations

import time

from .config import FPS, SCREEN_H, SCREEN_W, SPRITE_DIR, WINDOW_SCALE
from .game.game import Game
from .ui import Display, EventType, InputState

CLEAR_COLOR = (0, 0, 0)


def run(display: Display) -> None:
    """Drive the game on any Display using a fixed simulation timestep."""
    game = Game(display.width, display.height)
    inp = InputState()
    step = 1.0 / FPS
    accumulator = 0.0
    prev = time.perf_counter()

    while True:
        events = display.poll_events()
        if any(ev.type is EventType.QUIT for ev in events):
            break
        inp.apply(events)

        now = time.perf_counter()
        accumulator += min(now - prev, 0.25)
        prev = now
        while accumulator >= step:
            game.update(step, inp)
            inp.clear_pressed()
            accumulator -= step
        if game.quit_requested:
            break

        display.begin_frame(CLEAR_COLOR)
        game.render(display)
        display.end_frame()

        spare = step - (time.perf_counter() - now)
        if spare > 0:
            time.sleep(spare)


def main() -> None:
    from .ui.pygame_display import PygameDisplay

    display = PygameDisplay(SCREEN_W, SCREEN_H, WINDOW_SCALE, SPRITE_DIR)
    try:
        run(display)
    finally:
        display.close()


if __name__ == "__main__":
    main()
