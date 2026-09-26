"""Generate all game sprites as PNGs under rsc/sprites/<category>/<name>.png.

Character sprites are hand-drawn ASCII pixel art; tiles and backgrounds are
procedural. Output is deterministic, so it is safe to re-run at any time:

    .venv/Scripts/python src/tools/make_sprites.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pytfall.config import SCREEN_W, SPRITE_DIR  # noqa: E402
from pytfall.game.text import glyph_name  # noqa: E402

Color = tuple[int, int, int]

# ---------------------------------------------------------------- helpers

def save(surf: pygame.Surface, sprite_id: str) -> None:
    path = SPRITE_DIR / f"{sprite_id}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surf, str(path))


def from_ascii(rows: list[str], palette: dict[str, Color]) -> pygame.Surface:
    width = len(rows[0])
    assert all(len(r) == width for r in rows), rows
    surf = pygame.Surface((width, len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                surf.set_at((x, y), palette[ch])
    return surf


def mirror(rows: list[str]) -> list[str]:
    return [r[::-1] for r in rows]


def overlay(rows: list[str], points: list[tuple[int, int]], ch: str) -> list[str]:
    out = [list(r) for r in rows]
    for x, y in points:
        out[y][x] = ch
    return ["".join(r) for r in out]


def shade(c: Color, f: float) -> Color:
    return tuple(max(0, min(255, int(v * f))) for v in c)


# ---------------------------------------------------------------- player

PLAYER_PAL = {
    "h": (110, 60, 20),    # hair / hat
    "s": (236, 180, 130),  # skin
    "k": (20, 20, 20),     # eyes, belt, boots
    "g": (60, 170, 70),    # shirt
    "p": (70, 80, 170),    # trousers
}

HEAD_SIDE = [
    "....hhhh....",
    "...hhhhhhh..",
    "...hhsssss..",
    "...hssskss..",
    "....sssss...",
    ".....sss....",
]
HEAD_BACK = [
    "....hhhh....",
    "...hhhhhh...",
    "...hhhhhh...",
    "...hhhhhh...",
    "....ssss....",
    ".....ss.....",
]
TORSO_DOWN = [
    "...gggggg...",
    "..gggggggg..",
    "..sggggggs..",
    "..sggggggs..",
    "..sggggggs..",
    "...kkkkkk...",
]
TORSO_SWING = [
    "...gggggg...",
    "..gggggggg..",
    ".sggggggggs.",
    "s..gggggg..s",
    "...gggggg...",
    "...kkkkkk...",
]
TORSO_UP = [
    ".ssggggggss.",
    "..gggggggg..",
    "...gggggg...",
    "...gggggg...",
    "...gggggg...",
    "...kkkkkk...",
]
ARMS_UP = [(x, y) for y in range(6) for x in (1, 10)]

LEGS_STAND = [
    "...pppppp...",
    "...pp..pp...",
    "...pp..pp...",
    "...pp..pp...",
    "...pp..pp...",
    "...pp..pp...",
    "...pp..pp...",
    "...kkk.kkk..",
]
LEGS_STRIDE = [
    "...pppppp...",
    "..ppp..ppp..",
    "..pp....pp..",
    ".pp......pp.",
    ".pp......pp.",
    "pp........pp",
    "pp........pp",
    "kk.......kkk",
]
LEGS_PASS = [
    "...pppppp...",
    "....pppp....",
    "....pppp....",
    "....pp.pp...",
    "....pp..pp..",
    "....pp..kk..",
    "....pp......",
    "....kkk.....",
]
LEGS_JUMP = [
    "...pppppp...",
    "..pppppppp..",
    ".ppp....ppp.",
    ".pp......pp.",
    ".kk.....kk..",
    "............",
    "............",
    "............",
]
LEGS_CLIMB = [
    "...pppppp...",
    "...pp..pp...",
    "...pp..pp...",
    "...pp..kk...",
    "...pp.......",
    "...pp.......",
    "...kk.......",
    "............",
]


def player_frame(head, torso, legs, arms_up=False) -> pygame.Surface:
    rows = head + torso + legs
    if arms_up:
        rows = overlay(rows, ARMS_UP, "s")
    return from_ascii(rows, PLAYER_PAL)


def make_player() -> None:
    idle = player_frame(HEAD_SIDE, TORSO_DOWN, LEGS_STAND)
    save(idle, "player/idle")
    runs = [
        (TORSO_SWING, LEGS_STRIDE),
        (TORSO_DOWN, LEGS_PASS),
        (TORSO_SWING, LEGS_STRIDE),
        (TORSO_DOWN, mirror(LEGS_PASS)),
    ]
    for i, (torso, legs) in enumerate(runs):
        save(player_frame(HEAD_SIDE, torso, legs), f"player/run_{i}")
    save(player_frame(HEAD_SIDE, TORSO_UP, LEGS_JUMP, arms_up=True), "player/jump")
    save(player_frame(HEAD_SIDE, TORSO_UP, LEGS_STAND, arms_up=True), "player/swing")
    save(player_frame(HEAD_BACK, TORSO_UP, LEGS_CLIMB, arms_up=True), "player/climb_0")
    save(player_frame(HEAD_BACK, TORSO_UP, mirror(LEGS_CLIMB), arms_up=True), "player/climb_1")
    save(pygame.transform.rotate(idle, 90), "player/dead")

    life = from_ascii(
        [
            "..hhhh..",
            ".hhhhhh.",
            ".hsssss.",
            ".sssksss",
            "..ssss..",
            "..gggg..",
            ".gggggg.",
            ".gggggg.",
        ],
        PLAYER_PAL,
    )
    save(life, "hud/life")


# ---------------------------------------------------------------- monsters

def make_monsters() -> None:
    scorpion_pal = {"y": (235, 225, 190), "o": (170, 150, 110), "k": (20, 20, 20)}
    body = [
        "..yyy...........",
        ".y...y..........",
        ".y....y.........",
        "..y....y........",
        ".......yyyyyy.o.",
        "......yyyyyyyyo.",
        "......yyyyyyykyo",
        ".......yyyyyyyy.",
    ]
    legs_a = ["......y.y.y.y.y.", ".....y.y.y.y.y.."]
    legs_b = [".......y.y.y.y.y", "......y.y.y.y.y."]
    tail_b = ["...yyy..........", "..y..y.........."]
    save(from_ascii(body + legs_a, scorpion_pal), "monsters/scorpion_0")
    save(from_ascii(tail_b + body[2:] + legs_b, scorpion_pal), "monsters/scorpion_1")

    snake_pal = {"n": (70, 190, 60), "N": (30, 110, 30), "k": (10, 10, 10), "r": (220, 40, 40)}
    coil = [
        "....nnnnnnnn....",
        "..nnNNNNNNNNnn..",
        ".nnNnnnnnnnnNnn.",
        ".nNNNNNNNNNNNNn.",
        "..nnnnnnnnnnnn..",
        "................",
    ]
    head_a = [
        "..........nnn...",
        ".........nnnnn..",
        ".........nnknnr.",
        "..........nnn.r.",
        "...........nn...",
        "..........nn....",
    ]
    head_b = [
        "................",
        "..........nnn...",
        ".........nnnnn..",
        ".........nnknn..",
        "..........nnn...",
        "..........nn....",
    ]
    save(from_ascii(head_a + coil, snake_pal), "monsters/snake_0")
    save(from_ascii(head_b + coil, snake_pal), "monsters/snake_1")

    bat_pal = {"v": (130, 60, 170), "r": (255, 60, 60)}
    bat_up = [
        "vv............vv",
        ".vvv........vvv.",
        "..vvvv.vv.vvvv..",
        "...vvvvvvvvvv...",
        ".....vrvvrv.....",
        "......vvvv......",
        ".......vv.......",
        "................",
        "................",
        "................",
    ]
    bat_down = [
        "................",
        "................",
        ".......vv.......",
        "...vvvvvvvvvv...",
        ".vvvvvrvvrvvvvv.",
        "vvv...vvvv...vvv",
        "vv.....vv.....vv",
        "v..............v",
        "................",
        "................",
    ]
    save(from_ascii(bat_up, bat_pal), "monsters/bat_0")
    save(from_ascii(bat_down, bat_pal), "monsters/bat_1")


# ---------------------------------------------------------------- tiles

def speckle(surf: pygame.Surface, rng: random.Random, rect, colors: list[Color], density: float) -> None:
    x0, y0, w, h = rect
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if rng.random() < density:
                surf.set_at((x, y), rng.choice(colors))


def make_platforms() -> None:
    rng = random.Random(7)
    dirt = (112, 74, 38)
    dirt_spots = [(84, 54, 26), (140, 96, 52)]

    s = pygame.Surface((8, 8))
    s.fill(dirt)
    speckle(s, rng, (0, 0, 8, 8), dirt_spots, 0.3)
    save(s, "platforms/dirt")

    s = pygame.Surface((8, 8))
    s.fill(dirt)
    speckle(s, rng, (0, 0, 8, 8), dirt_spots, 0.3)
    for x in range(8):
        depth = rng.choice((3, 4, 4, 5))
        for y in range(depth):
            s.set_at((x, y), (50, 160, 50) if y else (110, 210, 80))
        if rng.random() < 0.4:
            s.set_at((x, depth - 1), (30, 110, 35))
    save(s, "platforms/grass")

    s = pygame.Surface((8, 8))
    s.fill((140, 64, 44))
    speckle(s, rng, (0, 0, 8, 8), [(120, 52, 36), (160, 80, 56)], 0.25)
    mortar = (70, 44, 36)
    for x in range(8):
        s.set_at((x, 3), mortar)
        s.set_at((x, 7), mortar)
    for y in range(0, 3):
        s.set_at((0, y), mortar)
    for y in range(4, 7):
        s.set_at((4, y), mortar)
    save(s, "platforms/brick")

    s = pygame.Surface((8, 8))
    s.fill((150, 96, 44))
    bark = (90, 55, 25)
    for x in range(8):
        s.set_at((x, 0), (180, 125, 65))
        s.set_at((x, 6), bark)
        s.set_at((x, 7), bark)
    for x in range(0, 8, 3):
        s.set_at((x, 3), (120, 76, 34))
    save(s, "platforms/log")


def make_props() -> None:
    wood, dark, light = (170, 115, 55), (100, 62, 28), (205, 150, 80)
    s = pygame.Surface((16, 8), pygame.SRCALPHA)
    for rail in (1, 12):
        s.fill(light, (rail, 0, 1, 8))
        s.fill(wood, (rail + 1, 0, 1, 8))
        s.fill(dark, (rail + 2, 0, 1, 8))
    for x in range(3, 13):
        s.set_at((x, 3), light)
        s.set_at((x, 4), dark)
    save(s, "props/ladder")

    s = pygame.Surface((2, 2))
    s.fill((200, 170, 110))
    s.set_at((1, 1), (150, 120, 70))
    save(s, "props/rope")

    s = pygame.Surface((10, 4), pygame.SRCALPHA)
    s.fill((90, 60, 30))
    pygame.draw.line(s, (60, 40, 20), (0, 3), (9, 3))
    save(s, "props/anchor")

    for frame in range(2):
        s = pygame.Surface((8, 14))
        for y in range(14):
            s.fill(shade((40, 110, 200), 1.0 - y * 0.04), (0, y, 8, 1))
        for x in range(8):
            if (x + frame * 2) % 4 == 0:
                s.set_at((x, 0), (170, 215, 250))
                s.set_at(((x + 1) % 8, 1), (120, 180, 240))
        save(s, f"props/water_{frame}")

    gold = from_ascii(
        [
            "..yyyyyyyy..",
            ".yYYYYYYYYo.",
            "yYYYYYYYYYYo",
            "yYYwYYYYYYYo",
            "yYYYYYYYYYYo",
            "yYYYYYYYYYYo",
            ".yooooooooo.",
            "............",
        ],
        {"y": (255, 230, 120), "Y": (240, 190, 40), "o": (170, 120, 20), "w": (255, 255, 230)},
    )
    save(gold, "items/gold")


def make_backgrounds() -> None:
    rng = random.Random(1982)
    h = 104
    s = pygame.Surface((SCREEN_W, h))
    top, bottom = (14, 40, 22), (36, 96, 44)
    for y in range(h):
        f = y / (h - 1)
        s.fill(tuple(int(a + (b - a) * f) for a, b in zip(top, bottom)), (0, y, SCREEN_W, 1))
    # far trunks
    for _ in range(14):
        x = rng.randrange(SCREEN_W)
        pygame.draw.rect(s, (40, 50, 30), (x, 10, rng.randint(3, 5), h))
    # near trunks
    for i in range(7):
        x = i * 48 + rng.randint(0, 24)
        w = rng.randint(7, 11)
        pygame.draw.rect(s, (96, 64, 32), (x, 0, w, h))
        pygame.draw.rect(s, (70, 44, 22), (x + w - 2, 0, 2, h))
        pygame.draw.rect(s, (120, 84, 44), (x + 1, 0, 1, h))
    # canopy
    for _ in range(90):
        c = rng.choice([(24, 84, 30), (34, 110, 40), (46, 132, 48), (20, 66, 26)])
        pygame.draw.circle(s, c, (rng.randrange(-10, SCREEN_W + 10), rng.randint(-6, 22)), rng.randint(6, 14))
    # hanging vines
    for _ in range(10):
        x = rng.randrange(SCREEN_W)
        pygame.draw.line(s, (40, 120, 40), (x, 10), (x + rng.randint(-3, 3), rng.randint(30, 60)))
    # undergrowth along the ground line
    for _ in range(40):
        c = rng.choice([(28, 90, 32), (40, 120, 44)])
        pygame.draw.circle(s, c, (rng.randrange(SCREEN_W), h + 2), rng.randint(4, 9))
    save(s, "background/jungle")

    s = pygame.Surface((SCREEN_W, 64))
    s.fill((30, 22, 18))
    speckle(s, rng, (0, 0, SCREEN_W, 64), [(42, 32, 26), (22, 16, 13), (50, 38, 30)], 0.12)
    for y in range(4):
        s.fill(shade((30, 22, 18), 0.5 + y * 0.12), (0, 16 + y, SCREEN_W, 1))
    save(s, "background/underground")


# ---------------------------------------------------------------- font

FONT = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11100", "10010", "10001", "10001", "10001", "10010", "11100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "10001", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "10001", "01010", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
}


def make_font() -> None:
    for ch, rows in FONT.items():
        s = pygame.Surface((6, 8), pygame.SRCALPHA)
        for y, row in enumerate(rows):
            for x, bit in enumerate(row):
                if bit == "1":
                    s.set_at((x + 1, y + 1), (0, 0, 0))
        for y, row in enumerate(rows):
            for x, bit in enumerate(row):
                if bit == "1":
                    s.set_at((x, y), (255, 255, 255))
        save(s, f"font/{glyph_name(ch)}")


def main() -> None:
    pygame.init()
    make_player()
    make_monsters()
    make_platforms()
    make_props()
    make_backgrounds()
    make_font()
    count = len(list(SPRITE_DIR.rglob("*.png")))
    print(f"wrote {count} sprites to {SPRITE_DIR}")


if __name__ == "__main__":
    main()
