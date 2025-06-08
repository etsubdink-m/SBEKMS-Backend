import pytest
import io
import tempfile
import os
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def temp_test_files():
    """Create temporary test files for integration testing"""
    files = {}
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Python file
    python_content = '''#!/usr/bin/env python3
"""
A simple Python script for testing
"""

def hello_world():
    """Print hello world message"""
    print("Hello, World!")
    return "Hello, World!"

def add_numbers(a, b):
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    result = hello_world()
    sum_result = add_numbers(5, 3)
    print(f"Sum: {sum_result}")
'''
    
    python_file = os.path.join(temp_dir, "test_script.py")
    with open(python_file, "w") as f:
        f.write(python_content)
    
    files["python"] = {
        "path": python_file,
        "content": python_content.encode(),
        "filename": "test_script.py",
        "content_type": "text/x-python"
    }
    
    # Markdown file
    markdown_content = '''# SBEKMS Test Documentation

## Overview
This is a comprehensive test document for the SBEKMS system.

## Features
- Semantic knowledge management
- RDF triple generation
- Ontology-based classification

## Code Examples

```python
def example_function():
    return "This is an example"
```

## Conclusion
This document demonstrates the documentation upload capability.
'''
    
    markdown_file = os.path.join(temp_dir, "test_docs.md")
    with open(markdown_file, "w") as f:
        f.write(markdown_content)
    
    files["markdown"] = {
        "path": markdown_file,
        "content": markdown_content.encode(),
        "filename": "test_docs.md",
        "content_type": "text/markdown"
    }
    
    # JSON configuration file
    json_content = '''{
    "name": "sbekms-test-project",
    "version": "1.0.0",
    "description": "Test project for SBEKMS integration testing",
    "dependencies": {
        "fastapi": "^0.68.0",
        "rdflib": "^6.0.0",
        "pytest": "^6.2.0"
    },
    "scripts": {
        "test": "pytest",
        "start": "uvicorn main:app --reload"
    },
    "author": "SBEKMS Team",
    "license": "MIT"
}'''
    
    json_file = os.path.join(temp_dir, "package.json")
    with open(json_file, "w") as f:
        f.write(json_content)
    
    files["json"] = {
        "path": json_file,
        "content": json_content.encode(),
        "filename": "package.json",
        "content_type": "application/json"
    }
    
    yield files
    
    # Cleanup
    for file_info in files.values():
        if os.path.exists(file_info["path"]):
            os.remove(file_info["path"])
    os.rmdir(temp_dir)


