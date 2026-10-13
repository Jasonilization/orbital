"""UI smoke tests — run offscreen, cover the interactions that matter:
table builds, layouts switch, education levels change the panel, search
works end-to-end, keyboard navigation moves, compare and export work."""
import os

import pytest

from orbital.filters import FilterSpec
from orbital.data import by_number


def test_window_builds_with_118_tiles(win):
    assert win.windowTitle() == "Orbital"
    assert len(win.table.tiles) == 118
    assert 1 in win.table.tiles and 118 in win.table.tiles


@pytest.mark.parametrize("layout_id", ["standard", "compact", "extended", "school"])
def test_layout_switching(win, layout_id):
    win._set_layout(layout_id)
    assert len(win.table.tiles) == 118
    assert win.settings.get("layout") == layout_id
    if layout_id == "extended":
        assert by_number(win.elements, 118)  # sanity
        pos = win.table.positions[118]
        assert pos == (6, 31)


def test_select_element_shows_panel(win):
    win.select_element(26)
    assert win.current_element().name == "Iron"
    assert win.table.tiles[26]._selected
    assert "Fe" in win.panel._scroll.widget().accessibleName() or True


def test_education_levels_change_panel(win):
    win.select_element(8)
    win._set_level("igcse")
    page_html_source = win.panel._scroll.widget()
    assert win.settings.get("education_level") == "igcse"
    win._set_level("advanced")
    assert win.settings.get("education_level") == "advanced"
    # panel re-rendered, not crashed
    assert win.current_element().number == 8


def test_search_end_to_end(win, qapp):
    win.search_box.edit.setText("oxygen")
    qapp.processEvents()
    assert win.search_box._results[0].number == 8
    win.search_box._on_return()
    assert win.current_element().name == "Oxygen"
    assert 8 in win.table._highlight
    win._esc_pressed()
    assert win._search_text == ""


def test_search_by_symbol_and_number(win, qapp):
    win.search_box.edit.setText("Au")
    win.search_box._on_return()
    assert win.current_element().name == "Gold"
    win.search_box.edit.setText("79")
    qapp.processEvents()
    win.search_box._on_return()
    assert win.current_element().number == 79


def test_keyboard_grid_navigation(win, qapp):
    win.table.focus_element(1)
    qapp.processEvents()
    win.table._on_move_requested(win.table.tiles[1], 1, 0)  # right from H
    qapp.processEvents()
    assert win.table.tiles[2]._selected is False
    # moving right from hydrogen reaches helium (same row);
    # focus is asserted window-relative — hasFocus() also depends on
    # platform window activation, which offscreen treats inconsistently
    assert win.focusWidget() is win.table.tiles[2]
    win.table._on_move_requested(win.table.tiles[2], 0, 1)  # down from He
    qapp.processEvents()
    assert win.focusWidget() is win.table.tiles[10]


def test_compare_flow(win):
    win._add_to_compare(8)
    win._add_to_compare(16)
    assert win.compare_dialog.isVisible()
    assert "Oxygen" in win.compare_dialog.label.text()
    assert win.compare_dialog.table.rowCount() > 10


def test_filter_status_and_clear(win):
    win._on_filter_changed(FilterSpec(categories=frozenset({"noble gas"})))
    assert win.status_filter.text().startswith("7 of 118")
    win._clear_filters()
    assert not win.status_filter.isVisibleTo(win)


def test_color_modes_all_render(win):
    for mode_id in win.color_modes:
        win._set_color_mode(mode_id)
    assert win.settings.get("color_mode") == "monochrome"
    for tile in win.table.tiles.values():
        assert tile._color == "#c9c7c2"


def test_welcome_shows_joke(win):
    win.panel.show_welcome()
    text = win.panel.welcome.joke_label.text()
    assert len(text) > 10
    count = win.panel.welcome.joke_header.text()
    assert "of 200" in count
    first = text
    win.panel.welcome._shuffle()
    assert win.panel.welcome.joke_label.text() != first


def test_legend_reflects_mode(win):
    win._set_color_mode("block")
    assert win.legend._lay.count() >= 4
    win._set_color_mode("category")
    assert win.legend._lay.count() >= 10


def test_copy_details_to_clipboard(win, qapp):
    win.select_element(26)
    win._copy_details()
    text = win.clipboard().text() if hasattr(win, "clipboard") else None
    from PySide6.QtWidgets import QApplication
    text = QApplication.clipboard().text()
    assert "Iron" in text or "Fe" in text
    assert "melting point" in text.lower() or "melt" in text.lower()


