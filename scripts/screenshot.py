#!/usr/bin/env python3
"""Render real screenshots of the app for the README.

Runs the actual MainWindow offscreen at 2x device scale and saves PNGs
into assets/screenshots/. These are genuine renders of the real UI —
not mockups.
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
OUT = os.path.join(REPO, "assets", "screenshots")
os.makedirs(OUT, exist_ok=True)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication

from orbital.settings import Settings
from orbital.ui.main_window import MainWindow
from orbital.ui.theme import apply_theme
from orbital.filters import FilterSpec


def render(name):
    app = QApplication.instance()
    app.processEvents()
    pix = win.grab()
    path = os.path.join(OUT, name)
    pix.save(path)
    print("wrote", path, pix.width(), "x", pix.height())


app = QApplication([])
QGuiApplication.primaryScreen()  # warm the screen object offscreen
settings = Settings(ini_path=os.path.join(tempfile.mkdtemp(), "shots.ini"))
settings.set("setup_done", True)

apply_theme("light", settings.accent_hex())
win = MainWindow(settings)
win.resize(1440, 860)
win.show()
app.processEvents()

# 1. First launch: welcome view with joke of the day, standard table
render("main-light.png")

# 2. Element selected, IGCSE level
win._set_level("igcse")
win.select_element(11)  # sodium — the school classic
app.processEvents()
render("element-igcse.png")

# 3. Dark theme, extended layout, colored by state
settings.set("theme", "dark")
apply_theme("dark", settings.accent_hex())
win._set_layout("extended")
win._set_color_mode("state")
win.select_element(79)  # gold
app.processEvents()
render("extended-dark.png")

# 4. Search active with highlight
settings.set("theme", "light")
apply_theme("light", settings.accent_hex())
win._set_layout("standard")
win._set_color_mode("category")
win._set_level("general")
win.search_box.edit.setText("iron")
win._on_search_query("iron")
app.processEvents()
render("search-highlight.png")

# 5. IGCSE assessment view: simple masses, syllabus focus
win._clear_search()
win._set_level("igcse")
win._set_layout("standard")
win._set_color_mode("category")
win.select_element(17)  # chlorine - the 35.5 classic
app.processEvents()
render("igcse-focus.png")

# 6. Compare dialog
win._clear_search()
win._add_to_compare(8)
win._add_to_compare(16)
win._add_to_compare(34)
win.compare_dialog.resize(760, 560)
win.compare_dialog.show()
app.processEvents()
cpix = win.compare_dialog.grab()
cpath = os.path.join(OUT, "compare.png")
cpix.save(cpath)
print("wrote", cpath)

win.compare_dialog.close()
win.close()
print("done")
