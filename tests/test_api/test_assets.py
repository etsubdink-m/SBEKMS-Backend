import pytest
import io
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.assets import AssetType


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_file_data():
    """Sample file data for testing uploads"""
    return {
        "python_file": {
            "content": b'print("Hello, World!")\n',
            "filename": "hello.py",
            "content_type": "text/x-python"
        },
        "markdown_file": {
            "content": b'# Test Document\nThis is a test.',
            "filename": "test.md",
            "content_type": "text/markdown"
        },
        "json_file": {
            "content": b'{"name": "test", "version": "1.0.0"}',
            "filename": "config.json",
            "content_type": "application/json"
        }
    }


class TestAssetsAPI:
    """Test cases for Assets API endpoints"""
    
    def test_assets_health_endpoint(self, client):
        """Test assets health check endpoint"""
        response = client.get("/api/assets/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "assets"
    
    @patch('app.core.semantic_annotator.SemanticAnnotator.annotate_asset')
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager')
    def test_upload_python_file(self, mock_ontology, mock_triplestore, mock_annotate, client, sample_file_data):
        """Test uploading a Python file"""
        # Setup mocks
        mock_triplestore.return_value = AsyncMock()
        mock_ontology.return_value = MagicMock()
        mock_annotate.return_value = 15
        
        file_data = sample_file_data["python_file"]
        
        response = client.post(
            "/api/assets/upload",
            files={"file": (file_data["filename"], io.BytesIO(file_data["content"]), file_data["content_type"])},
            data={
                "title": "Test Python File",
                "description": "A test Python script",
                "tags": "python,test,script",
                "project_name": "TestProject",
                "author": "Test User"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "uploaded and annotated successfully" in data["message"]
        assert data["data"]["file_name"] == file_data["filename"]
        assert data["data"]["asset_type"] == "source_code"
        assert "DigitalInformationCarrier" in data["data"]["wdo_classes"]
        assert "SourceCodeFile" in data["data"]["wdo_classes"]
        assert "PythonSourceCodeFile" in data["data"]["wdo_classes"]
        assert data["data"]["rdf_triples_count"] == 15
        assert "checksum" in data["data"]
    
    @patch('app.core.semantic_annotator.SemanticAnnotator.annotate_asset')
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager')
    def test_upload_markdown_file(self, mock_ontology, mock_triplestore, mock_annotate, client, sample_file_data):
        """Test uploading a markdown file"""
        # Setup mocks
        mock_triplestore.return_value = AsyncMock()
        mock_ontology.return_value = MagicMock()
        mock_annotate.return_value = 12
        
        file_data = sample_file_data["markdown_file"]
        
        response = client.post(
            "/api/assets/upload",
            files={"file": (file_data["filename"], io.BytesIO(file_data["content"]), file_data["content_type"])},
            data={
                "title": "Test Documentation",
                "description": "Test markdown documentation",
                "tags": "documentation,markdown",
                "project_name": "TestDocs",
                "author": "Doc Writer"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["data"]["asset_type"] == "documentation"
        assert "DocumentationFile" in data["data"]["wdo_classes"]
        assert data["data"]["rdf_triples_count"] == 12
    
    @patch('app.core.semantic_annotator.SemanticAnnotator.annotate_asset')
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager')
    def test_upload_json_file(self, mock_ontology, mock_triplestore, mock_annotate, client, sample_file_data):
        """Test uploading a JSON configuration file"""
        # Setup mocks
        mock_triplestore.return_value = AsyncMock()
        mock_ontology.return_value = MagicMock()
        mock_annotate.return_value = 18
        
        file_data = sample_file_data["json_file"]
        
        response = client.post(
            "/api/assets/upload",
            files={"file": (file_data["filename"], io.BytesIO(file_data["content"]), file_data["content_type"])},
            data={
                "title": "Configuration File",
                "description": "Project configuration",
                "tags": "config,json",
                "project_name": "ConfigTest",
                "author": "Config Manager"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["data"]["asset_type"] == "configuration"
        assert "ConfigurationFile" in data["data"]["wdo_classes"]
        assert data["data"]["rdf_triples_count"] == 18
    
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager')
    def test_upload_without_file(self, mock_ontology, mock_triplestore, client):
        """Test upload request without file"""
        response = client.post(
            "/api/assets/upload",
            data={"title": "No File Upload"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager')
    def test_upload_minimal_metadata(self, mock_ontology, mock_triplestore, client, sample_file_data):
        """Test upload with minimal metadata"""
        mock_triplestore.return_value = AsyncMock()
        mock_ontology.return_value = MagicMock()
        
        file_data = sample_file_data["python_file"]
        
        with patch('app.core.semantic_annotator.SemanticAnnotator.annotate_asset', return_value=8):
            response = client.post(
                "/api/assets/upload",
                files={"file": (file_data["filename"], io.BytesIO(file_data["content"]), file_data["content_type"])}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["data"]["file_name"] == file_data["filename"]
        # Should still classify correctly even without metadata
        assert data["data"]["asset_type"] == "source_code"
    
    def test_list_assets_endpoint(self, client):
        """Test list assets endpoint"""
        response = client.get("/api/assets/list")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "data" in data
        assert "assets" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "per_page" in data["data"]
    
    def test_list_assets_with_pagination(self, client):
        """Test list assets with pagination parameters"""
        response = client.get("/api/assets/list?page=2&per_page=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["page"] == 2
        assert data["data"]["per_page"] == 10
    
    def test_get_asset_by_id_not_found(self, client):
        """Test getting non-existent asset"""
        response = client.get("/api/assets/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @patch('app.core.semantic_annotator.SemanticAnnotator.annotate_asset')
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager')
    def test_upload_file_checksum_calculation(self, mock_ontology, mock_triplestore, mock_annotate, client, sample_file_data):
        """Test that file checksum is calculated correctly"""
        import hashlib
        
        mock_triplestore.return_value = AsyncMock()
        mock_ontology.return_value = MagicMock()
        mock_annotate.return_value = 10
        
        file_data = sample_file_data["python_file"]
        expected_checksum = hashlib.sha256(file_data["content"]).hexdigest()
        
        response = client.post(
            "/api/assets/upload",
            files={"file": (file_data["filename"], io.BytesIO(file_data["content"]), file_data["content_type"])},
            data={"title": "Checksum Test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["checksum"] == expected_checksum
        assert len(data["data"]["checksum"]) == 64  # SHA-256 hex length 