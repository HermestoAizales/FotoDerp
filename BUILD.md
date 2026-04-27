# FotoDerp — Build & Deployment Guide

## Architektur

```
FotoDerp App (pro Plattform)
├── Electron App (Renderer + Main Process)
│   ├── electron/          (main.js, preload.js)
│   ├── frontend/          (HTML/CSS/JS UI)
│   └── backend/           (Nuitka-compiled Binary)
│       └── fotoerp-backend  (native executable)
├── App-Daten (nutzerseitig)
│   └── ~/.../FotoDerp/    (SQLite DB, Einstellungen)
└── Uninstaller
    ├── uninstaller.nsh    (Windows NSIS)
    ├── uninstall-mac.sh   (macOS .app)
    └── uninstall.sh       (Linux)
```

## Voraussetzungen

### Backend Build (Nuitka)
- Python 3.11+ mit pip
- Nuitka: `pip install nuitka`
- Für Cross-Platform: VMs/CI für jede Zielplattform

### Electron Build
- Node.js 20+
- npm

## Build-Prozess

### 1. Backend kompilieren (Nuitka)

```bash
# Aktuelle Plattform
cd backend
python3 build_backend.py

# Output: dist/<platform>/fotoerp-backend (native binary)
```

### 2. Electron App bauen

```bash
# Alle Plattformen
npm run build

# Einzelne Plattformen
npm run build:linux   # AppImage
npm run build:mac     # dmg + zip
npm run build:win     # NSIS Installer
```

### 3. Output

```
dist/
├── FotoDerp-0.1.0.AppImage       (Linux)
├── FotoDerp 0.1.0.dmg            (macOS)
├── FotoDerp Setup 0.1.0.exe      (Windows)
└── ...
```

## Plattform-spezifische Details

### Windows (NSIS)
- **Installer**: NSIS (nicht-one-click, wählbares Installationsverzeichnis)
- **Desktop-Shortcut**: Ja
- **Startmenü**: Ja
- **Uninstaller**: Automatisiert über NSIS + custom uninstaller.nsh
- **Installationspfad**: `C:\Program Files\FotoDerp\` oder benutzerdefiniert

### macOS (dmg)
- **Installer**: dmg mit Drag-to-Applications
- **Hardened Runtime**: Ja (entitlements.plist)
- **Notarization**: Benötigt Apple Developer Account
- **Uninstaller**: `Uninstall FotoDerp.app` im dmg enthalten
- **Code Signing**: Benötigt Developer ID Certificate

### Linux (AppImage)
- **Installer**: AppImage (portable, keine Installation nötig)
- **Desktop-Integration**: .desktop file + Icons werden automatisch erstellt
- **Uninstaller**: `./uninstall.sh [--keep-data]`
- **Architektur**: x86_64

## Uninstall

### Windows
Automatisch über System-Systemsteuerung oder Startmenü-Eintrag.
Custom cleanup (Shortcuts, Registry) in `electron/uninstaller.nsh`.

### macOS
1. `Uninstall FotoDerp.app` aus dem dmg starten ODER
2. Manuelles Loeschen:
   ```bash
   rm -rf /Applications/FotoDerp.app
   rm -rf ~/Library/Application\ Support/FotoDerp
   rm -rf ~/Library/Caches/FotoDerp
   ```

### Linux
```bash
./uninstall.sh              # Mit Datenloeschung
./uninstall.sh --keep-data  # Nur App entfernen, Daten behalten
```

## CI/CD (Empfohlen)

FotoDerp verwendet GitHub Actions fuer automatisches Bauen aller Plattformen.

### Workflow-Struktur

| Datei | Zweck |
|-------|-------|
| `.github/workflows/ci.yml` | Quick checks (lint, compile, npm install) — laeuft bei jedem PR/Push |
| `.github/workflows/build.yml` | Vollstaendige Cross-Platform Builds — laeuft bei Push auf main/develop und Tags |

### Lokaler Build testen

Bevor du pushst, teste den Build lokal:

```bash
# Backend kompilieren
cd backend && pip install nuitka && python3 build_backend.py

# Electron bauen (aktuelle Plattform)
npm run build:linux   # oder: mac / win
```

### Release erstellen

```bash
git tag v0.2.0
git push origin v0.2.0
```

Das triggert automatisch den `build.yml` Workflow und erstellt ein Draft-Release mit allen Artifacts.

### macOS Notarization (optional)

Fuer signierte macOS Builds brauche die folgenden Secrets im Repo:

| Secret | Beschreibung |
|--------|-------------|
| `APPLE_ID` | Apple Developer Account E-Mail |
| `APPLE_PASSWORD` | App-spezifisches Passwort |
| `APPLE_TEAM_ID` | Team ID aus Developer Portal |

Die Notarization wird automatisch nach dem dmg Build ausgefuehrt.

## Troubleshooting

### Nuitka-Build fehlschlaegt
- Sicherstellen dass alle Dependencies installiert sind: `pip install -r requirements.txt`
- Fuer CUDA/GPU-Support: nvcc im PATH

### Electron-Build fehlschlaegt
- `npm cache clean --force && npm ci`
- electron-builder cache: `rm -rf ~/.cache/electron-builder`

### Backend startet nicht in bundled mode
- Binary executable permissions pruefen: `chmod +x dist/*/fotoerp-backend`
- Fehlenede Shared Libraries: `ldd dist/linux/fotoerp-backend` (Linux)

### Nuitka-compiled binary exits immediately (exit code 0, no output)
**Known issue on ARM64 Linux with Python 3.13 + Nuitka 2.8.x**

Symptoms:
- Binary starts but exits immediately with exit code 0
- No error output, no server logs
- Dev mode (`uvicorn`) works fine

Workarounds:
1. **Test on x86_64 first**: Use GitHub Actions Windows runner — the issue may be ARM64-specific
2. **Dev mode for testing**: Set `NODE_ENV=development` to use uvicorn instead of Nuitka binary
3. **Fallback**: Ship Python venv as runtime (`python -m fotoerp_backend.main`) instead of compiled binary

**Current status** (2025-04-27):
- ✅ Dev mode works on all platforms
- ❌ Nuitka 2.8.10 onefile crashes on ARM64 Linux
- ⏳ Testing on Windows x86_64 via GitHub Actions CI

## Disk Space Management

**Max 10GB project size on build machines.**

Cleanup steps after builds:
```bash
# Nuitka build artifacts
rm -rf backend/dist/linux/main.*
rm -rf backend/dist/win/main.*
rm -rf backend/dist/darwin*/main.*

# Electron node_modules
rm -rf node_modules

# Python cache
find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
```