class TestIntegration:
    """Integration tests for complete workflow"""
    
    @patch('app.core.semantic_annotator.SemanticAnnotator.annotate_asset')
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager')
    def test_complete_upload_workflow_python(self, mock_ontology, mock_triplestore, mock_annotate, client, temp_test_files):
        """Test complete upload workflow for Python file"""
        # Setup mocks
        mock_triplestore_instance = AsyncMock()
        mock_triplestore.return_value = mock_triplestore_instance
        mock_ontology.return_value = MagicMock()
        mock_annotate.return_value = 25  # Expected number of triples for rich metadata
        
        file_data = temp_test_files["python"]
        
        # Test file upload
        with open(file_data["path"], "rb") as f:
            response = client.post(
                "/api/assets/upload",
                files={"file": (file_data["filename"], f, file_data["content_type"])},
                data={
                    "title": "Integration Test Python Script",
                    "description": "A comprehensive Python script for testing the complete upload workflow",
                    "tags": "python,testing,integration,script",
                    "project_name": "SBEKMS-Integration-Test",
                    "author": "Integration Test Suite"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify upload response
        assert data["status"] == "success"
        assert "uploaded and annotated successfully" in data["message"]
        assert data["data"]["file_name"] == file_data["filename"]
        assert data["data"]["asset_type"] == "source_code"
        
        # Verify WDO classification
        wdo_classes = data["data"]["wdo_classes"]
        assert "DigitalInformationCarrier" in wdo_classes
        assert "SourceCodeFile" in wdo_classes
        assert "PythonSourceCodeFile" in wdo_classes
        
        # Verify semantic annotation
        assert data["data"]["rdf_triples_count"] == 25
        assert len(data["data"]["checksum"]) == 64  # SHA-256
        
        # Verify metadata preservation
        metadata = data["data"]["metadata"]
        assert metadata["title"] == "Integration Test Python Script"
        assert metadata["project_name"] == "SBEKMS-Integration-Test"
        assert metadata["author"] == "Integration Test Suite"
        assert "python" in metadata["tags"]
        assert "integration" in metadata["tags"]
        
        # Verify semantic annotator was called
        mock_annotate.assert_called_once()
    
    @patch('app.core.semantic_annotator.SemanticAnnotator.annotate_asset')
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager')
    def test_complete_upload_workflow_documentation(self, mock_ontology, mock_triplestore, mock_annotate, client, temp_test_files):
        """Test complete upload workflow for documentation file"""
        # Setup mocks
        mock_triplestore_instance = AsyncMock()
        mock_triplestore.return_value = mock_triplestore_instance
        mock_ontology.return_value = MagicMock()
        mock_annotate.return_value = 18
        
        file_data = temp_test_files["markdown"]
        
        with open(file_data["path"], "rb") as f:
            response = client.post(
                "/api/assets/upload",
                files={"file": (file_data["filename"], f, file_data["content_type"])},
                data={
                    "title": "SBEKMS Integration Documentation",
                    "description": "Comprehensive documentation for integration testing",
                    "tags": "documentation,markdown,integration,guide",
                    "project_name": "SBEKMS-Docs",
                    "author": "Documentation Team"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify documentation-specific classification
        assert data["data"]["asset_type"] == "documentation"
        wdo_classes = data["data"]["wdo_classes"]
        assert "DigitalInformationCarrier" in wdo_classes
        assert "DocumentationFile" in wdo_classes
        
        # Verify content analysis
        metadata = data["data"]["metadata"]
        assert metadata["line_count"] > 10  # Substantial content
        assert metadata["character_count"] > 100
    
    @patch('app.core.semantic_annotator.SemanticAnnotator.annotate_asset')
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager')
    def test_complete_upload_workflow_configuration(self, mock_ontology, mock_triplestore, mock_annotate, client, temp_test_files):
        """Test complete upload workflow for configuration file"""
        # Setup mocks
        mock_triplestore_instance = AsyncMock()
        mock_triplestore.return_value = mock_triplestore_instance
        mock_ontology.return_value = MagicMock()
        mock_annotate.return_value = 22
        
        file_data = temp_test_files["json"]
        
        with open(file_data["path"], "rb") as f:
            response = client.post(
                "/api/assets/upload",
                files={"file": (file_data["filename"], f, file_data["content_type"])},
                data={
                    "title": "Project Configuration",
                    "description": "NPM package configuration for SBEKMS test project",
                    "tags": "configuration,json,npm,package,dependencies",
                    "project_name": "SBEKMS-Config",
                    "author": "DevOps Team"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify configuration-specific classification
        assert data["data"]["asset_type"] == "configuration"
        wdo_classes = data["data"]["wdo_classes"]
        assert "DigitalInformationCarrier" in wdo_classes
        assert "ConfigurationFile" in wdo_classes
        
        # Verify JSON handling
        assert data["data"]["metadata"]["mime_type"] == "application/json"
    
    @patch('app.dependencies.get_triplestore_client')
    @patch('app.dependencies.get_ontology_manager') 
    def test_multiple_file_uploads_consistency(self, mock_ontology, mock_triplestore, client, temp_test_files):
        """Test uploading multiple files and verify consistency"""
        mock_triplestore_instance = AsyncMock()
        mock_triplestore.return_value = mock_triplestore_instance
        mock_ontology.return_value = MagicMock()
        
        uploaded_assets = []
        
        # Upload all test files
        for file_type, file_data in temp_test_files.items():
            with patch('app.core.semantic_annotator.SemanticAnnotator.annotate_asset', return_value=15):
                with open(file_data["path"], "rb") as f:
                    response = client.post(
                        "/api/assets/upload",
                        files={"file": (file_data["filename"], f, file_data["content_type"])},
                        data={
                            "title": f"Test {file_type.title()} File",
                            "description": f"Integration test for {file_type} file upload",
                            "tags": f"{file_type},integration,test",
                            "project_name": "Multi-Upload-Test",
                            "author": "Integration Tester"
                        }
                    )
                
                assert response.status_code == 200
                data = response.json()
                uploaded_assets.append(data["data"])
        
        # Verify all uploads were successful
        assert len(uploaded_assets) == 3
        
        # Verify unique asset IDs
        asset_ids = [asset["asset_id"] for asset in uploaded_assets]
        assert len(set(asset_ids)) == len(asset_ids)  # All unique
        
        # Verify correct classifications
        asset_types = [asset["asset_type"] for asset in uploaded_assets]
        assert "source_code" in asset_types
        assert "documentation" in asset_types
        assert "configuration" in asset_types
    
    def test_system_health_during_uploads(self, client):
        """Test that system remains healthy during file operations"""
        # Check initial health
        health_response = client.get("/api/system/health")
        assert health_response.status_code == 200
        
        # Check assets service health
        assets_health_response = client.get("/api/assets/health")
        assert assets_health_response.status_code == 200
        
        # Verify health response structure
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "system"
        assert "version" in health_data
        
        assets_health_data = assets_health_response.json()
        assert assets_health_data["status"] == "healthy"
        assert assets_health_data["service"] == "assets" 