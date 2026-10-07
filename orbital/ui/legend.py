"""Legend bar under the table — explains what the colours mean, always."""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen, QFont
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy, QFrame


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
        c0 = QColor("#eceae4")
        c1 = QColor("#3f6a8a")
        grad.setColorAt(0.0, c0)
        grad.setColorAt(1.0, c1)
        p.fillRect(self.rect(), grad)
        p.setPen(QPen(QColor("#8a8a85")))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))


class LegendBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(6, 2, 6, 2)
        self._lay.setSpacing(10)

    def set_mode(self, mode):
        while self._lay.count():
            item = self._lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        if mode is None:
            return
        for entry in mode.legend:
            row = QHBoxLayout()
            row.setSpacing(4)
            if entry.gradient:
                sw = _GradientSwatch()
            else:
                sw = _Swatch(entry.color)
            lab = QLabel()
            if entry.gradient:
                text = "%s:  %s \u2192 %s" % (
                    entry.label, entry.low_label, entry.high_label)
                if entry.null_label:
                    text += "   (%s: grey)" % entry.null_label
                lab.setText(text)
                row.addWidget(sw)
                row.addWidget(lab)
                self._lay.addLayout(row)
                continue
            lab.setText(entry.label)
            row.addWidget(sw)
            row.addWidget(lab)
            self._lay.addLayout(row)
        self._lay.addStretch(1)
