"""Minimal standard icons, drawn with QPainter — no icon files, no
dependency. Only a few, each with an obvious conventional meaning:
magnifier (search), funnel (filter), gear (settings), question (help),
sun/moon (theme), flask/box/clock/layers (sections), plus.
Follows the palette text colour so it works in every theme.

Icons are cached per (name, size, colour) — and the cache is cleared at
interpreter exit, because QPixmaps surviving past the QApplication are
a textbook PySide shutdown segfault (seen on Linux + py3.10 in CI).
"""
from __future__ import annotations

import atexit

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


_CACHE = {}


def clear_icon_cache():
    """Drop cached QIcons before Qt teardown — QPixmap outliving the
    QApplication segfaults at exit on some platforms."""
    _CACHE.clear()


atexit.register(clear_icon_cache)


def icon(name: str, size: int = 16) -> QIcon:
    color = _text_color().name()
    key = (name, size, color)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    ic = _draw(name, size)
    _CACHE[key] = ic
    return ic


def _draw(name: str, size: int) -> QIcon:
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
    elif name == "sun":
        p.drawEllipse(QRectF(4.5, 4.5, 7.0, 7.0))
        for angle in range(0, 360, 30):
            t = QTransform()
            t.rotate(angle)
            a = t.map(QPointF(0, -8.0)) + QPointF(8, 8)
            b = t.map(QPointF(0, -6.2)) + QPointF(8, 8)
            p.drawLine(a, b)
    elif name == "moon":
        p.drawArc(QRectF(3.5, 2.5, 10.0, 11.0), 30 * 16, 300 * 16)
    elif name == "flask":
        p.drawLine(QPointF(6, 13.5), QPointF(10, 13.5))
        p.drawLine(QPointF(10, 13.5), QPointF(10, 7.5))
        p.drawLine(QPointF(6, 13.5), QPointF(6, 10.5))
        p.drawLine(QPointF(6, 10.5), QPointF(9.6, 3.5))
        p.drawLine(QPointF(9.6, 3.5), QPointF(10.4, 3.5))
        p.drawLine(QPointF(10.4, 3.5), QPointF(14, 10.5))
        p.drawLine(QPointF(14, 10.5), QPointF(14, 13.5))
        p.drawLine(QPointF(14, 13.5), QPointF(10, 13.5))
    elif name == "box":
        p.drawRect(QRectF(2.5, 6.5, 11.0, 7.5))
        p.drawLine(QPointF(2.5, 6.5), QPointF(8, 3.0))
        p.drawLine(QPointF(8, 3.0), QPointF(13.5, 6.5))
        p.drawLine(QPointF(6, 9.5), QPointF(10, 9.5))
    elif name == "clock":
        p.drawEllipse(QRectF(3.0, 3.0, 10.0, 10.0))
        p.drawLine(QPointF(8, 8), QPointF(8, 4.5))
        p.drawLine(QPointF(8, 8), QPointF(10.6, 9.4))
    elif name == "layers":
        p.drawRect(QRectF(3.0, 7.5, 10.0, 5.5))
        p.drawRect(QRectF(5.0, 3.5, 6.0, 3.0))
    elif name == "plus":
        p.drawLine(QPointF(3.5, 8), QPointF(12.5, 8))
        p.drawLine(QPointF(8, 3.5), QPointF(8, 12.5))
    elif name == "help":
        f = p.font()
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, "?")
    else:
        raise ValueError("unknown icon %r" % name)
    p.end()
    return QIcon(pm)
