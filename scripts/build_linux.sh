#!/bin/bash
# Build Orbital for Linux. Produces a portable directory via PyInstaller and,
# when appimagetool is available, an AppImage.
# Usage: scripts/build_linux.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> building with PyInstaller"
python3 -m PyInstaller \
    --noconfirm --clean --windowed \
    --name orbital \
    --collect-data orbital \
    orbital/__main__.py

if [ ! -d dist/orbital ]; then
    echo "build failed: dist/orbital missing" >&2
    exit 1
fi

VERSION=$(python3 -c "import orbital; print(orbital.__version__)")

echo "==> portable tarball"
tar -czf "dist/Orbital-$VERSION-linux-x64.tar.gz" -C dist orbital

if command -v appimagetool >/dev/null 2>&1; then
    echo "==> AppImage"
    APPDIR="dist/AppDir"
    rm -rf "$APPDIR"
    mkdir -p "$APPDIR/usr" "$APPDIR/usr/share/metainfo" "$APPDIR/usr/share/icons/hicolor/256x256/apps"
    cp -r dist/orbital/* "$APPDIR/usr/"
    cp assets/icons/icon_256.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/orbital.png"
    cp assets/icons/icon_256.png "$APPDIR/orbital.png"
    cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/orbital" "$@"
EOF
    chmod +x "$APPDIR/AppRun"
    cat > "$APPDIR/orbital.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Orbital
Comment=A fast, offline periodic table
Exec=orbital
Icon=orbital
Categories=Education;Science;Chemistry;
Keywords=chemistry;periodic table;elements;science;
EOF
    appimagetool "$APPDIR" "dist/Orbital-$VERSION-x86_64.AppImage"
    echo "built dist/Orbital-$VERSION-x86_64.AppImage"
fi

echo "done. tarball: dist/Orbital-$VERSION-linux-x64.tar.gz"
