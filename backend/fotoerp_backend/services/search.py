"""FotoDerp Backend - Such-Service

Schlank: FTS5 Volltextsuche + Cosine Similarity für Vektoren.
Kein numpy, kein pgvector, kein hnswlib - alles stdlib.
"""

from typing import List, Optional
import logging

from fotoerp_backend.database import (
    search_photos, get_photo, list_photos,
    find_similar_embeddings, set_embedding, get_embedding,
)

logger = logging.getLogger(__name__)


class SearchService:
    """Suche über Fotos mit Text und Vektoren."""

    def __init__(self):
        """Initialisiert SearchService (kein DB-Session-Overhead)."""
        pass

    def search_text(self, query: str, limit: int = 50) -> List[dict]:
        """FTS5 Volltextsuche über Dateiname, Format, etc.
        
        Args:
            query: Suchbegriff
            limit: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste von Foto-Dictionaries
        """
        return search_photos(query, limit=limit)

    def search_semantic(self, query_embedding: list[float], limit: int = 50) -> List[dict]:
        """Semantische Suche via Cosine Similarity.
        
        Args:
            query_embedding: Embedding des Suchbegriffs.
            limit: Maximale Anzahl Ergebnisse.
            
        Returns:
            Liste von ähnlichen Fotos (noch nicht vollständig implementiert).
        """
        # TODO: Vollständige Implementierung mit Embedding-Comparison
        # Finde Fotos mit Embeddings
        # Vergleiche query_embedding mit allen Embeddings via Cosine Similarity
        # Sortiere nach Ähnlichkeit und returne Top-Limit
        logger.info("Semantische Suche noch nicht vollständig implementiert")
        return []

    def search_combined(self, query: str, limit: int = 50) -> List[dict]:
        """Kombinierte Suche (Text + Semantik)."""
        text_results = self.search_text(query, limit)
        # Semantik-Teil kommt später mit KI-Embedding
        return text_results

    def find_similar(self, photo_id: str, limit: int = 20) -> List[dict]:
        """Ähnliche Bilder via Embedding-Cosine-Similarity.
        
        Args:
            photo_id: ID des Referenzbildes
            limit: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste von ähnlichen Fotos mit Scores
        """
        embeddings = find_similar_embeddings(photo_id, limit=limit)
        results = []
        for emb in embeddings:
            photo = get_photo(emb["photo_id"])
            if photo:
                results.append({
                    'id': photo['id'],
                    'filename': photo['filename'],
                    'score': emb.get('similarity', emb.get('score', 0.0)),
                    'width': photo.get('width'),
                    'height': photo.get('height'),
                    'format': photo.get('format'),
                })
        return results

    def store_embedding(self, photo_id: str, vector: list[float]):
        """Embedding eines Fotos speichern."""
        set_embedding(photo_id, vector)
