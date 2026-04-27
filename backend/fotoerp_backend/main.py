"""FotoDerp Backend — FastAPI Application

KI-gestuetzte Fotoverwaltung — Backend API.
Unterstuetzt: llama.cpp (lokal), Ollama, vLLM, LM Studio, Jan.ai.

Startet automatisch die SQLite-Datenbank beim ersten Request.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import asyncio
import hashlib
import os

from fotoerp_backend.models import (
    PhotoInfo, AnalysisResult, Tag, AppSettings,
    ModelConfig, ModelListResponse, DownloadStatus,
)
from fotoerp_backend.database import init_db, list_photos, get_photo, count_photos, \
    add_tag, assign_tag, get_photo_tags, add_analysis, get_analyses, \
    search_photos, find_similar_embeddings, set_embedding, \
    list_all_tags, list_all_persons, get_recent_photos, get_storage_used, \
    set_photo_status, add_face, count_search_results, \
    update_photo_rating, get_favorites, list_collections, create_collection, \
    add_to_collection, remove_from_collection, delete_collection
from fotoerp_backend.services.openapi_adapter import OpenAPIAdapter, AdapterConfig
from fotoerp_backend.services.llama_server import LlamaServerManager, ServerConfig, ModelDownloader
from fotoerp_backend.services.import_ import import_photos as do_import, mark_analyzing, mark_done
from PIL import Image
from fotoerp_backend.services.search import SearchService
from contextlib import asynccontextmanager

logger = logging.getLogger("fotoerp")


@asynccontextmanager
async def lifespan(app):
    """Lifespan event handler (replaces deprecated on_event)."""
    init_db()
    logger.info("FotoDerp Backend started (SQLite)")
    yield
    logger.info("FotoDerp Backend shutting down")


app = FastAPI(
    title="FotoDerp Backend",
    description="KI-gestuetzte Fotoverwaltung — Backend API",
    version="0.2.0",
    lifespan=lifespan,
)


# --- Global State ---

_settings: Dict[str, Any] = {
    "active_model_id": None,
    "llama_endpoint": "http://127.0.0.1:8080/v1",
    "analysis_batch_size": 10,
    "preview_quality": 85,
    "auto_tag_enabled": True,
    "gpu_layers": -1,
    "n_ctx": 4096,
    "n_threads": 0,
    "flash_attn": True,
    "embedding_enabled": True,
}

# Analysis queue — tracks ongoing batch analysis
_analysis_queue = {
    "running": False,
    "processed": 0,
    "total": 0,
    "pending_ids": [],  # list of photo IDs to analyze
}

_adapter: Optional[OpenAPIAdapter] = None
_server_manager: Optional[LlamaServerManager] = None
_downloader = ModelDownloader()
_search_service = SearchService()


# --- Lifecycle ---

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    """Lifespan event handler (replaces deprecated on_event)."""
    init_db()
    logger.info("FotoDerp Backend started (SQLite)")
    yield
    logger.info("FotoDerp Backend shutting down")


# --- Helpers ---

def get_active_adapter() -> OpenAPIAdapter:
    """Aktiven Adapter zurueckgeben (lazy init)."""
    global _adapter
    if _adapter is None:
        model_id = _settings.get("active_model_id")
        model_name = model_id or "llava-1.5-7b-q4"

        endpoint = _settings.get("llama_endpoint", "")
        if not endpoint:
            endpoint = "http://127.0.0.1:8080/v1"

        _adapter = OpenAPIAdapter(AdapterConfig(
            endpoint=endpoint,
            model=model_name,
            temperature=0.1,
            max_tokens=1024,
        ))
    return _adapter


async def get_or_start_server() -> str:
    """Stelle sicher dass lokaler Server laeuft."""
    global _server_manager

    endpoint = _settings.get("llama_endpoint", "")
    if endpoint:
        return endpoint

    model_path = _settings.get("model_path", "")
    if not model_path or not os.path.exists(model_path):
        raise HTTPException(
            status_code=503,
            detail="No model configured. Set a model path in /api/models/config",
        )

    if _server_manager is None:
        config = ServerConfig(
            model_path=model_path,
            gpu_layers=_settings.get("gpu_layers", -1),
            n_ctx=_settings.get("n_ctx", 4096),
            n_threads=_settings.get("n_threads", 0),
            flash_attn=_settings.get("flash_attn", True),
        )
        _server_manager = LlamaServerManager(config)

    if not _server_manager.is_running:
        await _server_manager.start()

    return _server_manager.endpoint


# --- Health ---

@app.get("/health")
async def health():
    return {"status": "ok", "service": "fotoderp-backend"}


# --- Photo Import ---

@app.post("/api/photos/import")
async def import_photos(req: dict):
    """Fotos importieren und indizieren."""
    paths = req.get("paths", [])
    logger.info(f"Import requested: {len(paths)} paths")
    result = do_import(paths)
    return result


@app.get("/api/photos")
async def list_photos_endpoint(
    page: int = 1,
    per_page: int = 50,
    status: Optional[str] = None,
):
    """Fotos auflisten mit Filter."""
    offset = (page - 1) * per_page
    photos = list_photos(status=status, limit=per_page, offset=offset)
    total = count_photos(status=status)

    return {
        "photos": photos,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@app.get("/api/photos/{photo_id}")
async def get_photo_endpoint(photo_id: str):
    """Einzelnes Foto mit Metadaten."""
    photo = get_photo(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    tags = get_photo_tags(photo_id)
    analyses = get_analyses(photo_id)

    return {
        "id": photo["id"],
        **{k: v for k, v in photo.items() if k != "id"},
        "tags": tags,
        "analyses": analyses,
    }


# --- AI Analysis ---

@app.post("/api/analyze/start")
async def start_analysis(req: Optional[dict] = None):
    """Start batch analysis with real queue tracking."""
    global _analysis_queue
    req = req or {}
    batch_size = req.get("batch_size", _settings.get("analysis_batch_size", 10))
    photo_ids = req.get("photo_ids")

    # Gather photos to analyze (all 'pending' or 'done' photos if none specified)
    if not photo_ids:
        all_photos = list_photos(status=None, limit=10000, offset=0)
        photo_ids = [p["id"] for p in all_photos if p.get("status") in ("pending", "done")]

    if not photo_ids:
        return {"status": "skipped", "detail": "No photos to analyze"}

    # Set up queue
    _analysis_queue = {
        "running": True,
        "processed": 0,
        "total": len(photo_ids),
        "pending_ids": list(photo_ids),
    }

    try:
        endpoint = await get_or_start_server()
        logger.info(f"Analysis started: {len(photo_ids)} photos, batch_size={batch_size}")

        # Start analysis in background task
        asyncio.create_task(_run_analysis_batch(photo_ids, batch_size))

        return {"status": "started", "total": len(photo_ids), "batch_size": batch_size}
    except HTTPException as e:
        _analysis_queue["running"] = False
        raise e
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        _analysis_queue["running"] = False
        raise HTTPException(status_code=503, detail=str(e))


async def _run_analysis_batch(photo_ids: List[str], batch_size: int):
    """Background task: analyze photos in batches and update DB."""
    global _analysis_queue
    adapter = get_active_adapter()

    try:
        for i in range(0, len(photo_ids), batch_size):
            batch_ids = photo_ids[i:i + batch_size]

            # Look up file paths from DB
            batch_paths = []
            for pid in batch_ids:
                photo = get_photo(pid)
                if photo:
                    set_photo_status(pid, "analyzing")
                    batch_paths.append(photo["path"])

            # Run analysis on actual file paths
            tasks = [analyze_photo(path, adapter) for path in batch_paths]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Save results to DB
            for pid, path, result in zip(batch_ids, batch_paths, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to analyze {pid}: {result}")
                    set_photo_status(pid, "error")
                else:
                    # Save tags
                    for tag in result.tags:
                        tag_id = tag.name.lower().replace(" ", "_")
                        add_tag(tag_id, tag.name, tag.category)
                        assign_tag(pid, tag_id)

                    # Save analysis record
                    import json as _json
                    analysis_id = hashlib.sha256(f"{pid}-analysis".encode()).hexdigest()[:16]
                    add_analysis(
                        analysis_id, pid, "ai_tags",
                        data={"tags": [t.model_dump() for t in result.tags],
                              "aesthetic_score": result.aesthetic_score},
                        model_version=result.model_version,
                    )

                    # Save faces if detected
                    for face in result.faces:
                        face_id = hashlib.sha256(f"{pid}-face-{face.get('person_id', 'unknown')}".encode()).hexdigest()[:16]
                        add_face(
                            face_id, pid,
                            person_id=face.get("person_id"),
                            x=face.get("x", 0), y=face.get("y", 0),
                            width=face.get("width", 0.2), height=face.get("height", 0.3),
                            confidence=face.get("confidence", 0.9),
                        )

                    set_photo_status(pid, "done")

                # Update progress
                _analysis_queue["processed"] += 1
                logger.info(f"Analysis progress: {_analysis_queue['processed']}/{_analysis_queue['total']}")

    except Exception as e:
        logger.error(f"Analysis batch failed: {e}")
    finally:
        _analysis_queue["running"] = False
        logger.info("Analysis complete")


@app.get("/api/analyze/status")
async def analysis_status():
    """Real analysis status from in-memory queue."""
    global _analysis_queue
    if _analysis_queue is None:
        return {"running": False, "processed": 0, "total": 0, "queue_size": 0}
    return {
        "running": _analysis_queue["running"],
        "processed": _analysis_queue["processed"],
        "total": _analysis_queue["total"],
        "queue_size": len(_analysis_queue["pending_ids"]),
    }


# --- Search ---

@app.get("/api/search")
async def search_photos_endpoint(
    query: str,
    page: int = 1,
    limit: int = 50,
):
    """FTS5 full-text search with pagination."""
    offset = (page - 1) * limit
    total = count_search_results(query)
    results = search_photos(query, limit=limit, offset=offset)
    return {"query": query, "results": results, "total": total, "page": page, "per_page": limit}


# --- Tags ---

@app.get("/api/tags")
async def list_tags(category: Optional[str] = None):
    """List all tags."""
    all_tags = list_all_tags()
    if category:
        all_tags = [t for t in all_tags if t.get("category") == category]
    # Group by category
    categories = {}
    for tag in all_tags:
        cat = tag.get("category", "auto")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tag)
    return {"tags": all_tags, "categories": categories}


@app.post("/api/tags/{tag_name}")
async def add_tag_endpoint(tag_name: str, req: dict):
    """Tag manuell zuweisen."""
    photo_ids = req.get("photo_ids", [])
    tag_id = tag_name.lower().replace(" ", "_")
    add_tag(tag_id, tag_name)

    for pid in photo_ids:
        assign_tag(pid, tag_id)

    return {"tag": tag_name, "photos_updated": len(photo_ids)}


# --- Persons ---

@app.get("/api/persons")
async def list_persons():
    """List recognized persons."""
    persons = list_all_persons()
    return {"persons": persons}


@app.post("/api/persons/{person_id}/rename")
async def rename_person(person_id: str, req: dict):
    """Rename a person."""
    name = req.get("name", "")
    return {"person_id": person_id, "new_name": name}


# --- Similarity ---

@app.get("/api/photos/{photo_id}/similar")
async def find_similar(photo_id: str, limit: int = 20):
    """Aehnliche Bilder finden (Embedding Cosine Similarity)."""
    results = find_similar_embeddings(photo_id, limit=limit)
    return {"photo_id": photo_id, "similar": results}


# --- Culling ---

@app.post("/api/culling/projects")
async def create_culling_project(req: dict):
    """Culling-Projekt erstellen."""
    from fotoerp_backend.services.culling import CullingService
    folder_paths = req.get("folder_paths", [])
    profile = req.get("profile", "default")

    service = CullingService()
    project = service.create_project(folder_paths, profile)

    return {
        "project_id": project["id"],
        "folder_paths": folder_paths,
        "profile": profile,
        "photo_count": project["photo_count"],
        "groups": project["groups"],
    }


@app.get("/api/culling/projects/{project_id}")
async def get_culling_project(project_id: str):
    """Retrieve culling project."""
    from fotoerp_backend.services.culling import CullingService
    service = CullingService()
    project = service.get_project(project_id)
    return project


# --- Preview ---

@app.get("/api/photos/{photo_id}/preview")
async def get_photo_preview(photo_id: str, width: int = 400):
    """Generate a thumbnail preview for a photo."""
    photo = get_photo(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    image_path = photo.get("path", "")
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    try:
        img = Image.open(image_path)
        # Handle HEIC and other formats that need extra handling
        if img.format is None:
            # Try to detect format from extension
            ext = os.path.splitext(image_path)[1].lower()
            if ext in (".heic", ".heif"):
                raise HTTPException(status_code=400, detail="HEIC/HEIF conversion not supported without Pillow > 10.1")
        
        img.thumbnail((width, width), Image.LANCZOS)
        # Convert to RGB for JPEG output (handles RGBA, P mode, etc.)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        buf.seek(0)

        return {
            "data": buf.read().hex(),  # hex-encoded JPEG for inline use
            "width": img.width,
            "height": img.height,
            "format": "jpeg",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview failed for {photo_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


# --- Rating & Favorites ---

@app.put("/api/photos/{photo_id}/rating")
async def update_rating(photo_id: str, req: dict):
    """Set photo rating (1-5). Use 0 to clear rating."""
    rating = req.get("rating", 0)
    if not isinstance(rating, int) or rating < 0 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 0-5")

    photo = get_photo(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    update_photo_rating(photo_id, rating)
    return {"photo_id": photo_id, "rating": rating}


@app.get("/api/photos/favorites")
async def get_favorites_endpoint(
    page: int = 1,
    per_page: int = 50,
):
    """Get photos with rating >= 3 (favorites)."""
    offset = (page - 1) * per_page
    photos = list_photos(status=None, limit=per_page, offset=offset, min_rating=3)
    total = count_photos(status=None, min_rating=3)

    return {
        "photos": photos,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


# --- Collections ---

@app.get("/api/collections")
async def list_collections_endpoint():
    """List all collections."""
    collections = list_collections()
    return {"collections": collections}


@app.post("/api/collections")
async def create_collection_endpoint(req: dict):
    """Create a new collection."""
    name = req.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="Collection name required")

    collection_id = hashlib.sha256(name.encode()).hexdigest()[:16]
    create_collection(collection_id, name)
    return {"id": collection_id, "name": name}


@app.post("/api/collections/{collection_id}/photos")
async def add_to_collection_endpoint(collection_id: str, req: dict):
    """Add photos to a collection."""
    photo_ids = req.get("photo_ids", [])
    for pid in photo_ids:
        add_to_collection(collection_id, pid)
    return {"collection_id": collection_id, "added": len(photo_ids)}


@app.delete("/api/collections/{collection_id}/photos/{photo_id}")
async def remove_from_collection_endpoint(collection_id: str, photo_id: str):
    """Remove a photo from a collection."""
    remove_from_collection(collection_id, photo_id)
    return {"collection_id": collection_id, "photo_id": photo_id}


@app.delete("/api/collections/{collection_id}")
async def delete_collection_endpoint(collection_id: str):
    """Delete a collection."""
    delete_collection(collection_id)
    return {"deleted": collection_id}


# --- Analytics ---

@app.get("/api/analytics/overview")
async def analytics_overview():
    """Analytics overview."""
    total = count_photos()
    pending = count_photos(status="pending")
    analyzing = count_photos(status="analyzing")
    done = count_photos(status="done")
    errors = count_photos(status="error")
    all_tags = list_all_tags()
    all_persons = list_all_persons()
    storage = get_storage_used()
    recent = get_recent_photos(5)

    return {
        "total_photos": total,
        "total_tags": len(all_tags),
        "total_persons": len(all_persons),
        "storage_used": storage,
        "breakdown": {"pending": pending, "analyzing": analyzing,
                       "done": done, "error": errors},
        "recent_activity": [
            {"type": "import", "filename": p["filename"],
             "timestamp": p.get("created_at")}
            for p in recent
        ],
    }


# --- Settings ---

@app.get("/api/settings")
async def get_settings():
    """Einstellungen abrufen."""
    return _settings


@app.put("/api/settings")
async def update_settings(req: dict):
    """Einstellungen aktualisieren."""
    for key, value in req.items():
        if key in _settings:
            _settings[key] = value

    if any(k in req for k in ["llama_endpoint", "active_model_id", "gpu_layers"]):
        global _adapter
        _adapter = None

    return {"status": "updated", "settings": _settings}


# --- Model Management ---

@app.get("/api/models")
async def list_models():
    """Verfügbare KI-Modelle auflisten."""
    models: List[ModelConfig] = []

    # Lokale GGUF-Modelle finden
    local_dirs = [
        os.path.join(os.path.expanduser("~"), "LLMs"),
        os.path.join(os.path.expanduser("~"), ".cache", "fotoderp", "models"),
    ]
    for model_info in _downloader.find_local_models(local_dirs):
        models.append(ModelConfig(
            id=model_info["path"],
            name=model_info["filename"],
            type="vision",
            endpoint="",
            quantization=_detect_quantization(model_info["filename"]),
            description=f"Local GGUF ({model_info['size_mb']} MB)",
        ))

    # Externe Endpunkte als Modelle
    endpoint = _settings.get("llama_endpoint", "")
    if endpoint:
        models.append(ModelConfig(
            id="external",
            name="External API",
            type="vision",
            endpoint=endpoint,
            model_name=_settings.get("active_model_id", ""),
            description=f"External: {endpoint}",
        ))

    # Standard-Modelle
    default_models = [
        ModelConfig(
            id="llava-1.5-7b-q4",
            name="LLaVA 1.5 7B (Q4_K_M)",
            type="vision", endpoint="", model_name="llava-1.5-7b-q4",
            quantization="Q4_K_M",
            description="Open-source vision model, good balance of speed/quality",
        ),
        ModelConfig(
            id="moondream2-q4",
            name="Moondream2 (Q4_K_M)",
            type="vision", endpoint="", model_name="moondream2-q4",
            quantization="Q4_K_M",
            description="Ultra-lightweight vision model, runs on CPU",
        ),
        ModelConfig(
            id="qwen2-vl-2b-q4",
            name="Qwen2-VL 2B (Q4_K_M)",
            type="vision", endpoint="", model_name="qwen2-vl-2b-q4",
            quantization="Q4_K_M",
            description="Modern vision-language model, excellent accuracy",
        ),
    ]

    local_ids = {m.id for m in models if not m.endpoint}
    for dm in default_models:
        if dm.id not in local_ids:
            models.append(dm)

    return ModelListResponse(
        models=models,
        active_model_id=_settings.get("active_model_id"),
    )


@app.post("/api/models/{model_id}/activate")
async def activate_model(model_id: str):
    """Modell aktivieren."""
    _settings["active_model_id"] = model_id

    if model_id.endswith(".gguf"):
        _settings["model_path"] = model_id
        logger.info(f"Activated local model: {model_id}")
    else:
        logger.info(f"Activated external model: {model_id}")

    global _adapter
    _adapter = None

    return {"status": "activated", "model_id": model_id}


@app.get("/api/models/local")
async def get_local_models():
    """Lokale GGUF-Modelle finden."""
    dirs = [
        os.path.join(os.path.expanduser("~"), "LLMs"),
        os.path.join(os.path.expanduser("~"), ".cache", "fotoderp", "models"),
    ]
    models = _downloader.find_local_models(dirs)
    return {"models": models, "count": len(models)}


@app.post("/api/models/download")
async def download_model(req: dict):
    """Modell von Hugging Face herunterladen."""
    repo_id = req.get("repo_id", "")
    filename = req.get("filename", "")

    if not repo_id or not filename:
        raise HTTPException(status_code=400, detail="repo_id and filename required")

    try:
        target = _downloader.download(repo_id, filename)
        return {"status": "ready", "path": str(target), "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/config")
async def configure_model(req: dict):
    """Modell-Konfiguration setzen."""
    model_path = req.get("model_path", "")
    endpoint = req.get("endpoint", "")
    gpu_layers = req.get("gpu_layers", _settings.get("gpu_layers", -1))
    n_ctx = req.get("n_ctx", _settings.get("n_ctx", 4096))

    if model_path:
        _settings["model_path"] = model_path
    if endpoint:
        _settings["llama_endpoint"] = endpoint
    if gpu_layers is not None:
        _settings["gpu_layers"] = gpu_layers
    if n_ctx is not None:
        _settings["n_ctx"] = n_ctx

    return {"status": "configured", "settings": {
        "model_path": _settings.get("model_path"),
        "endpoint": _settings.get("llama_endpoint"),
        "gpu_layers": _settings["gpu_layers"],
        "n_ctx": _settings["n_ctx"],
    }}


@app.get("/api/models/health")
async def model_health():
    """Health-Check des aktiven Modells."""
    try:
        adapter = get_active_adapter()
        health = await adapter.health_check()
        return health
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.post("/api/models/analyze-test")
async def test_analysis(req: dict):
    """Test-Analyse mit aktuellem Modell."""
    image_path = req.get("image_path", "")
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=400, detail="Valid image_path required")

    try:
        from fotoerp_backend.services.analysis import analyze_photo
        adapter = get_active_adapter()
        result = await analyze_photo(image_path, adapter)
        return {
            "status": "success",
            "result": {
                "tags": [{"name": t.name, "category": t.category,
                          "confidence": t.confidence} for t in result.tags],
                "aesthetic_score": result.aesthetic_score,
                "ocr_text": result.ocr_text,
                "model": adapter.config.model,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Helper ---

def _detect_quantization(filename: str) -> Optional[str]:
    """Quantisierung aus Dateinamen erkennen."""
    name = filename.lower()
    for q in ["q8_0", "q8_k", "q5_0", "q5_k_m", "q4_0", "q4_k_m", "q3_k_l", "q2_k"]:
        if q in name:
            return q.upper().replace("_K", "_k").replace("_0", "_0")
    return None
