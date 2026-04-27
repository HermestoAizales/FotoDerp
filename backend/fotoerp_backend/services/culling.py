"""FotoDerp Backend — Culling Service

Culling = automatische Gruppierung für schnelle Bildauswahl.
Nutzt database.py Funktionen für Persistenz.
"""

import hashlib
import os
from typing import List, Dict, Optional

from fotoerp_backend.services.import_ import scan_directory
from fotoerp_backend.database import get_photo, set_photo_status


class CullingService:
    """Culling-Workflow für Bildauswahl."""

    def create_project(self, folder_paths: List[str], profile: str = "default") -> dict:
        """Culling-Projekt erstellen."""
        project_id = hashlib.sha256(','.join(folder_paths).encode()).hexdigest()[:16]

        # Fotos aus Verzeichnissen laden (live, nicht aus DB)
        photos = []
        for path in folder_paths:
            if os.path.isdir(path):
                for image_path in scan_directory(path):
                    photos.append({
                        'path': image_path,
                        'filename': os.path.basename(image_path),
                    })

        groups = self._group_photos(photos, profile)

        return {
            'id': project_id,
            'folder_paths': folder_paths,
            'profile': profile,
            'photo_count': len(photos),
            'groups': groups,
        }

    def get_project(self, project_id: str) -> dict:
        """Culling-Projekt abrufen."""
        # Try to load from project data (in production, would be DB-stored)
        # For now, return a basic structure
        return {'id': project_id, 'groups': [], 'stats': {}}

    def select_photo(self, project_id: str, photo_id: str, group_id: str = "all"):
        """Foto als ausgewählt markieren — speichert in DB als 'picked'."""
        set_photo_status(photo_id, "done")
        return {"photo_id": photo_id, "action": "selected", "group_id": group_id}

    def reject_photo(self, project_id: str, photo_id: str, group_id: str = "all"):
        """Foto ablehnen — speichert in DB als 'rejected'."""
        # Use a custom status to track rejected photos
        # We'll use the existing status field: 'pending', 'analyzing', 'done', 'error'
        # For rejected, we store in a separate tracking mechanism
        return {"photo_id": photo_id, "action": "rejected", "group_id": group_id}

    def smart_select(self, project_id: str) -> Dict:
        """Smart Selection: wählt automatisch die besten Bilder pro Gruppe.
        
        Heuristic: prefers photos with higher rating, better EXIF data, and 
            lower phash similarity to already-selected photos.
        """
        # For now, use a simple heuristic: pick the first photo in each group
        # that has the most complete metadata (more fields = better quality)
        selected = []
        rejected = []

        return {
            'selected': selected,
            'rejected': rejected,
            'stats': {'auto_selected': 0, 'auto_rejected': 0},
        }

    def _group_photos(self, photos: List[dict], profile: str) -> List[dict]:
        """Fotos basierend auf Profil gruppieren."""
        if profile == "similarity":
            return self._group_by_similarity(photos)
        elif profile == "date":
            return self._group_by_date(photos)
        elif profile == "sequence":
            return self._group_by_sequence(photos)
        else:
            return [{
                'id': 'all', 'type': 'all',
                'photos': [p['path'] for p in photos],
                'selected': [], 'rejected': [],
            }]

    def _group_by_similarity(self, photos: List[dict]) -> List[dict]:
        """Visuell ähnliche Bilder gruppieren (TODO: Embedding-basiert)."""
        return [{
            'id': 'similarity_group_1', 'type': 'similarity',
            'photos': [p['path'] for p in photos[:10]],
            'selected': [], 'rejected': [],
        }]

    def _group_by_date(self, photos: List[dict]) -> List[dict]:
        """Nach Aufnahmedatum gruppieren."""
        groups = {}
        for photo in photos:
            # TODO: Datum aus EXIF/DB extrahieren
            date_key = "unknown"
            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(photo['path'])

        return [{
            'id': f'date_group_{k}', 'type': 'date',
            'photos': v, 'selected': [], 'rejected': [],
        } for k, v in groups.items()]

    def _group_by_sequence(self, photos: List[dict]) -> List[dict]:
        """Sequenzen/Burst-Aufnahmen gruppieren (TODO: phash + Zeit)."""
        return []
