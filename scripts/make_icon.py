#!/usr/bin/env python3
"""Generate the Orbital app icon set.

The mark is the periodic table's own silhouette: the familiar two-tile
first period flanked left and right, with the two full periods below —
one tile picked out in the accent colour. Muted, geometric, no text.

Outputs:
  assets/icons/icon_*.png   (all sizes, for Linux/desktop use)
  assets/icons/Orbital.icns  (macOS, via iconutil)
  assets/icons/Orbital.ico   (Windows)
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = os.path.join(REPO, "assets", "icons")
os.makedirs(ICONS, exist_ok=True)

BG = (26, 28, 33)         # dark slate
TILE = (58, 61, 68)       # neutral dark tile
TILE_MUTED = (122, 138, 158)  # muted steel
ACCENT = (74, 125, 181)   # the app accent — one tile only
GAP = 3


def tile_grid(size):
    """Rows of (x, y) tile origins forming the table silhouette, normalized
    to a size x size canvas."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # geometry: grid 8 cols x 4 rows filling ~80% of the canvas
    u = size / 10.0
    global GAP
    gap = max(1, round(u * 0.12))
    left = (size - (8 * u + 7 * gap)) / 2
    top = (size - (4 * u + 3 * gap)) / 2

    def tile(col, row, color):
        x = left + col * (u + gap)
        y = top + row * (u + gap)
        r = max(1, u * 0.12)
        d.rounded_rectangle(
            [x, y, x + u, y + u], radius=r, fill=color)

    accent_pos = (0, 2)   # period 3, first column — the 'selected' tile
    for row in range(4):
        if row == 0:
            tile(0, 0, TILE_MUTED)   # H
            tile(7, 0, TILE_MUTED)   # He
        else:
            for col in range(8):
                if (col, row) == accent_pos:
                    tile(col, row, ACCENT)
                else:
                    tile(col, row, TILE)
    return img


def make(size, mask=True):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=size * 0.225,
                        fill=(*BG, 255))
    grid = tile_grid(size)
    img.alpha_composite(grid)
    return img


sizes = [1024, 512, 256, 128, 64, 32, 16]
for s in sizes:
    img = make(s)
    img.save(os.path.join(ICONS, "icon_%d.png" % s))
    print("png", s)

# macOS icns via iconset + iconutil
iconset = os.path.join(ICONS, "Orbital.iconset")
os.makedirs(iconset, exist_ok=True)
mapping = [
    (16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"), (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png"),
]
for s, name in mapping:
    make(s).save(os.path.join(iconset, name))
subprocess.run(
    ["iconutil", "-c", "icns", iconset, "-o", os.path.join(ICONS, "Orbital.icns")],
    check=True,
)
print("icns done")

# Windows ico
make(256).save(
    os.path.join(ICONS, "Orbital.ico"),
    sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
)
print("ico done")
