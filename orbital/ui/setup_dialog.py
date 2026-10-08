"""First-run setup: one dialog, one choice — how much detail do you need?

Shown once on first launch (and from Help -> First-time setup). No wizard,
no pages, no tour.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QRadioButton, QPushButton, QLabel, QGroupBox,
)

from orbital.profiles import EDUCATION_LEVELS

SETUP_TEXT = {
    "igcse": ("School (IGCSE)",
              "The 46 data-sheet elements, simple atomic masses (O 16, Cl 35.5), "
              "shells and exam-style detail only."),
    "general": ("General",
                "Everyday info — essentials, key properties, uses. "
                "Everything else one click away."),
    "alevel": ("A Level",
               "Full electron configurations, electronegativity, all "
               "oxidation states."),
    "advanced": ("Advanced",
                 "Everything the database holds, nothing hidden."),
}


class SetupDialog(QDialog):
    def __init__(self, parent, settings, first_run=True):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Welcome to Orbital")
        self.setModal(True)
        self.setMinimumWidth(470)

        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        title = QLabel("What do you need Orbital for?")
        f = QFont(title.font())
        f.setBold(True)
        f.setPointSizeF(f.pointSizeF() * 1.3)
        title.setFont(f)
        lay.addWidget(title)

        note = QLabel("You can change this any time from the Level menu "
                      "or Settings.")
        note.setProperty("muted", True)
        lay.addWidget(note)

        box = QGroupBox()
        box_lay = QVBoxLayout(box)
        box_lay.setSpacing(6)
        self.radios = {}
        current = settings.education_level()
        for lid in ("igcse", "general", "alevel", "advanced"):
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
            self.radios[lid] = radio
            box_lay.addWidget(radio)
            box_lay.addWidget(desc)
        lay.addWidget(box)

        start = QPushButton("Start")
        start.setDefault(True)
        start.clicked.connect(self.accept)
        lay.addWidget(start, 0, Qt.AlignRight)

    def selected_level(self):
        for lid, radio in self.radios.items():
            if radio.isChecked():
                return lid
        return "general"

    def accept(self):
        level = self.selected_level()
        s = self.settings
        s.set("education_level", level)
        s.set("tile_preset", EDUCATION_LEVELS[level].get("tile_preset", "standard"))
        s.set("tile_fields", None)
        if level == "igcse":
            s.set("igcse_focus", True)
        s.set("setup_done", True)
        super().accept()
