"""The periodic table canvas: grid of element tiles with headers, markers,
keyboard grid navigation, highlighting, layout switching, drag-to-pan
and zoom."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize, QEvent, QPoint
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QSizePolicy, QScrollArea, QPushButton, QLabel,
    QFrame,
)

from orbital.ui.tiles import ElementTile, BASE_SIZE, MIN_SCALE
from orbital.ui.theme import is_dark_theme


class _MarkerCell(QPushButton):
    """The '57-71' / '89-103' placeholder cells in detached-f-block layouts."""

    def __init__(self, text, jump_to, on_click):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setToolTip("Show the %s series" % text)
        self.clicked.connect(lambda: on_click(jump_to))
        self.setStyleSheet(
            "_MarkerCell { border: 1px solid %s; border-style: dashed;"
            " color: %s; font-size: 10px; background: transparent; }"
            % ("#a8a49d", "#6f6c66")
        )


class _HeaderLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)
        f = QFont(self.font())
        f.setPointSizeF(max(7.5, f.pointSizeF() * 0.85))
        self.setFont(f)
        self.setStyleSheet("color: %s;" % ("#8a8780" if not is_dark_theme() else "#9a9da5"))


class TableView(QWidget):
    """Holds the scroll area and the grid."""

    element_selected = Signal(int)      # user activated an element
    element_context_menu = Signal(int)  # right-click on an element tile
    move_focus = Signal(object, int, int)  # internal: tile, dx, dy

    def __init__(self, elements, settings, color_modes, parent=None):
        super().__init__(parent)
        self.elements = elements
        self.settings = settings
        self.color_modes = color_modes
        self.by_number = {e.number: e for e in elements}
        self.tiles = {}
        self.cells = {}        # (row, col) -> number
        self.positions = {}    # number -> (row, col)
        self.layout_obj = None
        self._highlight = None  # set of numbers, or None
        self._selected = None

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._inner = QWidget()
        self._grid = QGridLayout(self._inner)
        self._grid.setSpacing(2)
        self._grid.setSizeConstraint(QGridLayout.SetMinimumSize)
        self._scroll.setWidget(self._inner)

        outer = QGridLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)
        self._apply_tile_scale()

        # drag-to-pan on empty table background
        self._panning = False
        self._scroll.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self._scroll.viewport():
            et = event.type()
            if et == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                if obj.childAt(event.position().toPoint()) is None:
                    self._panning = True
                    self._pan_pos = event.globalPosition().toPoint()
                    h = self._scroll.horizontalScrollBar()
                    v = self._scroll.verticalScrollBar()
                    self._pan_h, self._pan_v = h.value(), v.value()
                    obj.setCursor(Qt.ClosedHandCursor)
                    return True
            elif et == QEvent.MouseButtonRelease and self._panning:
                self._panning = False
                obj.setCursor(Qt.ArrowCursor)
                return True
            elif et == QEvent.MouseMove and self._panning:
                pos = event.globalPosition().toPoint()
                dx = pos.x() - self._pan_pos.x()
                dy = pos.y() - self._pan_pos.y()
                h = self._scroll.horizontalScrollBar()
                v = self._scroll.verticalScrollBar()
                h.setValue(self._pan_h - dx)
                v.setValue(self._pan_v - dy)
                return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------ build

    def _tile_size(self) -> QSize:
        scale = max(MIN_SCALE, self.settings.get("tile_scale") or 1.0)
        layout_id = self.layout_obj.id if self.layout_obj else "standard"
        if layout_id == "extended":
            base = QSize(60, 52)   # 32 columns stay compact
        elif layout_id == "compact":
            base = QSize(72, 62)
        else:
            base = BASE_SIZE      # 86 x 74
        return QSize(int(base.width() * scale), int(base.height() * scale))

    def _apply_tile_scale(self):
        size = self._tile_size()
        for tile in self.tiles.values():
            tile.setFixedSize(size)
        self._scroll.updateGeometry()

    def rebuild(self):
        """(Re)create the grid for the current layout."""
        self.layout_obj = self.settings_layout()
        layout = self.layout_obj
        # Detach synchronously: deleteLater alone leaves orphaned children
        # painting over the fresh grid until the event loop reaps them.
        for tile in list(self.tiles.values()):
            self._grid.removeWidget(tile)
            tile.setParent(None)
            tile.deleteLater()
        self.tiles.clear()
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self.positions = {}
        self.cells = {}

        mode = self.color_modes.get(self.settings.get("color_mode"),
                                    self.color_modes["category"])
        size = self._tile_size()
        fields = self.settings.tile_fields()
        mass_igcse = self.settings.education_level() == "igcse"

        for cell in layout.cells:
            e = self.by_number[cell.number]
            color = mode.fn(e) if mode.fn else "#c9c7c2"
            tile = ElementTile(e, fields, color, mass_igcse=mass_igcse)
            tile.setFixedSize(size)
            tile.setAccessibleName(tile.accessible_name())
            tile.clicked.connect(self._on_tile_clicked)
            tile.move_requested.connect(self._on_move_requested)
            tile.context.connect(self.element_context_menu)
            self.tiles[cell.number] = tile
            self.positions[cell.number] = (cell.row, cell.col)
            self.cells[(cell.row, cell.col)] = cell.number
            self._grid.addWidget(tile, cell.row + 1, cell.col + 1)

        for marker in layout.markers:
            m = _MarkerCell(marker.text, marker.jump_to, self._on_marker_clicked)
            self._grid.addWidget(m, marker.row + 1, marker.col + 1)

        # headers
        for col, label in (layout.column_labels or {}).items():
            lab = _HeaderLabel(label)
            self._grid.addWidget(lab, 0, col + 1, Qt.AlignCenter)
        for row, label in enumerate(layout.row_labels):
            if label:
                lab = _HeaderLabel(label)
                self._grid.addWidget(lab, row + 1, 0, Qt.AlignCenter)

        # corner spacer keeps headers aligned
        self._grid.setColumnMinimumWidth(0, 22)
        self._grid.setRowMinimumHeight(0, 16)
        if layout.spacer_after_row is not None:
            self._grid.setRowMinimumHeight(layout.spacer_after_row + 1 + 1, 14)

        self.refresh_colors()
        self.refresh_highlight()
        if self._selected in self.tiles:
            self.tiles[self._selected].set_selected(True)

    def settings_layout(self):
        from orbital.layouts import build_layout, DEFAULT_LAYOUT, LAYOUTS
        lid = self.settings.get("layout")
        if lid not in LAYOUTS:
            lid = DEFAULT_LAYOUT
        return build_layout(lid, self.elements)

    # ------------------------------------------------------------------ state

    def set_color_modes(self, color_modes):
        self.color_modes = color_modes
        self.refresh_colors()

    def refresh_colors(self):
        mode = self.color_modes.get(self.settings.get("color_mode"),
                                    self.color_modes["category"])
        for number, tile in self.tiles.items():
            tile.set_color(mode.fn(self.by_number[number]))

    def refresh_highlight(self):
        for number, tile in self.tiles.items():
            if self._highlight is None:
                tile.set_dimmed(False)
            else:
                tile.set_dimmed(number not in self._highlight)

    def set_highlight(self, numbers):
        """numbers: set of visible/normal elements, or None for all."""
        self._highlight = numbers
        self.refresh_highlight()

    def select_element(self, number, scroll=True):
        if self._selected is not None and self._selected in self.tiles:
            self.tiles[self._selected].set_selected(False)
        self._selected = number
        if number in self.tiles:
            tile = self.tiles[number]
            tile.set_selected(True)
            if scroll:
                self._scroll.ensureWidgetVisible(tile, 60, 60)

    def focus_element(self, number):
        if number in self.tiles:
            self.tiles[number].setFocus(Qt.OtherFocusReason)

    def focus_position(self, pos):
        number = self.cells.get(pos)
        if number is not None:
            self.focus_element(number)
            return True
        return False

    def clear_focus(self):
        self._inner.clearFocus()

    # ------------------------------------------------------------------ input

    def _on_tile_clicked(self, number):
        self.select_element(number, scroll=False)
        self.element_selected.emit(number)

    def _on_marker_clicked(self, number):
        self.select_element(number)
        self.element_selected.emit(number)

    def _on_move_requested(self, tile, dx, dy):
        pos = self.positions.get(tile.element.number)
        if pos is None:
            return
        row, col = pos
        candidates = []
        for other_number, (r, c) in self.positions.items():
            if dx and ((dx > 0 and c > col) or (dx < 0 and c < col)) and r == row:
                candidates.append((abs(c - col), c, other_number))
            if dy and ((dy > 0 and r > row) or (dy < 0 and r < row)) and c == col:
                candidates.append((abs(r - row), r, other_number))
        if not candidates:
            # fall back: nearest tile strictly in that direction
            for other_number, (r, c) in self.positions.items():
                if dx > 0 and c > col:
                    candidates.append((1000 + (c - col) + abs(r - row) * 3, c, other_number))
                elif dx < 0 and c < col:
                    candidates.append((1000 + (col - c) + abs(r - row) * 3, c, other_number))
                elif dy > 0 and r > row:
                    candidates.append((1000 + (r - row) + abs(c - col) * 3, c, other_number))
                elif dy < 0 and r < row:
                    candidates.append((1000 + (row - r) + abs(c - col) * 3, c, other_number))
        if candidates:
            candidates.sort()
            self.focus_element(candidates[0][2])
