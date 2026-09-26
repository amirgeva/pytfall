"""Global configuration: paths and logical screen geometry."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
RSC_DIR = ROOT_DIR / "rsc"
SPRITE_DIR = RSC_DIR / "sprites"

# Logical resolution. All game coordinates are in these units; the display
# backend is responsible for scaling to the physical window.
SCREEN_W = 320
SCREEN_H = 200
WINDOW_SCALE = 3
FPS = 60
