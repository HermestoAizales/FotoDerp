# FotoDerp - Design & Architektur

## Ziel
Open-Source Fotoverwaltungssoftware mit ähnlicher UX wie FotoDerp, aber besser:
- **Schneller** — asynchrone Verarbeitung, Caching
- **Plattformunabhängig** — Electron (Windows/macOS/Linux)
- **KI-backend-unabhängig** — llama.cpp OpenAI-kompatibler Endpunkt
- **Modular** — Python Backend + Electron Frontend
- **Transparent** — Open Source, keine Blackbox-KI

---

## GUI-Design (FotoDerp-ähnlich, aber besser)

### Layout (3-Spalten-Design, more modern)

```
┌─────────────────────────────────────────────────────────────┐
│  Toolbar: Suche | Filter | Ansicht | Import | Analyse       │
├──────────┬──────────────────────────┬───────────────────────┤
│          │                          │                       │
│ NAV      │  HAUPTANSICHT            │  DETAIL/PREVIEW       │
│          │                          │                       │
│ Bibliothek│ ┌──┐ ┌──┐ ┌──┐ ┌──┐   │ Bild vorschau         │
│          │ │📷│ │📷│ │📷│ │📷│   │                         │
│ Ordner   │ ├──┤ ├──┤ ├──┤ ├──┤   │ Metadaten               │
│          │ │📷│ │📷│ │📷│ │📷│   │ ──────────────────      │
│ Stichworte│ └──┘ └──┘ └──┘ └──┘   │ Tags: [Hund][Strand]  │
│          │                          │                       │
│ Personen │ ┌──┐ ┌──┐ ┌──┐         │ KI-Tags:             │
│          │ 👤│ 👤│ 👤│           │ - Hund, golden       │
│          └──┘ └──┘ └──┘           │ - Strand, Tag        │
│          │                          │ - Weitwinkel         │
│ Culling  │ ┌──┐ ┌──┐             │                       │
│          │ 🗑│ ⭐│               │ Ähnliche Bilder:     │
│          └──┘ └──┘               │ ┌──┐ ┌──┐           │
│ Analytics│                        │ │📷│ │📷│           │
│          │                          │ └──┘ └──┘           │
├──────────┴──────────────────────────┴───────────────────────┤
│ Status: 12.847 Bilder | 3.214 Stichwörter | KI: bereit      │
└─────────────────────────────────────────────────────────────┘
```

### Was BESSER als FotoDerp ist:

| Aspekt | FotoDerp | FotoDerp |
|--------|------------|----------|
| GUI-Framework | Electron (?) | Electron (offiziell) |
| Suchgeschwindigkeit | Sekundenschwer | Millisekunden (Index + Vektoren) |
| KI-Analyse | Proprietär, nicht konfigurierbar | Jeder OpenAI-kompatible Endpoint |
| Plugin-System | Nur Lightroom | Erweiterbar (Python Plugins) |
| API | Begrenzt | Vollständige REST API |
| Lizenz | ~100€ einmalig | Kostenlos, Open Source |
| Multimodal | Nein (nur Bildanalyse) | Ja — Vision-Modelle für Text in Bildern |
| OCR | Nicht vorhanden | Integriert via Vision-Modell |
| Zusammenarbeit | Nur Office Edition | Native Sharing-Funktionen |
| Performance | Single-threaded Analyse | Async, parallele Verarbeitung |

---

## Architektur

