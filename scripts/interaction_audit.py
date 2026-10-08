"""Interaction audit — systematically exercise every click path in the app.

Run offscreen; prints a PASS/FAIL line per interaction so it doubles as a
manual checklist. Anything that raises or breaks state fails loudly.
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QFileDialog
from PySide6.QtTest import QTest

from orbital.settings import Settings
from orbital.ui.main_window import MainWindow
from orbital.ui.theme import apply_theme
from orbital.layouts import LAYOUTS
from orbital.profiles import EDUCATION_LEVELS, TILE_PRESETS

PASS = []
FAIL = []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print("PASS  %s" % name)
    except Exception:
        FAIL.append(name)
        print("FAIL  %s" % name)
        traceback.print_exc()


app = QApplication([])
settings = Settings(ini_path=os.path.join(tempfile.mkdtemp(), "audit.ini"))
settings.set("setup_done", True)
apply_theme("light", settings.accent_hex())
win = MainWindow(settings)
win.resize(1440, 860)
win.show()
app.processEvents()
win._fit_tiles_first_run()
app.processEvents()


# --------------------------------------------------------------------------
# menus

def _trigger(actions, name):
    for act in actions:
        act.trigger()
        app.processEvents()
        return
    raise AssertionError("no actions in " + name)


check("menu: layout actions x4", lambda: [_trigger(win._layout_actions, "layout") for _ in LAYOUTS] or [win._set_layout(l) for l in LAYOUTS])
check("menu: layout per id", lambda: [win._set_layout(l) for l in LAYOUTS])
check("menu: colour actions", lambda: [win._set_color_mode(m) for m in win.color_modes])
check("menu: education levels", lambda: [win._set_level(l) for l in EDUCATION_LEVELS])
check("menu: theme cycle", lambda: [win._set_theme(t) for t in ("dark", "light", "system")])
check("menu: legend toggle", lambda: (win.legend_action.trigger(), win.legend_action.trigger()))
check("menu: reset view", lambda: win._reset_view())


def export_click():
    real = QFileDialog.getSaveFileName
    QFileDialog.getSaveFileName = staticmethod(
        lambda *a, **k: (os.path.join(tempfile.mkdtemp(), "t.png"), "PNG"))
    try:
        win._export_png()
    finally:
        QFileDialog.getSaveFileName = real


check("menu: export table PNG", export_click)


def copy_details_click():
    win.select_element(29)
    win._copy_details()
    assert "Copper" in QApplication.clipboard().text(), QApplication.clipboard().text()[:80]


check("menu: copy details", copy_details_click)


def about_click():
    real_about = QMessageBox.about
    real_info = QMessageBox.information
    QMessageBox.about = staticmethod(lambda *a, **k: None)
    QMessageBox.information = staticmethod(lambda *a, **k: None)
    try:
        win._show_about()
        win._show_shortcuts()
    finally:
        QMessageBox.about = real_about
        QMessageBox.information = real_info


check("menu: about + shortcuts dialogs", about_click)


def settings_click():
    from orbital.ui.main_window import SettingsDialog as RealDialog

    class FakeDialog:
        instances = []

        def __init__(self, parent, settings, *a):
            self.real = RealDialog(parent, settings)
            FakeDialog.instances.append(self)

        def exec(self):
            self.real.tile_preset.setCurrentIndex(2)
            self.real.mass_precision.setValue(2)
            self.real.theme.setCurrentIndex(1)
            return True

        def apply(self):
            self.real.apply()

    import orbital.ui.main_window as mw
    mw.SettingsDialog = FakeDialog
    try:
        win._open_settings()
    finally:
        mw.SettingsDialog = RealDialog
    assert win.settings.get("mass_precision") == 2


check("menu: settings dialog flow", settings_click)

# --------------------------------------------------------------------------
# toolbar combos

check("toolbar: level combo", lambda: (win.level_combo.setCurrentIndex(3), app.processEvents(), None) if win.level_combo.currentIndex() != 3 else None)
check("toolbar: layout combo", lambda: win.layout_combo.setCurrentIndex(1) if win.layout_combo.currentIndex() != 1 else None)
check("toolbar: colour combo", lambda: win.color_combo.setCurrentIndex(5) if win.color_combo.currentIndex() != 5 else None)


def filter_dialog_flow():
    win._toggle_filter_dialog()
    app.processEvents()
    assert win.filter_dialog.isVisible()
    dlg = win.filter_dialog
    dlg.cat_checks["noble gas"].setChecked(True)
    app.processEvents()
    assert "of 118" in win.status_filter.text()
    dlg._clear()
    dlg.block_checks["f"].setChecked(True)
    app.processEvents()
    assert "of 118" in win.status_filter.text()
    win._toggle_filter_dialog()  # close
    assert not dlg.isVisible()
    win._clear_filters()


check("toolbar: filter dialog open/set/clear/close", filter_dialog_flow)


def search_flow():
    win._focus_search()
    QTest.keyClicks(win.search_box.edit, "gold")
    app.processEvents()
    QTest.keyClick(win.search_box.edit, Qt.Key_Return)
    app.processEvents()
    assert win.current_element().number == 79
    QTest.keyClick(win.search_box.edit, Qt.Key_Escape)
    app.processEvents()
    assert win._search_text == ""


check("toolbar: search type/return/escape", search_flow)

# --------------------------------------------------------------------------
# sidebar


def sidebar_click():
    # click the second element in the first category (alkali metals -> Na)
    tree = win.sidebar.tree
    section = tree.topLevelItem(0)
    assert section.childCount() > 1
    child = section.child(1)
    number = win.sidebar._item_numbers[id(child)]
    tree.setCurrentItem(child)
    win.sidebar._on_click(child, 0)
    app.processEvents()
    assert win.current_element().number == number


check("sidebar: click element row", sidebar_click)


def sidebar_header_click():
    tree = win.sidebar.tree
    section = tree.topLevelItem(3)  # transition metals
    was = section.isExpanded()
    win.sidebar._on_click(section, 0)
    assert section.isExpanded() != was


check("sidebar: collapse/expand category", sidebar_header_click)

# --------------------------------------------------------------------------
# table


def tile_mouse_click():
    tile = win.table.tiles[50]
    QTest.mouseClick(tile, Qt.LeftButton)
    app.processEvents()
    assert win.current_element().number == 50


check("table: mouse click on tile", tile_mouse_click)


def marker_click():
    win._set_layout("standard")
    app.processEvents()
    # find the 57-71 marker cell among the grid children
    from orbital.ui.table_view import _MarkerCell
    markers = [w for w in win.table._inner.findChildren(_MarkerCell)]
    assert markers, "no marker cells found"
    QTest.mouseClick(markers[0], Qt.LeftButton)
    app.processEvents()
    assert win.current_element().number in (57, 89)


check("table: 57-71 marker jump", marker_click)


def tile_context_menu():
    import orbital.ui.main_window as mw
    chosen = {}

    class FakeMenu:
        def __init__(self, *a):
            self.actions = []
        def addAction(self, label):
            act = (label,)
            self.actions.append(act)
            return act
        def addSeparator(self):
            return None
        def exec(self, pos):
            chosen["action"] = self.actions[-1]  # pick last ("copy details")
            return self.actions[-1]

    real = mw.QMenu
    mw.QMenu = FakeMenu
    try:
        win._tile_context_menu(26)
    finally:
        mw.QMenu = real
    assert win.current_element() is not None


check("table: context menu -> copy details", tile_context_menu)


def keyboard_arrows():
    win._set_layout("standard")
    win.table.focus_element(1)
    app.processEvents()
    QTest.keyClick(win.table.tiles[1], Qt.Key_Right)
    app.processEvents()
    assert win.focusWidget() is win.table.tiles[2]
    QTest.keyClick(win.table.tiles[2], Qt.Key_Down)
    app.processEvents()
    assert win.focusWidget() is win.table.tiles[10]
    QTest.keyClick(win.table.tiles[10], Qt.Key_Return)
    app.processEvents()
    assert win.current_element().number == 10


check("keyboard: arrows + enter open", keyboard_arrows)


def keyboard_shortcuts():
    # QShortcut firing itself can't be simulated offscreen (the platform
    # refuses keyboard grabs), so verify the bindings exist and exercise
    # the slots they're wired to — including the text-input guard.
    from PySide6.QtGui import QShortcut
    shortcuts = win.findChildren(QShortcut)
    assert len(shortcuts) >= 4, "expected /, Ctrl+F, Esc, Ctrl+L shortcuts"
    win.table.focus_element(1)
    app.processEvents()
    win._focus_search()  # '/' slot from normal (non-text) focus
    app.processEvents()
    # window-relative: offscreen never activates a window, so
    # QApplication.focusWidget() stays None at app level
    assert win.focusWidget() is win.search_box.edit
    QTest.keyClicks(win.search_box.edit, "fe")
    # guard: typing focus in a text field must not be hijacked.
    # App-level focus is None offscreen, so pretend it's the edit:
    real_focus = QApplication.focusWidget
    QApplication.focusWidget = lambda: win.search_box.edit
    try:
        win._focus_search()
    finally:
        QApplication.focusWidget = real_focus
    app.processEvents()
    assert win.focusWidget() is win.search_box.edit
    assert "fe" in win.search_box.edit.text()
    # guarded call must not have select-all'd the field
    assert not win.search_box.edit.hasSelectedText()
    win.search_box.edit.clear()
    win._on_search_query("")
    # Esc slot chain: search -> filters -> panel
    win._search_text = "x"
    win._esc_pressed()
    assert win._search_text == ""
    win.filter_spec = None if False else win.filter_spec
    win._on_filter_changed(__import__("orbital.filters", fromlist=["FilterSpec"]).FilterSpec(
        categories=frozenset({"halogen"})))
    win._esc_pressed()
    assert not win.filter_spec.is_active()


check("keyboard: shortcut bindings + slots + guards", keyboard_shortcuts)

# --------------------------------------------------------------------------
# detail panel


def panel_compare_button():
    # one element via the panel button: dialog opens, prompts for a second
    win.select_element(8)
    app.processEvents()
    page = win.panel._scroll.widget()
    from PySide6.QtWidgets import QPushButton
    buttons = page.findChildren(QPushButton)
    assert buttons, "no button on detail page"
    buttons[0].click()  # "Compare…"
    app.processEvents()
    assert win.compare_dialog.isVisible()
    assert "at least two" in win.compare_dialog.label.text()
    # add a second element via the same button: both names show
    win.select_element(16)
    app.processEvents()
    page2 = win.panel._scroll.widget()
    page2.findChildren(QPushButton)[0].click()
    app.processEvents()
    assert "Oxygen" in win.compare_dialog.label.text()
    assert "Sulfur" in win.compare_dialog.label.text()
    win.compare_dialog.close()
    win.compare_selection = []


check("panel: compare button click (1 -> 2 elements)", panel_compare_button)


def panel_section_collapse():
    win._set_level("advanced")
    win.select_element(26)
    app.processEvents()
    page = win.panel._scroll.widget()
    from orbital.ui.detail_panel import _Section
    sections = page.findChildren(_Section)
    assert sections, "no sections rendered"
    sect = sections[-1]  # history, starts open at advanced
    was_visible = sect.body.isVisible()
    sect.toggle.setChecked(False)
    app.processEvents()
    assert sect.body.isHidden()
    sect.toggle.setChecked(True)
    app.processEvents()


check("panel: section collapse/expand", panel_section_collapse)


def welcome_shuffle():
    win.panel.show_welcome()
    first = win.panel.welcome.joke_label.text()
    win.panel.welcome.shuffle.click()
    app.processEvents()
    assert win.panel.welcome.joke_label.text() != first


check("panel: welcome joke shuffle button", welcome_shuffle)


def compare_limits():
    for n in (1, 2, 3, 4, 5):
        win._add_to_compare(n)
    # capped at 4
    assert len(win.compare_selection) == 4
    assert win.compare_dialog.table.columnCount() == 5  # property + 4
    win.compare_dialog.set_elements([8])  # below minimum
    assert "at least two" in win.compare_dialog.label.text()
    win.compare_dialog.close()
    win.compare_selection = []


check("compare: cap at 4 and minimum 2", compare_limits)


def tile_presets_matrix():
    for preset in TILE_PRESETS:
        settings.set("tile_preset", preset)
        settings.set("tile_fields", None)
        app.processEvents()
        fields = win.settings.tile_fields()
        assert fields == list(TILE_PRESETS[preset]["fields"])
    settings.set("tile_fields", ["symbol", "name"])
    app.processEvents()
    assert win.settings.tile_fields() == ["symbol", "name"]
    settings.set("tile_fields", None)


check("settings: all tile presets + custom fields", tile_presets_matrix)


def mass_precision_flow():
    win.select_element(16)
    settings.set("mass_precision", 1)
    app.processEvents()
    page = win.panel._scroll.widget()
    settings.set("mass_precision", 4)
    app.processEvents()


check("settings: mass precision re-render", mass_precision_flow)


def settings_reset():
    settings.set("theme", "dark")
    settings.set("tile_scale", 1.3)
    settings.reset()
    assert settings.get("theme") == "system"
    assert settings.get("tile_scale") == 1.0


check("settings: reset restores defaults", settings_reset)


def theme_button():
    from orbital.ui.theme import is_dark_theme
    assert not is_dark_theme()
    win.theme_button.setChecked(True)
    app.processEvents()
    assert is_dark_theme() and win.settings.get("theme") == "dark"
    win.theme_button.setChecked(False)
    app.processEvents()
    assert not is_dark_theme()


check("toolbar: light/dark toggle", theme_button)


def resize_flow():
    win.resize(680, 460)
    app.processEvents()
    assert len(win.table.tiles) == 118
    from PySide6.QtCore import Qt
    assert win.panel._scroll.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    win.resize(1440, 860)
    app.processEvents()


check("window: resizes small, panel never scrolls horizontally", resize_flow)

# --------------------------------------------------------------------------
print()
print("=== %d passed, %d failed ===" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)
win.close()
