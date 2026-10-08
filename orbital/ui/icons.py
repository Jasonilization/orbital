"""Minimal standard icons, drawn with QPainter — no icon files, no
dependency. Only four, each with an obvious conventional meaning:
magnifier (search), funnel (filter), gear (settings), question (help).
Follows the palette text colour so it works in every theme.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (QIcon, QPainter, QPen, QColor, QPixmap, QPalette,
                          QTransform)
from PySide6.QtWidgets import QApplication


def _text_color() -> QColor:
    pal = QApplication.palette() if QApplication.instance() else None
    if pal is not None:
        c = pal.color(QPalette.Text)
        if c.isValid():
            return c
    return QColor("#1c1c19")


def icon(name: str, size: int = 16) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(_text_color(), 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)

    if name == "search":
        p.drawEllipse(QRectF(3.0, 3.0, 8.0, 8.0))
        p.drawLine(QPointF(10.5, 10.5), QPointF(13.5, 13.5))
    elif name == "filter":
        p.drawLine(QPointF(2.5, 4.0), QPointF(13.5, 4.0))
        p.drawLine(QPointF(5.0, 8.0), QPointF(11.0, 8.0))
        p.drawLine(QPointF(7.0, 12.0), QPointF(9.0, 12.0))
    elif name == "settings":
        p.drawEllipse(QRectF(4.5, 4.5, 7.0, 7.0))
        for angle in range(0, 360, 45):
            t = QTransform()
            t.rotate(angle)
            a = t.map(QPointF(0, -6.0)) + QPointF(8, 8)
            b = t.map(QPointF(0, -5.0)) + QPointF(8, 8)
            p.drawLine(a, b)
        p.drawEllipse(QRectF(7.0, 7.0, 2.0, 2.0))
    elif name == "help":
        f = p.font()
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, "?")
    else:
        raise ValueError("unknown icon %r" % name)
    p.end()
    return QIcon(pm)
