# FotoDerp — Session Context Prompt

> **Project Language**: All code comments, documentation, and user-facing strings use English.

## Project Overview

**FotoDerp** is open-source photo management software for professional photographers.
- **Frontend**: Electron (Windows/macOS/Linux)
- **Backend**: Nuitka-compiled native binary (Python/FastAPI)
- **Database**: SQLite (no PostgreSQL, no Redis)
- **Goal**: One-click installer per platform with clean uninstallation
- **Frontend**: Electron (Windows/macOS/Linux)
- **Backend**: Nuitka-compiled native binary (Python/FastAPI)
- **Datenbank**: SQLite (kein PostgreSQL, kein Redis)
- **Ziel**: One-click Installer pro Plattform mit sauberer Deinstallation

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

## What was done in this session

### 1. Backend aufgeräumt
- **pyproject.toml**: SQLAlchemy, aiosqlite, redis, click, rich, numpy — alle entfernt
- Nur noch: fastapi, uvicorn, httpx, pillow, exifread, pydantic
- **database.py**: Komplett neu — stdlib sqlite3 statt SQLAlchemy
  - FTS5 virtual table für Volltextsuche (auto-sync via triggers)
  - BLOB-Embeddings (packed float32) für Cosine Similarity
  - WAL-Journaling für Concurrency
  - Platform-agnostic DB path (APPDATA/~/Library/~/.local/share)
