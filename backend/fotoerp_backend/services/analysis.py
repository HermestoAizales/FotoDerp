"""FotoDerp Backend — KI-Analyse Service

Kommuniziert mit llama.cpp OpenAI-kompatiblem Endpoint für:
- Objekterkennung / Tagging
- Gesichtserkennung
- Ästhetik-Bewertung
- OCR (Texterkennung)
- Embeddings für Ähnlichkeitssuche
"""

import base64
import hashlib
import httpx
from typing import List, Dict, Optional
from ..models import AnalysisResult, Tag


async def analyze_photo(
    photo_path: str,
    llama_endpoint: str,
    model: str = "llava-1.5-7b-q4",
) -> AnalysisResult:
    """Foto mit KI analysieren"""
    
    # Bild als Base64 kodieren
    image_b64 = _encode_image(photo_path)
    
    # Prompt für die Analyse
    prompt = (
        "Analyze this photo comprehensively. Return JSON with:\n"
        "- tags: list of relevant tags (objects, scene, colors, season)\n"
        "- faces: list of detected faces with {person_id, x, y, width, height, confidence}\n"
        "- aesthetic_score: 0.0-1.0 quality score\n"
        "- ocr_text: any visible text in the image\n"
        "Keep it concise. No explanations."
    )

    # llama.cpp Endpoint aufrufen
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{llama_endpoint}/chat/completions",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1,
            },
        )
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # JSON parsen (robust)
        try:
            import json
            analysis = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: versuche JSON aus dem Text zu extrahieren
            analysis = _extract_json(content)

    return AnalysisResult(
        photo_id=hashlib.sha256(photo_path.encode()).hexdigest()[:16],
        tags=[Tag(**t) for t in analysis.get('tags', [])],
        faces=analysis.get('faces', []),
        aesthetic_score=analysis.get('aesthetic_score'),
        ocr_text=analysis.get('ocr_text'),
    )


async def generate_embedding(
    photo_path: str,
    llama_endpoint: str,
    model: str = "nomic-embed-text-v1",
) -> Optional[List[float]]:
    """Embedding für ein Bild generieren"""
    
    image_b64 = _encode_image(photo_path)
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{llama_endpoint}/embeddings",
            json={
                "model": model,
                "input": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    }
                ],
            },
        )
        
        result = response.json()
        return result['data'][0]['embedding']


def _encode_image(path: str) -> str:
    """Bild als Base64 kodieren"""
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def _extract_json(text: str) -> dict:
    """Versuche JSON aus einem Text-Block zu extrahieren"""
    import re
    
    # Suche nach JSON-Block
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        import json
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Suche nach erstem { ... }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        import json
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    return {}
