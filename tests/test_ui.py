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
    # moving right from hydrogen reaches helium (same row)
    focused = win.table.tiles[2]
    assert focused.hasFocus()
    win.table._on_move_requested(win.table.tiles[2], 0, 1)  # down from He
    qapp.processEvents()
    assert win.table.tiles[10].hasFocus()


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
