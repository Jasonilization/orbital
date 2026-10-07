"""Filter popover — deliberately simple: categories, state, block,
natural/synthetic, radioactive, discovery year range."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QLabel,
    QPushButton, QSpinBox, QGroupBox, QComboBox,
)

from orbital.data import CATEGORIES, BLOCKS, STATES
from orbital.filters import FilterSpec


class FilterDialog(QDialog):
    changed = Signal(object)  # FilterSpec

    def __init__(self, parent, spec: FilterSpec):
        super().__init__(parent)
        self.setWindowTitle("Filter elements")
        self.setModal(False)
        self.spec = spec

        lay = QVBoxLayout(self)
        lay.setSpacing(8)

        grid = QGridLayout()
        grid.setSpacing(10)

        # categories
        cat_box = QGroupBox("Category")
        cat_lay = QGridLayout(cat_box)
        self.cat_checks = {}
        for i, cat in enumerate(CATEGORIES):
            cb = QCheckBox(cat.title())
            cb.setChecked(cat in spec.categories)
            self.cat_checks[cat] = cb
            cat_lay.addWidget(cb, i // 2, i % 2)
        grid.addWidget(cat_box, 0, 0, 2, 1)

        # state / block
        sb_box = QGroupBox("State and block")
        sb_lay = QGridLayout(sb_box)
        self.state_checks = {}
        for i, st in enumerate(STATES):
            cb = QCheckBox(st.title())
            cb.setChecked(st in spec.states)
            self.state_checks[st] = cb
            sb_lay.addWidget(cb, 0, i)
        self.block_checks = {}
        for i, b in enumerate(BLOCKS):
            cb = QCheckBox(b + "-block")
            cb.setChecked(b in spec.blocks)
            self.block_checks[b] = cb
            sb_lay.addWidget(cb, 1, i)
        grid.addWidget(sb_box, 0, 1)

        # classification
        class_box = QGroupBox("Classification")
        cl = QVBoxLayout(class_box)
        self.synthetic = QComboBox()
        self.synthetic.addItems(["Any", "Natural only", "Synthetic only"])
        self.synthetic.setCurrentIndex(
            0 if spec.synthetic is None else (2 if spec.synthetic else 1))
        self.radioactive = QComboBox()
        self.radioactive.addItems(["Any", "Stable only", "Radioactive only"])
        self.radioactive.setCurrentIndex(
            0 if spec.radioactive is None else (2 if spec.radioactive else 1))
        cl.addWidget(QLabel("Origin:"))
        cl.addWidget(self.synthetic)
        cl.addWidget(QLabel("Radioactivity:"))
        cl.addWidget(self.radioactive)
        grid.addWidget(class_box, 1, 1)

        # discovery year
        year_box = QGroupBox("Discovery year")
        yl = QHBoxLayout(year_box)
        yl.addWidget(QLabel("after"))
        self.after = QSpinBox()
        self.after.setRange(0, 2100)
        self.after.setValue(spec.discovered_after or 0)
        self.after.setSpecialValueText("any")
        yl.addWidget(self.after)
        yl.addWidget(QLabel("before"))
        self.before = QSpinBox()
        self.before.setRange(0, 2100)
        self.before.setValue(spec.discovered_before or 2100)
        self.before.setSpecialValueText("any")
        yl.addWidget(self.before)
        grid.addWidget(year_box, 2, 0, 1, 2)

        lay.addLayout(grid)

        btns = QHBoxLayout()
        clear = QPushButton("Clear all")
        clear.clicked.connect(self._clear)
        apply_btn = QPushButton("Apply")
        apply_btn.setDefault(True)
        apply_btn.clicked.connect(self._apply)
        close = QPushButton("Close")
        close.clicked.connect(self.close)
        btns.addWidget(clear)
        btns.addStretch(1)
        btns.addWidget(apply_btn)
        btns.addWidget(close)
        lay.addLayout(btns)

        for cb in list(self.cat_checks.values()) + list(self.state_checks.values()) + \
                list(self.block_checks.values()):
            cb.stateChanged.connect(self._apply)
        self.synthetic.currentIndexChanged.connect(self._apply)
        self.radioactive.currentIndexChanged.connect(self._apply)
        self.after.valueChanged.connect(self._apply)
        self.before.valueChanged.connect(self._apply)

    def _clear(self):
        for cb in self.cat_checks.values():
            cb.setChecked(False)
        for cb in self.state_checks.values():
            cb.setChecked(False)
        for cb in self.block_checks.values():
            cb.setChecked(False)
        self.synthetic.setCurrentIndex(0)
        self.radioactive.setCurrentIndex(0)
        self.after.setValue(0)
        self.before.setValue(2100)

    def _apply(self):
        categories = frozenset(c for c, cb in self.cat_checks.items() if cb.isChecked())
        states = frozenset(c for c, cb in self.state_checks.items() if cb.isChecked())
        blocks = frozenset(c for c, cb in self.block_checks.items() if cb.isChecked())
        synthetic = None if self.synthetic.currentIndex() == 0 else (
            self.synthetic.currentIndex() == 2)
        radioactive = None if self.radioactive.currentIndex() == 0 else (
            self.radioactive.currentIndex() == 2)
        after = self.after.value() if self.after.value() > 0 else None
        before = self.before.value() if self.before.value() < 2100 else None
        self.spec = FilterSpec(
            categories=categories, states=states, blocks=blocks,
            synthetic=synthetic, radioactive=radioactive,
            discovered_after=after, discovered_before=before,
        )
        self.changed.emit(self.spec)
