"""Settings persistence, backed by QSettings (native storage on each
platform: defaults on macOS, registry on Windows, INI on Linux).

A single Settings object is passed around the app; it emits ``changed(key)``
so views can react without a reload. All keys have defaults, and reset()
restores them.
"""
from __future__ import annotations

from PySide6.QtCore import QSettings, QObject, Signal

from orbital.profiles import (EDUCATION_LEVELS, TILE_PRESETS, DEFAULT_LEVEL,
                              TILE_CHOICE_FIELDS)
from orbital.layouts import LAYOUTS, DEFAULT_LAYOUT

DEFAULTS = {
    "theme": "system",            # system | light | dark
    "accent": "#4a7db5",           # muted steel blue
    "layout": DEFAULT_LAYOUT,
    "color_mode": "category",
    "education_level": DEFAULT_LEVEL,
    "tile_preset": "standard",
    "tile_fields": None,          # list -> custom config; None -> follow preset
    "tile_scale": 1.0,            # density multiplier
    "tile_font_scale": 1.0,
    "mass_precision": 3,
    "show_legend": True,
    "remember_layout": True,      # restore last layout at startup
    "open_details_on_select": True,
}

_ACCENTS = {
    "steel blue": "#4a7db5",
    "teal": "#3d8a80",
    "green": "#548254",
    "rust": "#b06a4a",
    "plum": "#8a5b7d",
    "graphite": "#6b6f73",
}


class Settings(QObject):
    changed = Signal(str)

    def __init__(self, ini_path: str = None, parent=None):
        super().__init__(parent)
        if ini_path:
            self._qs = QSettings(ini_path, QSettings.IniFormat)
        else:
            self._qs = QSettings("Orbital", "Orbital")

    # -- typed get/set ------------------------------------------------------

    def get(self, key):
        default = DEFAULTS[key]
        value = self._qs.value(key, defaultValue=default)
        # QSettings stores strings on some platforms; coerce back.
        if isinstance(default, bool):
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes")
            return bool(value)
        if isinstance(default, float):
            try:
                return float(value)
            except (TypeError, ValueError):
                return default
        if isinstance(default, int) and not isinstance(default, bool):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        if isinstance(default, list) or default is None and key == "tile_fields":
            if value is None:
                return default
            if isinstance(value, str):
                import json
                try:
                    value = json.loads(value)
                except ValueError:
                    return default
            return list(value) if value is not None else None
        return value

    def set(self, key, value):
        # No-op on unchanged values: this is what breaks signal feedback
        # loops between settings -> UI widgets -> setters.
        try:
            if self.get(key) == value:
                return
        except Exception:
            pass
        if key == "tile_fields" and isinstance(value, list):
            import json
            self._qs.setValue(key, json.dumps(value))
        else:
            self._qs.setValue(key, value)
        self.changed.emit(key)

    def has(self, key) -> bool:
        return self._qs.contains(key)

    def reset(self):
        for key in DEFAULTS:
            self._qs.remove(key)
            self.changed.emit(key)

    # -- convenience --------------------------------------------------------

    def layout_id(self) -> str:
        if self.get("remember_layout"):
            lid = self.get("layout")
            return lid if lid in LAYOUTS else DEFAULT_LAYOUT
        return DEFAULT_LAYOUT

    def education_level(self) -> str:
        level = self.get("education_level")
        return level if level in EDUCATION_LEVELS else DEFAULT_LEVEL

    def tile_fields(self) -> list:
        custom = self.get("tile_fields")
        if custom:
            valid = set(TILE_CHOICE_FIELDS)
            return [f for f in custom if f in valid] or list(
                TILE_PRESETS["standard"]["fields"])
        preset = self.get("tile_preset")
        preset = preset if preset in TILE_PRESETS else "standard"
        return list(TILE_PRESETS[preset]["fields"])

    def accent_hex(self) -> str:
        accent = self.get("accent")
        if isinstance(accent, str):
            if accent in _ACCENTS:
                return _ACCENTS[accent]
            if accent.startswith("#") and len(accent) == 7:
                return accent
        return DEFAULTS["accent"]

    ACCENTS = _ACCENTS
