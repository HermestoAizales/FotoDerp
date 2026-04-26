#!/bin/bash
# FotoDerp macOS Uninstaller
# usage: ./uninstall-mac.sh [--keep-data]

KEEP_DATA=false
if [[ "${1}" == "--keep-data" ]]; then
    KEEP_DATA=true
fi

APP_NAME="FotoDerp"
APP_PATH="/Applications/$APP_NAME.app"
CONTENTS="$APP_PATH/Contents"
DATA_DIR="$HOME/Library/Application Support/FotoDerp"
CACHE_DIR="$HOME/Library/Caches/FotoDerp"
PREFS="$HOME/Library/Preferences/com.fotoerp.app.plist"

echo "=== FotoDerp macOS Uninstaller ==="

# App entfernen
if [ -d "$APP_PATH" ]; then
    echo "Removing $APP_NAME.app..."
    rm -rf "$APP_PATH"
else
    echo "App not found at $APP_PATH"
fi

# .desktop file (falls via Flatpak/Homebrew)
rm -f ~/Applications/"$APP_NAME".app 2>/dev/null || true

# LaunchServices-Cache aktualisieren
echo "Updating LaunchServices..."
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$HOME" 2>/dev/null || true

# App-Daten (optional)
if [ "$KEEP_DATA" = false ]; then
    echo "Removing app data..."
    rm -rf "$DATA_DIR"
    rm -rf "$CACHE_DIR"
    rm -f "$PREFS"
else
    echo "Keeping app data (--keep-data specified)"
fi

echo ""
echo "FotoDerp deinstalliert."
if [ "$KEEP_DATA" = false ]; then
    echo "App-Daten wurden geloescht."
else
    echo "App-Daten wurden beibehalten: $DATA_DIR"
fi
