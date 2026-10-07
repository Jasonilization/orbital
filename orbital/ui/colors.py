"""Colour modes for the periodic table.

Each mode maps an element to a tile colour and describes its own legend.
Categorical modes use hand-tuned muted palettes; numeric modes use a
restrained sequential ramp from neutral to accent. Unknown values fall
back to a flat neutral so missing data never pretends to be a value.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Optional

from PySide6.QtGui import QColor


# Muted, print-like category palette. Deliberately low-saturation so
# text stays readable and the table reads as one object, not confetti.
CATEGORY_COLORS = {
    "alkali metal": "#dfa48f",
    "alkaline earth metal": "#e8c48c",
    "transition metal": "#a9c2dd",
    "post-transition metal": "#8fc6ba",
    "metalloid": "#b3cfa0",
    "nonmetal": "#e0d79a",
    "halogen": "#9fd3d6",
    "noble gas": "#bcb1dc",
    "lanthanide": "#dcaeac",
    "actinide": "#d8a9b0",
}

BLOCK_COLORS = {
    "s": "#dfa48f",
    "p": "#b3cfa0",
    "d": "#a9c2dd",
    "f": "#e0d79a",
}

STATE_COLORS = {
    "solid": "#aeb6c2",
    "liquid": "#9fd3d6",
    "gas": "#c4b78f",
    "unknown": "#c9c7c2",
}

# Sequential ramp endpoints: neutral -> deep accent (set at runtime so the
# ramp can follow the user's accent colour).
RAMP_LOW = "#e9e7e2"
RAMP_HIGH_DARK = "#31556f"


def _ramp_color(t: float, dark: bool = False) -> QColor:
    """t in [0,1] -> muted sequential colour."""
    low = QColor(RAMP_LOW)
    high = QColor(RAMP_HIGH_DARK if dark else "#3f6a8a")
    t = max(0.0, min(1.0, t))
    r = low.red() + (high.red() - low.red()) * t
    g = low.green() + (high.green() - low.green()) * t
    b = low.blue() + (high.blue() - low.blue()) * t
    return QColor(int(r), int(g), int(b))


@dataclass(frozen=True)
class LegendEntry:
    label: str
    color: str  # hex, or "" for a gradient slot
    # for gradient legends: value range shown
    low: Optional[float] = None
    high: Optional[float] = None
    low_label: str = ""
    high_label: str = ""
    gradient: bool = False
    null_label: str = ""


@dataclass(frozen=True)
class ColorMode:
    id: str
    name: str
    # returns hex colour for the element
    fn: object = None
    legend: tuple = ()
    sequential: bool = False


def _category_mode():
    def fn(e):
        return CATEGORY_COLORS.get(e.category, "#c9c7c2")

    legend = tuple(
        LegendEntry(label=cat.title(), color=col)
        for cat, col in CATEGORY_COLORS.items()
    )
    return ColorMode("category", "Element category", fn, legend)


def _block_mode():
    legend = tuple(
        LegendEntry(label=b + "-block", color=col)
        for b, col in BLOCK_COLORS.items()
    )
    return ColorMode("block", "Block", lambda e: BLOCK_COLORS.get(e.block, "#c9c7c2"), legend)


def _state_mode():
    legend = tuple(
        LegendEntry(label={"solid": "Solid", "liquid": "Liquid",
                           "gas": "Gas", "unknown": "Unknown"}[s], color=col)
        for s, col in STATE_COLORS.items()
    )
    return ColorMode("state", "State at room temp.", lambda e: STATE_COLORS.get(e.state, "#c9c7c2"), legend)


def _group_mode():
    def fn(e):
        if e.group is None:
            return "#c9c7c2"
        hue = (e.group - 1) / 17.0
        c = QColor()
        c.setHsv(int(8 + hue * 300), 70, 200)
        return c.name()

    legend = (LegendEntry(label="Group 1 \u2192 18 (hue wheel)", color="", gradient=True,
                          low=1, high=18, low_label="1", high_label="18"),
              LegendEntry(label="no group (f-block)", color="#c9c7c2"))
    return ColorMode("group", "Group", fn, legend)


def _period_mode():
    def fn(e):
        t = (e.period - 1) / 6.0
        return QColor(_ramp_color(t)).name()

    legend = (LegendEntry(label="Period", color="", gradient=True,
                           low=1, high=7, low_label="1", high_label="7"),)
    return ColorMode("period", "Period", fn, legend)


def _numeric_mode(mid, name, fid):
    def build(elements):
        values = [v for v in (mid(e) for e in elements) if v is not None]
        lo, hi = (min(values), max(values)) if values else (0.0, 1.0)
        span = (hi - lo) or 1.0

        def fn(e, lo=lo, span=span):
            v = mid(e)
            if v is None:
                return None
            t = (v - lo) / span
            # widen the ramp so extremes aren't pure white/pure black
            return QColor(_ramp_color(0.06 + 0.88 * t)).name()

        legend = (
            LegendEntry(label=name, color="", gradient=True,
                        low=lo, high=hi, low_label=_fmt(lo), high_label=_fmt(hi),
                        null_label="unknown"),
        )
        return ColorMode(fid, name, fn, legend, sequential=True)

    return build


def _fmt(v):
    if v is None:
        return "?"
    if v == int(v):
        return str(int(v))
    return "%.3g" % v


_MASS = lambda e: e.atomic_mass
_MELT = lambda e: e.melt_k
_BOIL = lambda e: e.boil_k
_EN = lambda e: e.electronegativity
_DENSITY = lambda e: e.density_g_cm3
_IE = lambda e: e.ionization_energy_kj


def _discovery_year(e):
    y = e.discovery.year
    return None if y == "ancient" else y


def _discovery_mode():
    def fn(e):
        y = e.discovery.year
        if y == "ancient":
            return "#c9c9c2"
        if y < 1700:
            return "#bfae94"
        if y < 1800:
            return "#d3bd8e"
        if y < 1900:
            return "#c7cbb0"
        if y < 2000:
            return "#9fbccb"
        return "#8aa8c8"

    legend = (
        LegendEntry(label="Antiquity", color="#c9c9c2"),
        LegendEntry(label="1200s\u20131700s", color="#bfae94"),
        LegendEntry(label="1700s\u20131800s", color="#d3bd8e"),
        LegendEntry(label="1800s\u20131900s", color="#c7cbb0"),
        LegendEntry(label="1900s\u20132000s", color="#9fbccb"),
        LegendEntry(label="2000s\u2013", color="#8aa8c8"),
    )
    return ColorMode("discovery", "Discovered (by era)", fn, legend)


def _synthetic_mode():
    return ColorMode(
        "synthetic", "Natural vs synthetic",
        lambda e: "#b3c2ce" if e.synthetic else "#dcc9a8",
        (LegendEntry(label="Natural", color="#dcc9a8"),
         LegendEntry(label="Synthetic", color="#b3c2ce")),
    )


def _radioactive_mode():
    return ColorMode(
        "radioactive", "Radioactive",
        lambda e: "#d9a794" if e.radioactive else "#c3ccc5",
        (LegendEntry(label="Radioactive", color="#d9a794"),
         LegendEntry(label="Not classified radioactive", color="#c3ccc5")),
    )


def _monochrome_mode():
    return ColorMode(
        "monochrome", "Monochrome",
        lambda e: "#c9c7c2",
        (LegendEntry(label="All elements \u2014 structure only", color="#c9c7c2"),),
    )


def build_color_modes(elements) -> dict:
    """Colour mode id -> ColorMode. Numeric modes are bound to the data."""
    modes = {
        "category": _category_mode(),
        "block": _block_mode(),
        "state": _state_mode(),
        "group": _group_mode(),
        "period": _period_mode(),
        "mass": _numeric_mode(_MASS, "Atomic mass", "mass")(elements),
        "melt": _numeric_mode(_MELT, "Melting point", "melt")(elements),
        "boil": _numeric_mode(_BOIL, "Boiling point", "boil")(elements),
        "electronegativity": _numeric_mode(_EN, "Electronegativity", "electronegativity")(elements),
        "density": _numeric_mode(_DENSITY, "Density", "density")(elements),
        "ionization": _numeric_mode(_IE, "1st ionisation energy", "ionization")(elements),
        "discovery": _discovery_mode(),
        "synthetic": _synthetic_mode(),
        "radioactive": _radioactive_mode(),
        "monochrome": _monochrome_mode(),
    }
    return modes


DEFAULT_MODE = "category"
