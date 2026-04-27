# Project Profile: FotoDerp

Open-source AI-powered photo management for professional photographers. Desktop application with Electron frontend and Python/FastAPI backend. Features AI auto-tagging, face recognition, semantic search, culling workflow, and aesthetic rating. UX inspired by professional photo management tools with improved workflow.

> Last updated: 2026-04-27T00:55:19.720Z | Version: 2

## Goals

- **feature** [high]: Erstellung und Verbesserung von FotoDerp - erste Testversion für Windows (active)
- **feature** [high]: Vollständiger Feature-Set: AI-Tagging, Face Recognition, Semantic Search, Similarity Search, Culling Workflow, Aesthetic Rating, OCR, Collections, Analytics (active)
- **quality** [high]: Sauberer Code, Tests, Profi-Standards (wie von einem professionellen Entwickler erwartet) (active)
- **technology** [medium]: CUDA/Vulkan Unterstützung für AI-Inference optimieren (pending)
- **technology** [high]: Multi-Platform Support (Linux, macOS, Windows) mit stabilen Builds (active)
- **ux** [high]: UX orientiert an professionellen Foto-Verwaltungs-Tools, aber besser - intuitive Bedienung für Profi-Fotografen (active)

## Tech Stack

### Languages

- Python v3.11+ (primary)
- JavaScript (primary)
- HTML/CSS (frontend)

### Frameworks

- FastAPI vlatest [backend-web]
- Electron v^33.0.0 [desktop]
- electron-builder v^25.0.0 [build]

### Databases

- SQLite (embedded) vlatest

### Infrastructure

- llama.cpp [ai-inference]
- Ollama [ai-inference]
- vLLM [ai-inference]
- CUDA [gpu-acceleration]
- Vulkan [gpu-acceleration]

**Build tools:** Nuitka (Python compiler), electron-builder

**Package managers:** npm, pip

## Architecture

**Pattern:** Desktop application with separate backend service (Electron + Python FastAPI)
**Data flow:** Electron app launches Python FastAPI backend (via npm start script), frontend (HTML/JS) communicates with backend via HTTP API (localhost:8765), backend uses SQLite for storage and llama.cpp-compatible endpoints for AI features

### Modules

| Module | Path | Description |
|--------|------|-------------|
| electron | `electron/` | Electron desktop app shell - main process and preload scripts |
| frontend | `frontend/` | Vanilla HTML/CSS/JS frontend served by Electron |
| backend | `backend/` | Python FastAPI backend with AI services, photo management, and SQLite database |
| icons | `icons/` | Application icons and icon generation scripts |

**Entry points:** `electron/main.js`, `backend/fotoerp_backend/main.py`, `frontend/js/app.js`

## Team

- **pi agent (Babysitter)** (Lead Developer / Orchestrator): Full development, Architecture, Testing, Build, Deployment, Autonomous operation

## Workflows

### development

Local development workflow with npm scripts
**Triggers:** manual

1. npm run start:backend
2. npm run dev

### build

Build distributable packages for multiple platforms
**Triggers:** manual, ci-build, release

1. npm run build:backend
2. electron-builder --linux/mac/win

### ci

GitHub Actions CI pipeline
**Triggers:** push, pull_request

1. python syntax check
2. npm ci check
3. python lint (ruff)

### trunk-based

Direct commits to main branch (single developer workflow)
**Triggers:** development-complete

1. develop
2. commit
3. push to main

## Processes

- **cradle/project-install** (`undefined`, undefined) - Project setup and onboarding

## Tools

### Linting

- ruff

## Services

- **llama.cpp** (ai-inference) - http://127.0.0.1:8080/v1
- **Ollama** (ai-inference) - http://127.0.0.1:11434
- **GitHub** (version-control) - https://github.com/HermestoAizales/FotoDerp
- **Hugging Face** (model-repository) - https://huggingface.co/

## CI/CD

**Provider:** GitHub Actions
**Config files:** `.github/workflows/build.yml`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`

### Pipelines

- **CI Checks** (trigger: push to main, develop,pull_request to main)
  Stages: python-check -> npm-check -> lint-python
- **Build** (trigger: push to main,tags v*)
  Stages: build-linux -> build-mac -> build-windows

## Pain Points

- **high** [build]: Complex build process with Nuitka compilation and multi-platform electron-builder
  - Remediation: Stabilize build system, add comprehensive tests for build process
- **medium** [build]: Windows builds require special handling (Dependencies, DLL management)
  - Remediation: Create dedicated Windows build workflow with proper dependency management
- **high** [development]: Entwicklung stoppt weil das Model stoppt
  - Remediation: Autonomous operation with babysitter orchestration - no manual intervention required

## Bottlenecks

- Build system instability - multiple commits fixing Nuitka, electron-builder, Windows-specific issues at build.yml, package.json, build_backend.py (12+ fix commits)
  Impact: high
- Windows build challenges with DLL dependencies and icon handling at build.yml, electron-builder config (5+ commits)
  Impact: medium

## Conventions

### Naming

- **javascript:** camelCase for functions/variables, PascalCase for classes
- **python:** snake_case for functions/variables, PascalCase for classes

### Git

- **commitFormat:** Conventional commits (ci:, fix:, feat:, docs:, Translate:)
- **branchStrategy:** trunk-based (direct commits to main)
- **mergeStrategy:** Direct commits, no merge commits

**Error handling:** Try-except blocks in Python, try-catch in JavaScript, HTTP exception handling via FastAPI

**Testing:** Comprehensive tests required (pytest for Python, Jest/Vitest for JS when added)

### Additional Rules

- German comments in Python backend code allowed
- English comments in JavaScript frontend code
- API endpoints follow RESTful conventions with /api/ prefix
- All documentation in English (migrated from German)
- Clean code standards - as expected from a professional developer
- Never mention 'Excire Foto 2027' or similar inspiration sources in code or docs

## Repositories

- **FotoDerp** - https://github.com/HermestoAizales/FotoDerp.git

## CLAUDE.md Instructions

- Use 'babysitter call --process gsd/execute' for autonomous task execution
- Use 'babysitter call --process gsd/plan' for feature planning
- Use 'babysitter call --process gsd/verify' for feature verification
- Use 'babysitter call --process methodologies/TDD' for Test-Driven Development
- Focus on professional photo management features (tagging, face rec, search, culling)
- Maintain clean code standards with proper tests (TDD)
- Build for Windows first, then optimize (CUDA/Vulkan support)
- UX should be intuitive for professional photographers - better than existing tools
- Autonomous operation - let babysitter handle the orchestration
- Never mention 'Excire Foto 2027' or similar inspiration sources in code or docs
- Use fotoderp-rdp-testing skill for Windows VM testing via RDP

## Installed Extensions

- Skills: fotoderp-rdp-testing
- Processes: cradle/project-install