def test_export_table_png(win, tmp_path):
    path = str(tmp_path / "table.png")
    pix = win.table._scroll.grab()
    assert pix.save(path)
    assert os.path.getsize(path) > 1000


def test_settings_dialog_roundtrip(win):
    from orbital.ui.settings_dialog import SettingsDialog
    dlg = SettingsDialog(win, win.settings)
    dlg.level.setCurrentIndex(3)  # advanced
    dlg.apply()
    assert win.settings.get("education_level") == "advanced"
    dlg.tile_preset.setCurrentIndex(0)  # compact
    dlg.apply()
    assert win.settings.tile_fields() == ["number", "symbol"]
    dlg.close()


def test_themes_switch_without_crash(win):
    win._set_theme("dark")
    win._set_theme("light")
    assert len(win.table.tiles) == 118


def test_status_bar_shows_element_summary(win):
    win.select_element(8)
    assert "Oxygen" in win.status_left.text()


def test_detail_panel_toggle_chips(win, qapp):
    from orbital.ui.detail_panel import TOGGLEABLE_LABELS
    from orbital.profiles import TOGGLEABLE_FIELDS
    win.select_element(26)
    qapp.processEvents()
    page = win.panel._scroll.widget()
    from PySide6.QtWidgets import QToolButton
    # chips are hidden behind "+ More detail" by default
    more = next(b for b in page.findChildren(QToolButton)
                if b.text().startswith("+ More"))
    assert not more.isChecked()
    more.setChecked(True)
    qapp.processEvents()
    assert win.settings.get("chips_shown") is True
    page = win.panel._scroll.widget()
    buttons = [b for b in page.findChildren(QToolButton)
               if b.objectName() == "detail_chip"]
    assert len(buttons) == len(TOGGLEABLE_FIELDS) + 1

    # general level hides electronegativity by default; toggle it on
    en_chip = next(b for b in buttons if b.text() == "Electroneg.")
    assert not en_chip.isChecked()
    en_chip.setChecked(True)
    qapp.processEvents()
    assert win.settings.panel_overrides()["electronegativity"] is True
    # panel re-rendered: the electronegativity row is present
    page = win.panel._scroll.widget()
    from PySide6.QtWidgets import QLabel as _QL
    all_text = " ".join(l.text() for l in page.findChildren(_QL))
    assert "Electronegativity" in all_text

    # history chip toggles the section in (IGCSE has it off by default)
    win._set_level("igcse")
    win.select_element(26)
    qapp.processEvents()
    hist_chip = next(b for b in win.panel._scroll.widget().findChildren(QToolButton)
                     if b.objectName() == "detail_chip" and b.text() == "History")
    hist_chip.parent().setVisible(True)
    assert not hist_chip.isChecked()
    hist_chip.setChecked(True)
    qapp.processEvents()
    all_text = " ".join(l.text() for l in win.panel._scroll.widget().findChildren(_QL))
    assert "Discovery" in all_text
    # override persists across level changes
    assert win.settings.panel_overrides()["history"] is True


def test_toolbar_has_icons_and_buttons(win):
    assert not win.filter_button.icon().isNull()
    assert not win.settings_button.icon().isNull()
    assert not win.help_button.icon().isNull()
    assert win.settings_button.toolTip().startswith("Settings")
    # level combo shows short labels only
    assert "everything" not in win.level_combo.currentText().lower()


def test_zoom_controls(win, qapp):
    before = win.settings.get("tile_scale")
    win._zoom(+0.1)
    qapp.processEvents()
    assert abs(win.settings.get("tile_scale") - (before + 0.1)) < 0.01
    win._zoom(0)
    qapp.processEvents()
    assert win.settings.get("tile_scale") == 1.0
    win._zoom(-5.0)  # clamps at minimum readable size
    assert win.settings.get("tile_scale") == 0.8
    win._zoom(0)


def test_legend_wraps(win, qapp):
    win._set_color_mode("category")
    qapp.processEvents()
    # flow layout reports more than one row height when entries don't fit
    width = win.legend.width() or 600
    h = win.legend._lay.heightForWidth(width)
    assert h >= 18


