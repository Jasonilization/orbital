"""Tile layout geometry tests — the guarantee that text never overlaps.

layout_fields is pure: it must stack rows within the tile and never emit
a stack that exceeds the available height, for every preset at every
supported scale.
"""
import pytest

from orbital.ui.tiles import layout_fields, BASE_SIZE, MIN_SCALE
from orbital.profiles import TILE_PRESETS


SCALES = [MIN_SCALE, 0.9, 1.0, 1.25, 1.5]


@pytest.mark.parametrize("preset", list(TILE_PRESETS))
@pytest.mark.parametrize("scale", SCALES)
def test_stack_never_exceeds_tile(preset, scale):
    w = int(BASE_SIZE.width() * scale)
    h = int(BASE_SIZE.height() * scale)
    rows = layout_fields(w, h, TILE_PRESETS[preset]["fields"])
    assert rows, "no rows laid out"
    for field, x, y, pt, avail in rows:
        assert 0 <= x < w
        assert y >= 0
        assert y + pt * 1.45 <= h + 1.5, (
            "row %r overflows tile at %s/%s" % (field, preset, scale))
        assert pt >= 6.5


@pytest.mark.parametrize("preset", list(TILE_PRESETS))
@pytest.mark.parametrize("scale", SCALES)
def test_no_row_overlap(preset, scale):
    w = int(BASE_SIZE.width() * scale)
    h = int(BASE_SIZE.height() * scale)
    rows = [r for r in layout_fields(w, h, TILE_PRESETS[preset]["fields"])]
    stack = sorted([r for r in rows if r[0] != "name"], key=lambda r: r[2])
    name = next((r for r in rows if r[0] == "name"), None)
    # every stack row starts at or below the previous row's bottom edge
    for above, below in zip(stack, stack[1:]):
        assert below[2] >= above[2] + above[3] * 1.45 - 0.01, (
            "%s/%s: %r overlaps %r" % (preset, scale, above[0], below[0]))
    # the name row, when present, must clear the stack
    if name:
        bottom_of_stack = stack[-1][2] + stack[-1][3] * 1.45
        assert name[2] >= bottom_of_stack - 1.0, (
            "%s/%s: name overlaps the stack" % (preset, scale))


def test_symbol_and_number_always_fit_at_minimum(preset=None):
    for scale in [MIN_SCALE, 1.0]:
        w = int(BASE_SIZE.width() * scale)
        h = int(BASE_SIZE.height() * scale)
        rows = layout_fields(w, h, ["number", "symbol", "mass"])
        fields = [r[0] for r in rows]
        assert fields == ["number", "symbol", "mass"], (scale, fields)


def test_degenerate_config_drops_gracefully():
    # absurdly small tile: must still emit rows without overlapping
    rows = layout_fields(30, 22, ["number", "symbol", "mass", "name"])
    for above, below in zip(rows, rows[1:]):
        if above[0] == "name":
            continue
        assert below[2] >= above[2] + above[3] * 1.45 - 0.01


def test_larger_scale_gives_larger_symbol():
    small = layout_fields(70, 60, ["number", "symbol", "mass"])
    large = layout_fields(100, 86, ["number", "symbol", "mass"])
    small_sym = next(r for r in small if r[0] == "symbol")
    large_sym = next(r for r in large if r[0] == "symbol")
    assert large_sym[3] >= small_sym[3]
