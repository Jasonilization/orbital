"""Right-hand detail panel.

Two states: the welcome state (nothing selected) which shows one of the
200 chemistry jokes, and the element view, which renders the fields the
current education profile exposes — sections collapsible, secondary
information (history) collapsed by default per profile.
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
    level_profile, section_title, FIELDS,
)

JOKES_PATH = Path(__file__).resolve().parent.parent / "data" / "jokes.json"


def load_jokes():
    with open(JOKES_PATH, "r", encoding="utf-8") as f:
        jokes = json.load(f)
    return jokes


class WelcomeView(QWidget):
    """Shown when no element is selected: quick guide + joke of the day."""

    joke_requested = Signal(int)  # index

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
            "Enter opens the focused element."
        )
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

    def show_next(self):
        self._index = (self._index + 1) % len(self.jokes)
        self._show()


class _Section(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.toggle = QToolButton()
        self.toggle.setText(title)
        self.toggle.setCheckable(True)
        self.toggle.setChecked(True)
        self.toggle.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.toggle.setStyleSheet("QToolButton { border: none; font-weight: bold; padding: 4px; }")
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
    element_pinned = Signal(int)     # add to comparison
    compare_requested = Signal(int)  # open compare with this element

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.element = None

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._root.addWidget(self._scroll)

        self.welcome = WelcomeView()
        self._scroll.setWidget(self.welcome)

    def _swap(self, widget):
        old = self._scroll.takeWidget()
        self._scroll.setWidget(widget)
        if old is not None and old is not self.welcome:
            old.deleteLater()

    # ------------------------------------------------------------------ view

    def show_welcome(self):
        self.element = None
        self._scroll.setWidget(self.welcome)

    def show_element(self, element: Element):
        self.element = element
        level = self.settings.education_level()
        profile = level_profile(level)
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
        subtitle.setStyleSheet("color: palette(mid);")
        namebox.addWidget(name)
        namebox.addWidget(subtitle)
        head.addLayout(namebox, 1)

        btn_row = QHBoxLayout()
        pin = QPushButton("Compare\u2026")
        pin.clicked.connect(lambda: self.compare_requested.emit(element.number))
        pin.setToolTip("Add %s to a side-by-side comparison" % element.name)
        btn_row.addWidget(pin)
        head.addLayout(btn_row)
        lay.addLayout(head)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        lay.addWidget(divider)

        common_ox = bool(profile.get("common_ox_states_only"))
        config_style = "short"
        if level in ("alevel", "advanced"):
            config_style = "full"

        collapsed = set(profile.get("collapsed", ()))
        for section_id in profile["sections"]:
            fields = profile["fields"].get(section_id, [])
            if not fields:
                continue
            sect = _Section(section_title(section_id))
            for fid in fields:
                if fid == "symbol" or fid == "number":
                    continue  # already in the header
                value = field_value(
                    element, fid, config_style=config_style,
                    ox_common_only=(fid == "oxidation_states" and common_ox),
                    mass_precision=mass_precision,
                )
                row = self._field_row(field_label(fid), value, fid)
                sect.body_lay.addLayout(row)
            sect._set_open(section_id not in collapsed)
            lay.addWidget(sect)

        lay.addStretch(1)
        page.adjustSize()
        self._swap(page)

    def _field_row(self, label, value, fid):
        from PySide6.QtWidgets import QHBoxLayout
        row = QHBoxLayout()
        lab = QLabel(label)
        lab.setStyleSheet("color: palette(mid); padding-right: 8px;")
        lab.setWordWrap(True)
        row.addWidget(lab, 1)
        if isinstance(value, tuple):
            if not value:
                value = ("\u2014",)
            text = "<br>".join(
                ("\u2022&nbsp;" + formula_html(v)) if fid == "compounds" else
                ("\u2022&nbsp;" + v) for v in value
            )
            val = QLabel(text)
            val.setTextFormat(Qt.RichText)
        else:
            val = QLabel("\u2014" if value in (None, "") else str(value))
        val.setWordWrap(True)
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row.addWidget(val, 2)
        return row
