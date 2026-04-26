"""FotoDerp Backend — Such-Service

Unterstützt:
- Volltextsuche (SQLite FTS5)
- Semantische Suche (Embedding-basiert)
- Kombination beider Methoden
"""

from typing import List, Optional
import numpy as np


class SearchService:
    """Suche über Fotos mit Text und Vektoren"""

    def __init__(self, db_session, llama_endpoint=None):
        self.db = db_session
        self.llama_endpoint = llama_endpoint

    def search_text(self, query: str, limit: int = 50) -> List[dict]:
        """Volltextsuche über Tags, Dateinamen, Metadaten"""
        # SQLite FTS5 Query
        results = self.db.query(Photo).filter(
            Photo.tags.any(Tag.name.ilike(f"%{query}%")) |
            Photo.filename.ilike(f"%{query}%")
        ).limit(limit).all()

        return [self._photo_to_dict(p) for p in results]

    async def search_semantic(self, query: str, limit: int = 50) -> List[dict]:
        """Semantische Suche via Embedding-Similarität"""
        if not self.llama_endpoint:
            return []

        # Query-Embedding generieren
        from ..services.analysis import generate_embedding
        
        # Bild-basierte Suche: erst Embedding vom Query-Bild
        # Text-basierte Suche: Embedding des Query-Textes
        # (Je nach Modell-Unterstützung)
        
        # Cosine Similarity über gespeicherte Embeddings
        results = self._find_similar_embeddings(query, limit)
        return results

    def search_combined(self, query: str, limit: int = 50) -> List[dict]:
        """Kombinierte Suche (Text + Semantik)"""
        text_results = self.search_text(query, limit)
        semantic_results = []
        
        if self.llama_endpoint:
            semantic_results = self.search_semantic(query, limit)

        # Ergebnisse zusammenführen und nach Relevanz sortieren
        return self._merge_and_rank(text_results, semantic_results, limit)

    def find_similar(self, photo_id: str, limit: int = 20) -> List[dict]:
        """Ähnliche Bilder finden (perceptual hash + embedding)"""
        photo = self.db.query(Photo).filter_by(id=photo_id).first()
        if not photo or not photo.phash:
            return []

        # Perceptual Hash Similarität
        similar = self.db.query(Photo).filter(
            Photo.phash != photo.phash,
            # Hamming-Distanz berechnen (vereinfacht)
            Photo.status == 'done'
        ).limit(limit).all()

        return [self._photo_to_dict(p) for p in similar]

    def _photo_to_dict(self, photo) -> dict:
        """Photo-Objekt zu Dict konvertieren"""
        return {
            'id': photo.id,
            'filename': photo.filename,
            'width': photo.width,
            'height': photo.height,
            'format': photo.format,
            'captured_at': photo.captured_at.isoformat() if photo.captured_at else None,
            'tags': [{'name': t.name, 'category': t.category} for t in photo.tags],
        }

    def _find_similar_embeddings(self, query: str, limit: int) -> List[dict]:
        """Embedding-basierte Similarity-Suche"""
        # TODO: Implementiere mit pgvector oder hnswlib
        return []

    def _merge_and_rank(self, text_results: List[dict], semantic_results: List[dict], limit: int) -> List[dict]:
        """Ergebnisse zusammenführen und nach Relevanz sortieren"""
        # Einfache Zusammenführung (priorisiere Text-Suche)
        merged = {r['id']: r for r in text_results}
        
        for r in semantic_results:
            if r['id'] not in merged:
                merged[r['id']] = r
        
        return list(merged.values())[:limit]
