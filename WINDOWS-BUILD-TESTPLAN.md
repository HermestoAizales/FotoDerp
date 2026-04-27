# Windows Testversion — Build & Test Plan

## Ziel
Eine testbare Windows-Version von FotoDerp innerhalb weniger Stunden erstellen.

## Status (2025-04-27)

### Was funktioniert
- ✅ Backend Dev-Modus (`uvicorn fotoerp_backend.main:app`) — alle Endpoints
- ✅ Absolute Imports in allen Python-Dateien (fix für Nuitka)
- ✅ `lifespan` statt deprecated `@app.on_event("startup")`
- ✅ CI/CD Pipeline konfiguriert (build.yml + release.yml)
- ✅ Linux AppImage gebaut (216MB, ARM64) — lokal getestet

### Was noch nicht funktioniert
- ❌ Nuitka-compiled Binary crasht sofort auf ARM64 Linux
  - Exit code 0, keine Fehlermeldung
  - Wahrscheinlich ARM64-spezifisch oder Python 3.13 + Nuitka 2.8.x Inkompatibilität
- ⏳ Windows Build noch nicht getestet (kein x86_64 System verfügbar)

## Vorgehen

### Schritt 1: Changes pushen
```bash
cd /home/hermes/FotoDerp
git add .github/workflows/build.yml BUILD.md SESSION-PROMPT.md \
       backend/build_backend.py backend/fotoerp_backend/ \
       package.json
git commit -m "ci: optimize build pipeline + fix Nuitka import issues"
git push origin main
```

### Schritt 2: Windows-Build auf GitHub Actions starten
1. Gehe zu: https://github.com/[repo]/actions/workflows/build.yml
2. Klicke "Run workflow"
3. Wähle Plattform: **windows** (oder leer für alle)
4. Workflow startet automatisch auf `windows-2025` Runner

### Schritt 3: Build-Artefakt herunterladen
- Nach ~15-20 Minuten sollte das Artifact verfügbar sein
- Download: `FotoDerp Setup *.exe` aus den Artifacts
- Installieren und testen

### Schritt 4: Ergebnis dokumentieren
- **Falls Windows-Build funktioniert**: Nuitka-Problem ist ARM64-spezifisch
- **Falls Windows auch crasht**: Auf PyInstaller oder Python venv umstellen

## Wichtige Dateien

| Datei | Änderung |
|-------|----------|
| `.github/workflows/build.yml` | Disk-Cleanup, Python 3.12, optimierte Pipes |
| `backend/fotoerp_backend/main.py` | Absolute Imports, lifespan handler |
| `backend/fotoerp_backend/services/*.py` | Absolute Imports |
| `backend/build_backend.py` | onefile für alle Plattformen |
| `package.json` | Venv-aware build script, x64 Linux target |
| `BUILD.md` | Nuitka Troubleshooting + Disk Space Guide |
| `SESSION-PROMPT.md` | Session Context + aktuelle Erkenntnisse |

## Plattformspezifische Backend-Pfade im Installer

| Plattform | Pfad im App-Verzeichnis |
|-----------|------------------------|
| Windows | `backend/windows/fotoerp-backend.exe` |
| macOS | `backend/darwin-arm64/fotoerp-backend` oder `darwin-x86_64/` |
| Linux | `backend/linux/fotoerp-backend` |

## Disk Space Limits

- **Max 10GB** für das gesamte Projekt auf Build-Maschinen
- GitHub Actions Runner: ~14GB free (bereinigt nach Builds)
- Nuitka build dirs werden automatisch nach dem Build gelöscht
- node_modules wird nach Build entfernt

## Backup Plan (falls Nuitka auch auf Windows crasht)

### Option A: Python venv als Runtime
```javascript
// electron/main.js — statt Nuitka-Binary:
backendProcess = spawn(pythonPath, [
  '-m', 'fotoerp_backend.main',
], { cwd: backendDir });
```
- Vorteil: Keine Compilation nötig, funktioniert sofort
- Nachteil: Größerer Installer (Python Runtime ~50MB)

### Option B: PyInstaller statt Nuitka
```bash
pip install pyinstaller
pyinstaller --onefile --name fotoerp-backend fotoerp_backend/main.py
```
- Vorteil: Bewährt auf allen Plattformen
- Nachteil: Größeres Binary als Nuitka

### Option C: Uvicorn in Electron packen
- Python + uvicorn + dependencies als extraResource
- Startet via `python -m uvicorn ...` beim App-Start
- Einfachste Lösung, aber langsamster Start
