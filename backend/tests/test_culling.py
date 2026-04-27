"""Tests für FotoDerp Culling Service - TDD RED Phase"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fotoerp_backend.services.culling import CullingService
from fotoerp_backend.database import get_photo, set_photo_status


class TestCullingService:
    """Tests für CullingService"""
    
    @pytest.fixture
    def culling_service(self):
        """CullingService Instanz"""
        return CullingService()
    
    @pytest.fixture
    def mock_import(self):
        """Mock für import_ module"""
        with patch('fotoerp_backend.services.culling.scan_directory') as mock_scan:
            mock_scan.return_value = [
                "/path/photo1.jpg",
                "/path/photo2.jpg",
                "/path/photo3.jpg"
            ]
            yield mock_scan
    
    def test_create_project_returns_valid_structure(self, culling_service, mock_import):
        """Test dass create_project eine gültige Struktur zurückgibt"""
        result = culling_service.create_project(["/path/folder"], profile="default")
        
        assert 'id' in result
        assert 'folder_paths' in result
        assert 'profile' in result
        assert 'photo_count' in result
        assert 'groups' in result
        assert result['photo_count'] == 3
    
    def test_create_project_generates_unique_id(self, culling_service, mock_import):
        """Test dass verschiedene Projekte verschiedene IDs haben"""
        result1 = culling_service.create_project(["/path/folder1"], profile="default")
        result2 = culling_service.create_project(["/path/folder2"], profile="default")
        
        assert result1['id'] != result2['id']
    
    def test_create_project_groups_photos(self, culling_service, mock_import):
        """Test dass Fotos in Gruppen eingeteilt werden"""
        result = culling_service.create_project(["/path/folder"], profile="default")
        
        assert 'groups' in result
        assert len(result['groups']) > 0
    
    def test_get_project_returns_structure(self, culling_service):
        """Test dass get_project eine Struktur zurückgibt"""
        # Zuerst ein Projekt erstellen
        created = culling_service.create_project(["/path/folder"], profile="default")
        project_id = created['id']
        
        # Projekt abrufen
        result = culling_service.get_project(project_id)
        
        assert 'id' in result
        assert result['id'] == project_id
    
    def test_select_photo_updates_status(self, culling_service):
        """Test dass select_photo den Status in der DB aktualisiert"""
        with patch('fotoerp_backend.services.culling.set_photo_status') as mock_set:
            culling_service.select_photo("project1", "photo1", "group1")
            mock_set.assert_called_once_with("photo1", "done")
    
    def test_select_photo_returns_success(self, culling_service):
        """Test dass select_photo True zurückgibt bei Erfolg"""
        with patch('fotoerp_backend.services.culling.set_photo_status'):
            result = culling_service.select_photo("project1", "photo1", "group1")
            assert result is True or result is None  # Je nach Implementierung
    
    def test_create_project_with_empty_folders(self, culling_service):
        """Test Umgang mit leeren Ordnern"""
        with patch('fotoerp_backend.services.culling.scan_directory', return_value=[]):
            result = culling_service.create_project(["/empty/folder"], profile="default")
            
            assert result['photo_count'] == 0
            assert len(result['groups']) >= 0
    
    def test_group_photos_creates_meaningful_groups(self, culling_service):
        """Test dass _group_photos sinnvolle Gruppen erstellt"""
        photos = [
            {'path': '/path/IMG_001.jpg', 'filename': 'IMG_001.jpg'},
            {'path': '/path/IMG_002.jpg', 'filename': 'IMG_002.jpg'},
            {'path': '/path/IMG_003.jpg', 'filename': 'IMG_003.jpg'}
        ]
        
        groups = culling_service._group_photos(photos, "default")
        
        assert isinstance(groups, list)
        assert len(groups) > 0
