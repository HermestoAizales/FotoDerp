"""Tests für FotoDerp AI Analysis Service - TDD RED Phase"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fotoerp_backend.services.analysis import analyze_photo, generate_embedding, analyze_photo_batch
from fotoerp_backend.models import AnalysisResult, Tag, FaceInfo


class TestAnalyzePhoto:
    """Tests für analyze_photo Funktion"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Mock für OpenAPIAdapter"""
        adapter = Mock()
        adapter.image_analysis = AsyncMock(return_value={
            "tags": [
                {"name": "landscape", "category": "scene", "confidence": 0.95},
                "sunset",
                {"name": "nature", "confidence": 0.88}
            ],
            "faces": [
                {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4, "confidence": 0.99}
            ],
            "aesthetic_score": 0.85,
            "ocr_text": "Sample text"
        })
        adapter.config = Mock()
        adapter.config.model = "llama3.2-vision"
        return adapter
    
    @pytest.mark.asyncio
    async def test_analyze_photo_returns_analysis_result(self, mock_adapter):
        """Test dass analyze_photo ein AnalysisResult zurückgibt"""
        result = await analyze_photo("/path/to/photo.jpg", mock_adapter)
        
        assert isinstance(result, AnalysisResult)
        assert result.photo_id is not None
        assert len(result.tags) > 0
        assert result.aesthetic_score == 0.85
    
    @pytest.mark.asyncio
    async def test_analyze_photo_parses_tags_correctly(self, mock_adapter):
        """Test dass Tags korrekt geparst werden (dict und string)"""
        result = await analyze_photo("/path/to/photo.jpg", mock_adapter)
        
        # Prüfe dict-style tags
        tag_names = [t.name for t in result.tags]
        assert "landscape" in tag_names
        assert "nature" in tag_names
        
        # Prüfe string-style tags
        assert "sunset" in tag_names
    
    @pytest.mark.asyncio
    async def test_analyze_photo_parses_faces(self, mock_adapter):
        """Test dass Face-Info korrekt geparst wird"""
        result = await analyze_photo("/path/to/photo.jpg", mock_adapter)
        
        assert len(result.faces) == 1
        face = result.faces[0]
        assert face.x == 0.1
        assert face.y == 0.2
        assert face.width == 0.3
        assert face.height == 0.4
        assert face.confidence == 0.99
    
    @pytest.mark.asyncio
    async def test_analyze_photo_handles_error(self, mock_adapter):
        """Test Fehlerbehandlung bei Adapter-Fehlern"""
        mock_adapter.image_analysis.side_effect = Exception("Model error")
        
        with pytest.raises(Exception):
            await analyze_photo("/path/to/photo.jpg", mock_adapter)
    
    @pytest.mark.asyncio
    async def test_analyze_photo_generates_correct_photo_id(self, mock_adapter):
        """Test dass photo_id korrekt aus photo_path generiert wird"""
        photo_path = "/path/to/test_image.jpg"
        result = await analyze_photo(photo_path, mock_adapter)
        
        # photo_id sollte ein Hash des Pfades sein
        assert isinstance(result.photo_id, str)
        assert len(result.photo_id) > 0


class TestGenerateEmbedding:
    """Tests für generate_embedding Funktion"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Mock für OpenAPIAdapter"""
        adapter = Mock()
        adapter.embedding = AsyncMock(return_value={
            "data": [
                {"embedding": [0.1, 0.2, 0.3, 0.4, 0.5]}
            ]
        })
        return adapter
    
    @pytest.mark.asyncio
    async def test_generate_embedding_returns_list(self, mock_adapter):
        """Test dass generate_embedding eine Liste von Floats zurückgibt"""
        result = await generate_embedding("Sample text", mock_adapter)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(x, float) for x in result)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_calls_adapter(self, mock_adapter):
        """Test dass der Adapter korrekt aufgerufen wird"""
        await generate_embedding("Test text", mock_adapter)
        
        mock_adapter.embedding.assert_called_once_with("Test text")
    
    @pytest.mark.asyncio
    async def test_generate_embedding_handles_empty_response(self, mock_adapter):
        """Test Umgang mit leerer Antwort"""
        mock_adapter.embedding.return_value = {"data": []}
        
        result = await generate_embedding("Test", mock_adapter)
        
        assert result is None


class TestAnalyzePhotoBatch:
    """Tests für analyze_photo_batch Funktion"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Mock für OpenAPIAdapter"""
        adapter = Mock()
        adapter.image_analysis = AsyncMock(side_effect=[
            {"tags": [{"name": f"tag_{i}", "confidence": 0.9}], "faces": [], "aesthetic_score": 0.8, "ocr_text": None}
            for i in range(10)
        ])
        adapter.config = Mock()
        adapter.config.model = "llama3.2-vision"
        return adapter
    
    @pytest.mark.asyncio
    async def test_analyze_photo_batch_returns_list(self, mock_adapter):
        """Test dass analyze_photo_batch eine Liste zurückgibt"""
        photo_paths = [f"/path/photo_{i}.jpg" for i in range(5)]
        
        results = await analyze_photo_batch(photo_paths, mock_adapter, batch_size=2)
        
        assert isinstance(results, list)
        assert len(results) == 5
    
    @pytest.mark.asyncio
    async def test_analyze_photo_batch_handles_errors(self, mock_adapter):
        """Test dass Fehler in einzelnen Fotos behandelt werden"""
        mock_adapter.image_analysis.side_effect = [
            {"tags": [{"name": "good", "confidence": 0.9}], "faces": [], "aesthetic_score": 0.8, "ocr_text": None},
            Exception("Error"),
            {"tags": [{"name": "another", "confidence": 0.85}], "faces": [], "aesthetic_score": 0.75, "ocr_text": None}
        ]
        
        photo_paths = ["/path/1.jpg", "/path/2.jpg", "/path/3.jpg"]
        results = await analyze_photo_batch(photo_paths, mock_adapter)
        
        # Sollte 2 Ergebnisse haben (eines fehlgeschlagen)
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_photo_batch_processes_in_batches(self, mock_adapter):
        """Test dass die Batch-Verarbeitung funktioniert"""
        photo_paths = [f"/path/photo_{i}.jpg" for i in range(10)]
        
        await analyze_photo_batch(photo_paths, mock_adapter, batch_size=3)
        
        # Adapter sollte 10 mal aufgerufen worden sein
        assert mock_adapter.image_analysis.call_count == 10
