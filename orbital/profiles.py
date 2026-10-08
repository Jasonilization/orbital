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
    "atomic_mass":       ("essentials", "Relative atomic mass"),
    "group":             ("essentials", "Group"),
    "period":            ("essentials", "Period"),
    "block":             ("essentials", "Block"),
    "category":          ("essentials", "Category"),
    "state":             ("essentials", "State at room temp."),
    # chemistry
    "configuration":     ("chemistry", "Electron configuration"),
    "shells":            ("chemistry", "Shell arrangement"),
    "oxidation_states":  ("chemistry", "Oxidation states"),
    "electronegativity": ("chemistry", "Electronegativity (Pauling)"),
    "ionization":        ("chemistry", "1st ionisation energy"),
    "radius":            ("chemistry", "Atomic radius"),
    "melt":              ("chemistry", "Melting point"),
    "boil":              ("chemistry", "Boiling point"),
    "density":           ("chemistry", "Density"),
    # practical
    "uses":              ("practical", "Common uses"),
    "compounds":         ("practical", "Important compounds"),
    # history
    "discovered":        ("history", "Discovery"),
    "origin":            ("history", "Origin of the name"),
    # advanced-only extras
    "abundance":         ("advanced", "Crustal abundance"),
    "mass_note":          ("advanced", "Atomic mass note"),
}

SECTION_TITLES = {
    "essentials": "Essentials",
    "chemistry": "Chemistry",
    "practical": "Practical",
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
