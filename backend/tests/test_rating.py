"""Tests für Rating Feature - TDD GREEN Phase"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fotoerp_backend.main import app


class TestRatingFeature:
    """Tests für Rating und Favoriten"""
    
    def test_update_rating_valid_value(self):
        """Test dass Rating (1-5) aktualisiert wird"""
        with patch('fotoerp_backend.main.get_photo') as mock_get, \
             patch('fotoerp_backend.main.update_photo_rating') as mock_update:
            
            mock_get.return_value = {"id": "photo1", "filename": "test.jpg"}
            
            client = TestClient(app)
            response = client.put("/api/photos/photo1/rating", json={"rating": 4})
            
            assert response.status_code == 200
            mock_update.assert_called_once_with("photo1", 4)
    
    def test_update_rating_clear_rating(self):
        """Test dass Rating mit 0 gelöscht wird (NULL)"""
        with patch('fotoerp_backend.main.get_photo') as mock_get, \
             patch('fotoerp_backend.main.update_photo_rating') as mock_update:
            
            mock_get.return_value = {"id": "photo1"}
            
            client = TestClient(app)
            response = client.put("/api/photos/photo1/rating", json={"rating": 0})
            
            assert response.status_code == 200
            mock_update.assert_called_once_with("photo1", 0)
    
    def test_update_rating_invalid_value_too_high(self):
        """Test dass ungültiges Rating (>5) abgelehnt wird"""
        client = TestClient(app)
        
        response = client.put("/api/photos/photo1/rating", json={"rating": 6})
        assert response.status_code == 400
    
    def test_update_rating_invalid_value_negative(self):
        """Test dass ungültiges Rating (<0) abgelehnt wird"""
        client = TestClient(app)
        
        response = client.put("/api/photos/photo1/rating", json={"rating": -1})
        assert response.status_code == 400
    
    def test_update_rating_photo_not_found(self):
        """Test dass Fehler geworfen wird wenn Foto nicht existiert"""
        with patch('fotoerp_backend.main.get_photo', return_value=None):
            client = TestClient(app)
            response = client.put("/api/photos/photo1/rating", json={"rating": 3})
            
            assert response.status_code == 404
    
    def test_get_favorites_pagination(self):
        """Test Favoriten mit Paginierung"""
        with patch('fotoerp_backend.main.list_photos') as mock_list, \
             patch('fotoerp_backend.main.count_photos') as mock_count:
            
            mock_list.return_value = [
                {"id": "photo1", "rating": 5, "filename": "test1.jpg"},
                {"id": "photo2", "rating": 4, "filename": "test2.jpg"}
            ]
            mock_count.return_value = 2
            
            client = TestClient(app)
            response = client.get("/api/photos/favorites?page=1&per_page=10")
            
            assert response.status_code == 200
            data = response.json()
            assert 'photos' in data
            assert 'total' in data
            assert 'page' in data
    
    def test_rating_in_photo_response(self):
        """Test dass Rating im Foto-Objekt enthalten ist"""
        with patch('fotoerp_backend.main.get_photo') as mock_get:
            mock_get.return_value = {
                "id": "photo1", 
                "filename": "test.jpg",
                "rating": 4,
                "tags": []
            }
            
            client = TestClient(app)
            response = client.get("/api/photos/photo1")
            
            assert response.status_code == 200
            data = response.json()
            assert 'rating' in data
            assert data['rating'] == 4
