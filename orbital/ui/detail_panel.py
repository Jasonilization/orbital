"""Right-hand detail panel.

Two states: the welcome state (nothing selected) which shows one of the
200 chemistry jokes, and the element view, which renders the fields the
current education profile exposes. Above the sections sits a row of
toggle chips — the user's one-click control over how much detail shows
(overrides persist and stack on top of the education level, so nothing
is ever more than a click away).
"""
from __future__ import annotations

import datetime
import json
import random
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QSizePolicy,
    QScrollArea, QFrame, QPushButton,
)

from orbital.data import Element
from orbital.formatting import field_value, field_label, formula_html
from orbital.profiles import (
    level_profile, section_title, TOGGLEABLE_FIELDS, FIELDS,
    SECTION_FIELDS,
)
from orbital.ui.icons import icon as _icon

SECTION_ICONS = {
    "chemistry": "flask",
    "practical": "box",
    "history": "clock",
    "advanced": "layers",
    "essentials": None,
}

JOKES_PATH = Path(__file__).resolve().parent.parent / "data" / "jokes.json"

TOGGLEABLE_LABELS = {
    "configuration": "Config",
    "oxidation_states": "Oxidation",
    "electronegativity": "Electroneg.",
    "ionization": "Ionisation",
    "radius": "Radius",
    "history": "History",
}


def load_jokes():
    with open(JOKES_PATH, "r", encoding="utf-8") as f:
        jokes = json.load(f)
    return jokes


