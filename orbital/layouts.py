"""Periodic table layouts.

A layout maps each element to a (row, col) grid cell. Layouts are pure
functions of atomic structure (group / period / block) — element data files
know nothing about them, so a new layout can be added by writing one build
function and registering it in LAYOUTS.

Coordinates are 0-based; the UI renders headers from ``column_labels`` and
``row_labels`` and may insert a visual spacer after ``spacer_after_row``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Cell:
    number: int
    row: int
    col: int


@dataclass(frozen=True)
class Marker:
    row: int
    col: int
    text: str
    jump_to: int  # atomic number to select when clicked


@dataclass(frozen=True)
class Layout:
    id: str
    name: str
    description: str
    rows: int
    columns: int
    cells: tuple
    markers: tuple = ()
    spacer_after_row: Optional[int] = None
    column_labels: Optional[dict] = None
    row_labels: tuple = ()


# --------------------------------------------------------------------------
# Standard long form: 18 columns, f-block detached below with a spacer.
# --------------------------------------------------------------------------

def _standard_cells(elements):
    cells = []
    for e in elements:
        if e.group is not None:
            cells.append(Cell(e.number, e.period - 1, e.group - 1))
        elif 57 <= e.number <= 71:
            cells.append(Cell(e.number, 7, e.number - 55))  # La at col 2 .. Lu at 16
        else:
            cells.append(Cell(e.number, 8, e.number - 87))  # Ac at col 2 .. Lr at 16
    return tuple(cells)


def build_standard(elements):
    return Layout(
        id="standard",
        name="Standard",
        description="The familiar 18-column long form. Lanthanides and actinides "
                    "sit in detached rows below the main table.",
        rows=9,
        columns=18,
        cells=_standard_cells(elements),
        markers=(
            Marker(5, 2, "57\u201371", 57),
            Marker(6, 2, "89\u2013103", 89),
        ),
        spacer_after_row=6,
        column_labels={c: str(c + 1) for c in range(18)},
        row_labels=("1", "2", "3", "4", "5", "6", "7", "57\u201371", "89\u2013103"),
    )


# --------------------------------------------------------------------------
# Compact: same chemistry, wasted space removed — no spacer row between the
# main table and the f-block, tighter footprint for small windows.
# --------------------------------------------------------------------------

def build_compact(elements):
    layout = build_standard(elements)
    return Layout(
        id="compact",
        name="Compact",
        description="The standard arrangement with the vertical dead space "
                    "removed — the f-block sits directly under the main table. "
                    "Best for small windows.",
        rows=9,
        columns=18,
        cells=layout.cells,
        markers=layout.markers,
        spacer_after_row=None,
        column_labels=layout.column_labels,
        row_labels=layout.row_labels,
    )


# --------------------------------------------------------------------------
# Extended 32-column form: the f-block inline in the main table.
# --------------------------------------------------------------------------

def build_extended(elements):
    cells = []
    for e in elements:
        row = e.period - 1
        if e.group is not None:
            if e.group <= 3:
                col = e.group - 1
            else:
                col = e.group + 13  # group 4 -> column 17 ... group 18 -> 31
        elif 57 <= e.number <= 71:
            if e.number == 57:  # La sits in the group-3 column (Sc, Y above it)
                col = 2
            else:
                col = e.number - 55  # Ce at col 3 ... Lu at 16
        else:
            if e.number == 89:  # Ac mirrors La
                col = 2
            else:
                col = e.number - 87  # Th at col 3 ... Lr at 16
        cells.append(Cell(e.number, row, col))
    labels = {0: "1", 1: "2", 2: "3"}
    for g in range(4, 19):
        labels[g + 13] = str(g)
    return Layout(
        id="extended",
        name="Extended",
        description="The full 32-column wide form with the lanthanides and "
                    "actinides inline — every element in its true group column.",
        rows=7,
        columns=32,
        cells=tuple(cells),
        column_labels=labels,
        row_labels=("1", "2", "3", "4", "5", "6", "7"),
    )


# --------------------------------------------------------------------------
# School form: standard positions, classic school numbering (groups 1-7 and 0,
# transition metals unnumbered). Positionally identical to standard.
# --------------------------------------------------------------------------

def build_school(elements):
    layout = build_standard(elements)
    labels = {c: str(c + 1) for c in range(2)}
    labels.update({c: str(c - 9) for c in range(12, 18)})  # 13-18 -> 3,4,5,6,7,0
    labels[17] = "0"
    return Layout(
        id="school",
        name="School",
        description="The classroom form: main groups numbered 1-7 and 0, "
                    "transition metals left unnumbered, f-block detached below.",
        rows=9,
        columns=18,
        cells=layout.cells,
        markers=layout.markers,
        spacer_after_row=6,
        column_labels=labels,
        row_labels=layout.row_labels,
    )


LAYOUTS = {
    "standard": build_standard,
    "compact": build_compact,
    "extended": build_extended,
    "school": build_school,
}

DEFAULT_LAYOUT = "standard"


def build_layout(layout_id, elements):
    if layout_id not in LAYOUTS:
        raise ValueError("unknown layout: %r" % layout_id)
    return LAYOUTS[layout_id](elements)


def validate_layout(layout, elements):
    """Every element placed exactly once, within bounds, no collisions."""
    numbers = sorted(c.number for c in layout.cells)
    if numbers != list(range(1, 119)):
        raise ValueError("layout %s: not all 118 elements placed" % layout.id)
    seen = set()
    for c in layout.cells:
        if not (0 <= c.row < layout.rows and 0 <= c.col < layout.columns):
            raise ValueError("layout %s: cell out of bounds %r" % (layout.id, c))
        key = (c.row, c.col)
        if key in seen:
            raise ValueError("layout %s: collision at %r" % (layout.id, key))
        seen.add(key)
    for m in layout.markers:
        key = (m.row, m.col)
        if key in seen:
            raise ValueError("layout %s: marker collides with cell at %r" % (layout.id, key))
    return layout
