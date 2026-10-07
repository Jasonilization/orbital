"""The element tile: a small custom widget painting the configured fields.

Fields (top to bottom): number, symbol, mass, name, state — the tile
preset decides which appear and in what order. The tile paints itself in
one pass; 118 of these render instantly.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QFont, QPen, QPalette
from PySide6.QtWidgets import QWidget

from orbital.ui.theme import is_dark_theme, readable_text_on


class ElementTile(QWidget):
    clicked = Signal(int)          # atomic number, left click / Enter
    context = Signal(int)          # context menu requested
    move_requested = Signal(object, int, int)  # tile, dx, dy — grid navigation

    def __init__(self, element, fields, color, parent=None):
        super().__init__(parent)
        self.element = element
        self.fields = list(fields)
        self._color = color
        self._selected = False
        self._dimmed = False
        self._hover = False
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setToolTip(self._tooltip())

    # -- state ---------------------------------------------------------------

    def set_color(self, hexcolor):
        self._color = hexcolor
        self.update()

    def set_selected(self, on):
        if self._selected != on:
            self._selected = on
            self.update()

    def set_dimmed(self, on):
        if self._dimmed != on:
            self._dimmed = on
            self.update()

    def _tooltip(self):
        e = self.element
        parts = ["%d. %s (%s)" % (e.number, e.name, e.symbol)]
        if e.category:
            parts.append(e.category.title())
        if e.atomic_mass:
            parts.append("A\u1d63 = %s" % e.mass_string())
        parts.append(e.state_string().lower())
        return "\n".join(parts)

    # -- Qt ------------------------------------------------------------------

    def accessible_name(self):
        e = self.element
        return "%d %s, symbol %s, %s" % (e.number, e.name, e.symbol,
                                         e.state_string().lower())

    def sizeHint(self):
        return QSize(78, 66)

    def minimumSizeHint(self):
        return QSize(46, 40)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.element.number)
        self.setFocus(Qt.MouseFocusReason)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        self.context.emit(self.element.number)
        event.accept()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.clicked.emit(self.element.number)
            return
        deltas = {
            Qt.Key_Left: (-1, 0), Qt.Key_Right: (1, 0),
            Qt.Key_Up: (0, -1), Qt.Key_Down: (0, 1),
        }
        d = deltas.get(event.key())
        if d:
            self.move_requested.emit(self, d[0], d[1])
            return
        super().keyPressEvent(event)

    # -- painting ------------------------------------------------------------

    def paintEvent(self, event):
        e = self.element
        w, h = self.width(), self.height()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setRenderHint(QPainter.TextAntialiasing, True)

        base = QColor(self._color)
        if base.lightness() > 250:  # mode returned near-white; clamp
            base = QColor("#c9c7c2")
        if self._hover:
            base = base.lighter(106) if not is_dark_theme() else base.lighter(112)

        # fill — dimmed tiles blend toward the window colour and paint
        # opaque, so nothing underneath can ever bleed through
        rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        if self._dimmed:
            pal = self.palette()
            win_c = pal.color(QPalette.Window)
            base = QColor(
                int(base.red() * 0.14 + win_c.red() * 0.86),
                int(base.green() * 0.14 + win_c.green() * 0.86),
                int(base.blue() * 0.14 + win_c.blue() * 0.86),
            )
        p.fillRect(rect, base)
        if self._dimmed:
            p.setOpacity(0.38)
        text = readable_text_on(base)
        p.setPen(text)

        small = QFont(self.font())
        small.setPointSizeF(max(6.5, self.font().pointSizeF() * 0.78))
        bold = QFont(self.font())
        bold.setBold(True)

        # dynamic layout: number pinned top-left, symbol centre-left,
        # remaining fields distributed under the symbol
        pad = 4
        x_text = pad + 1
        if "number" in self.fields:
            f = QFont(small)
            p.setFont(f)
            p.drawText(self.rect().adjusted(x_text, 2, -2, 0),
                       Qt.TextSingleLine, str(e.number))
            top = 2 + p.fontMetrics().height() - 2
        else:
            top = pad

        has_name = "name" in self.fields
        has_state = "state" in self.fields

        # symbol: as large as space allows
        size_avail = h - top - (16 if has_name or "mass" in self.fields else 6)
        sym_size = max(10, min(21, size_avail * 0.42))
        bf = QFont(bold)
        bf.setPointSizeF(sym_size)
        p.setFont(bf)
        y = top + 1
        p.drawText(self.rect().adjusted(x_text, y, -2, 0),
                   Qt.TextSingleLine, e.symbol)
        y += p.fontMetrics().height() - 3

        p.setFont(QFont(small))
        if "mass" in self.fields:
            p.drawText(self.rect().adjusted(x_text, y, -2, 0), Qt.TextSingleLine,
                       e.mass_string())
            y += p.fontMetrics().height() - 2
        if has_state:
            p.drawText(self.rect().adjusted(x_text, y, -2, 0), Qt.TextSingleLine,
                      e.state_string()[0])  # S / L / G initial
            y += p.fontMetrics().height() - 2
        if "config" in self.fields and h > 74:
            p.drawText(self.rect().adjusted(x_text, y, -2, 0), Qt.TextSingleLine,
                       e.electron_configuration)
        if has_name:
            p.drawText(QRectF(2, h - 15, w - 4, 13),
                       Qt.AlignHCenter | Qt.AlignBottom | Qt.TextSingleLine,
                       e.name)

        p.setOpacity(1.0 if not self._dimmed else 0.45)

        # borders: structure over decoration
        pen = QPen(QColor("#8a8a85") if not is_dark_theme() else QColor("#54575e"))
        pen.setWidthF(1)
        p.setPen(pen)
        p.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))

        if self._selected:
            pen = QPen(self.palette().color(self.foregroundRole()))
            pen.setWidthF(2.4)
            p.setPen(pen)
            p.drawRect(rect.adjusted(1.4, 1.4, -1.4, -1.4))

        if self.hasFocus():
            pen = QPen(self.palette().color(self.foregroundRole()), 1, Qt.DashLine)
            p.setPen(pen)
            p.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))
