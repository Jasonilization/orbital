"""Side-by-side element comparison dialog (2 to 4 elements)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView,
)

from orbital.compare import compare_rows, MAX_COMPARE
from orbital.data import by_number


class CompareDialog(QDialog):
    def __init__(self, parent, elements, selected_numbers, settings):
        super().__init__(parent)
        self.elements = elements
        self.settings = settings
        self.setWindowTitle("Compare elements")
        self.resize(760, 520)

        lay = QVBoxLayout(self)
        self.label = QLabel()
        lay.addWidget(self.label)
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setWordWrap(True)
        lay.addWidget(self.table, 1)

        hint = QLabel("Add elements with right-click \u2192 'Add to comparison', "
                      "or 'Compare\u2026' on an element. Up to %d elements." % MAX_COMPARE)
        hint.setStyleSheet("color: palette(mid);")
        lay.addWidget(hint)

        btns = QHBoxLayout()
        btns.addStretch(1)
        close = QPushButton("Close")
        close.clicked.connect(self.close)
        btns.addWidget(close)
        lay.addLayout(btns)

        self.set_elements(selected_numbers)

    def set_elements(self, numbers):
        numbers = list(dict.fromkeys(numbers))[:MAX_COMPARE]
        els = [by_number(self.elements, n) for n in numbers]
        if len(els) < 2:
            self.table.clear()
            self.label.setText("Pick at least two elements to compare.")
            return
        rows = compare_rows(els, mass_precision=self.settings.get("mass_precision"))
        self.label.setText(
            "%s" % "  vs  ".join(e.name for e in els))
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(els) + 1)
        headers = ["Property"] + [e.symbol for e in els]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(False)
        for r, (fid, label, values) in enumerate(rows):
            item = QTableWidgetItem(label)
            item.setForeground(Qt.gray)
            f = item.font()
            f.setBold(True)
            item.setFont(f)
            self.table.setItem(r, 0, item)
            for c, v in enumerate(values):
                text = v if v not in (None, "") else "\u2014"
                self.table.setItem(r, c + 1, QTableWidgetItem(text))
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
