"""Main window: table + category sidebar + detail panel, menus, toolbar,
status bar, filters, compare and settings wiring."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QComboBox, QPushButton, QLabel, QMenu, QMessageBox, QFileDialog,
    QApplication, QSizePolicy, QLineEdit,
)

from orbital.data import load_elements, by_number
from orbital.filters import FilterSpec, apply_filter, matching_numbers
from orbital.layouts import LAYOUTS
from orbital.profiles import EDUCATION_LEVELS
from orbital.search import search as do_search
from orbital.ui.colors import build_color_modes, DEFAULT_MODE
from orbital.ui.detail_panel import DetailPanel
from orbital.ui.icons import icon as _icon
from orbital.ui.tiles import BASE_SIZE, MIN_SCALE

BASE_W = BASE_SIZE.width()
from orbital.ui.filter_popover import FilterDialog
from orbital.ui.compare_dialog import CompareDialog
from orbital.ui.legend import LegendBar
from orbital.ui.search_box import SearchBox
from orbital.ui.settings_dialog import SettingsDialog
from orbital.ui.sidebar import Sidebar
from orbital.ui.table_view import TableView
from orbital.ui.theme import apply_theme
from orbital.formatting import field_value


class MainWindow(QMainWindow):
    def __init__(self, settings, elements=None):
        super().__init__()
        self.settings = settings
        self.elements = elements or load_elements()
        self.color_modes = build_color_modes(self.elements)
        self.filter_spec = FilterSpec()
        self.compare_selection = []
        self.filter_dialog = None
        self.compare_dialog = None
        self._search_text = ""

        self.setWindowTitle("Orbital")
        self.resize(1280, 800)
        self.setMinimumSize(980, 560)

        self._build_ui()
        self._build_menus()
        self._apply_state()
        self.settings.changed.connect(self._on_setting_changed)

    # ------------------------------------------------------------------ ui

    def _build_ui(self):
        # toolbar -------------------------------------------------------------
        from orbital.ui.icons import icon as _icon

        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        def label(text):
            lab = QLabel(" " + text)
            f = lab.font()
            f.setBold(True)
            lab.setFont(f)
            return lab

        self.toolbar.addWidget(label("Level"))
        self.level_combo = QComboBox()
        for lid, prof in EDUCATION_LEVELS.items():
            self.level_combo.addItem(prof["label"], lid)
            self.level_combo.setItemData(
                self.level_combo.count() - 1, prof["description"], Qt.ToolTipRole)
        self.level_combo.setToolTip("How much detail each element shows")
        self.level_combo.setMinimumWidth(100)
        self.level_combo.setCurrentText(
            EDUCATION_LEVELS[self.settings.education_level()]["label"])
        self.level_combo.currentIndexChanged.connect(self._on_level_combo)
        self.toolbar.addWidget(self.level_combo)

        self.toolbar.addWidget(label("Layout"))
        self.layout_combo = QComboBox()
        for lid, builder in LAYOUTS.items():
            self.layout_combo.addItem(lid.title(), lid)
        self.layout_combo.setToolTip("Table layout")
        self.layout_combo.setMinimumWidth(90)
        self.layout_combo.setCurrentText(self.settings.get("layout").title())
        self.layout_combo.currentIndexChanged.connect(self._on_layout_combo)
        self.toolbar.addWidget(self.layout_combo)

        self.toolbar.addWidget(label("Colour"))
        self.color_combo = QComboBox()
        for mid, mode in self.color_modes.items():
            self.color_combo.addItem(mode.name, mid)
        self.color_combo.setToolTip("What the tile colours mean (legend below the table)")
        self.color_combo.setMinimumWidth(120)
        self.color_combo.setCurrentText(
            self.color_modes.get(self.settings.get("color_mode"),
                                 self.color_modes[DEFAULT_MODE]).name)
        self.color_combo.currentIndexChanged.connect(self._on_color_combo)
        self.toolbar.addWidget(self.color_combo)

        self.filter_button = QPushButton(_icon("filter"), "Filter")
        self.filter_button.setCheckable(True)
        self.filter_button.setToolTip("Show only elements matching…")
        self.filter_button.clicked.connect(self._toggle_filter_dialog)
        self.toolbar.addWidget(self.filter_button)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)

        self.settings_button = QPushButton(_icon("settings"), "")
        self.settings_button.setToolTip("Settings (Ctrl+,)")
        self.settings_button.clicked.connect(self._open_settings)
        self.toolbar.addWidget(self.settings_button)

        self.help_button = QPushButton(_icon("help"), "")
        self.help_button.setToolTip("Keyboard shortcuts (Ctrl+/)")
        self.help_button.clicked.connect(self._show_shortcuts)
        self.toolbar.addWidget(self.help_button)

        self.search_box = SearchBox(self.elements)
        self.search_box.edit.addAction(
            _icon("search"), QLineEdit.LeadingPosition)
        self.search_box.picked.connect(self._on_search_picked)
        self.search_box.active_query.connect(self._on_search_query)
        self.search_box.escaped.connect(self._clear_search)
        self.toolbar.addWidget(self.search_box)

        # central --------------------------------------------------------------
        self.splitter = QSplitter(Qt.Horizontal)

        self.sidebar = Sidebar(self.elements, self.color_modes)
        self.sidebar.element_selected.connect(
            lambda n: self.select_element(n, scroll=True))
        self.sidebar.setMinimumWidth(150)
        self.sidebar.setMaximumWidth(230)
        self.splitter.addWidget(self.sidebar)

        centre = QWidget()
        centre_lay = QVBoxLayout(centre)
        centre_lay.setContentsMargins(4, 4, 4, 0)
        centre_lay.setSpacing(2)
        self.table = TableView(self.elements, self.settings, self.color_modes)
        self.table.rebuild()
        self.table.element_selected.connect(
            lambda n: self.select_element(n, scroll=False))
        centre_lay.addWidget(self.table, 1)
        self.legend = LegendBar()
        centre_lay.addWidget(self.legend)
        self.legend.set_mode(
            self.color_modes.get(self.settings.get("color_mode"),
                                 self.color_modes[DEFAULT_MODE]))
        self.splitter.addWidget(centre)

        self.panel = DetailPanel(self.settings)
        self.panel.setMinimumWidth(260)
        self.panel.compare_requested.connect(self._add_to_compare)
        self.splitter.addWidget(self.panel)

        self.splitter.setSizes([190, 700, 310])
        self.setCentralWidget(self.splitter)
        # On first run, size tiles so the standard table fits the window
        # instead of forcing horizontal scrolling on laptops.
        QTimer.singleShot(0, self._fit_tiles_first_run)

        # status bar -----------------------------------------------------------
        self.status_left = QLabel("")
        self.statusBar().addWidget(self.status_left, 1)
        self.status_filter = QPushButton("")
        self.status_filter.setFlat(True)
        self.status_filter.clicked.connect(self._clear_filters)
        self.status_filter.setVisible(False)
        self.statusBar().addPermanentWidget(self.status_filter)

    # ------------------------------------------------------------------ menus

    def _build_menus(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        export = QAction("Export table as image\u2026", self)
        export.setShortcut("Ctrl+Shift+E")
        export.triggered.connect(self._export_png)
        file_menu.addAction(export)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setMenuRole(QAction.QuitRole)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = mb.addMenu("View")
        layout_menu = view_menu.addMenu("Table layout")
        group = QActionGroup(self)
        for i, lid in enumerate(LAYOUTS, start=1):
            act = QAction(lid.title(), self, checkable=True)
            act.setData(lid)
            act.setShortcut("Ctrl+%d" % i)
            act.setChecked(lid == self.settings.get("layout"))
            act.triggered.connect(lambda checked=False, a=act: self._set_layout(a.data()))
            group.addAction(act)
            layout_menu.addAction(act)
        self._layout_actions = group.actions()

        colour_menu = view_menu.addMenu("Colour by")
        cgroup = QActionGroup(self)
        for mid, mode in self.color_modes.items():
            act = QAction(mode.name, self, checkable=True)
            act.setData(mid)
            act.setChecked(mid == self.settings.get("color_mode"))
            act.triggered.connect(lambda checked=False, a=act: self._set_color_mode(a.data()))
            cgroup.addAction(act)
            colour_menu.addAction(act)
        self._color_actions = cgroup.actions()

        theme_menu = view_menu.addMenu("Theme")
        tgroup = QActionGroup(self)
        for tid, label in (("system", "System"), ("light", "Light"), ("dark", "Dark")):
            act = QAction(label, self, checkable=True)
            act.setData(tid)
            act.setChecked(tid == self.settings.get("theme"))
            act.triggered.connect(lambda checked=False, a=act: self._set_theme(a.data()))
            tgroup.addAction(act)
            theme_menu.addAction(act)

        view_menu.addSeparator()
        zoom_in = QAction("Zoom in", self)
        zoom_in.setShortcut("Ctrl+=")
        zoom_in.triggered.connect(lambda: self._zoom(+0.1))
        view_menu.addAction(zoom_in)
        zoom_out = QAction("Zoom out", self)
        zoom_out.setShortcut("Ctrl+-")
        zoom_out.triggered.connect(lambda: self._zoom(-0.1))
        view_menu.addAction(zoom_out)
        zoom_reset = QAction("Reset zoom", self)
        zoom_reset.setShortcut("Ctrl+0")
        zoom_reset.triggered.connect(lambda: self._zoom(0))
        view_menu.addAction(zoom_reset)

        view_menu.addSeparator()
        self.legend_action = QAction("Show legend", self, checkable=True)
        self.legend_action.setChecked(bool(self.settings.get("show_legend")))
        self.legend_action.toggled.connect(
            lambda on: (self.settings.set("show_legend", on), self.legend.setVisible(on)))
        view_menu.addAction(self.legend_action)

        view_menu.addSeparator()
        reset_view = QAction("Reset view", self)
        reset_view.triggered.connect(self._reset_view)
        view_menu.addAction(reset_view)

        edu_menu = mb.addMenu("Education")
        egroup = QActionGroup(self)
        for lid, prof in EDUCATION_LEVELS.items():
            act = QAction(prof["label"], self, checkable=True)
            act.setData(lid)
            act.setStatusTip(prof["description"])
            act.setChecked(lid == self.settings.education_level())
            act.triggered.connect(lambda checked=False, a=act: self._set_level(a.data()))
            egroup.addAction(act)
            edu_menu.addAction(act)
        self._level_actions = egroup.actions()

        element_menu = mb.addMenu("Element")
        copy_action = QAction("Copy details", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self._copy_details)
        element_menu.addAction(copy_action)
        compare_action = QAction("Compare\u2026", self)
        compare_action.setShortcut("Ctrl+Shift+C")
        compare_action.triggered.connect(
            lambda: self._add_to_compare(self.current_element().number
                                         if self.current_element() else 1))
        element_menu.addAction(compare_action)
        element_menu.addSeparator()
        settings_action = QAction("Settings\u2026", self)
        settings_action.setMenuRole(QAction.PreferencesRole)
        settings_action.setShortcut(QKeySequence.Preferences)
        settings_action.triggered.connect(self._open_settings)
        element_menu.addAction(settings_action)

        # context menu on tiles
        self.table.element_context_menu.connect(self._tile_context_menu)

        # global shortcuts ------------------------------------------------------
        slash = QShortcut(QKeySequence("/"), self)
        slash.activated.connect(self._focus_search)
        find = QShortcut(QKeySequence.Find, self)
        find.activated.connect(self._focus_search)
        esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        esc.activated.connect(self._esc_pressed)
        focus_table = QShortcut(QKeySequence("Ctrl+L"), self)
        focus_table.activated.connect(lambda: self.table.focus_element(
            self.current_element().number if self.current_element() else 1))

        help_menu = mb.addMenu("Help")
        shortcuts_action = QAction("Keyboard shortcuts", self)
        shortcuts_action.setShortcut("Ctrl+/")
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)
        about_action = QAction("About Orbital", self)
        about_action.setMenuRole(QAction.AboutRole)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # ------------------------------------------------------------------ state

    def current_element(self):
        return self.panel.element

    def _apply_state(self):
        self.legend.setVisible(bool(self.settings.get("show_legend")))
        apply_theme(self.settings.get("theme"), self.settings.accent_hex())
        self._refresh_icons()

    def _refresh_icons(self):
        """Icons are drawn from the palette text colour — redraw on theme change."""
        self.filter_button.setIcon(_icon("filter"))
        self.settings_button.setIcon(_icon("settings"))
        self.help_button.setIcon(_icon("help"))
        for action in (self.search_box.edit.actions()
                       if hasattr(self.search_box, "edit") else []):
            self.search_box.edit.removeAction(action)
        self.search_box.edit.addAction(_icon("search"), QLineEdit.LeadingPosition)

    def select_element(self, number, scroll=True):
        self.table.select_element(number, scroll=scroll)
        self.sidebar.select_element(number)
        e = by_number(self.elements, number)
        if self.settings.get("open_details_on_select"):
            self.panel.show_element(e)
        self.status_left.setText(
            "%d \u00b7 %s (%s) \u00b7 A\u1d63 %s \u00b7 %s"
            % (e.number, e.name, e.symbol, e.mass_string(), e.category.title()))

    # -- toolbar handlers ----------------------------------------------------

    def _fit_tiles_first_run(self):
        if self.settings.has("tile_scale"):
            return
        viewport = self.table._scroll.viewport().width()
        if viewport <= 0:
            return
        needed = 18 * BASE_W + 17 * 2 + 24  # tiles + spacing + row-label column
        scale = max(MIN_SCALE, min(1.0, (viewport - 12) / needed))
        self.settings.set("tile_scale", round(scale, 2))
        self.table._apply_tile_scale()
        self.table.rebuild()

    def _on_level_combo(self, index):
        self._set_level(self.level_combo.itemData(index))

    def _on_layout_combo(self, index):
        self._set_layout(self.layout_combo.itemData(index))

    def _on_color_combo(self, index):
        self._set_color_mode(self.color_combo.itemData(index))

    @staticmethod
    def _block(widget, fn):
        """Run fn with the widget's signals blocked (prevents UI echo loops)."""
        widget.blockSignals(True)
        try:
            fn()
        finally:
            widget.blockSignals(False)

    def _set_level(self, level_id):
        self.settings.set("education_level", level_id)
        self._block(self.level_combo,
                    lambda: self.level_combo.setCurrentText(EDUCATION_LEVELS[level_id]["label"]))
        for act in self._level_actions:
            act.setChecked(act.data() == level_id)
        if self.current_element():
            self.panel.show_element(self.current_element())

    def _set_layout(self, layout_id):
        self.settings.set("layout", layout_id)
        self._block(self.layout_combo,
                    lambda: self.layout_combo.setCurrentText(layout_id.title()))
        for act in self._layout_actions:
            act.setChecked(act.data() == layout_id)
        self.table.rebuild()
        if self.current_element():
            self.table.select_element(self.current_element().number)

    def _set_color_mode(self, mode_id):
        self.settings.set("color_mode", mode_id)
        self._block(self.color_combo,
                    lambda: self.color_combo.setCurrentText(self.color_modes[mode_id].name))
        for act in self._color_actions:
            act.setChecked(act.data() == mode_id)
        self.table.refresh_colors()
        self.legend.set_mode(self.color_modes[mode_id])

    def _zoom(self, delta):
        current = float(self.settings.get("tile_scale"))
        new = 1.0 if delta == 0 else round(current + delta, 2)
        new = max(0.8, min(1.6, new))
        if new == current:
            return
        self.settings.set("tile_scale", new)
        self.table.rebuild()

    def _set_theme(self, theme_id):
        self.settings.set("theme", theme_id)
        self.table.rebuild()
        self.sidebar._build()

    def _reset_view(self):
        self._clear_search()
        self._clear_filters()
        self._set_layout("standard")
        self._set_color_mode("category")
        self.panel.show_welcome()
        self.table.clear_focus()

    # -- search / filter ------------------------------------------------------

    def _on_search_picked(self, number):
        self.select_element(number, scroll=True)
        self.table.focus_element(number)

    def _on_search_query(self, text):
        self._search_text = text.strip()
        self._update_highlight()
        self._refresh_status()

    def _clear_search(self):
        self.search_box.edit.clear()
        self._search_text = ""
        self._update_highlight()

    def _toggle_filter_dialog(self):
        if self.filter_dialog is None:
            self.filter_dialog = FilterDialog(self, self.filter_spec)
            self.filter_dialog.changed.connect(self._on_filter_changed)
        if self.filter_dialog.isVisible():
            self.filter_dialog.close()
            self.filter_button.setChecked(False)
        else:
            self.filter_dialog.show()
            self.filter_button.setChecked(True)

    def _on_filter_changed(self, spec):
        self.filter_spec = spec
        self._update_highlight()
        self._refresh_status()

    def _clear_filters(self):
        self.filter_spec = FilterSpec()
        if self.filter_dialog is not None:
            self.filter_dialog._clear()
            self.filter_dialog.close()
        self.filter_button.setChecked(False)
        self._update_highlight()
        self._refresh_status()

    def _update_highlight(self):
        numbers = matching_numbers(self.elements, self.filter_spec)
        if self._search_text:
            results = {e.number for e in do_search(self._search_text, self.elements)}
            numbers = results if numbers is None else (numbers & results)
        self.table.set_highlight(numbers)

    def _refresh_status(self):
        """One place computes the right-hand status text."""
        shown = matching_numbers(self.elements, self.filter_spec)
        if self._search_text:
            results = {e.number for e in do_search(self._search_text, self.elements)}
            count = len(results if shown is None else (shown & results))
            self.status_filter.setText("%d elements match search \u2014 clear" % count)
            self.status_filter.setVisible(True)
        elif shown is not None:
            self.status_filter.setText(
                "%d of 118 elements \u2014 clear filters" % len(shown))
            self.status_filter.setVisible(True)
        else:
            self.status_filter.setText("")
            self.status_filter.setVisible(False)

    # -- compare / misc --------------------------------------------------------

    def _add_to_compare(self, number):
        if number not in self.compare_selection:
            self.compare_selection.append(number)
        self.compare_selection = self.compare_selection[-4:]
        if self.compare_dialog is None:
            self.compare_dialog = CompareDialog(
                self, self.elements, self.compare_selection, self.settings)
        else:
            self.compare_dialog.set_elements(self.compare_selection)
        self.compare_dialog.show()
        self.compare_dialog.raise_()

    def _focus_search(self):
        from PySide6.QtWidgets import QLineEdit, QAbstractSpinBox
        fw = QApplication.focusWidget()
        if isinstance(fw, (QLineEdit, QAbstractSpinBox)):
            return  # let text input behave normally
        self.search_box.select_all_and_focus()

    def _esc_pressed(self):
        if self._search_text:
            self._clear_search()
            return
        if self.filter_spec.is_active():
            self._clear_filters()
            return
        if self.current_element() is not None:
            self.panel.show_welcome()
            self.table.clear_focus()

    def _tile_context_menu(self, number):
        e = by_number(self.elements, number)
        from PySide6.QtGui import QCursor
        menu = QMenu(self)
        open_action = menu.addAction("Open %s" % e.name)
        menu.addSeparator()
        compare_action = menu.addAction("Add %s to comparison" % e.symbol)
        copy_action = menu.addAction("Copy %s details" % e.symbol)
        chosen = menu.exec(QCursor.pos())
        if chosen == open_action:
            self.select_element(e.number)
        elif chosen == compare_action:
            self._add_to_compare(e.number)
        elif chosen == copy_action:
            self._copy_element(e)

    def _copy_details(self):
        e = self.current_element()
        if e is None:
            return
        self._copy_element(e)

    def _copy_element(self, e):
        lines = []
        for fid in ("number", "symbol", "name", "atomic_mass", "group", "period",
                    "block", "category", "state", "configuration", "shells",
                    "electronegativity", "melt", "boil", "density"):
            v = field_value(e, fid)
            if isinstance(v, tuple):
                v = "; ".join(v)
            if v not in (None, "", ()):
                lines.append("%s: %s" % (fid.replace("_", " "), v))
        QApplication.clipboard().setText("\n".join(lines))
        self.statusBar().showMessage("Copied %s details" % e.name, 2000)

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export table", "orbital-table.png", "PNG image (*.png)")
        if not path:
            return
        pix = self.table._scroll.grab()
        pix.save(path)
        self.statusBar().showMessage("Exported %s" % path, 3000)

    def _open_settings(self):
        dlg = SettingsDialog(self, self.settings)
        if dlg.exec():
            dlg.apply()
            self.table.rebuild()
            if self.current_element():
                self.panel.show_element(self.current_element())
            self._apply_state()

    def _on_setting_changed(self, key):
        if key in ("theme", "accent"):
            self._apply_state()
            self.table.rebuild()
            self.sidebar._build()
        elif key == "layout":
            self.table.rebuild()
            self._block(self.layout_combo,
                        lambda: self.layout_combo.setCurrentText(self.settings.get("layout").title()))
        elif key in ("tile_preset", "tile_fields", "tile_scale"):
            self.table.rebuild()
        elif key == "color_mode":
            self._set_color_mode(self.settings.get("color_mode"))
        elif key == "education_level":
            level = self.settings.education_level()
            self._block(self.level_combo,
                        lambda: self.level_combo.setCurrentText(EDUCATION_LEVELS[level]["label"]))
            for act in self._level_actions:
                act.setChecked(act.data() == level)
            if self.current_element():
                self.panel.show_element(self.current_element())
        elif key == "show_legend":
            self.legend.setVisible(bool(self.settings.get("show_legend")))
            self.legend_action.setChecked(bool(self.settings.get("show_legend")))
        elif key == "mass_precision":
            if self.current_element():
                self.panel.show_element(self.current_element())

    def _show_shortcuts(self):
        QMessageBox.information(
            self, "Keyboard shortcuts",
            "<b>/</b> or <b>Ctrl+F</b> \u2014 search<br>"
            "<b>Arrows</b> \u2014 move around the table<br>"
            "<b>Enter</b> \u2014 open the focused element<br>"
            "<b>Esc</b> \u2014 clear search / close filter<br>"
            "<b>Ctrl+1..4</b> \u2014 switch table layout<br>"
            "<b>Ctrl+Shift+C</b> \u2014 add to comparison<br>"
            "<b>Ctrl+,</b> \u2014 settings<br>"
            "<b>Ctrl+Shift+E</b> \u2014 export table image")

    def _show_about(self):
        from orbital import __version__
        QMessageBox.about(
            self, "Orbital",
            "<h3>Orbital %s</h3>"
            "A fast, offline periodic table for macOS, Windows and Linux.<br><br>"
            "118 elements, 4 table layouts, education levels from IGCSE to "
            "Advanced, and 200 chemistry jokes.<br><br>"
            "MIT licensed. Data sources: IUPAC, CRC, NIST \u2014 see the repo." % __version__)
