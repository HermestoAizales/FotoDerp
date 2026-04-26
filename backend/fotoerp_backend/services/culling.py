"""FotoDerp Backend — Culling Service

Culling = automatische Gruppierung und Vorauswahl von Bildern
für schnelle Bildauswahl (z.B. nach Hochzeit, Event, etc.)

Gruppierungs-Profile:
- similarity: Visuell ähnliche Bilder
- person: Nach Personen gruppiert
- date: Nach Aufnahmedatum
- sequence: Sequenzen/Burst-Aufnahmen
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta


class CullingService:
    """Culling-Workflow für Bildauswahl"""

    def __init__(self, db_session):
        self.db = db_session

    def create_project(self, folder_paths: List[str], profile: str = "default") -> dict:
        """Culling-Projekt erstellen"""
        import hashlib
        project_id = hashlib.sha256(','.join(folder_paths).encode()).hexdigest()[:16]

        # Fotos aus Verzeichnissen laden
        photos = self._get_photos_in_folders(folder_paths)
        
        # Gruppieren basierend auf Profil
        groups = self._group_photos(photos, profile)

        return {
            'id': project_id,
            'folder_paths': folder_paths,
            'profile': profile,
            'photo_count': len(photos),
            'groups': groups,
        }

    def get_project(self, project_id: str) -> dict:
        """Culling-Projekt abrufen"""
        # TODO: Projekt aus DB laden
        return {'id': project_id, 'groups': [], 'stats': {}}

    def select_photo(self, project_id: str, photo_id: str, group_id: str):
        """Bild als ausgewählt markieren"""
        # TODO: Markiere Foto als "selected"
        pass

    def reject_photo(self, project_id: str, photo_id: str, group_id: str):
        """Bild ablehnen"""
        # TODO: Markiere Foto als "rejected"
        pass

    def smart_select(self, project_id: str) -> Dict:
        """Smart Selection: KI wählt automatisch die besten Bilder pro Gruppe"""
        # TODO: Implementiere mit KI-Ranking
        return {'selected': [], 'stats': {}}

    def _get_photos_in_folders(self, folder_paths: List[str]) -> List[dict]:
        """Fotos aus Verzeichnissen laden"""
        from ..services.import import scan_directory
        
        photos = []
        for path in folder_paths:
            for image_path in scan_directory(path):
                photos.append({
                    'path': image_path,
                    'filename': os.path.basename(image_path),
                })
        return photos

    def _group_photos(self, photos: List[dict], profile: str) -> List[dict]:
        """Fotos basierend auf Profil gruppieren"""
        if profile == "similarity":
            return self._group_by_similarity(photos)
        elif profile == "person":
            return self._group_by_person(photos)
        elif profile == "date":
            return self._group_by_date(photos)
        elif profile == "sequence":
            return self._group_by_sequence(photos)
        else:
            # Default: alle in einer Gruppe
            return [{
                'id': 'all',
                'type': 'all',
                'photos': [p['path'] for p in photos],
                'selected': [],
                'rejected': [],
            }]

    def _group_by_similarity(self, photos: List[dict]) -> List[dict]:
        """Nach visueller Ähnlichkeit gruppieren"""
        # TODO: Implementiere mit Embedding-Similarität
        return [{
            'id': 'similarity_group_1',
            'type': 'similarity',
            'photos': [p['path'] for p in photos[:10]],
            'selected': [],
            'rejected': [],
        }]

    def _group_by_person(self, photos: List[dict]) -> List[dict]:
        """Nach Personen gruppieren"""
        # TODO: Implementiere mit Gesichtserkennung
        return []

    def _group_by_date(self, photos: List[dict]) -> List[dict]:
        """Nach Aufnahmedatum gruppieren (z.B. pro Tag)"""
        groups = {}
        for photo in photos:
            # TODO: Datum aus EXIF extrahieren
            date_key = "unknown"
            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(photo['path'])

        return [{
            'id': f'date_group_{k}',
            'type': 'date',
            'photos': v,
            'selected': [],
            'rejected': [],
        } for k, v in groups.items()]

    def _group_by_sequence(self, photos: List[dict]) -> List[dict]:
        """Sequenzen/Burst-Aufnahmen gruppieren"""
        # TODO: Implementiere mit phash + Zeitstempel
        return []
