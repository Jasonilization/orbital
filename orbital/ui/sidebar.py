"""Category browser — the GarageBand-style left sidebar.

Element categories are the 'instrument families'; each section lists its
elements as compact rows (number, symbol, name) with a colour dot. Click
to select, arrows + Enter work throughout. Sections expand and collapse.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QSizePolicy,
)

from orbital.data import CATEGORIES

CATEGORY_ORDER = (
    "alkali metal", "alkaline earth metal", "transition metal",
    "post-transition metal", "metalloid", "nonmetal", "halogen",
    "noble gas", "lanthanide", "actinide",
)


class Sidebar(QWidget):
    element_selected = Signal(int)

    def __init__(self, elements, color_modes, parent=None):
        super().__init__(parent)
        self.elements = elements
        self.color_modes = color_modes
        self._item_numbers = {}
        self._filter_numbers = None  # set of visible atomic numbers, or None

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
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(10)
        self.tree.setUniformRowHeights(True)
        self.tree.setVerticalScrollMode(QTreeWidget.ScrollPerPixel)
        lay.addWidget(self.tree, 1)

        self.tree.itemClicked.connect(self._on_click)
        self._build()

    def set_filter(self, numbers):
        """Restrict the list to these atomic numbers (None = all 118)."""
        self._filter_numbers = numbers
        self._build()

    def _build(self):
        mode = self.color_modes.get("category")
        self.tree.clear()
        self._item_numbers = {}
        by_cat = {}
        for e in self.elements:
            if self._filter_numbers is not None and e.number not in self._filter_numbers:
                continue
            by_cat.setdefault(e.category, []).append(e)

        for cat in CATEGORY_ORDER:
            els = by_cat.get(cat, [])
            section = QTreeWidgetItem([cat.title() + " (%d)" % len(els)])
            f = section.font(0)
            f.setBold(True)
            section.setFont(0, f)
            self.tree.addTopLevelItem(section)
            section.setExpanded(True)
            for e in els:
                label = "%-2s  %s" % (e.symbol, e.name)
                item = QTreeWidgetItem([label])
                item.setToolTip(0, "%d \u00b7 %s" % (e.number, e.name))
                section.addChild(item)
                self._item_numbers[id(item)] = e.number

    def _on_click(self, item, _col):
        number = self._item_numbers.get(id(item))
        if number is not None:
            self.element_selected.emit(number)
        else:
            item.setExpanded(not item.isExpanded())

    def select_element(self, number):
        for item_id, n in self._item_numbers.items():
            if n == number:
                # find the actual widget item and select it
                for i in range(self.tree.topLevelItemCount()):
                    section = self.tree.topLevelItem(i)
                    for j in range(section.childCount()):
                        child = section.child(j)
                        if self._item_numbers.get(id(child)) == number:
                            self.tree.blockSignals(True)
                            self.tree.setCurrentItem(child)
                            self.tree.scrollToItem(child)
                            self.tree.blockSignals(False)
                            return

    def refresh_colors(self):
        # colour dots aren't drawn per-row in the tree; instead the header
        # hint carries the mode. Kept intentionally minimal.
        pass
