#!/bin/zsh
# Build Orbital.app for macOS, ad-hoc signed, then a DMG.
# Usage: scripts/build_mac.sh [--skip-dmg]
set -euo pipefail
cd "$(dirname "$0")/.."

PY=".venv/bin/python"
command -v "$PY" >/dev/null 2>&1 || PY="python3"

echo "==> building with PyInstaller"
"$PY" -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name Orbital \
    --icon assets/icons/Orbital.icns \
    --collect-data orbital \
    orbital/__main__.py

APP="dist/Orbital.app"
if [ ! -d "$APP" ]; then
    echo "build failed: $APP missing" >&2
    exit 1
fi

echo "==> ad-hoc code signing (not notarized — Gatekeeper will ask on first launch)"
codesign --force --deep --sign - "$APP"

VERSION=$("$PY" -c "import orbital; print(orbital.__version__)")

if [ "${1:-}" != "--skip-dmg" ]; then
    echo "==> packaging DMG"
    DMG="dist/Orbital-$VERSION.dmg"
    rm -f "$DMG"
    hdiutil create -volname "Orbital" -srcfolder "$APP" -ov -format UDZO "$DMG" >/dev/null
    echo "built $DMG"
fi
echo "done: $APP"
