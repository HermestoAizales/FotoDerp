# CLAUDE.md - FotoDerp Project Instructions

Open-source AI-powered photo management for professional photographers.

## Project Overview

FotoDerp is a desktop application with:
- **Frontend**: Electron + Vanilla HTML/CSS/JS
- **Backend**: Python FastAPI with SQLite
- **AI Features**: Auto-tagging, face recognition, semantic search, culling workflow, aesthetic rating
- **Build Targets**: Linux, macOS, Windows

## Development Commands

```bash
# Start development
npm run start:backend  # Start Python backend
npm run dev              # Start Electron app

# Build
npm run build:linux     # Linux build
npm run build:mac       # macOS build
npm run build:win       # Windows build
npm run build           # All platforms
```

## Architecture

- `electron/` - Electron main process and preload scripts
- `frontend/` - Vanilla JS/CSS frontend
- `backend/fotoerp_backend/` - FastAPI backend with AI services
- `backend/build_backend.py` - Nuitka compilation script

## Conventions

- **Python**: snake_case for functions/variables, PascalCase for classes, German comments allowed
- **JavaScript**: camelCase for functions/variables, PascalCase for classes
- **API Endpoints**: RESTful with `/api/` prefix
- **Git Commits**: Conventional commits (ci:, fix:, feat:, docs:)
- **Branch Strategy**: Trunk-based (direct commits to main)

## Testing

- Python: pytest (to be implemented)
- JS: No framework - vanilla JS with manual testing
- CI uses: ruff linting, py_compile

## Babysitter

Babysitter is configured for autonomous project orchestration.

### Available Commands

```bash
# Orchestrate complex workflows
babysitter call --process gsd/execute

# Plan features
babysitter call --process gsd/plan

# Verify implementation
babysitter call --process gsd/verify

# Run TDD methodology
babysitter call --process methodologies/TDD
```

### Installed Processes

- `cradle/project-install` - Project setup and onboarding (completed)
- `gsd/execute` - Autonomous task execution
- `gsd/plan` - Feature planning
- `gsd/verify` - Feature verification
- `methodologies/TDD` - Test-Driven Development

### CI/CD Integration

Babysitter runs automatically in GitHub Actions on:
- Push to main
- Tags (v*)
- Manual trigger (workflow_dispatch)

See `.github/workflows/babysitter.yml` for configuration.

### Project Goals

1. **Windows Test Version** - Erstellung und Verbesserung von FotoDerp, erste Testversion für Windows
2. **Full Feature Set** - AI-Tagging, Face Recognition, Semantic Search, Culling, Rating, OCR, Collections
3. **Clean Code & Tests** - Profi-Standards mit TDD
4. **CUDA/Vulkan Support** - GPU acceleration for AI inference (planned)
5. **UX Excellence** - Intuitive interface for professional photographers

### Autonomous Operation

This project is configured for autonomous operation with babysitter orchestration. The pi agent handles:
- Full development lifecycle
- Architecture decisions
- Testing and quality assurance
- Build and deployment

### Recommended Methodology

**TDD (Test-Driven Development)** with iterative convergence for quality assurance.

### Special Notes

- Never mention "Excire Foto 2027" or similar inspiration sources in code or documentation
- Windows builds require special DLL handling (see `.github/workflows/build.yml`)
- Use `babysitter call` for all complex workflows - let babysitter handle orchestration
- Focus on professional photo management features with improved UX
