import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.core.semantic_annotator import SemanticAnnotator


@pytest.fixture
def semantic_annotator():
    """Create a SemanticAnnotator instance for testing"""
    return SemanticAnnotator()


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing"""
    return {
        "id": "test-asset-123",
        "file_name": "test.py",
        "file_size": 1024,
        "mime_type": "text/x-python",
        "wdo_classes": ["DigitalInformationCarrier", "SourceCodeFile", "PythonSourceCodeFile"],
        "line_count": 25,
        "title": "Test Python File",
        "description": "A test Python file for unit testing",
        "author": "Test User",
        "tags": ["test", "python", "unit-test"],
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def mock_triplestore():
    """Mock triplestore for testing"""
    mock = AsyncMock()
    mock.add_triples.return_value = True
    return mock


class TestSemanticAnnotator:
    """Test cases for SemanticAnnotator"""
    
    async def test_annotate_asset_success(self, semantic_annotator, sample_metadata, mock_triplestore):
        """Test successful asset annotation"""
        result = await semantic_annotator.annotate_asset(sample_metadata, mock_triplestore)
        
        assert result > 0  # Should return number of triples created
        assert result >= 10  # Should have at least 10 triples for comprehensive metadata
        mock_triplestore.add_triples.assert_called_once()
    
    async def test_annotate_asset_minimal_metadata(self, semantic_annotator, mock_triplestore):
        """Test annotation with minimal metadata"""
        minimal_metadata = {
            "id": "minimal-asset",
            "file_name": "simple.txt"
        }
        
        result = await semantic_annotator.annotate_asset(minimal_metadata, mock_triplestore)
        
        assert result > 0  # Should still create some triples
        assert result >= 2  # At least type and label triples
        mock_triplestore.add_triples.assert_called_once()
    
    async def test_annotate_asset_with_tags(self, semantic_annotator, mock_triplestore):
        """Test annotation with multiple tags"""
        metadata_with_tags = {
            "id": "tagged-asset",
            "file_name": "tagged.js",
            "tags": ["javascript", "frontend", "web-dev"]
        }
        
        result = await semantic_annotator.annotate_asset(metadata_with_tags, mock_triplestore)
        
        assert result > 0
        # Should have created triples for each tag (3 tags × 3 triples each + basic triples)
        assert result >= 11  # 2 basic + 9 tag-related triples
        mock_triplestore.add_triples.assert_called_once()
    
    async def test_annotate_asset_triplestore_failure(self, semantic_annotator, sample_metadata):
        """Test annotation when triplestore fails"""
        mock_triplestore = AsyncMock()
        mock_triplestore.add_triples.return_value = False
        
        result = await semantic_annotator.annotate_asset(sample_metadata, mock_triplestore)
        
        assert result == 0  # Should return 0 on failure
        mock_triplestore.add_triples.assert_called_once()
    
    async def test_annotate_asset_exception_handling(self, semantic_annotator, mock_triplestore):
        """Test exception handling during annotation"""
        mock_triplestore.add_triples.side_effect = Exception("Triplestore error")
        
        result = await semantic_annotator.annotate_asset({}, mock_triplestore)
        
        assert result == 0  # Should return 0 on exception
    
    def test_namespace_initialization(self, semantic_annotator):
        """Test that namespaces are properly initialized"""
        assert semantic_annotator.WDO is not None
        assert semantic_annotator.SBEKMS is not None
        assert str(semantic_annotator.WDO) == "http://purl.example.org/web_dev_km_bfo#"
        assert str(semantic_annotator.SBEKMS) == "http://sbekms.example.org/instances/" 