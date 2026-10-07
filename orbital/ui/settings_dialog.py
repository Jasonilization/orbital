"""Settings dialog: Appearance, Element tiles, Information, Behaviour, Data."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QPushButton, QDialogButtonBox, QTabWidget,
    QWidget, QListWidget, QLabel,
)

from orbital.profiles import EDUCATION_LEVELS, TILE_PRESETS, TILE_CHOICE_FIELDS, TILE_FIELD_LABELS
from orbital.settings import DEFAULTS, Settings


class SettingsDialog(QDialog):
    def __init__(self, parent, settings: Settings, data_version="2026-10"):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(460)

        lay = QVBoxLayout(self)
        tabs = QTabWidget()

        # -- Appearance -------------------------------------------------------
        appearance = QWidget()
        af = QFormLayout(appearance)
        self.theme = QComboBox()
        self.theme.addItems(["System", "Light", "Dark"])
        current = settings.get("theme")
        self.theme.setCurrentIndex(["system", "light", "dark"].index(current))
        af.addRow("Theme", self.theme)

        self.accent = QComboBox()
        self.accent.setEditable(True)
        for name, hexv in Settings.ACCENTS.items():
            self.accent.addItem(name, hexv)
        self.accent.setCurrentText("steel blue")
        current_accent = settings.get("accent")
        matched = False
        for i in range(self.accent.count()):
            if self.accent.itemData(i) == current_accent:
                self.accent.setCurrentIndex(i)
                matched = True
        if not matched and isinstance(current_accent, str):
            self.accent.setCurrentText(current_accent)
        af.addRow("Accent", self.accent)

        self.tile_scale = QDoubleSpinBox()
        self.tile_scale.setRange(0.8, 1.6)
        self.tile_scale.setSingleStep(0.05)
        self.tile_scale.setValue(float(settings.get("tile_scale")))
        af.addRow("Tile size", self.tile_scale)
        tabs.addTab(appearance, "Appearance")

        # -- Element tiles ----------------------------------------------------
        tiles = QWidget()
        tf = QFormLayout(tiles)
        self.tile_preset = QComboBox()
        for pid, preset in TILE_PRESETS.items():
            self.tile_preset.addItem(preset["label"], pid)
        self.tile_preset.setCurrentIndex(
            max(0, list(TILE_PRESETS).index(settings.get("tile_preset"))))
        tf.addRow("Tile preset", self.tile_preset)

        self.custom_fields = QListWidget()
        self.custom_fields.setSelectionMode(QListWidget.MultiSelection)
        for fid in TILE_CHOICE_FIELDS:
            self.custom_fields.addItem(TILE_FIELD_LABELS[fid])
        custom = settings.get("tile_fields") or []
        for i in range(self.custom_fields.count()):
            item = self.custom_fields.item(i)
            item.setData(Qt.UserRole, TILE_CHOICE_FIELDS[i])
            item.setSelected(TILE_CHOICE_FIELDS[i] in custom)
        self.custom_fields.setToolTip("Selecting any field here switches the "
                                      "tile to a custom configuration")
        tf.addRow("Custom fields", self.custom_fields)

        self.tile_font_scale = QDoubleSpinBox()
        self.tile_font_scale.setRange(0.8, 1.4)
        self.tile_font_scale.setSingleStep(0.05)
        self.tile_font_scale.setValue(float(settings.get("tile_font_scale")))
        tf.addRow("Tile font size", self.tile_font_scale)
        tabs.addTab(tiles, "Element tiles")

        # -- Information ------------------------------------------------------
        info = QWidget()
        inf = QFormLayout(info)
        self.level = QComboBox()
        for lid, prof in EDUCATION_LEVELS.items():
            self.level.addItem(prof["label"] + " \u2014 " + prof["description"], lid)
        current_level = settings.get("education_level")
        self.level.setCurrentIndex(list(EDUCATION_LEVELS).index(current_level))
        inf.addRow("Education level", self.level)

        self.mass_precision = QSpinBox()
        self.mass_precision.setRange(1, 4)
        self.mass_precision.setValue(int(settings.get("mass_precision")))
        inf.addRow("Atomic mass decimals", self.mass_precision)
        tabs.addTab(info, "Information")

        # -- Behaviour --------------------------------------------------------
        behaviour = QWidget()
        bf = QFormLayout(behaviour)
        self.remember_layout = QCheckBox("Remember last table layout")
        self.remember_layout.setChecked(bool(settings.get("remember_layout")))
        bf.addRow(self.remember_layout)
        self.show_legend = QCheckBox("Show colour legend")
        self.show_legend.setChecked(bool(settings.get("show_legend")))
        bf.addRow(self.show_legend)
        self.open_details = QCheckBox("Open element details on click")
        self.open_details.setChecked(bool(settings.get("open_details_on_select")))
        bf.addRow(self.open_details)
        tabs.addTab(behaviour, "Behaviour")

        # -- Data -------------------------------------------------------------
        data = QWidget()
        df = QFormLayout(data)
        df.addRow("Element data version", QLabel(data_version))
        df.addRow("Sources", QLabel("IUPAC (weights), CRC Handbook-style values, "
                                    "NIST (ionisation energies). See docs/data-sources.md"))
        reset = QPushButton("Reset all customizations")
        reset.clicked.connect(self._reset)
        df.addRow(reset)
        tabs.addTab(data, "Data")

        lay.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _reset(self):
        self.settings.reset()

    def apply(self):
        s = self.settings
        s.set("theme", ["system", "light", "dark"][self.theme.currentIndex()])
        s.set("accent", self.accent.currentData() or self.accent.currentText())
        s.set("tile_scale", float(self.tile_scale.value()))
        s.set("tile_preset", self.tile_preset.currentData())
        selected = [
            self.custom_fields.item(i).data(Qt.UserRole)
            for i in range(self.custom_fields.count())
            if self.custom_fields.item(i).isSelected()
        ]
        s.set("tile_fields", selected if selected else None)
        s.set("tile_font_scale", float(self.tile_font_scale.value()))
        s.set("education_level", self.level.currentData())
        s.set("mass_precision", int(self.mass_precision.value()))
        s.set("remember_layout", self.remember_layout.isChecked())
        s.set("show_legend", self.show_legend.isChecked())
        s.set("open_details_on_select", self.open_details.isChecked())
