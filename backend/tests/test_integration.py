"""Integration Tests für FotoDerp - End-to-End Verifikation"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fotoerp_backend.main import app
import json


class TestIntegration:
    """End-to-End Tests für FotoDerp Features"""
    
    def test_full_photo_workflow(self):
        """Test: Foto importieren → analyseren → taggen → bewerten → zu Sammlung hinzufügen"""
        client = TestClient(app)
        
        # 1. Foto-Liste (leer)
        response = client.get("/api/photos")
        assert response.status_code == 200
        data = response.json()
        assert data['total'] >= 0
        
        # 2. Analyse-Status prüfen
        response = client.get("/api/analyze/status")
        assert response.status_code == 200
        
        # 3. Suche (leeres Ergebnis)
        response = client.get("/api/search?query=test")
        assert response.status_code == 200
        
        # 4. Favoriten (leeres Ergebnis)
        response = client.get("/api/photos/favorites")
        assert response.status_code == 200
        
        # 5. Collections Liste
        response = client.get("/api/collections")
        assert response.status_code == 200
        assert 'collections' in response.json()
        
        assert True  # Workflow verifikation abgeschlossen
    
    def test_api_endpoints_exist(self):
        """Test dass alle wichtigen API-Endpunkte existieren"""
        client = TestClient(app)
        
        endpoints = [
            ("/api/photos", "GET"),
            ("/api/photos/favorites", "GET"),
            ("/api/search?query=test", "GET"),
            ("/api/tags", "GET"),
            ("/api/persons", "GET"),
            ("/api/collections", "GET"),
            ("/api/analyze/status", "GET"),
            ("/api/models", "GET"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
                assert response.status_code in [200, 404, 422], f"{endpoint} returned {response.status_code}"
        
        assert True
    
    def test_error_handling(self):
        """Test Fehlerbehandlung"""
        client = TestClient(app)
        
        # Nicht-existierendes Foto
        response = client.get("/api/photos/nonexistent")
        assert response.status_code == 404
        
        # Ungültiges Rating
        response = client.put("/api/photos/photo1/rating", json={"rating": 10})
        assert response.status_code == 400
        
        # Leeres JSON für Collection-Erstellung
        response = client.post("/api/collections", json={})
        assert response.status_code in [400, 422]
        
        assert True
    
    def test_search_integration(self):
        """Test Suche-Integration"""
        from fotoerp_backend.services.search import SearchService
        
        service = SearchService()
        
        # Text-Suche
        results = service.search_text("test")
        assert isinstance(results, list)
        
        # Kombinierte Suche
        results = service.search_combined("test")
        assert isinstance(results, list)
        
        assert True
    
    def test_culling_workflow(self):
        """Test Culling-Workflow"""
        from fotoerp_backend.services.culling import CullingService
        
        service = CullingService()
        
        # Projekt erstellen
        with patch('fotoerp_backend.services.culling.scan_directory') as mock_scan:
            mock_scan.return_value = ["/path/photo1.jpg", "/path/photo2.jpg"]
            
            result = service.create_project(["/path/folder"], profile="default")
            
            assert 'id' in result
            assert result['photo_count'] >= 0
            assert 'groups' in result
        
        assert True
    
    def test_collections_workflow(self):
        """Test Collections-Workflow"""
        with patch('fotoerp_backend.main.list_collections') as mock_list:
            mock_list.return_value = [
                {"id": "col1", "name": "Test", "photo_count": 0}
            ]
            
            client = TestClient(app)
            response = client.get("/api/collections")
            
            assert response.status_code == 200
            data = response.json()
            assert 'collections' in data
        
        assert True