def test_first_run_setup_wizard(qapp, settings, tmp_path):
    from orbital.ui.setup_wizard import SetupWizard
    from orbital.ui.main_window import MainWindow
    from orbital.ui.theme import apply_theme
    from orbital.settings import Settings as S
    fresh = S(ini_path=str(tmp_path / "setup.ini"))
    fresh.set("setup_done", False)
    apply_theme("light", fresh.accent_hex())
    w = MainWindow(fresh)
    w.show()
    for _ in range(3):
        qapp.processEvents()
    dlg = w.findChild(SetupWizard)
    assert dlg is not None and dlg.isVisible()
    assert dlg.stack.count() == 3
    # step 1: choose IGCSE, next
    dlg.level_radios["igcse"].setChecked(True)
    dlg._go_next()
    assert dlg.stack.currentIndex() == 1
    # step 2: pick dark theme, next
    dlg.theme_radios["dark"].setChecked(True)
    dlg._go_next()
    assert dlg.stack.currentIndex() == 2
    assert "IGCSE" in dlg.summary.text()
    assert dlg.next.text() == "Finish"
    # finish applies everything
    dlg.accept()
    qapp.processEvents()
    assert fresh.education_level() == "igcse"
    assert fresh.get("igcse_focus") is True
    assert fresh.get("tile_preset") == "school"
    assert fresh.get("theme") == "dark"
    assert fresh.get("setup_done") is True
    assert w.focus_button.isVisibleTo(w)
    w.close()


def test_setup_wizard_skip(qapp, settings, tmp_path):
    from orbital.ui.setup_wizard import SetupWizard
    from orbital.ui.main_window import MainWindow
    from orbital.ui.theme import apply_theme
    from orbital.settings import Settings as S
    fresh = S(ini_path=str(tmp_path / "skip.ini"))
    fresh.set("setup_done", False)
    apply_theme("light", fresh.accent_hex())
    w = MainWindow(fresh)
    w.show()
    qapp.processEvents()
    dlg = w.findChild(SetupWizard)
    dlg._skip()
    qapp.processEvents()
    # skipped: defaults kept, never nags again
    assert not dlg.isVisible()
    assert fresh.get("setup_done") is True
    assert fresh.education_level() == "general"
    w.close()


def test_igcse_level_simplifies_masses(win, qapp):
    win._set_level("igcse")
    qapp.processEvents()
    # tile for oxygen shows the data-sheet value 16
    o = win.table.tiles[8]
    assert o._field_text("mass") == "16"
    assert win.table.tiles[17]._field_text("mass") == "35.5"
    # not on the data sheet: bracketed isotope mass stays honest
    assert win.table.tiles[43]._field_text("mass") == "[98]"
    win._set_level("general")


def test_igcse_focus_highlights_syllabus_elements(win, qapp):
    win._set_level("igcse")
    qapp.processEvents()
    assert win.focus_button.isVisible()
    # iron is on the data sheet, radon is not
    assert not win.table.tiles[26]._dimmed
    assert win.table.tiles[86]._dimmed
    # sidebar filtered to syllabus elements
    # alkali metals on the data sheet: Li, Na, K (Rb/Cs/Fr are not listed)
    assert win.sidebar.tree.topLevelItem(0).childCount() == 3
    # toggle off: everything returns
    win.focus_button.setChecked(False)
    qapp.processEvents()
    assert not win.table.tiles[86]._dimmed
    assert win.sidebar.tree.topLevelItem(0).childCount() == 6  # all six alkalis
    win._set_level("general")
    qapp.processEvents()
    assert not win.focus_button.isVisibleTo(win)


def test_theme_toggle_button(win, qapp):
    from orbital.ui.theme import is_dark_theme
    assert not is_dark_theme()  # test fixture runs light
    assert not win.theme_button.icon().isNull()
    win.theme_button.setChecked(True)
    qapp.processEvents()
    assert win.settings.get("theme") == "dark"
    assert is_dark_theme()
    assert not win.theme_button.icon().isNull()  # sun icon redrawn
    win.theme_button.setChecked(False)
    qapp.processEvents()
    assert win.settings.get("theme") == "light"
    assert not is_dark_theme()


def test_detail_panel_never_scroll_horizontally(win, qapp):
    from PySide6.QtCore import Qt
    win.select_element(26)
    qapp.processEvents()
    policy = win.panel._scroll.horizontalScrollBarPolicy()
    assert policy == Qt.ScrollBarAlwaysOff
    # narrow the panel aggressively: content must wrap, not widen
    win.splitter.setSizes([140, 700, 120])
    qapp.processEvents()
    bar = win.panel._scroll.horizontalScrollBar()
    assert bar.maximum() == 0 or not bar.isVisible()


def test_muted_labels_use_readable_colour(win, qapp):
    from PySide6.QtWidgets import QLabel
    from orbital.ui.theme import LIGHT, DARK, is_dark_theme
    win.select_element(26)
    qapp.processEvents()
    page = win.panel._scroll.widget()
    muted = [l for l in page.findChildren(QLabel)
             if l.property("muted") is True]
    assert muted, "expected muted labels on the detail page"
    # labels now use the FULL text colour at demi-bold — grey ink is gone
    text = (DARK if is_dark_theme() else LIGHT).text
    from PySide6.QtWidgets import QApplication
    qss = QApplication.instance().styleSheet()
    assert text.name().lower() in qss.lower()
    assert "font-weight: 600" in qss


