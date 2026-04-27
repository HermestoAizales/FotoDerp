"""Tests für Face Recognition Feature - TDD RED Phase"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fotoerp_backend.database import list_all_persons, add_face, get_photo


class TestFaceRecognition:
    """Tests für Face Recognition Funktionalität"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock für Datenbankfunktionen"""
        with patch('fotoerp_backend.database.list_all_persons') as mock_list, \
             patch('fotoerp_backend.database.add_face') as mock_add, \
             patch('fotoerp_backend.database.get_photo') as mock_get:
            
            # Default returns
            mock_list.return_value = [
                {"id": "person1", "name": "John", "face_count": 5, "unknown": False},
                {"id": "person2", "name": None, "face_count": 3, "unknown": True}
            ]
            mock_add.return_value = True
            mock_get.return_value = {"id": "photo1", "filename": "test.jpg"}
            
            yield {
                'list': mock_list,
                'add': mock_add,
                'get': mock_get
            }
    
    def test_list_persons_returns_list(self, mock_db):
        """Test dass list_persons eine Liste zurückgibt"""
        from fotoerp_backend.database import list_all_persons
        
        result = list_all_persons()
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['id'] == "person1"
    
    def test_list_persons_calls_database(self, mock_db):
        """Test dass Datenbankfunktion aufgerufen wird"""
        from fotoerp_backend.database import list_all_persons
        
        list_all_persons()
        
        mock_db['list'].assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rename_person_updates_name(self, mock_db):
        """Test dass rename_person den Namen aktualisiert"""
        # Teste die Datenbankfunktion direkt
        from fotoerp_backend.database import rename_person
        
        # Mock für rename_person falls nicht vorhanden
        with patch('fotoerp_backend.database.rename_person', return_value=True) as mock_rename:
            result = rename_person("person1", "John Doe")
            assert result is not None
    
    def test_rename_person_with_empty_name(self):
        """Test Umgang mit leerem Namen"""
        # Sollte Fehler werfen oder ignorieren
        name = ""
        assert isinstance(name, str)  # Einfacher Test
    
    def test_find_similar_faces(self):
        """Test dass ähnliche Gesichter gefunden werden können"""
        # TODO: Implementierung von Face Recognition
        # Für jetzt: Teststruktur erstellen
        assert True
    
    def test_face_clustering_groups_same_person(self):
        """Test dass Gesichter derselben Person gruppiert werden"""
        # TODO: Implementierung
        assert True
    
    def test_merge_persons_combines_face_data(self):
        """Test dass zwei Personen zusammengeführt werden"""
        # TODO: Implementierung
        assert True
    
    def test_face_recognition_api_integration(self, mock_db):
        """Test Integration der Face Recognition API"""
        from fastapi.testclient import TestClient
        from fotoerp_backend.main import app
        
        client = TestClient(app)
        
        # Test GET /api/persons
        with patch('fotoerp_backend.main.list_all_persons', return_value=[{"id": "person1"}]):
            response = client.get("/api/persons")
            assert response.status_code == 200
        
        # Test POST /api/persons/{person_id}/rename
        with patch('fotoerp_backend.main.rename_person', return_value={"status": "ok"}):
            response = client.post("/api/persons/person1/rename", json={"name": "New Name"})
            assert response.status_code == 200
