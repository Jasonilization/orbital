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


def pytest_sessionfinish(session, exitstatus):
    """Clear Qt object caches and flush events before interpreter exit —
    leaves QObjects alive past the QApplication is what segfaults the
    Linux runners."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is not None:
        from orbital.ui.icons import clear_icon_cache
        clear_icon_cache()
        app.processEvents()


@pytest.fixture()
def settings(tmp_path):
    from orbital.settings import Settings
    s = Settings(ini_path=str(tmp_path / "settings.ini"))
    s.set("setup_done", True)   # keep the first-run dialog out of UI tests
    return s


@pytest.fixture()
def win(qapp, settings):
    from orbital.ui.main_window import MainWindow
    from orbital.ui.theme import apply_theme
    apply_theme("light", settings.accent_hex())
    w = MainWindow(settings)
    w.show()
    qapp.processEvents()
    # run (and thereby disarm) the deferred first-run tile fit so no timer
    # can fire mid-test and rebuild the table under a test's feet
    w._fit_tiles_first_run()
    qapp.processEvents()
    yield w
    w.close()
    qapp.processEvents()
