"""Category browser — the GarageBand-style left sidebar.

GarageBand's library shows instrument families as sections, each row an
icon + name. Orbital's version: element categories as bold section
headers (with counts), each element row painted with a coloured symbol
chip — the tile colour of that element — plus the name and number.

A QItemDelegate paints the chips so the tree keeps native keyboard
navigation, selection and filtering.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QFont, QPen, QPalette
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel,
    QStyledItemDelegate, QStyle, QStyleOptionViewItem,
)

from orbital.data import CATEGORIES
from orbital.ui.theme import is_dark_theme, readable_text_on

CATEGORY_ORDER = (
    "alkali metal", "alkaline earth metal", "transition metal",
    "post-transition metal", "metalloid", "nonmetal", "halogen",
    "noble gas", "lanthanide", "actinide",
)

CHIP = 26
CHIP_PAD = 7


class _RowData:
    """Per-item paint data (avoids per-paint lookups)."""
    __slots__ = ("kind", "symbol", "number", "chip_color", "count", "title")

    def __init__(self, kind, symbol="", number=0, chip_color="#c9c7c2",
                 count=0, title=""):
        self.kind = kind
        self.symbol = symbol
        self.number = number
        self.chip_color = chip_color
        self.count = count
        self.title = title


class SidebarDelegate(QStyledItemDelegate):
    """Paints: section headers (bold, larger) and element rows (chip +
    symbol, name, number on the right)."""

    def paint(self, painter, option, index):
        data = index.data(Qt.UserRole)
        if data is None:
            super().paint(painter, option, index)
            return
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        # selection / focus background from the style, then our content on top
        opt.widget.style().drawControl(QStyle.CE_ItemViewItem, opt, painter,
                                       opt.widget)

        rect = opt.rect
        if data.kind == "header":
            font = QFont(opt.font)
            font.setBold(True)
            font.setPointSizeF(opt.font.pointSizeF() * 1.02)
            painter.setFont(font)
            painter.setPen(opt.palette.color(QPalette.Text))
            label = data.title if not data.count else "%s  (%d)" % (
                data.title, data.count)
            painter.drawText(rect.adjusted(CHIP_PAD + 2, 0, -8, 0),
                             Qt.AlignVCenter | Qt.AlignLeft, label)
        else:
            # coloured symbol chip
            chip = QRectF(rect.left() + CHIP_PAD,
                          rect.center().y() - CHIP / 2.0, CHIP, CHIP)
            color = QColor(data.chip_color)
            painter.setBrush(color)
            painter.setPen(QPen(QColor("#8a8a85") if not is_dark_theme()
                                else QColor("#54575e"), 1))
            painter.drawRoundedRect(chip, 4.0, 4.0)
            painter.setBrush(Qt.NoBrush)
            f = QFont(opt.font)
            f.setBold(True)
            f.setPointSizeF(opt.font.pointSizeF() * 0.95)
            painter.setFont(f)
            painter.setPen(readable_text_on(color))
            painter.drawText(chip, Qt.AlignCenter, data.symbol)
            # element name + number
            painter.setPen(opt.palette.color(QPalette.Text))
            name_font = QFont(opt.font)
            name_font.setBold(False)
            painter.setFont(name_font)
            painter.drawText(rect.adjusted(CHIP_PAD * 2 + CHIP, 0, -34, 0),
                             Qt.AlignVCenter | Qt.AlignLeft, data.title)
            f2 = QFont(opt.font)
            f2.setPointSizeF(opt.font.pointSizeF() * 0.9)
            painter.setFont(f2)
            painter.setPen(opt.palette.color(QPalette.Text))
            painter.drawText(rect.adjusted(0, 0, -CHIP_PAD - 2, 0),
                             Qt.AlignVCenter | Qt.AlignRight,
                             str(data.number))
        painter.restore()

    def sizeHint(self, option, index):
        data = index.data(Qt.UserRole)
        base = super().sizeHint(option, index)
        if data is not None and data.kind == "row":
            return QSize(base.width(), max(base.height(), CHIP + 8))
        return base


class Sidebar(QWidget):
    element_selected = Signal(int)

    def __init__(self, elements, color_modes, parent=None):
        super().__init__(parent)
        self.elements = elements
        self.color_modes = color_modes
        self._item_numbers = {}
        self._items_by_number = {}
        self._filter_numbers = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        header = QLabel("Elements")
        f = QFont(header.font())
        f.setBold(True)
        header.setFont(f)
        lay.addWidget(header)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(0)
        self.tree.setUniformRowHeights(False)
        self.tree.setVerticalScrollMode(QTreeWidget.ScrollPerPixel)
        self.tree.setItemDelegate(SidebarDelegate(self.tree))
        lay.addWidget(self.tree, 1)

        self.tree.itemClicked.connect(self._on_click)
        self._build()

    # ------------------------------------------------------------------ data

    def set_filter(self, numbers):
        """Restrict the list to these atomic numbers (None = all 118)."""
        self._filter_numbers = numbers
        self._build()

    def _chip_color(self, element):
        mode = self.color_modes.get("category")
        if mode and mode.fn:
            return mode.fn(element)
        return "#c9c7c2"

    def _build(self):
        self.tree.clear()
        self._item_numbers = {}
        self._items_by_number = {}
        by_cat = {}
        for e in self.elements:
            if self._filter_numbers is not None and e.number not in self._filter_numbers:
                continue
            by_cat.setdefault(e.category, []).append(e)

        for cat in CATEGORY_ORDER:
            els = by_cat.get(cat, [])
            if not els:
                continue
            section = QTreeWidgetItem([""])
            section.setData(0, Qt.UserRole, _RowData(
                "header", title=cat.title(), count=len(els)))
            section.setFlags(Qt.ItemIsEnabled)  # header: not selectable
            self.tree.addTopLevelItem(section)
            section.setExpanded(True)
            for e in els:
                item = QTreeWidgetItem([""])
                item.setData(0, Qt.UserRole, _RowData(
                    "row", symbol=e.symbol, number=e.number,
                    chip_color=self._chip_color(e), title=e.name))
                item.setToolTip(0, "%d \u00b7 %s" % (e.number, e.name))
                section.addChild(item)
                self._item_numbers[id(item)] = e.number
                self._items_by_number[e.number] = item

    # ------------------------------------------------------------------ input

    def _on_click(self, item, _col):
        number = self._item_numbers.get(id(item))
        if number is not None:
            self.element_selected.emit(number)
        else:
            item.setExpanded(not item.isExpanded())

    def select_element(self, number):
        item = self._items_by_number.get(number)
        if item is not None:
            self.tree.blockSignals(True)
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)
            self.tree.blockSignals(False)
