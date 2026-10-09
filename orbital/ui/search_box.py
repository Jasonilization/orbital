"""Search field with a live results popup. Qt-free logic lives in
orbital.search; this is just the widget."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLineEdit, QWidget, QVBoxLayout

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

        self.edit.textChanged.connect(self._on_text)
        self.edit.returnPressed.connect(self._on_return)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.edit.setFocus()

    def _on_text(self, text):
        self.active_query.emit(text)
        self._results = search(text, self.elements)

    def _on_return(self):
        text = self.edit.text().strip()
        if not text:
            self.escaped.emit()
            return
        if self._results:
            self.picked.emit(self._results[0].number)

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
