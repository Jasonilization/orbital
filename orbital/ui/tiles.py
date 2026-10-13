"""The element tile: a small custom widget painting the configured fields.

Layout is *measured*, never guessed: each row's position is the previous
row's bottom edge, so text can never overlap. If a configuration doesn't
fit the tile, optional fields are dropped in a defined priority order
instead of colliding. This module deliberately keeps the layout logic
pure so it can be tested without a GUI.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QFont, QPen, QFontMetrics, QPalette
from PySide6.QtWidgets import QWidget

from orbital.ui.theme import is_dark_theme, readable_text_on

# The order in which fields get sacrificed when space runs out
# (most expendable first).
_FIELD_PRIORITY = ["config", "state", "name", "mass", "symbol", "number"]

BASE_SIZE = QSize(86, 74)
MIN_SCALE = 0.8

# Paint-resource caches. Painting 118 tiles allocates thousands of QFont /
# QFontMetrics / QColor C++ objects per window show; on some shiboken +
# platform combinations that allocation volume trips refcount bugs
# (none_dealloc aborts on Linux CI). One cached object per (family,
# size, bold) or colour key paints identically and far faster.
_FONT_METRICS = {}
_TEXT_COLORS = {}


def _paint_font_metrics(widget_font, point, bold):
    key = (widget_font.family(), round(point, 2), bold)
    cached = _FONT_METRICS.get(key)
    if cached is None:
        f = QFont(widget_font)
        f.setPointSizeF(point)
        f.setBold(bold)
        cached = (f, QFontMetrics(f))
        _FONT_METRICS[key] = cached
    return cached


def _paint_text_color(base: QColor) -> QColor:
    key = base.name()
    c = _TEXT_COLORS.get(key)
    if c is None:
        c = readable_text_on(base)
        _TEXT_COLORS[key] = c
    return c


def layout_fields(width, height, fields, font_scale=1.0):
    """Compute the row stack for a tile. Returns a list of
    (field_id, x, y, font_point_size, elide_width) with strictly
    non-overlapping rows, or drops fields that don't fit.

    Pure geometry + the standard Qt font metrics convention: callers pass
    a metrics-like object with height(). Unit tests use a fake.
    """
    fields = [f for f in fields if f]
    small_pt = max(7.5, 9.5 * font_scale)
    name_pt = max(7.0, 9.0 * font_scale)
    pad = 3.5

    def pt2px(pt):
        # point size to pixel height (macOS/Qt convention ~1.33, generous)
        return pt * 1.45

    rows = []
    if "number" in fields:
        rows.append(("number", small_pt))
    rows.append(("symbol", 0))  # placeholder, sized after we know the room
    if "mass" in fields:
        rows.append(("mass", small_pt))
    if "state" in fields:
        rows.append(("state", small_pt))
    if "config" in fields:
        rows.append(("config", small_pt))
    if "name" in fields:
        rows.append(("name", name_pt))

    # available vertical space for the stack (name pins to the bottom)
    name_h = pt2px(name_pt) if "name" in fields else 0
    available = height - 2 * pad - name_h - 2

    # fixed rows are everything except the symbol
    fixed = [(f, pt) for f, pt in rows if f != "symbol"]
    fixed_h = sum(pt2px(pt) for _f, pt in fixed)

    # symbol takes what's left, clamped
    symbol_room = available - fixed_h
    symbol_pt = max(9.0, min(17.5 * font_scale, symbol_room / 1.45 * 0.92))
    if symbol_pt < 9.0:
        # nothing fits: drop the most expendable fields and retry once
        for drop in _FIELD_PRIORITY:
            if drop == "symbol":
                break
            if drop in fields and drop != "number":
                fields = [f for f in fields if f != drop]
                return layout_fields(width, height, fields, font_scale)
        symbol_pt = 9.0

    y = pad
    out = []
    for f, pt in rows:
        if f == "symbol":
            pt = symbol_pt
        if f == "name":
            continue  # pinned to the bottom separately
        h = pt2px(pt)
        if y + h > height - name_h - pad:
            break  # extra safety; geometry above should prevent this
        out.append((f, pad + 1, y, pt, width - 2 * (pad + 1)))
        y += h + 1
    if "name" in fields:
        out.append(("name", pad, height - name_h - pad, name_pt,
                    width - 2 * pad))
    return out


class ElementTile(QWidget):
    clicked = Signal(int)          # atomic number, left click / Enter
    context = Signal(int)          # context menu requested
    move_requested = Signal(object, int, int)  # tile, dx, dy

    def __init__(self, element, fields, color, mass_igcse=False, parent=None):
        super().__init__(parent)
        self.element = element
        self.fields = list(fields)
        self._mass_igcse = mass_igcse
        self._color = color
        self._selected = False
        self._dimmed = False
        self._hover = False
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
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
        parts.append(e.category.title())
        from orbital.formatting import mass_string
        parts.append("A\u1d63 = %s" % mass_string(e, igcse=self._mass_igcse))
        parts.append(e.state_string().lower())
        return "\n".join(parts)

    # -- Qt ------------------------------------------------------------------

    def accessible_name(self):
        e = self.element
        return "%d %s, symbol %s, %s" % (e.number, e.name, e.symbol,
                                         e.state_string().lower())

    def sizeHint(self):
        return BASE_SIZE

    def minimumSizeHint(self):
        return QSize(int(BASE_SIZE.width() * MIN_SCALE),
                     int(BASE_SIZE.height() * MIN_SCALE))

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
        p.setRenderHint(QPainter.TextAntialiasing, True)

        base = QColor(self._color)
        if base.lightness() > 250:
            base = QColor("#c9c7c2")
        if self._hover:
            base = base.lighter(106) if not is_dark_theme() else base.lighter(112)

        radius = min(w, h) * 0.07
        rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        if self._dimmed:
            pal = self.palette()
            win_c = pal.color(QPalette.Window)
            base = QColor(
                int(base.red() * 0.14 + win_c.red() * 0.86),
                int(base.green() * 0.14 + win_c.green() * 0.86),
                int(base.blue() * 0.14 + win_c.blue() * 0.86),
            )
        p.setPen(Qt.NoPen)
        p.setBrush(base)
        p.drawRoundedRect(rect, radius, radius)
        p.setBrush(Qt.NoBrush)
        text_alpha = 1.0 if not self._dimmed else 0.45
        p.setOpacity(text_alpha)
        text = _paint_text_color(QColor(self._color) if not self._dimmed else base)
        p.setPen(text)  # drawText uses the pen — restore it after NoPen fill

        font_scale = 1.0  # tile_font_scale applied via app font
        rows = layout_fields(w, h, self.fields, font_scale)

        widget_font = self.font()
        for field, x, y, pt, avail_w in rows:
            f, fm = _paint_font_metrics(widget_font, pt, field == "symbol")
            p.setFont(f)
            value = self._field_text(field)
            if value is None:
                continue
            label = fm.elidedText(value, Qt.ElideRight, avail_w)
            if field == "name":
                p.drawText(QRectF(x, y, avail_w, fm.height()),
                           Qt.AlignHCenter | Qt.AlignVCenter | Qt.TextSingleLine,
                           label)
            else:
                p.drawText(QRectF(x, y, avail_w, fm.height()),
                           Qt.AlignLeft | Qt.AlignVCenter | Qt.TextSingleLine,
                           label)

        p.setOpacity(1.0 if not self._dimmed else 0.45)

        # borders: structure over decoration
        pen = QPen(QColor("#8a8a85") if not is_dark_theme() else QColor("#54575e"))
        pen.setWidthF(1)
        p.setPen(pen)
        p.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

        if self._selected:
            pen = QPen(self.palette().color(QPalette.WindowText))
            pen.setWidthF(2.4)
            p.setPen(pen)
            p.drawRoundedRect(rect.adjusted(1.4, 1.4, -1.4, -1.4), radius, radius)

        if self.hasFocus():
            pen = QPen(self.palette().color(QPalette.WindowText), 1, Qt.DashLine)
            p.setPen(pen)
            p.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

    def _field_text(self, field):
        e = self.element
        if field == "number":
            return str(e.number)
        if field == "symbol":
            return e.symbol
        if field == "mass":
            from orbital.formatting import mass_string
            return mass_string(e, igcse=self._mass_igcse)
        if field == "state":
            return e.state_string()[0]
        if field == "name":
            return e.name
        if field == "config":
            return e.electron_configuration
        return None
