#!/bin/bash
# FotoDerp Uninstaller (Linux)
# usage: sudo ./uninstall.sh [--keep-data]

KEEP_DATA=false
if [[ "${1}" == "--keep-data" ]]; then
    KEEP_DATA=true
fi

APP_NAME="FotoDerp"
DESKTOP_FILE="/usr/share/applications/fotoderp.desktop"
ICON_DIR="/usr/share/icons/hicolor"
DATA_DIR="$HOME/.local/share/FotoDerp"
CONFIG_DIR="$HOME/.config/FotoDerp"

echo "=== FotoDerp Uninstaller ==="

# AppImage entfernen (wenn in /opt)
if [ -f "/opt/$APP_NAME/$APP_NAME" ]; then
    echo "Removing AppImage from /opt..."
    sudo rm -rf "/opt/$APP_NAME"
fi

# .desktop file entfernen
if [ -f "$DESKTOP_FILE" ]; then
    echo "Removing desktop entry..."
    sudo rm -f "$DESKTOP_FILE"
fi

# MIME-Type-Association entfernen
echo "Removing MIME associations..."
xdg-mime default null image/x-fotoderp 2>/dev/null || true

# Icons entfernen
if [ -d "$ICON_DIR/hicolor" ]; then
    echo "Removing icons..."
    sudo rm -rf "$ICON_DIR/hicolor/512x512/apps/fotoderp*" 2>/dev/null || true
fi

# Startmenü-Verzeichnis entfernen
START_MENU="$HOME/.local/share/applications"
if [ -f "$START_MENU/fotoderp.desktop" ]; then
    rm -f "$START_MENU/fotoderp.desktop"
fi

# App-Daten (optional)
if [ "$KEEP_DATA" = false ]; then
    echo "Removing app data..."
    rm -rf "$DATA_DIR"
    rm -rf "$CONFIG_DIR"
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