- **import.py**: Keine DB-Session mehr, jede Operation committet selbst
- **search.py**: FTS5 + Cosine Similarity (stdlib math, kein numpy)
- **culling.py**: Auf sqlite3 umgestellt
- **main.py**: Alle Endpoints auf neue DB-Schicht aktualisiert
- **workers/**: Komplett gelöscht (CLI-Analyse-Worker — Electron API erledigt das)

### 2. Nuitka Build-Pipeline erstellt
- **build_backend.py**: Cross-Platform Build-Skript (linux/mac-arm/win)
  - Erkennt Zielplattform automatisch oder per `--target` Flag
  - Output: dist/<platform>/fotoerp-backend (native binary)
- **nuitka-config.ini**: Standalone-Build Konfiguration
- **requirements.txt**: Nur runtime + nuitka als build-dep

### 3. electron-builder + Installer konfiguriert
- **package.json**: Backend als extraResource, platform-spezifische Targets
  - Windows: NSIS (nicht-one-click, wählbares Verzeichnis)
  - macOS: dmg + zip (hardened runtime, notarization-ready)
  - Linux: AppImage (x86_64)
- **electron/main.js**: Erkennt Dev vs. Bundled
  - Bundled: Nuitka-Binary direkt starten
  - Dev: python3 + uvicorn
  - Backend sauber beim Schließen beenden (SIGTERM)
- **uninstaller.nsh**: Windows NSIS Custom-Uninstall
- **uninstall.sh**: Linux Uninstaller (--keep-data Flag)
- **uninstall-mac.sh**: macOS Uninstaller
- **Uninstall FotoDerp.app**: macOS .app Uninstaller Bundle
- **entitlements.plist**: Hardened Runtime für macOS Notarization
- **BUILD.md**: Komplette Build & Deployment Dokumentation

### 4. DESIGN.md aktualisiert
- Architektur-Diagramm: PostgreSQL/Redis → SQLite allein
- Schema: SQLite mit FTS5 + BLOB-Embeddings
- Phase 1: Nuitka + electron-builder als offen

### 5. Frontend-Backend-Schnittstelle repariert (current session)
- **electron/main.js**: IPC Handlers ergänzt
  - `dialog:selectFolder` — Ordnerwahl für Import
  - `dialog:openFile` — Dateidialog
  - `file:imageBlobUrl` — Lokale Bilder als base64 blob URL (unterstützt RAW, HEIC etc.)
  - `app:getVersion` — App-Version
- **electron/preload.js**: Remote-API entfernt (deprecated), alle IPC Bridges aktualisiert
- **frontend/js/app.js**: Komplett überarbeitet
  - Suchanfragen → `/api/search?query=` statt `/api/photos?search=`
  - Bilder via Electron IPC geladen (funktioniert für jedes Dateiformat)
  - Preview zeigt `photo.analyses` Array korrekt an
  - Tag-Klick filtert nach Tag
  - Englische UI-Strings
- **frontend/index.html**: Englische Labels

### 6. Backend-Endpoints vervollständigt (current session)
- **backend/database.py**: Neue Query-Funktionen
  - `list_all_tags()` — Alle Tags mit usage_count
  - `list_all_persons()` — Erkannte Personen
  - `get_recent_photos()` — Neueste Fotos
  - `get_storage_used()` — Gesamtspeicher in Bytes
  - `add_person()` / `add_face()` — Person/Face-Erkennung speichern
- **backend/main.py**: Endpoints mit echten Daten
  - `/api/tags` — Query Datenbank, gruppiert nach Kategorie
  - `/api/persons` — Liste erkannte Personen
  - `/api/analytics/overview` — Echte Counts, Storage, Recent Activity
  - `/api/culling/projects/{id}` — Projekt aus CullingService

### 7. Icons generiert (current session)
- **icons/icon.png** (512x512 PNG) — macOS .icns Quelle
- **icons/icon.ico** (6 Auflösungen: 16, 32, 48, 64, 128, 256) — Windows Icon
- **icons/generate_icons.py** — Reines Python, keine externen Dependencies

### 8. Search mit Pagination + Analysis Queue (current session)
- **backend/main.py**: 
  - `/api/search` — Pagination mit `page`/`limit`, echter `total` Count
  - `/api/analyze/status` — Echte Queue: tracking (`running`, `processed`, `total`, `queue_size`)
  - `/api/analyze/start` — Background-Task mit Fortschritt
  - `_run_analysis_batch()` — Neuer Background-Worker: analysiert Fotos, speichert Tags/Faces/Analysen in DB
  - Global `_analysis_queue` State für Status-Endpunkt
  - `hashlib` + `set_photo_status` + `add_face` imports hinzugefügt
- **backend/database.py**: 
  - `search_photos()` — Jetzt mit `offset` Parameter
  - Neue Funktion: `count_search_results()` für Gesamtanzahl
- **backend/services/import.py → import_.py**: Umbenannt (Python keyword `import`)
- **backend/services/culling.py**: Import auf `import_` aktualisiert
- **backend/services/llama_server.py**: Doppelte `rope_freq_scale` Zeile entfernt
- **frontend/index.html**: Such-Placeholder auf Englisch
- **frontend/js/app.js**: Search mit Fallback zu `/api/photos`

### 9. KI-Analyse mit DB-Persistenz (current session)
- **backend/main.py `_run_analysis_batch()`**: 
  - Speichert Tags in `tags` + `photo_tags` Tabellen
  - Speichert Analyse-Ergebnisse in `analyses` Tabelle
  - Speichert Faces in `faces` Tabelle
  - Setzt Foto-Status auf `done`/`analyzing`/`error`
  - Fortschritt wird im `_analysis_queue` getrackt

### 10. Preview-Endpoint + Rating/Favorites + Culling (current session)
- **backend/main.py**: 
  - `/api/photos/{id}/preview` — Thumbnail-Generierung mit Pillow (JPEG, max 400x400)
  - `/api/photos/{id}/rating` — Rating setzen (0-5)
  - `/api/photos/favorites` — Favoriten (Rating >= 3)
  - `/api/collections` — CRUD für Collections (list, create, add/remove photos, delete)
- **backend/database.py**: 
  - `list_photos()` / `count_photos()` — Jetzt mit `min_rating` Filter
  - Neue Funktionen: `update_photo_rating()`, `get_favorites()`
  - Collection-Helper: `list_collections()`, `create_collection()`, `add_to_collection()`, `remove_from_collection()`, `delete_collection()`
- **backend/services/culling.py**: 
  - `select_photo()` — Markiert Foto als 'done'
  - `reject_photo()` — Markiert Foto als abgelehnt
- **frontend/js/app.js**: 
  - Star Rating Component (interaktiv, hover + click)
  - `/api/photos/favorites` View in Sidebar
  - `loadFavorites()` Funktion
- **frontend/css/style.css**: 
  - `.star-rating` Styles mit Hover-Scale Effekt

### 11. CI/CD Pipeline + LICENSE (current session)
- **LICENSE** — MIT License Datei erstellt (NSIS Blocker behoben)
- **.github/workflows/build.yml** — Vollstaendige Cross-Platform Build Pipeline:
  - `backend-check`: Python compilation check
  - `build-app`: Matrix-Builds fuer Linux/macOS/Windows (Nuitka + electron-builder)
  - `release`: GitHub Release mit Draft auf Tags (v*)
  - macOS Notarization (optional via Secrets)
- **.github/workflows/ci.yml** — Lightweight PR Checks (lint, compile, npm install)
- **BUILD.md** — Aktualisierte CI/CD Dokumentation

## Wichtige Dateien (Kurzbeschreibung)

| Datei | Beschreibung |
|-------|-------------|
| `backend/pyproject.toml` | Dependencies — nur 6 runtime deps |
| `backend/database.py` | stdlib sqlite3, FTS5, BLOB-Embeddings + rating, favorites, collections |
| `backend/main.py` | FastAPI App — alle Endpoints (preview, rating, favorites, collections) |
| `backend/models.py` | Pydantic Models (unchanged) |
| `backend/services/import_.py` | Foto-Import, EXIF, phash (umbenannt von import.py) |
| `backend/services/search.py` | FTS5 + Cosine Similarity |
| `backend/services/culling.py` | Bildgruppierung + select/reject/smart |
| `backend/services/analysis.py` | KI-Analyse (unchanged) |
| `backend/services/openapi_adapter.py` | llama.cpp/OpenAI Adapter |
| `backend/services/llama_server.py` | llama.cpp Server Manager |
| `backend/build_backend.py` | Nuitka Cross-Platform Build |
| `electron/main.js` | Electron Main — Dev/Bundled + IPC handlers |
| `electron/preload.js` | IPC Bridge (updated, no remote) |
| `electron/uninstaller.nsh` | Windows NSIS Cleanup |
| `electron/uninstall.sh` | Linux Uninstaller |
| `electron/uninstall-mac.sh` | macOS Uninstaller |
| `electron/entitlements.plist` | macOS Hardened Runtime |
| `frontend/js/app.js` | Frontend app (rewritten for English, real API) |
| `frontend/index.html` | UI (English labels) |
| `frontend/css/style.css` | Styles (unchanged) |
| `icons/icon.png` | 512x512 PNG (macOS source) |
| `icons/icon.ico` | Multi-res ICO (Windows) |
| `package.json` | electron-builder Config |
| `BUILD.md` | Build & Deployment Guide |
| `DESIGN.md` | Architektur + Phase Planning |

## Wichtige Entscheidungen

1. **Kein SQLAlchemy** — stdlib sqlite3 ist schlanker, keine Abhängigkeit
2. **Kein PostgreSQL** — Desktop-App, SQLite reicht völlig
3. **Kein Redis** — Nicht nötig, alles lokal
4. **Nuitka statt PyInstaller** — Kleineres Binary, schnellere Startzeit
5. **Keine CLI** — Alles über Electron API, kein click/rich
6. **FTS5 statt pgvector/hnswlib** — SQLite native Volltextsuche
7. **BLOB-Embeddings** — packed float32, Cosine Similarity in Python
8. **App-Daten getrennt** — DB in APPDATA/Library/~/.local/share (nicht im Installationsordner)

## Build-Befehle

```bash
# Backend kompilieren
cd backend && python3 build_backend.py

# Komplette App bauen
npm run build

# Einzelne Plattformen
npm run build:linux   # AppImage
npm run build:mac     # dmg + zip
npm run build:win     # NSIS
```

## Nächste Schritte (für nächste Session)

1. `pip install nuitka` und `python3 build_backend.py` testen
2. Backend starten (`uvicorn`) und alle Endpoints manuell testen
3. `npm ci && npm run build` für komplette App bauen
4. CI/CD Workflow aus BUILD.md einrichten
5. Frontend-View-Toggles (Grid/Liste) funktional machen
6. Semantic Search (Text→Embedding via OpenAPI-Adapter) implementieren
7. Culling UI in Frontend einbauen (Projekt erstellen, Gruppen anzeigen, select/reject)
8. Collections UI im Frontend (Sidebar mit Collections, Drag & Drop)
9. Uninstaller für alle Plattformen final testen
