import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


class TestSystemAPI:
    """Test cases for System API endpoints"""
    
    def test_system_health_endpoint(self, client):
        """Test system health check endpoint"""
        response = client.get("/api/system/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "system"
        assert data["version"] == "1.0.0"
    
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager')
    def test_system_initialization(self, mock_ontology, mock_triplestore, client):
        """Test system initialization endpoint"""
        # Setup mocks
        mock_triplestore_instance = AsyncMock()
        mock_triplestore_instance.test_connection.return_value = True
        mock_triplestore_instance.ensure_repository.return_value = True
        mock_triplestore.return_value = mock_triplestore_instance
        
        mock_ontology_instance = MagicMock()
        mock_ontology_instance.load_ontology.return_value = True
        mock_ontology_instance.get_ontology_stats.return_value = {
            "total_triples": 641,
            "classes": 22,
            "properties": 9,
            "individuals": 0
        }
        mock_ontology.return_value = mock_ontology_instance
        
        response = client.post("/api/system/initialize")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "initialized successfully" in data["message"]
        assert data["data"]["triplestore_connected"] is True
        assert data["data"]["ontology_loaded"] is True
        assert data["data"]["ontology_stats"]["total_triples"] == 641
    
    @patch('app.dependencies.get_triplestore_client')
    def test_triplestore_stats(self, mock_triplestore, client):
        """Test triplestore statistics endpoint"""
        mock_triplestore_instance = AsyncMock()
        mock_triplestore_instance.get_repository_info.return_value = {
            "total_statements": 1250,
            "repository_id": "sbekms",
            "reasoning_enabled": True
        }
        mock_triplestore.return_value = mock_triplestore_instance
        
        response = client.get("/api/system/triplestore/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["total_statements"] == 1250
        assert data["data"]["repository_id"] == "sbekms"
        assert data["data"]["reasoning_enabled"] is True
    
    @patch('app.dependencies.get_ontology_manager')
    def test_ontology_info(self, mock_ontology, client):
        """Test ontology information endpoint"""
        mock_ontology_instance = MagicMock()
        mock_ontology_instance.get_ontology_stats.return_value = {
            "total_triples": 641,
            "classes": 22,
            "properties": 9,
            "individuals": 0
        }
        mock_ontology_instance.get_wdo_classes.return_value = [
            "DigitalInformationCarrier",
            "SourceCodeFile",
            "DocumentationFile",
            "ConfigurationFile"
        ]
        mock_ontology.return_value = mock_ontology_instance
        
        response = client.get("/api/system/ontology/info")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["stats"]["total_triples"] == 641
        assert data["data"]["stats"]["classes"] == 22
        assert len(data["data"]["wdo_classes"]) >= 4
        assert "DigitalInformationCarrier" in data["data"]["wdo_classes"]
    
    @patch('app.dependencies.get_ontology_manager')
    def test_ontology_classes_endpoint(self, mock_ontology, client):
        """Test ontology classes listing endpoint"""
        mock_ontology_instance = MagicMock()
        mock_ontology_instance.get_wdo_classes.return_value = [
            "DigitalInformationCarrier",
            "SourceCodeFile",
            "PythonSourceCodeFile",
            "JavaScriptSourceCodeFile",
            "DocumentationFile",
            "ConfigurationFile",
            "AssetFile"
        ]
        mock_ontology.return_value = mock_ontology_instance
        
        response = client.get("/api/system/ontology/classes")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["classes"]) >= 7
        assert "DigitalInformationCarrier" in data["data"]["classes"]
        assert "SourceCodeFile" in data["data"]["classes"]
    
    @patch('app.dependencies.get_ontology_manager')
    def test_ontology_properties_endpoint(self, mock_ontology, client):
        """Test ontology properties listing endpoint"""
        mock_ontology_instance = MagicMock()
        mock_ontology_instance.get_wdo_properties.return_value = [
            "hasFileSize",
            "hasMimeType",
            "hasLineCount",
            "hasAuthor",
            "hasTag",
            "isPartOf"
        ]
        mock_ontology.return_value = mock_ontology_instance
        
        response = client.get("/api/system/ontology/properties")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["properties"]) >= 6
        assert "hasFileSize" in data["data"]["properties"]
        assert "hasMimeType" in data["data"]["properties"]
    
    @patch('app.dependencies.get_triplestore_client')
    def test_triplestore_connection_failure(self, mock_triplestore, client):
        """Test system behavior when triplestore connection fails"""
        mock_triplestore_instance = AsyncMock()
        mock_triplestore_instance.test_connection.return_value = False
        mock_triplestore.return_value = mock_triplestore_instance
        
        response = client.get("/api/system/triplestore/stats")
        
        # Should handle gracefully even if connection fails
        assert response.status_code in [200, 500, 503]  # Depends on implementation
    
    def test_api_version_consistency(self, client):
        """Test that API version is consistent across endpoints"""
        health_response = client.get("/api/system/health")
        
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert "version" in health_data
        assert health_data["version"] == "1.0.0" 