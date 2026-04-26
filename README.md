# FotoDerp

Open-Source KI-gestützte Fotoverwaltung — ähnlich wie FotoDerp, aber besser.

## Features (geplant)

- Automatische KI-Tagging und Gesichtserkennung
- Semantische Freitextsuche ("Hund am Strand bei Sonnenuntergang")
- Ähnlichkeitssuche (finde visuelle Duplikate und ähnliche Bilder)
- Culling-Workflow für schnelle Bildauswahl
- Ästhetik-Bewertung per KI
- OCR — Texterkennung in Fotos
- Cross-platform (Web UI + CLI)
- KI-backend-unabhängig: llama.cpp OpenAI-kompatibler Endpunkt

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **KI**: llama.cpp `/v1/chat/completions` + `/v1/embeddings`
- **Datenbank**: PostgreSQL (mit pgvector für Vektorsuche)
- **Frontend**: React / Svelte (Web UI)
- **CLI**: Python (rich)

## Installation

```bash
cd FotoDerp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Erste Schritte

```bash
# Datenbank initialisieren
fotoerp db init

# Bilderverzeichnis importieren
fotoerp import /pfad/zu/fotos

# KI-Analyse starten
fotoerp analyze --start

# Web UI starten
fotoerp serve
```

## Lizenz

MIT — Open Source
