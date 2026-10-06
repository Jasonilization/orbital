"""Layout engine tests — placement, structure, and switching."""
import pytest

from orbital.data import load_elements
from orbital.layouts import (
    LAYOUTS, DEFAULT_LAYOUT, build_layout, validate_layout,
)


@pytest.fixture(scope="module")
def elements():
    return load_elements()


@pytest.mark.parametrize("layout_id", list(LAYOUTS))
def test_layout_places_all_elements(elements, layout_id):
    layout = validate_layout(build_layout(layout_id, elements), elements)
    assert len(layout.cells) == 118


@pytest.mark.parametrize("layout_id", list(LAYOUTS))
def test_positions_in_bounds(elements, layout_id):
    layout = build_layout(layout_id, elements)
    for cell in layout.cells:
        assert 0 <= cell.row < layout.rows
        assert 0 <= cell.col < layout.columns


def test_standard_positions(elements):
    layout = build_layout("standard", elements)
    pos = {c.number: (c.row, c.col) for c in layout.cells}
    assert pos[1] == (0, 0)       # H
    assert pos[2] == (0, 17)      # He
    assert pos[4] == (1, 1)       # Be
    assert pos[21] == (3, 2)      # Sc
    assert pos[30] == (3, 11)     # Zn
    assert pos[57] == (7, 2)      # La
    assert pos[71] == (7, 16)     # Lu
    assert pos[89] == (8, 2)      # Ac
    assert pos[103] == (8, 16)    # Lr
    assert pos[118] == (6, 17)    # Og
    assert layout.rows == 9 and layout.columns == 18
    assert layout.spacer_after_row == 6
    # markers sit where the f-block would be
    assert any(m.row == 5 and m.col == 2 for m in layout.markers)
    assert any(m.row == 6 and m.col == 2 for m in layout.markers)


def test_compact_has_no_spacer(elements):
    standard = build_layout("standard", elements)
    compact = build_layout("compact", elements)
    assert compact.spacer_after_row is None
    assert standard.spacer_after_row == 6
    assert compact.cells == standard.cells


def test_extended_positions(elements):
    layout = build_layout("extended", elements)
    pos = {c.number: (c.row, c.col) for c in layout.cells}
    assert pos[2] == (0, 31)      # He at the far right
    assert pos[40] == (4, 17)     # Zr in the true group-4 column (18th)
    assert pos[72] == (5, 17)     # Hf directly beneath Zr
    assert pos[57] == (5, 2)      # La under Sc (3,2) and Y (4,2)
    assert pos[58] == (5, 3)      # Ce
    assert pos[71] == (5, 16)     # Lu
    assert pos[89] == (6, 2)
    assert pos[118] == (6, 31)
    assert layout.rows == 7 and layout.columns == 32


def test_school_numbering(elements):
    layout = build_layout("school", elements)
    assert layout.column_labels[0] == "1"
    assert layout.column_labels[1] == "2"
    assert layout.column_labels[12] == "3"   # old group 3 = modern 13
    assert layout.column_labels[17] == "0"   # noble gases = group 0
    # transition columns are unnumbered
    for col in range(2, 12):
        assert col not in layout.column_labels


def test_default_layout_exists():
    assert DEFAULT_LAYOUT in LAYOUTS


def test_unknown_layout_rejected(elements):
    with pytest.raises(ValueError):
        build_layout("spiral", elements)


def test_layout_switching_preserves_all_elements(elements):
    layouts = [build_layout(lid, elements) for lid in LAYOUTS]
    base = {c.number for c in layouts[0].cells}
    for layout in layouts[1:]:
        assert {c.number for c in layout.cells} == base
