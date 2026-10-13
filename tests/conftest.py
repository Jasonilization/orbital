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
    """CI-only teardown guard: after a fully green run under the
    offscreen platform, flush and exit hard without touching Qt at all.
    PySide's interpreter-exit teardown races Qt's cleanup on some
    runners (access violation / SIGABRT after all tests pass), and
    processing pending events at this point can fire handlers on
    already-deleted widgets. Failures exit normally so pytest can print
    details."""
    if exitstatus != 0:
        return
    if os.environ.get("ORBITAL_HARD_EXIT") != "1":
        return   # local runs: normal exit, full pytest output
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


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
