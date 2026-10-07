"""Shared fixtures for the test suite. UI tests run offscreen so they work
on every platform (including headless CI)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def settings(tmp_path):
    from orbital.settings import Settings
    return Settings(ini_path=str(tmp_path / "settings.ini"))


@pytest.fixture()
def win(qapp, settings):
    from orbital.ui.main_window import MainWindow
    from orbital.ui.theme import apply_theme
    apply_theme("light", settings.accent_hex())
    w = MainWindow(settings)
    w.show()
    qapp.processEvents()
    yield w
    w.close()
    qapp.processEvents()
