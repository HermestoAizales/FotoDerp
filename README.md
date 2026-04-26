# FotoDerp

Open-source AI-powered photo management for professional photographers.

## Features

- 🤖 **Automatic AI tagging** — auto-generates tags from image content using vision models
- 👤 **Face recognition** — detects and groups faces across your photo library
- 🔍 **Semantic search** — natural language queries like "dog on the beach at sunset"
- 🔁 **Similarity search** — find visual duplicates and similar images via embeddings
- ✂️ **Culling workflow** — group similar shots, quickly select the best ones
- ⭐ **Aesthetic rating** — AI-powered quality scoring (1-5 stars)
- 📝 **OCR** — text recognition embedded in photos
- 📚 **Collections** — organize photos into custom collections
- 📊 **Analytics** — overview stats, recent activity, storage usage

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Nuitka (compiled)
- **AI**: llama.cpp `/v1/chat/completions` + `/v1/embeddings`
- **Database**: SQLite (embedded, no external dependencies)
- **Frontend**: Vanilla HTML/CSS/JS (no framework)
- **Desktop**: Electron (cross-platform packaging)
- **Multi-backend**: llama.cpp, Ollama, vLLM, LM Studio, Jan.ai

## Quick Start

```bash
# Clone the repo
git clone https://github.com/HermestoAizales/FotoDerp.git
cd FotoDerp

# Start the backend (dev mode)
npm run start:backend

# In another terminal, launch the desktop app
npm run dev
```

Or use the build script to compile the backend and create a standalone app:

```bash
npm run build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/photos/import` | Import photo directories |
| `GET` | `/api/photos` | List photos (paginated, filterable) |
| `GET` | `/api/photos/{id}` | Get single photo with metadata |
| `GET` | `/api/photos/{id}/preview` | Generate thumbnail preview |
| `POST` | `/api/analyze/start` | Start batch AI analysis |
| `GET` | `/api/analyze/status` | Real-time analysis progress |
| `GET` | `/api/search` | Full-text / semantic search |
| `GET` | `/api/tags` | List all tags (grouped by category) |
| `POST` | `/api/tags/{name}` | Assign tag to photos |
| `GET` | `/api/persons` | List recognized persons |
| `GET` | `/api/photos/{id}/similar` | Find similar images |
| `POST` | `/api/culling/projects` | Create culling project |
| `GET` | `/api/collections` | List collections |
| `POST` | `/api/collections` | Create collection |
| `PUT` | `/api/photos/{id}/rating` | Set photo rating (0-5) |
| `GET` | `/api/photos/favorites` | Get favorite photos |
| `GET` | `/api/analytics/overview` | Analytics dashboard data |
| `GET/PUT` | `/api/settings` | App settings |
| `GET` | `/api/models` | List available AI models |
| `POST` | `/api/models/{id}/activate` | Activate a model |
| `POST` | `/api/models/download` | Download model from Hugging Face |

## Model Support

### Local GGUF Models
Auto-discovers GGUF files in `~/LLMs/` and `~/.cache/fotoderp/models/`.

### Default Models
- **LLaVA 1.5 7B** — Good balance of speed/quality
- **Moondream2** — Ultra-lightweight, runs on CPU
- **Qwen2-VL 2B** — Modern vision-language model

### External Endpoints
Configure any OpenAI-compatible API via `/api/settings` or the UI.

## Build & Distribution

Built with Electron + electron-builder for cross-platform releases:

| Platform | Format | Architecture |
|----------|--------|-------------|
| Linux | AppImage | x64 |
| macOS | DMG / ZIP | arm64, x64 |
| Windows | NSIS Installer | x64 |

CI builds automatically on push to `main` and on tags (`v*`).

## License

MIT — Open Source
