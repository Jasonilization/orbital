"""Legend bar under the table — explains what the colours mean, always.
Entries wrap onto multiple rows instead of overlapping on narrow windows
(simple flow layout)."""
from __future__ import annotations

from PySide6.QtCore import Qt, QRect, QSize, QPoint
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QSizePolicy, QFrame, QLayout, QLayoutItem,
)


class FlowLayout(QLayout):
    """Lays children out left-to-right, wrapping to new rows as needed."""

    def __init__(self, parent=None, margin=6, spacing=10):
        super().__init__(parent)
        self.setContentsMargins(margin, 2, margin, 2)
        self._spacing = spacing
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return QSize(size.width() + m.left() + m.right(),
                     size.height() + m.top() + m.bottom())

    def _do_layout(self, rect, test):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        line_height = 0
        right = rect.right() - m.right()
        for item in self._items:
            hint = item.sizeHint()
            next_x = x + hint.width()
            if next_x > right and line_height > 0:
                x = rect.x() + m.left()
                y = y + line_height + self._spacing
                next_x = x + hint.width()
                line_height = 0
            if not test:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x + self._spacing
            line_height = max(line_height, hint.height())
        return y + line_height + m.bottom() - rect.y()


class _Swatch(QFrame):
    def __init__(self, hexcolor, parent=None):
        super().__init__(parent)
        self.color = QColor(hexcolor)
        self.setFixedSize(14, 14)
        self.setFrameShape(QFrame.Box)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), self.color)
        p.setPen(QPen(QColor("#8a8a85")))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))


class _GradientSwatch(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 14)

    def paintEvent(self, event):
        p = QPainter(self)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, QColor("#eceae4"))
        grad.setColorAt(1.0, QColor("#3f6a8a"))
        p.fillRect(self.rect(), grad)
        p.setPen(QPen(QColor("#8a8a85")))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))


class LegendBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lay = FlowLayout(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def set_mode(self, mode):
        while self._lay.count():
            item = self._lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        if mode is None:
            return
        for entry in mode.legend:
            if entry.gradient:
                text = "%s: %s \u2192 %s" % (
                    entry.label, entry.low_label, entry.high_label)
                if entry.null_label:
                    text += "  (%s: grey)" % entry.null_label
                self._lay.addWidget(_GradientSwatch())
                self._lay.addWidget(QLabel(text))
                continue
            self._lay.addWidget(_Swatch(entry.color))
            self._lay.addWidget(QLabel(entry.label))
