"""Backend-neutral UI abstraction.

The game only ever talks to a ``Display``: it draws sprites by id and reads
abstract key events. A backend can be a local pygame window, or later a
socket server that forwards the draw commands to a remote client and receives
its key events back. Every call and event here is plain data (strings, ints,
enums) so it serializes trivially.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class Key(Enum):
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    JUMP = "jump"
    START = "start"
    QUIT = "quit"


class EventType(Enum):
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    QUIT = "quit"


@dataclass(frozen=True)
class InputEvent:
    type: EventType
    key: Key | None = None


class Display(ABC):
    """Drawing surface of fixed logical size.

    A frame is ``begin_frame`` -> any number of ``draw_sprite`` -> ``end_frame``.
    Sprite ids are paths relative to ``rsc/sprites`` without extension, e.g.
    ``"player/run_0"``. Coordinates are the sprite's top-left corner in
    logical pixels.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    @abstractmethod
    def begin_frame(self, clear_color: tuple[int, int, int] = (0, 0, 0)) -> None: ...

    @abstractmethod
    def draw_sprite(self, sprite_id: str, x: int, y: int, flip_x: bool = False) -> None: ...

    @abstractmethod
    def end_frame(self) -> None: ...

    @abstractmethod
    def poll_events(self) -> list[InputEvent]: ...

    def close(self) -> None:
        pass


class InputState:
    """Tracks held keys and keys newly pressed since the last game update."""

    def __init__(self) -> None:
        self._held: set[Key] = set()
        self._pressed: set[Key] = set()

    def apply(self, events: list[InputEvent]) -> None:
        for ev in events:
            if ev.type is EventType.KEY_DOWN and ev.key is not None:
                if ev.key not in self._held:
                    self._pressed.add(ev.key)
                self._held.add(ev.key)
            elif ev.type is EventType.KEY_UP and ev.key is not None:
                self._held.discard(ev.key)

    def clear_pressed(self) -> None:
        self._pressed.clear()

    def held(self, key: Key) -> bool:
        return key in self._held

    def pressed(self, key: Key) -> bool:
        return key in self._pressed
