"""Search field with a live results popup. Qt-free logic lives in
orbital.search; this is just the widget."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QStringListModel
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QLineEdit, QCompleter, QWidget, QVBoxLayout,
)

from orbital.data import by_number
from orbital.search import search


class SearchBox(QWidget):
    """Emits picked(number) when an element is chosen, and
    active_query(text) as the user types (for table highlighting)."""

    picked = Signal(int)
    active_query = Signal(str)
    escaped = Signal()

    def __init__(self, elements, parent=None):
        super().__init__(parent)
        self.elements = elements
        self._results = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Search name, symbol or number\u2026")
        self.edit.setClearButtonEnabled(True)
        self.edit.setFixedWidth(260)
        lay.addWidget(self.edit)

        self.completer = QCompleter([])
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.edit.setCompleter(self.completer)

        self.edit.textChanged.connect(self._on_text)
        self.edit.returnPressed.connect(self._on_return)
        self.completer.activated.connect(self._on_activated)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.edit.setFocus()

    def _on_text(self, text):
        self.active_query.emit(text)
        self._results = search(text, self.elements)
        labels = []
        for e in self._results[:10]:
            labels.append("%-3s %-16s %3d" % (e.symbol, e.name, e.number))
        model = QStringListModel(labels)
        self.completer.setModel(model)

    def _on_return(self):
        text = self.edit.text().strip()
        if not text:
            self.escaped.emit()
            return
        if self._results:
            self.picked.emit(self._results[0].number)

    def _on_activated(self, label):
        # user picked a completion entry; find the number from the label
        text = label.strip()
        for e in self._results:
            if text.startswith(e.symbol):
                self.picked.emit(e.number)
                return

    def select_all_and_focus(self):
        self.edit.setFocus()
        self.edit.selectAll()

    def clear_and_focus(self):
        self.edit.clear()
        self.edit.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.edit.text():
                self.edit.clear()
                self.active_query.emit("")
            else:
                self.escaped.emit()
            return
        super().keyPressEvent(event)
