"""Education-level profiles and tile presets.

The element database is always complete; a profile only controls
*presentation*: which sections of the detail panel exist, which fields
appear in them, which sections start collapsed, and which tile preset is
used by default. Users can override any of it in Settings.

Field ids are shared between the detail panel, the compare view and the
tile renderer, so a field needs to be declared exactly once (in FIELDS).
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# Field registry. id -> (section, label, priority for compare ordering)
# --------------------------------------------------------------------------

FIELDS = {
    # essentials
    "number":            ("essentials", "Atomic number"),
    "symbol":            ("essentials", "Symbol"),
    "atomic_mass":       ("essentials", "Atomic mass"),
    "group":             ("essentials", "Group"),
    "period":            ("essentials", "Period"),
    "block":             ("essentials", "Block"),
    "category":          ("essentials", "Category"),
    "state":             ("essentials", "State"),
    # chemistry
    "configuration":     ("chemistry", "Electron config."),
    "shells":            ("chemistry", "Shell arrangement"),
    "oxidation_states":  ("chemistry", "Oxidation states"),
    "electronegativity": ("chemistry", "Electronegativity"),
    "ionization":        ("chemistry", "Ionisation energy"),
    "radius":            ("chemistry", "Atomic radius"),
    "melt":              ("chemistry", "Melting point"),
    "boil":              ("chemistry", "Boiling point"),
    "density":           ("chemistry", "Density"),
    # practical
    "uses":              ("practical", "Uses"),
    "compounds":         ("practical", "Compounds"),
    # history
    "discovered":        ("history", "Discovery"),
    "origin":            ("history", "Name origin"),
    # advanced-only extras
    "abundance":         ("advanced", "Abundance"),
    "mass_note":          ("advanced", "Mass note"),
}

SECTION_TITLES = {
    "essentials": "Essentials",
    "chemistry": "Chemistry",
    "practical": "Uses",
    "advanced": "More detail",
    "history": "History",
}

# The order fields appear in when a section is rendered.
SECTION_FIELDS = {
    "essentials": ["number", "symbol", "atomic_mass", "group", "period", "block",
                   "category", "state"],
    "chemistry": ["configuration", "shells", "oxidation_states", "electronegativity",
                  "ionization", "radius", "melt", "boil", "density"],
    "practical": ["uses", "compounds"],
    "advanced": ["abundance", "mass_note"],
    "history": ["discovered", "origin"],
}

# Fields the compare view shows, in order.
COMPARE_FIELDS = [
    "number", "symbol", "atomic_mass", "group", "period", "block", "category",
    "state", "configuration", "shells", "oxidation_states", "electronegativity",
    "melt", "boil", "density", "ionization",
]

# --------------------------------------------------------------------------
# Education levels
# --------------------------------------------------------------------------

# Fields that don't appear in the General default view but can be toggled
# on per-user from the detail panel (and persist). Everything the database
# holds stays one click away — detail is never sacrificed.
TOGGLEABLE_FIELDS = ["configuration", "oxidation_states", "electronegativity",
                     "ionization", "radius"]

EDUCATION_LEVELS = {
    "general": {
        "label": "General",
        "description": "Useful everyday periodic-table information.",
        "sections": ["essentials", "chemistry", "practical", "history"],
        "fields": {
            "essentials": ["number", "symbol", "atomic_mass", "group", "period",
                           "category", "state"],
            "chemistry": ["shells", "melt", "boil", "density"],
            "practical": ["uses", "compounds"],
            "history": ["discovered", "origin"],
        },
        "collapsed": ["history"],
        "tile_preset": "standard",
    },
    "igcse": {
        "label": "IGCSE",
        "description": "Only what an IGCSE chemistry student needs by default.",
        "sections": ["essentials", "chemistry", "practical"],
        "fields": {
            "essentials": ["number", "symbol", "atomic_mass", "group", "period",
                           "state"],
            "chemistry": ["shells", "oxidation_states", "melt", "boil", "density"],
            "practical": ["uses", "compounds"],
        },
        "collapsed": [],
        "tile_preset": "school",
        "common_ox_states_only": True,
    },
    "alevel": {
        "label": "A Level",
        "description": "Adds the detail A Level chemistry actually uses.",
        "sections": ["essentials", "chemistry", "practical", "history"],
        "fields": {
            "essentials": ["number", "symbol", "atomic_mass", "group", "period",
                           "block", "category", "state"],
            "chemistry": ["configuration", "shells", "oxidation_states",
                          "electronegativity", "melt", "boil", "density", "radius"],
            "practical": ["uses", "compounds"],
            "history": ["discovered", "origin"],
        },
        "collapsed": ["history"],
        "tile_preset": "standard",
    },
    "advanced": {
        "label": "Advanced",
        "description": "Everything the database holds, nothing hidden.",
        "sections": ["essentials", "chemistry", "practical", "advanced", "history"],
        "fields": {
            "essentials": SECTION_FIELDS["essentials"],
            "chemistry": SECTION_FIELDS["chemistry"],
            "practical": SECTION_FIELDS["practical"],
            "advanced": SECTION_FIELDS["advanced"],
            "history": SECTION_FIELDS["history"],
        },
        "collapsed": [],
        "tile_preset": "detailed",
    },
}

# Which section a toggled-on field lands in.
TOGGLEABLE_SECTION = {fid: "chemistry" for fid in TOGGLEABLE_FIELDS}

DEFAULT_LEVEL = "general"

# ---------------------------------------------------------------------------
# IGCSE assessment data. The Cambridge IGCSE Chemistry (0620) data sheet
# lists relative atomic masses for the elements below as simple values
# (mostly integers; Cl 35.5 and Cu 63.5 are the classic halves). When the
# IGCSE level is active, masses render from this table; every element not
# listed here can be de-emphasised via syllabus focus.
# ---------------------------------------------------------------------------

IGCSE_MASSES = {
    1: 1, 2: 4, 3: 7, 4: 9, 5: 11, 6: 12, 7: 14, 8: 16, 9: 19, 10: 20,
    11: 23, 12: 24, 13: 27, 14: 28, 15: 31, 16: 32, 17: 35.5, 18: 40,
    19: 39, 20: 40, 21: 45, 22: 48, 23: 51, 24: 52, 25: 55, 26: 56,
    27: 59, 28: 59, 29: 63.5, 30: 65, 31: 70, 32: 73, 33: 75, 34: 79,
    35: 80, 36: 84, 47: 108, 50: 119, 53: 127, 56: 137, 74: 184, 78: 195,
    79: 197, 80: 201, 82: 207, 92: 238,
}

IGCSE_ELEMENTS = frozenset(IGCSE_MASSES)

# --------------------------------------------------------------------------
# Tile presets: which fields render inside each element tile.
# --------------------------------------------------------------------------

TILE_PRESETS = {
    "compact": {
        "label": "Compact",
        "fields": ["number", "symbol"],
    },
    "standard": {
        "label": "Standard",
        "fields": ["number", "symbol", "mass"],
    },
    "school": {
        "label": "School",
        "fields": ["number", "symbol", "mass", "name"],
    },
    "detailed": {
        "label": "Detailed",
        "fields": ["number", "symbol", "mass", "name", "state"],
    },
}

TILE_FIELD_LABELS = {
    "number": "Atomic number",
    "symbol": "Symbol",
    "mass": "Atomic mass",
    "name": "Name",
    "state": "State",
    "group": "Group",
    "period": "Period",
    "config": "Electron config.",
}

# Fields a custom tile configuration may choose from.
TILE_CHOICE_FIELDS = ["number", "symbol", "mass", "name", "state", "group",
                      "period", "config"]


def level_profile(level_id: str) -> dict:
    if level_id not in EDUCATION_LEVELS:
        raise ValueError("unknown education level: %r" % level_id)
    return EDUCATION_LEVELS[level_id]


def tile_preset_fields(preset_id: str):
    if preset_id not in TILE_PRESETS:
        raise ValueError("unknown tile preset: %r" % preset_id)
    return list(TILE_PRESETS[preset_id]["fields"])


def section_title(section_id: str) -> str:
    return SECTION_TITLES.get(section_id, section_id.title())