```
┌──────────────────────────────────────────────────────────────┐
│                    ELEKTRON APP (Desktop)                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              Renderer Process (HTML/CSS/JS)          │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │           Frontend (index.html + app.js)     │   │    │
│  │  │  - Photo Grid / Detail View                  │   │    │
│  │  │  - Search UI                                 │   │    │
│  │  │  - Sidebar Navigation                        │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  └─────────────────────────┬────────────────────────────┘    │
│                            │ IPC                              │
│  ┌─────────────────────────▼────────────────────────────┐    │
│  │              Main Process (main.js)                   │    │
│  │  - Fenster-Management                                │    │
│  │  - Backend-Start/Stop                                │    │
│  │  - IPC Bridge                                        │    │
│  └─────────────────────────┬────────────────────────────┘    │
├────────────────────────────┼─────────────────────────────────┤
│                             │ HTTP / WebSocket               │
│                     FOTO DERP BACKEND                      │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              FastAPI (Python)                        │    │
│  │  ┌──────────┐ ┌──────────────┐ ┌──────────────────┐  │    │
│  │  │  API     │ │  Worker      │ │  Scheduler       │  │    │
│  │  │  Routes  │ │  Queue       │ │  (asyncio)       │  │    │
│  │  └────┬─────┘ └──────┬───────┘ └────────┬─────────┘  │    │
│  │       │              │                   │            │    │
│  │  ┌────▼──────────────▼───────────────────▼─────────┐  │    │
│  │  │              Core Engine                        │  │    │
│  │  │  - Bild-Import & Metadaten                       │  │    │
│  │  │  - Vorschau-Generierung                          │  │    │
│  │  │  - KI-Analyse-Pipeline                           │  │    │
│  │  │  - Index-Verwaltung                              │  │    │
│  │  └─────────────────────┬───────────────────────────┘  │    │
│  └────────────────────────┼──────────────────────────────┘    │
│                           │                                   │
│  ┌────────────────────────▼──────────────────────────────┐    │
│  │              KI Backend Adapter                       │    │
│  │  ┌──────────────────────────────────────────────┐     │    │
│  │  │  llama.cpp OpenAI-kompatibler Endpunkt        │     │    │
│  │  │  /v1/chat/completions                         │     │    │
│  │  │  /v1/embeddings                               │     │    │
│  │  └──────────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐                             │
│  │ SQLite     │  │ Redis      │                             │
│  │ (Index)    │  │ (Cache)    │                             │
│  └────────────┘  └────────────┘                             │
└──────────────────────────────────────────────────────────────┘
```

---

## Kernkomponenten

### 1. Bild-Import & Metadaten
- Rekursiver Scan von Verzeichnissen
- EXIF/IPTC/XMP Extraktion (exifread, Pillow)
- RAW-Unterstützung (rawpy/libraw)
- Deduplizierung via Perceptual Hash (pHash)

### 2. Vorschau-Generierung
- Thumbnail (150x150), Preview (1200px breit), Original
- Asynchrone Generierung im Hintergrund
- Adaptive Qualität basierend auf Hardware

### 3. KI-Analyse-Pipeline
```
Bild → [Metadaten] → [Vorschau] → [KI-Analyse] → [Index]
                              │
                    ┌─────────▼──────────┐
                    │  llama.cpp Endpoint │
                    │                      │
                    │  - Objekterkennung   │
                    │  - Szenenerkennung   │
                    │  - Gesichtserkennung │
                    │  - Ästhetik-Rating   │
                    │  - Text/OCR          │
                    │  - Embeddings        │
                    └──────────────────────┘
```

### 4. Such-Engine
- **Textsuche**: Volltextindex (SQLite FTS5)
- **Vektorsuche**: Embeddings für semantische Suche
- **Filter**: Kombination aus Metadaten + KI-Tags + Gesichtern
- **Ähnlichkeitssuche**: Cosine-Similarity über Embeddings

### 5. Datenbank-Schema (vereinfacht)
```sql
photos: id, path, filename, width, height, format, size,
        captured_at, gps_lat, gps_lon, phash, preview_path,
        status (pending/analyzing/done/error), rating

faces: id, photo_id, person_id, x, y, width, height, confidence

persons: id, name, embedding, face_count

tags: id, name, category, usage_count

photo_tags: photo_id, tag_id

analyses: id, photo_id, type (object/scene/aesthetic/ocr),
          data (JSON), confidence, model_version

embeddings: photo_id, vector (embedding)

collections: id, name, photo_ids (JSONB), created_at
```

---

## Phase-Planung

### Phase 1 — MVP (Kernfunktionalität) ✅
- [x] Electron Grundgerüst
- [x] Python Backend mit FastAPI
- [x] Basis-Web-UI (Bildergalerie, Detailansicht)
- [x] EXIF-Metadaten-Extraktion
- [x] Vorschau-Generierung
- [x] Basic-Suche (Dateiname, Datum, Ort)
- [ ] KI-Backend-Anbindung (llama.cpp)

### Phase 2 — KI-Features
- [ ] Automatisches Tagging via KI
- [ ] Gesichtserkennung & Personenerkennung
- [ ] Ähnlichkeitssuche (Embeddings)
- [ ] Semantische Freitextsuche
- [ ] Ästhetik-Bewertung

### Phase 3 — Workflow-Tools
- [ ] Culling-Workflow
- [ ] Duplikat-Erkennung
- [ ] Batch-Operationen (Tags, Umbenennung, Export)
- [ ] Collections/Sammlungen

### Phase 4 — Erweitertes
- [ ] OCR/Texterkennung in Bildern
- [ ] Analytics-Dashboard
- [ ] Plugin-System
- [ ] API für Dritte
- [ ] Multi-User & Sharing