class WelcomeView(QWidget):
    """Shown when no element is selected: quick guide + joke of the day."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(10)

        title = QLabel("Orbital")
        f = QFont(title.font())
        f.setBold(True)
        f.setPointSizeF(f.pointSizeF() * 1.35)
        title.setFont(f)
        lay.addWidget(title)

        hint = QLabel(
            "Select an element on the table to see its details.\n\n"
            "Press <b>/</b> to search. Arrow keys move around the table; "
            "Enter opens the focused element.")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        self.joke_header = QLabel()
        jf = QFont(self.joke_header.font())
        jf.setBold(True)
        self.joke_header.setFont(jf)
        lay.addSpacing(8)
        lay.addWidget(self.joke_header)

        self.joke_label = QLabel()
        self.joke_label.setWordWrap(True)
        self.joke_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.joke_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.joke_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.joke_label, 1)

        self.shuffle = QPushButton("Another one")
        self.shuffle.clicked.connect(self._shuffle)
        lay.addWidget(self.shuffle, 0, Qt.AlignLeft)

        self.jokes = load_jokes()
        self._index = self._joke_of_the_day_index()
        self._show()

    def _joke_of_the_day_index(self):
        today = datetime.date.today().toordinal()
        return today % len(self.jokes)

    def _show(self):
        self.joke_label.setTextFormat(Qt.PlainText)
        self.joke_label.setText(self.jokes[self._index])
        self.joke_header.setText(
            "Chemistry joke %d of %d" % (self._index + 1, len(self.jokes)))

    def _shuffle(self):
        if len(self.jokes) < 2:
            return
        new = self._index
        while new == self._index:
            new = random.randrange(len(self.jokes))
        self._index = new
        self._show()


class _Section(QFrame):
    def __init__(self, title, icon_name=None, parent=None):
        super().__init__(parent)
        self.setObjectName("detail_section")
        self.setFrameShape(QFrame.NoFrame)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.toggle = QToolButton()
        if icon_name:
            self.toggle.setIcon(_icon(icon_name))
            self.toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle.setText(title)
        self.toggle.setCheckable(True)
        self.toggle.setChecked(True)
        self.toggle.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.toggle.setStyleSheet(
            "QToolButton { border: none; font-weight: bold; padding: 4px; }")
        self.body = QWidget()
        self.body_lay = QVBoxLayout(self.body)
        self.body_lay.setContentsMargins(6, 2, 6, 6)
        self.body_lay.setSpacing(4)
        lay.addWidget(self.toggle)
        lay.addWidget(self.body)
        self.toggle.toggled.connect(self._set_open)

    def _set_open(self, on):
        self.body.setVisible(on)
        self.toggle.setArrowType(Qt.DownArrow if on else Qt.RightArrow)


class DetailPanel(QWidget):
    element_pinned = Signal(int)
    compare_requested = Signal(int)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.element = None

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._root.addWidget(self._scroll)

        self.welcome = WelcomeView()
        self._scroll.setWidget(self.welcome)

    def _swap(self, widget):
        old = self._scroll.takeWidget()
        self._scroll.setWidget(widget)
        if old is not None and old is not self.welcome:
            old.deleteLater()

    def show_welcome(self):
        self.element = None
        self._swap(self.welcome)

    # -- toggle chips ------------------------------------------------------

    def _chips(self, effective):
        row = QHBoxLayout()
        row.setSpacing(4)
        lead = QLabel("Show:")
        lead.setProperty("muted", True)
        row.addWidget(lead)
        for fid in TOGGLEABLE_FIELDS + ["history"]:
            chip = QToolButton()
            chip.setObjectName("detail_chip")
            chip.setText(TOGGLEABLE_LABELS.get(fid, fid))
            chip.setCheckable(True)
            chip.setChecked(bool(effective.get(fid)))
            chip.setToolTip(field_label(fid) if fid in FIELDS
                            else "Discovery and naming details")
            chip.setStyleSheet(
                "QToolButton { border: 1px solid palette(mid);"
                " border-radius: 3px; padding: 2px 6px; }"
                "QToolButton:checked { background: palette(highlight);"
                " color: palette(highlighted-text); }")
            chip.toggled.connect(
                lambda on, f=fid: self._on_chip(f, on))
            row.addWidget(chip)
        row.addStretch(1)
        wrap = QWidget()
        wrap.setLayout(row)
        return wrap

    def _on_chip(self, field_id, shown):
        self.settings.set_panel_override(field_id, shown)
        if self.element is not None:
            self.show_element(self.element)

    # -- element page -------------------------------------------------------

    def _effective(self, profile):
        """Apply the user's stored toggle overrides to the profile."""
        overrides = self.settings.panel_overrides()
        fields = {k: list(v) for k, v in profile["fields"].items()}
        sections = list(profile["sections"])

        for fid in TOGGLEABLE_FIELDS:
            default_on = fid in fields.get("chemistry", [])
            shown = overrides.get(fid, default_on)
            if shown and fid not in fields.get("chemistry", []):
                fields.setdefault("chemistry", []).append(fid)
            elif not shown and fid in fields.get("chemistry", []):
                fields["chemistry"] = [f for f in fields["chemistry"] if f != fid]

        history_default = "history" in sections
        if "history" in overrides:
            if overrides["history"] and "history" not in sections:
                sections.append("history")
                fields.setdefault("history", list(SECTION_FIELDS["history"]))
            elif not overrides["history"] and "history" in sections:
                sections.remove("history")

        effective = {fid: (overrides.get(fid, fid in fields.get("chemistry", [])))
                     for fid in TOGGLEABLE_FIELDS}
        effective["history"] = "history" in sections
        return sections, fields, effective

    def show_element(self, element: Element):
        self.element = element
        level = self.settings.education_level()
        profile = level_profile(level)
        sections, fields, effective = self._effective(profile)
        mass_precision = self.settings.get("mass_precision")

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        # header
        head = QHBoxLayout()
        head.setSpacing(10)
        sym = QLabel(element.symbol)
        sf = QFont(sym.font())
        sf.setBold(True)
        sf.setPointSizeF(sf.pointSizeF() * 2.4)
        sym.setFont(sf)
        head.addWidget(sym)
        namebox = QVBoxLayout()
        name = QLabel(element.name)
        nf = QFont(name.font())
        nf.setBold(True)
        nf.setPointSizeF(nf.pointSizeF() * 1.2)
        name.setFont(nf)
        subtitle = QLabel("%d \u00b7 %s" % (element.number, element.category.title()))
        subtitle.setProperty("muted", True)
        namebox.addWidget(name)
        namebox.addWidget(subtitle)
        head.addLayout(namebox, 1)

        btn = QPushButton("Compare\u2026")
        btn.clicked.connect(lambda: self.compare_requested.emit(element.number))
        btn.setToolTip("Add %s to a side-by-side comparison" % element.name)
        head.addWidget(btn)
        lay.addLayout(head)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        lay.addWidget(divider)

        # compact facts strip replaces the old Essentials section:
        # "Group 16  ·  Period 3  ·  State Solid  ·  Mass 32.06"
        facts = self._facts_strip(element, fields.get("essentials", []), level)
        if facts:
            strip = QLabel(facts)
            strip.setTextFormat(Qt.RichText)
            strip.setWordWrap(True)
            f = QFont(strip.font())
            f.setPointSizeF(f.pointSizeF() * 0.95)
            strip.setFont(f)
            lay.addWidget(strip)
            thin = QFrame()
            thin.setFrameShape(QFrame.HLine)
            lay.addWidget(thin)

        # detail toggles live behind one compact "+ More detail" button —
        # the default view stays clean; everything is still one click away
        self._more_button = QToolButton()
        self._more_button.setObjectName("detail_more")
        self._more_button.setCheckable(True)
        self._more_button.setIcon(_icon("plus"))
        self._more_button.setText("+ More detail")
        chips = self._chips(effective)
        chips_visible = bool(self.settings.get("chips_shown"))
        chips.setVisible(chips_visible)
        self._more_button.setChecked(chips_visible)
        self._more_button.toggled.connect(lambda on: (
            chips.setVisible(on),
            self.settings.set("chips_shown", on),
            self._more_button.setText("− Less" if on else "+ More detail")))
        lay.addWidget(self._more_button)
        lay.addWidget(chips)

        common_ox = bool(profile.get("common_ox_states_only"))
        config_style = "full" if level in ("alevel", "advanced") else "short"

        collapsed = set(profile.get("collapsed", ()))
        if "history" not in profile["sections"]:
            # history is present only because the user toggled it on —
            # respect their intent and show it expanded
            collapsed.discard("history")

        for section_id in sections:
            if section_id == "essentials":
                continue  # rendered as the facts strip
            section_fields = fields.get(section_id, [])
            if not section_fields:
                continue
            sect = _Section(section_title(section_id),
                            SECTION_ICONS.get(section_id))
            for fid in section_fields:
                if fid in ("symbol", "number"):
                    continue  # already in the header
                value = field_value(
                    element, fid, config_style=config_style,
                    ox_common_only=(fid == "oxidation_states" and common_ox),
                    mass_precision=mass_precision,
                    igcse=(level == "igcse"),
                )
                sect.body_lay.addLayout(self._field_row(field_label(fid), value, fid))
            sect._set_open(section_id not in collapsed)
            lay.addWidget(sect)

        lay.addStretch(1)
        page.adjustSize()
        self._swap(page)

    def _facts_strip(self, element, essentials, level):
        order = ["group", "period", "state", "atomic_mass", "block", "category"]
        include = [f for f in order if f in essentials]
        if not include:
            return ""
        from orbital.ui.theme import is_dark_theme, LIGHT, DARK
        secondary = (DARK if is_dark_theme() else LIGHT).secondary_text.name()
        parts = []
        for fid in include:
            value = field_value(element, fid, igcse=(level == "igcse"))
            if value in (None, ""):
                continue
            label = field_label(fid)
            parts.append(
                '<span style="color:%s;">%s</span> <b>%s</b>'
                % (secondary, label, value))
        return "  \u00b7  ".join(parts)

    def _render_list(self, items, fid, limit=3):
        def render(list_):
            return "<br>".join(
                ("\u2022&nbsp;" + formula_html(v)) if fid == "compounds" else
                ("\u2022&nbsp;" + v) for v in list_)
        val = QLabel(render(items[:limit]))
        val.setTextFormat(Qt.RichText)
        if len(items) > limit:
            more = QToolButton()
            more.setObjectName("list_more")
            more.setText("+ %d more" % (len(items) - limit))
            more.setCursor(Qt.PointingHandCursor)
            more.setStyleSheet("border: none; font-weight: 600;")
            more.clicked.connect(
                lambda: (val.setText(render(items)), more.hide()))
            return val, more
        return val, None

    def _field_row(self, label, value, fid):
        row = QHBoxLayout()
        lab = QLabel(label)
        lab.setProperty("muted", True)
        lab.setStyleSheet("padding-right: 8px;")
        lab.setWordWrap(True)
        row.addWidget(lab, 1)
        if isinstance(value, tuple):
            if not value:
                value = ("\u2014",)
            val, more = self._render_list(value, fid)
            box = QVBoxLayout()
            box.setSpacing(0)
            box.addWidget(val)
            if more is not None:
                box.addWidget(more, 0, Qt.AlignRight)
            wrap = QWidget()
            wrap.setLayout(box)
            wrap_item = wrap
        else:
            val = QLabel("\u2014" if value in (None, "") else str(value))
            wrap_item = val
        val.setWordWrap(True)
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row.addWidget(wrap_item, 2)
        return row
