"""Tests für Collections Feature - TDD GREEN Phase"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fotoerp_backend.main import app


class TestCollectionsFeature:
    """Tests für Collections (Foto-Sammlungen)"""
    
    def test_list_collections_returns_list(self):
        """Test dass collections eine Liste zurückgibt"""
        with patch('fotoerp_backend.main.list_collections') as mock_list:
            mock_list.return_value = [
                {"id": "col1", "name": "Urlaub", "photo_count": 5},
                {"id": "col2", "name": "Familie", "photo_count": 10}
            ]
            
            client = TestClient(app)
            response = client.get("/api/collections")
            
            assert response.status_code == 200
            data = response.json()
            assert 'collections' in data
            assert len(data['collections']) == 2
    
    def test_list_collections_empty(self):
        """Test dass leere Liste zurückgegeben wird wenn keine Collections existieren"""
        with patch('fotoerp_backend.main.list_collections', return_value=[]):
            client = TestClient(app)
            response = client.get("/api/collections")
            
            assert response.status_code == 200
            data = response.json()
            assert data['collections'] == []
    
    def test_create_collection(self):
        """Test dass eine neue Collection erstellt werden kann"""
        with patch('fotoerp_backend.main.create_collection') as mock_create:
            mock_create.return_value = {"id": "new_col", "name": "Test Collection"}
            
            client = TestClient(app)
            response = client.post("/api/collections", json={"name": "Test Collection"})
            
            assert response.status_code == 200
            data = response.json()
            assert 'id' in data
            assert data['name'] == "Test Collection"
    
    def test_create_collection_missing_name(self):
        """Test dass Fehler bei fehlendem Namen geworfen wird"""
        client = TestClient(app)
        response = client.post("/api/collections", json={})
        
        # Sollte 400 oder 422 (Validation Error) zurückgeben
        assert response.status_code in [400, 422]
    
    def test_add_photo_to_collection(self):
        """Test dass ein Foto zu einer Collection hinzugefügt werden kann"""
        with patch('fotoerp_backend.main.add_to_collection') as mock_add:
            client = TestClient(app)
            response = client.post("/api/collections/col1/photos", json={"photo_id": "photo1"})
            
            assert response.status_code == 200
            mock_add.assert_called_once_with("col1", "photo1")
    
    def test_remove_photo_from_collection(self):
        """Test dass ein Foto aus einer Collection entfernt werden kann"""
        with patch('fotoerp_backend.main.remove_from_collection') as mock_remove:
            client = TestClient(app)
            response = client.delete("/api/collections/col1/photos/photo1")
            
            assert response.status_code == 200
            mock_remove.assert_called_once_with("col1", "photo1")
    
    def test_delete_collection(self):
        """Test dass eine Collection gelöscht werden kann"""
        with patch('fotoerp_backend.main.delete_collection', return_value=True) as mock_delete:
            client = TestClient(app)
            response = client.delete("/api/collections/col1")
            
            assert response.status_code == 200
            mock_delete.assert_called_once_with("col1")
    
    def test_collection_response_has_photo_count(self):
        """Test dass Collection-Objekt photo_count enthält"""
        with patch('fotoerp_backend.main.list_collections') as mock_list:
            mock_list.return_value = [
                {"id": "col1", "name": "Test", "photo_count": 3}
            ]
            
            client = TestClient(app)
            response = client.get("/api/collections")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data['collections']) == 1
            assert 'photo_count' in data['collections'][0]
            assert data['collections'][0]['photo_count'] == 3
