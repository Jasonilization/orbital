"""Quick element comparison. Pure logic — the compare dialog renders rows
produced here."""
from __future__ import annotations

from orbital.profiles import COMPARE_FIELDS
from orbital.formatting import field_value, field_label

MAX_COMPARE = 4


def compare_rows(elements, *, mass_precision: int = 3):
    """Return (field_id, label, [values...]) rows for the selected elements."""
    if not 2 <= len(elements) <= MAX_COMPARE:
        raise ValueError("compare needs 2-%d elements, got %d"
                         % (MAX_COMPARE, len(elements)))
    rows = []
    for field_id in COMPARE_FIELDS:
        values = []
        for e in elements:
            v = field_value(e, field_id, mass_precision=mass_precision)
            if isinstance(v, tuple):
                v = "; ".join(v) if v else None
            values.append(v)
        rows.append((field_id, field_label(field_id), values))
    return rows


def comparable(elements, number: int) -> bool:
    """Can this element be added to the comparison (max 4, no duplicates)?"""
    return number not in {e.number for e in elements} and len(elements) < MAX_COMPARE
