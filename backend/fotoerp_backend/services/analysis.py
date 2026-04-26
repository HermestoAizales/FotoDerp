"""FotoDerp Backend — KI-Analyse Service

Verwendet den OpenAPI-Adapter für universellen Zugriff auf
verschiedene KI-Modelle (llama.cpp, Ollama, vLLM, etc.).
"""

import hashlib
from typing import List, Optional
from ..models import AnalysisResult, Tag
from .openapi_adapter import OpenAPIAdapter, AdapterConfig


async def analyze_photo(
    photo_path: str,
    adapter: OpenAPIAdapter,
) -> AnalysisResult:
    """Foto mit einem Vision-Modell analysieren"""
    
    result = await adapter.image_analysis(photo_path)
    
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
        model_version=adapter.config.model,
    )


async def generate_embedding(
    text: str,
    adapter: OpenAPIAdapter,
) -> Optional[List[float]]:
    """Text-Embedding generieren"""
    
    result = await adapter.embedding(text)
    data = result.get("data", [{}])[0]
    return data.get("embedding")


async def analyze_photo_batch(
    photo_paths: List[str],
    adapter: OpenAPIAdapter,
    batch_size: int = 10,
) -> List[AnalysisResult]:
    """Batch-Analyse mehrerer Fotos (async parallel)"""
    import asyncio
    
    results = []
    for i in range(0, len(photo_paths), batch_size):
        batch = photo_paths[i:i + batch_size]
        tasks = [analyze_photo(path, adapter) for path in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for path, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                print(f"Error analyzing {path}: {result}")
            else:
                results.append(result)
    
    return results
