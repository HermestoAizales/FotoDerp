"""FotoDerp Backend — Such-Service

Schlank: FTS5 Volltextsuche + Cosine Similarity für Vektoren.
Kein numpy, kein pgvector, kein hnswlib — alles stdlib.
"""

from typing import List, Optional

from ..database import (
    search_photos, get_photo, list_photos,
    find_similar_embeddings, set_embedding, get_embedding,
)


class SearchService:
    """Suche über Fotos mit Text und Vektoren."""

    def __init__(self):
        pass  # Kein DB-Session-Overhead mehr

    def search_text(self, query: str, limit: int = 50) -> List[dict]:
        """FTS5 Volltextsuche über Dateiname, Format, etc."""
        return search_photos(query, limit=limit)

    def search_semantic(self, query_embedding: list[float], limit: int = 50) -> List[dict]:
        """Semantische Suche via Cosine Similarity.

        query_embedding: Embedding des Suchbegriffs (vom KI-Modell).
        """
        # Für text-basierte semantische Suche: Embedding generieren
        # und dann ähnlichkeitsbasiert suchen
        # Hier nehmen wir ein photo_id als Referenz
        # (Die eigentliche Text→Embedding-Conversion passiert im Adapter)
        pass

    def search_combined(self, query: str, limit: int = 50) -> List[dict]:
        """Kombinierte Suche (Text + Semantik)."""
        text_results = self.search_text(query, limit)
        # Semantik-Teil kommt später mit KI-Embedding
        return text_results

    def find_similar(self, photo_id: str, limit: int = 20) -> List[dict]:
        """Ähnliche Bilder via Embedding-Cosine-Similarity."""
        embeddings = find_similar_embeddings(photo_id, limit=limit)
        results = []
        for emb in embeddings:
            photo = get_photo(emb["photo_id"])
            if photo:
                results.append({
                    'id': photo['id'],
                    'filename': photo['filename'],
                    'score': emb['score'],
                    'width': photo.get('width'),
                    'height': photo.get('height'),
                    'format': photo.get('format'),
                })
        return results

    def store_embedding(self, photo_id: str, vector: list[float]):
        """Embedding eines Fotos speichern."""
        set_embedding(photo_id, vector)
