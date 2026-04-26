# FotoDerp

Open-source AI-powered photo management for professional photographers.

## Planned Features

- Automatic AI tagging and face recognition
- Semantic free-text search ("dog on the beach at sunset")
- Similarity search (find visual duplicates and similar images)
- Culling workflow for fast image selection
- Aesthetic rating via AI
- OCR — text recognition in photos
- Cross-platform (Web UI + CLI)
- AI-backend-independent: llama.cpp OpenAI-compatible endpoint

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **AI**: llama.cpp `/v1/chat/completions` + `/v1/embeddings`
- **Database**: PostgreSQL (with pgvector for vector search)
- **Frontend**: React / Svelte (Web UI)
- **CLI**: Python (rich)

## Installation

```bash
cd FotoDerp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Getting Started

```bash
# Initialize database
fotoerp db init

# Import photo directory
fotoerp import /path/to/photos

# Start AI analysis
fotoerp analyze --start

# Start web UI
fotoerp serve
```

## License

MIT — Open Source
