# FotoDerp - Design & Architecture

## Goal
Open-source photo management software with modern UX for professional photographers:
- **Faster** — asynchronous processing, caching
- **Cross-platform** — Electron (Windows/macOS/Linux)
- **AI-backend-independent** — llama.cpp OpenAI-compatible endpoint
- **Modular** — Python backend + Electron frontend
- **Transparent** — Open source, no black-box AI

---

## GUI Design

### Layout (3-Column Design)

```
┌─────────────────────────────────────────────────────────────┐
│  Toolbar: Search | Filter | View | Import | Analyze         │
├──────────┬──────────────────────────┬───────────────────────┤
│          │                          │                       │
│ NAV      │  MAIN VIEW               │  DETAIL/PREVIEW       │
│          │                          │                       │
│ Library  │ ┌──┐ ┌──┐ ┌──┐ ┌──┐     │ Image preview         │
│          │ │📷│ │📷│ │📷│ │📷│     │                       │
│ Folders  │ ├──┤ ├──┤ ├──┤ ├──┤     │ Metadata              │
│          │ │📷│ │📷│ │📷│ │📷│     │ ──────────────────    │
│ Keywords │ └──┘ └──┘ └──┘ └──┘     │ Tags: [Dog][Beach]  │
│          │                          │                       │
│ People   │ ┌──┐ ┌──┐ ┌──┐           │ AI Tags:             │
│          │ 👤│ 👤│ 👤│             │ - Dog, golden       │
│          └──┘ └──┘ └──┘            │ - Beach, Day        │
│          │                          │ - Wide-angle        │
│ Culling  │ ┌──┐ ┌──┐               │ Similar Images:     │
│          │ 🗑│ ⭐│                 │ ┌──┐ ┌──┐           │
│          └──┘ └──┘                 │ │📷│ │📷│           │
│ Analytics│                         │ └──┘ └──┘           │
│          │                          │ └──┘ └──┘           │
├──────────┴──────────────────────────┴───────────────────────┤
│ Status: 12,847 images | 3,214 keywords | AI: ready          │
└─────────────────────────────────────────────────────────────┘
```

### What makes FotoDerp better:

| Aspect | Alternative A | FotoDerp |
|--------|-------------|----------|
| GUI Framework | Electron | Electron (official) |
| Search Speed | Second-heavy | Milliseconds (index + vectors) |
| AI Analysis | Proprietary, not configurable | Any OpenAI-compatible endpoint |
| Plugin System | Only Lightroom | Extensible (Python plugins) |
| API | Limited | Full REST API |
| License | Commercial (~$100) | Free, Open Source |
| Multimodal | No (image analysis only) | Yes — Vision models for text in images |
| OCR | Not available | Integrated via Vision model |
| Collaboration | Only Office Edition | Native sharing features |
| Performance | Single-threaded analysis | Async, parallel processing |

---

## Architecture

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
│  │  - Window Management                                 │    │
│  │  - Backend Start/Stop                                │    │
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
│  │  │  - Image Import & Metadata                       │  │    │
│  │  │  - Preview Generation                            │  │    │
│  │  │  - AI Analysis Pipeline                          │  │    │
│  │  │  - Index Management                              │  │    │
│  │  └─────────────────────┬───────────────────────────┘  │    │
│  └────────────────────────┼──────────────────────────────┘    │
│                           │                                   │
│  ┌────────────────────────▼──────────────────────────────┐    │
│  │              AI Backend Adapter                       │    │
│  │  ┌──────────────────────────────────────────────┐     │    │
│  │  │  llama.cpp OpenAI-compatible Endpoint         │     │    │
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

## Core Components

### 1. Image Import & Metadata
- Recursive directory scanning
- EXIF/IPTC/XMP extraction (exifread, Pillow)
- RAW support (rawpy/libraw)
- Deduplication via Perceptual Hash (pHash)

### 2. Preview Generation
- Thumbnail (150x150), Preview (1200px wide), Original
- Asynchronous background generation
- Adaptive quality based on hardware

### 3. AI Analysis Pipeline
```
Image → [Metadata] → [Preview] → [AI Analysis] → [Index]
                          │
                  ┌─────────▼──────────┐
                  │  llama.cpp Endpoint │
                  │                      │
                  │  - Object Detection   │
                  │  - Scene Recognition  │
                  │  - Face Recognition   │
                  │  - Aesthetic Rating   │
                  │  - Text/OCR           │
                  │  - Embeddings         │
                  └──────────────────────┘
```

### 4. Search Engine
- **Text Search**: Full-text index (SQLite FTS5)
- **Vector Search**: Embeddings for semantic search
- **Filter**: Combination of metadata + AI tags + faces
- **Similarity Search**: Cosine similarity over embeddings

### 5. Database Schema (simplified)
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

## Phase Planning

### Phase 1 — MVP (Core Functionality) ✅
- [x] Electron skeleton
- [x] Python backend with FastAPI
- [x] Basic web UI (photo gallery, detail view)
- [x] EXIF metadata extraction
- [x] Preview generation
- [x] Basic search (filename, date, location)
- [ ] AI backend integration (llama.cpp)

### Phase 2 — AI Features
- [ ] Automatic AI tagging
- [ ] Face & person recognition
- [ ] Similarity search (embeddings)
- [ ] Semantic free-text search
- [ ] Aesthetic rating

### Phase 3 — Workflow Tools
- [ ] Culling workflow
- [ ] Duplicate detection
- [ ] Batch operations (tags, renaming, export)
- [ ] Collections

### Phase 4 — Advanced
- [ ] OCR/text recognition in images
- [ ] Analytics dashboard
- [ ] Plugin system
- [ ] Third-party API
- [ ] Multi-user & sharing
