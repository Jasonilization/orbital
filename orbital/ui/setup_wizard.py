"""First-run wizard: three short steps, skippable at any point.

Step 1 — level: how much detail you need (General / IGCSE / A Level /
Advanced). Step 2 — look: theme and accent. Step 3 — done: summary and
the three shortcuts that matter. "Skip setup" keeps the defaults and
never nags again; finishing applies the choices. Both set setup_done.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget, QWidget, QLabel,
    QPushButton, QRadioButton, QGroupBox, QButtonGroup,
)

from orbital.profiles import EDUCATION_LEVELS
from orbital.ui.setup_dialog import SETUP_TEXT


LEVELS = ("igcse", "general", "alevel", "advanced")
THEMES = (("system", "System"), ("light", "Light"), ("dark", "Dark"))


class SetupWizard(QDialog):
    finished_setup = Signal(dict)   # {"level", "theme", "accent"} on Finish

    def __init__(self, parent, settings):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Welcome to Orbital")
        self.setModal(True)
        self.setMinimumWidth(500)

        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        title = QLabel("Set up Orbital")
        f = QFont(title.font())
        f.setBold(True)
        f.setPointSizeF(f.pointSizeF() * 1.35)
        title.setFont(f)
        lay.addWidget(title)

        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)

        self.stack.addWidget(self._level_page())
        self.stack.addWidget(self._theme_page())
        self.stack.addWidget(self._done_page())

        # buttons: skip (left) | back | next/finish (right)
        row = QHBoxLayout()
        self.skip = QPushButton("Skip setup")
        self.skip.setToolTip("Keep the defaults — everything is changeable later")
        self.skip.clicked.connect(self._skip)
        row.addWidget(self.skip)
        row.addStretch(1)
        self.back = QPushButton("Back")
        self.back.clicked.connect(self._go_back)
        row.addWidget(self.back)
        self.next = QPushButton("Next")
        self.next.setDefault(True)
        self.next.clicked.connect(self._go_next)
        row.addWidget(self.next)
        lay.addLayout(row)

        self._update_buttons()

    # ---------------------------------------------------------------- pages

    def _level_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(4)
        intro = QLabel("What do you need Orbital for?")
        intro.setProperty("muted", True)
        lay.addWidget(intro)
        box = QGroupBox()
        box_lay = QVBoxLayout(box)
        box_lay.setSpacing(6)
        self.level_radios = {}
        current = self.settings.education_level()
        for lid in LEVELS:
            heading, description = SETUP_TEXT[lid]
            radio = QRadioButton(heading)
            rf = QFont(radio.font())
            rf.setBold(True)
            radio.setFont(rf)
            desc = QLabel(description)
            desc.setWordWrap(True)
            desc.setProperty("muted", True)
            desc.setStyleSheet("margin-left: 20px;")
            radio.setChecked(lid == current)
            self.level_radios[lid] = radio
            box_lay.addWidget(radio)
            box_lay.addWidget(desc)
        lay.addWidget(box)
        lay.addStretch(1)
        return page

    def _theme_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(4)
        intro = QLabel("How should it look?")
        intro.setProperty("muted", True)
        lay.addWidget(intro)

        theme_box = QGroupBox("Theme")
        tb = QHBoxLayout(theme_box)
        self.theme_radios = {}
        group = QButtonGroup(self)
        current_theme = self.settings.get("theme")
        for tid, label in THEMES:
            radio = QRadioButton(label)
            radio.setChecked(tid == current_theme)
            group.addButton(radio)
            self.theme_radios[tid] = radio
            tb.addWidget(radio)
        lay.addWidget(theme_box)

        accent_box = QGroupBox("Accent")
        ab = QHBoxLayout(accent_box)
        self.accent_buttons = {}
        from orbital.settings import Settings
        current_accent = self.settings.accent_hex()
        for name, hexv in Settings.ACCENTS.items():
            b = QPushButton("  ")
            b.setFixedSize(28, 22)
            b.setStyleSheet(
                "background-color: %s; border: 1px solid #999; "
                "border-radius: 6px;" % hexv)
            b.setToolTip(name.title())
            b.setCheckable(True)
            b.setChecked(QColor(hexv).name().lower() == current_accent.lower())
            b.clicked.connect(lambda checked=False, h=hexv: self._pick_accent(h))
            self.accent_buttons[hexv] = b
            ab.addWidget(b)
        ab.addStretch(1)
        lay.addWidget(accent_box)
        lay.addStretch(1)
        return page

    def _done_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(8)
        done = QLabel("You're set.")
        df = QFont(done.font())
        df.setBold(True)
        df.setPointSizeF(df.pointSizeF() * 1.2)
        done.setFont(df)
        lay.addWidget(done)
        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        lay.addWidget(self.summary)
        keys = QLabel(
            "<b>/</b> search &nbsp;\u00b7&nbsp; <b>arrows</b> move &nbsp;\u00b7&nbsp; "
            "<b>Enter</b> open &nbsp;\u00b7&nbsp; "
            "<b>Ctrl+scroll</b> zoom &nbsp;\u00b7&nbsp; "
            "<b>Esc</b> clear")
        keys.setProperty("muted", True)
        lay.addWidget(keys)
        lay.addStretch(1)
        return page

    # ---------------------------------------------------------------- logic

    def _update_buttons(self):
        i = self.stack.currentIndex()
        self.back.setVisible(i > 0)
        self.next.setText("Finish" if i == self.stack.count() - 1 else "Next")

    def _go_back(self):
        self.stack.setCurrentIndex(self.stack.currentIndex() - 1)
        self._update_buttons()

    def _go_next(self):
        i = self.stack.currentIndex()
        if i < self.stack.count() - 1:
            if i == 0:
                # remember the choice so step 3 can summarise it
                self._chosen_level = next(
                    lid for lid, r in self.level_radios.items() if r.isChecked())
            if i == 1:
                self._chosen_theme = next(
                    tid for tid, r in self.theme_radios.items() if r.isChecked())
                self.summary.setText(
                    "Level: <b>%s</b> &nbsp;\u00b7&nbsp; Theme: <b>%s</b>"
                    % (EDUCATION_LEVELS[self._chosen_level]["label"],
                       self.theme_radios[self._chosen_theme].text()))
            self.stack.setCurrentIndex(i + 1)
            self._update_buttons()
        else:
            self.accept()

    def _skip(self):
        self._skipped = True
        # skipping means "don't nag me" — keep defaults, stay done
        self.settings.set("setup_done", True)
        self.reject()

    def _pick_accent(self, hexv):
        for h, b in self.accent_buttons.items():
            b.setChecked(h == hexv)
        self._chosen_accent = hexv

    # ---------------------------------------------------------------- apply

    def accept(self):
        s = self.settings
        s.set("education_level", self._chosen_level)
        s.set("tile_preset", EDUCATION_LEVELS[self._chosen_level].get(
            "tile_preset", "standard"))
        s.set("tile_fields", None)
        s.set("theme", self._chosen_theme)
        if getattr(self, "_chosen_accent", None):
            s.set("accent", self._chosen_accent)
        if self._chosen_level == "igcse":
            s.set("igcse_focus", True)
        s.set("setup_done", True)
        self.finished_setup.emit({
            "level": self._chosen_level,
            "theme": self._chosen_theme,
            "accent": getattr(self, "_chosen_accent", None),
        })
        super().accept()

    def skip_was_pressed(self):
        return getattr(self, "_skipped", False)
