"""Application bootstrap."""
from __future__ import annotations

import sys


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--version" in argv:
        from orbital import __version__
        print("Orbital %s" % __version__)
        return 0
    if "--help" in argv:
        print(__doc__.strip())
        print("\nUsage: orbital [--version]")
        return 0

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from orbital.settings import Settings
    from orbital.ui.main_window import MainWindow
    from orbital.ui.theme import apply_theme

    app = QApplication(argv)
    app.setApplicationName("Orbital")
    app.setOrganizationName("Orbital")
    app.setDesktopFileName("orbital")

    settings = Settings()
    apply_theme(settings.get("theme"), settings.accent_hex())

    win = MainWindow(settings)
    win.show()
    return app.exec()
