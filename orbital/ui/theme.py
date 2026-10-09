"""Themes: light / dark / system, plus accent colour.

Restrained palettes built on QPalette so native widgets (menus, dialogs,
scrollbars) follow automatically. No web-app QSS styling; borders, spacing
and typography do the work.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget


class Palette:
    def __init__(self, base, text, window, bright_text, link,
                 button, button_text, highlight, highlighted_text,
                 mid, light, dark, disabled_text, tile_base, border,
                 secondary_text):
        self.base = QColor(base)
        self.text = QColor(text)
        self.window = QColor(window)
        self.bright_text = QColor(bright_text)
        self.link = QColor(link)
        self.button = QColor(button)
        self.button_text = QColor(button_text)
        self.highlight = QColor(highlight)
        self.highlighted_text = QColor(highlighted_text)
        self.mid = QColor(mid)
        self.light = QColor(light)
        self.dark = QColor(dark)
        self.disabled_text = QColor(disabled_text)
        self.tile_base = QColor(tile_base)
        self.border = QColor(border)
        self.secondary_text = QColor(secondary_text)


LIGHT = Palette(
    base="#f4f3f1", text="#1c1c19", window="#fbfbfa", bright_text="#000000",
    link="#2a6496", button="#e9e8e6", button_text="#1c1c19",
    highlight="#d8e2ee", highlighted_text="#10151c",
    mid="#c9c7c2", light="#e2e0dc", dark="#a8a49d",
    disabled_text="#9b9891", tile_base="#ffffff", border="#c5c2bc",
    secondary_text="#51504a",
)

DARK = Palette(
    base="#212328", text="#e6e5e1", window="#1a1c20", bright_text="#ffffff",
    link="#8fb8dc", button="#2c2f36", button_text="#e6e5e1",
    highlight="#3a4553", highlighted_text="#f2f6fa",
    mid="#3a3d44", light="#42454c", dark="#131418",
    disabled_text="#7a7d84", tile_base="#2a2d33", border="#3d4046",
    secondary_text="#b9b9b2",
)


def apply_theme(theme: str, accent_hex: str):
    """theme: 'system' | 'light' | 'dark'. Applies to the running app."""
    app = QApplication.instance()
    if not app:
        return
    if theme == "system":
        is_dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    else:
        is_dark = theme == "dark"

    pal_src = DARK if is_dark else LIGHT
    accent = QColor(accent_hex)

    pal = QPalette()
    pal.setColor(QPalette.Base, pal_src.base)
    pal.setColor(QPalette.Text, pal_src.text)
    pal.setColor(QPalette.Window, pal_src.base)
    pal.setColor(QPalette.WindowText, pal_src.text)
    pal.setColor(QPalette.BrightText, pal_src.bright_text)
    pal.setColor(QPalette.Link, accent if accent.isValid() else pal_src.link)
    pal.setColor(QPalette.Button, pal_src.button)
    pal.setColor(QPalette.ButtonText, pal_src.button_text)
    pal.setColor(QPalette.Mid, pal_src.mid)
    pal.setColor(QPalette.Light, pal_src.light)
    pal.setColor(QPalette.Dark, pal_src.dark)
    pal.setColor(QPalette.ToolTipBase, pal_src.tile_base)
    pal.setColor(QPalette.ToolTipText, pal_src.text)
    pal.setColor(QPalette.PlaceholderText, pal_src.disabled_text)

    # selection: accent-tinted, readable in both modes
    sel_bg = QColor(accent) if accent.isValid() else QColor(pal_src.link)
    if is_dark:
        sel_bg = sel_bg.darker(150)
    else:
        sel_bg = sel_bg.lighter(165)
    pal.setColor(QPalette.Highlight, sel_bg)
    pal.setColor(QPalette.HighlightedText, pal_src.bright_text)

    for group in (QPalette.Disabled,):
        pal.setColor(group, QPalette.Text, pal_src.disabled_text)
        pal.setColor(group, QPalette.ButtonText, pal_src.disabled_text)
        pal.setColor(group, QPalette.WindowText, pal_src.disabled_text)

    app.setPalette(pal)
    app.setStyleSheet("")

    # tiny global QSS: focus rings + label style. Labels marked "muted"
    # use the FULL text colour at demi-bold — readability comes from
    # weight and size, never from grey ink.
    app.setStyleSheet(
        "*[muted=\"true\"] {{ color: {text}; font-weight: 600; }}"
        # rounded, calm controls: a bit of radius, solid borders, no gradients
        "QPushButton {{ border: 1px solid {border}; border-radius: 6px;"
        "  padding: 4px 12px; background: {button}; }}"
        "QPushButton:hover {{ background: {hover}; }}"
        "QPushButton:pressed {{ background: {pressed}; }}"
        "QToolButton {{ border-radius: 9px; }}"
        "QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {{"
        "  border: 1px solid {border}; border-radius: 6px; padding: 3px 8px;"
        "  background: {tile}; }}"
        "QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus"
        " {{ border: 1px solid {accent}; }}"
        "QFrame#detail_section {{ border: 1px solid {border};"
        "  border-radius: 9px; background: {tile}; }}"
        "QMenu {{ border-radius: 6px; }}"
        "QMenu::item:disabled {{ color: {disabled}; }}"
        "QToolTip {{ border: 1px solid {border}; border-radius: 5px; padding: 3px; }}"
        .format(
            text=pal_src.text.name(),
            disabled=pal_src.disabled_text.name(),
            accent=accent.name(),
            border=pal_src.border.name(),
            button=pal_src.button.name(),
            hover=(pal_src.button.lighter(106) if not is_dark
                   else pal_src.button.lighter(112)).name(),
            pressed=(pal_src.button.darker(108) if not is_dark
                     else pal_src.button.darker(150)).name(),
            tile=pal_src.tile_base.name(),
        )
    )
    return is_dark


def is_dark_theme() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    return app.palette().color(QPalette.Base).lightness() < 128


def readable_text_on(color: QColor) -> QColor:
    """Black or white text for best contrast on the given fill."""
    return QColor("#1c1c19") if color.lightness() > 138 else QColor("#f0efec")
