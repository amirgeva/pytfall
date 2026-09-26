"""Text rendering built on the draw_sprite primitive (one sprite per glyph)."""

from __future__ import annotations

from ..ui import Display

GLYPH_W = 6
GLYPH_H = 8

_SPECIAL_NAMES = {":": "colon", "-": "dash", "!": "bang", ".": "dot"}


def glyph_name(ch: str) -> str:
    return _SPECIAL_NAMES.get(ch, ch)


def text_width(text: str) -> int:
    return len(text) * GLYPH_W


def draw_text(display: Display, text: str, x: int, y: int) -> None:
    for ch in text.upper():
        if ch != " ":
            display.draw_sprite(f"font/{glyph_name(ch)}", x, y)
        x += GLYPH_W


def draw_text_centered(display: Display, text: str, y: int) -> None:
    draw_text(display, text, (display.width - text_width(text)) // 2, y)
