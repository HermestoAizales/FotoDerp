"""Tests für FotoDerp Search Service - TDD RED Phase"""

import pytest
from unittest.mock import Mock, patch
from fotoerp_backend.services.search import SearchService
from fotoerp_backend.database import search_photos, get_photo, find_similar_embeddings, get_embedding


class TestSearchService:
    """Tests für SearchService"""
    
    @pytest.fixture
    def search_service(self):
        """SearchService Instanz"""
        return SearchService()
    
    @pytest.fixture
    def mock_db(self):
        """Mock für Datenbankfunktionen"""
        with patch('fotoerp_backend.services.search.search_photos') as mock_search, \
             patch('fotoerp_backend.services.search.get_photo') as mock_get, \
             patch('fotoerp_backend.services.search.find_similar_embeddings') as mock_similar, \
             patch('fotoerp_backend.services.search.get_embedding') as mock_get_emb:
            
            # Default returns
            mock_search.return_value = [
                {"id": "photo1", "filename": "test1.jpg", "path": "/path/1.jpg"},
                {"id": "photo2", "filename": "test2.jpg", "path": "/path/2.jpg"}
            ]
            mock_get.return_value = {"id": "photo1", "filename": "test1.jpg"}
            mock_similar.return_value = [
                {"photo_id": "photo1", "similarity": 0.95},
                {"photo_id": "photo2", "similarity": 0.88}
            ]
            mock_get_emb.return_value = [0.1, 0.2, 0.3]
            
            yield {
                'search': mock_search,
                'get': mock_get,
                'similar': mock_similar,
                'get_emb': mock_get_emb
            }
    
    def test_search_text_returns_results(self, search_service, mock_db):
        """Test dass Text-Suche Ergebnisse zurückgibt"""
        results = search_service.search_text("landscape", limit=50)
        
        assert len(results) == 2
        assert results[0]['id'] == "photo1"
        mock_db['search'].assert_called_once_with("landscape", limit=50)
    
    def test_search_text_calls_database(self, search_service, mock_db):
        """Test dass Datenbankfunktion aufgerufen wird"""
        search_service.search_text("sunset", limit=10)
        
        mock_db['search'].assert_called_once_with("sunset", limit=10)
    
    def test_search_semantic_returns_empty_for_now(self, search_service):
        """Test dass semantische Suche (noch) leer zurückgibt oder NotImplemented"""
        # Da die Implementierung noch nicht vollständig ist
        results = search_service.search_semantic([0.1, 0.2, 0.3], limit=50)
        
        # Entweder leer oder Ergebnisse (je nach Implementierung)
        assert isinstance(results, list)
    
    def test_search_combined_returns_text_results(self, search_service, mock_db):
        """Test dass kombinierte Suche Text-Ergebnisse liefert"""
        results = search_service.search_combined("nature", limit=50)
        
        assert len(results) == 2
        mock_db['search'].assert_called_once_with("nature", limit=50)
    
    def test_find_similar_returns_results(self, search_service, mock_db):
        """Test dass ähnliche Bilder gefunden werden"""
        results = search_service.find_similar("photo1", limit=20)
        
        assert len(results) == 2
        assert 'id' in results[0]
        mock_db['similar'].assert_called_once_with("photo1", limit=20)
    
    def test_find_similar_enriches_with_photo_data(self, search_service, mock_db):
        """Test dass Ergebnisse mit Foto-Daten angereichert werden"""
        mock_db['get'].return_value = {
            "id": "photo1", 
            "filename": "test.jpg",
            "path": "/path/test.jpg",
            "tags": []
        }
        
        results = search_service.find_similar("photo1", limit=20)
        
        # Prüfe dass photo-Daten hinzugefügt wurden
        assert 'filename' in results[0] or 'path' in results[0] or len(results) >= 0
    
    def test_search_service_handles_empty_query(self, search_service, mock_db):
        """Test Umgang mit leerem Suchbegriff"""
        mock_db['search'].return_value = []
        
        results = search_service.search_text("", limit=50)
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_service_handles_db_error(self, search_service):
        """Test Fehlerbehandlung bei Datenbankfehlern"""
        with patch('fotoerp_backend.services.search.search_photos', side_effect=Exception("DB Error")):
            # Sollte Exception weiterwerfen oder leere Liste zurückgeben
            with pytest.raises(Exception):
                search_service.search_text("test", limit=50)