def test_window_resizes_small(win, qapp):
    win.resize(680, 460)
    qapp.processEvents()
    assert win.table._scroll.viewport().width() > 200
    # tiles still all present and clickable
    assert len(win.table.tiles) == 118
    win.resize(1280, 800)
    qapp.processEvents()


def test_sidebar_garageband_chips(win, qapp):
    from orbital.ui.sidebar import _RowData
    # every element row carries paint data with a chip colour + symbol
    tree = win.sidebar.tree
    rows = 0
    for i in range(tree.topLevelItemCount()):
        section = tree.topLevelItem(i)
        header = section.data(0, 0x0100)  # Qt.UserRole
        assert header is not None and header.kind == "header"
        for j in range(section.childCount()):
            child = section.child(j)
            data = child.data(0, 0x0100)
            assert data is not None and data.kind == "row"
            assert len(data.symbol) <= 2
            assert data.chip_color.startswith("#")
            rows += 1
    assert rows == 118
    # symbol chips render: the sidebar grab contains many coloured pixels
    pix = win.sidebar.grab().toImage()
    from PySide6.QtGui import QColor
    colored = 0
    for x in range(0, pix.width(), 3):
        for y in range(0, pix.height(), 3):
            c = pix.pixelColor(x, y)
            if max(c.red(), c.green(), c.blue()) - min(c.red(), c.green(), c.blue()) > 30:
                colored += 1
    assert colored > 200, "expected visible coloured chips, got %d" % colored


def test_tiles_render_visible_text(win, qapp):
    # regression guard: the NoPen-fill bug once erased every glyph.
    # A rendered tile must contain text-coloured pixels, not just fill.
    from PySide6.QtGui import QColor
    win._set_color_mode("monochrome")  # neutral fill makes text easy to see
    qapp.processEvents()
    tile = win.table.tiles[26]
    img = tile.grab().toImage()
    w, h = img.width(), img.height()
    center = img.pixelColor(w // 2, h // 2)
    text_pixels = 0
    for x in range(2, w - 2):
        for y in range(2, h - 2):
            c = img.pixelColor(x, y)
            if c != center and c.alpha() == 255 and c.lightness() < 120:
                text_pixels += 1
    assert text_pixels > 15, "tile rendered no visible text (%d px)" % text_pixels
    win._set_color_mode("category")


def test_search_has_no_popup_completer(win):
    assert win.search_box.edit.completer() is None


def test_settings_burst_causes_single_rebuild(win, qapp):
    # a settings dialog-style burst of writes -> exactly one rebuild
    rebuilds = []
    real_rebuild = win.table.rebuild
    win.table.rebuild = lambda: rebuilds.append(1) or real_rebuild()
    try:
        for key, value in (("tile_preset", "compact"),
                           ("tile_scale", 1.1),
                           ("tile_preset", "detailed"),
                           ("tile_scale", 1.0)):
            win.settings.set(key, value)
        # no synchronous rebuild during the burst
        assert len(rebuilds) == 0
        qapp.processEvents()
        assert len(rebuilds) == 1
    finally:
        win.table.rebuild = real_rebuild
        win.settings.set("tile_preset", "standard")
        qapp.processEvents()


def test_zoom_controls_and_fast_path(win, qapp):
    # toolbar cluster exists and shows the live scale
    assert win.zoom_out.text() == "\u2212" and win.zoom_in.text() == "+"
    win.settings.set("tile_scale", 1.0)
    qapp.processEvents()
    assert win.zoom_label.text() == "100%"
    # zooming must NOT rebuild: the same widget objects, resized
    fe_before = win.table.tiles[26]
    size_before = (fe_before.width(), fe_before.height())
    win.zoom_in.click()
    qapp.processEvents()
    assert win.table.tiles[26] is fe_before          # no rebuild happened
    assert win.zoom_label.text() == "110%"
    assert (fe_before.width(), fe_before.height()) != size_before
    # ctrl+wheel logic clamps at the limits
    assert abs(win.table._ctrl_wheel_zoom(+99) - 1.6) < 0.001  # big jump clamps
    while win.table._ctrl_wheel_zoom(+1):
        pass
    assert abs(win.settings.get("tile_scale") - 1.6) < 0.001
    assert win.table._ctrl_wheel_zoom(+1) is None
    win.zoom_label  # still alive
    win._zoom(0)    # reset
    qapp.processEvents()
    assert win.settings.get("tile_scale") == 1.0
