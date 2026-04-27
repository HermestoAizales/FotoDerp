"""FotoDerp Backend - KI-Analyse Service

Verwendet den OpenAPI-Adapter für universellen Zugriff auf
verschiedene KI-Modelle (llama.cpp, Ollama, vLLM, etc.).
"""

import hashlib
import logging
from typing import List, Optional
from fotoerp_backend.models import AnalysisResult, Tag
from fotoerp_backend.services.openapi_adapter import OpenAPIAdapter, AdapterConfig

logger = logging.getLogger(__name__)


async def analyze_photo(
    photo_path: str,
    adapter: OpenAPIAdapter,
) -> AnalysisResult:
    """Foto mit einem Vision-Modell analysieren.
    
    Args:
        photo_path: Pfad zum Foto
        adapter: OpenAPI Adapter für KI-Modell-Zugriff
        
    Returns:
        AnalysisResult mit Tags, Faces, Scores
    """
    try:
        result = await adapter.image_analysis(photo_path)
    except Exception as e:
        logger.error(f"Fehler bei KI-Analyse von {photo_path}: {e}")
        raise
    
    # Parse tags
    tags = []
    for t in result.get("tags", []):
        if isinstance(t, dict):
            tags.append(Tag(
                name=t.get("name", ""),
                category=t.get("category", "auto"),
                confidence=t.get("confidence", 0.9),
            ))
        elif isinstance(t, str):
            tags.append(Tag(name=t, category="auto", confidence=0.9))

    return AnalysisResult(
        photo_id=hashlib.sha256(photo_path.encode()).hexdigest()[:16],
        tags=tags,
        faces=result.get("faces", []),
        aesthetic_score=result.get("aesthetic_score"),
        ocr_text=result.get("ocr_text"),
        model_version=str(adapter.config.model) if adapter.config.model else "unknown",
    )


async def generate_embedding(
    text: str,
    adapter: OpenAPIAdapter,
) -> Optional[List[float]]:
    """Text-Embedding generieren"""
    
    result = await adapter.embedding(text)
    data = result.get("data", [])
    if not data:
        return None
    return data[0].get("embedding")


async def analyze_photo_batch(
    photo_paths: List[str],
    adapter: OpenAPIAdapter,
    batch_size: int = 10,
) -> List[AnalysisResult]:
    """Batch-Analyse mehrerer Fotos (async parallel).
    
    Args:
        photo_paths: Liste von Foto-Pfaden
        adapter: OpenAPI Adapter
        batch_size: Anzahl paralleler Analysen
        
    Returns:
        Liste von AnalysisResult (fehlgeschlagene Analysen werden übersprungen)
    """
    import asyncio
    
    results = []
    for i in range(0, len(photo_paths), batch_size):
        batch = photo_paths[i:i + batch_size]
        tasks = [analyze_photo(path, adapter) for path in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for path, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                logger.error(f"Fehler bei Analyse von {path}: {result}")
            else:
                results.append(result)
    
    return results
