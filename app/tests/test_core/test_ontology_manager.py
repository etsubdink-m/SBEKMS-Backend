import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL

from app.core.ontology_manager import OntologyManager


@pytest.fixture
def ontology_manager():
    """Create an OntologyManager instance for testing"""
    return OntologyManager()


@pytest.fixture
def sample_ontology_graph():
    """Create a sample ontology graph for testing"""
    g = Graph()
    WDO = Namespace("http://purl.example.org/web_dev_km_bfo#")
    
    # Add some sample classes
    g.add((WDO.DigitalInformationCarrier, RDF.type, OWL.Class))
    g.add((WDO.SourceCodeFile, RDF.type, OWL.Class))
    g.add((WDO.SourceCodeFile, RDFS.subClassOf, WDO.DigitalInformationCarrier))
    g.add((WDO.PythonSourceCodeFile, RDF.type, OWL.Class))
    g.add((WDO.PythonSourceCodeFile, RDFS.subClassOf, WDO.SourceCodeFile))
    
    # Add some sample properties
    g.add((WDO.hasFileSize, RDF.type, OWL.DatatypeProperty))
    g.add((WDO.hasMimeType, RDF.type, OWL.DatatypeProperty))
    
    return g


class TestOntologyManager:
    """Test cases for OntologyManager"""
    
    @patch('app.core.ontology_manager.OntologyManager._load_wdo_ontology')
    def test_initialization(self, mock_load, ontology_manager):
        """Test ontology manager initialization"""
        assert ontology_manager.WDO is not None
        assert str(ontology_manager.WDO) == "http://purl.example.org/web_dev_km_bfo#"
    
    def test_load_ontology_success(self, ontology_manager, sample_ontology_graph):
        """Test successful ontology loading"""
        with patch.object(ontology_manager, 'ontology', sample_ontology_graph):
            stats = ontology_manager.get_ontology_stats()
            
            assert stats["total_triples"] == len(sample_ontology_graph)
            assert stats["classes"] >= 3
            assert stats["properties"] >= 2
    
    def test_get_wdo_classes(self, ontology_manager, sample_ontology_graph):
        """Test retrieval of WDO classes"""
        with patch.object(ontology_manager, 'ontology', sample_ontology_graph):
            classes = ontology_manager.get_wdo_classes()
            
            assert len(classes) >= 3
            assert "DigitalInformationCarrier" in classes
            assert "SourceCodeFile" in classes
            assert "PythonSourceCodeFile" in classes
    
    def test_get_wdo_properties(self, ontology_manager, sample_ontology_graph):
        """Test retrieval of WDO properties"""
        with patch.object(ontology_manager, 'ontology', sample_ontology_graph):
            properties = ontology_manager.get_wdo_properties()
            
            assert len(properties) >= 2
            assert "hasFileSize" in properties
            assert "hasMimeType" in properties
    
    def test_validate_wdo_class_valid(self, ontology_manager, sample_ontology_graph):
        """Test validation of valid WDO class"""
        with patch.object(ontology_manager, 'ontology', sample_ontology_graph):
            assert ontology_manager.validate_wdo_class("SourceCodeFile") is True
            assert ontology_manager.validate_wdo_class("PythonSourceCodeFile") is True
    
    def test_validate_wdo_class_invalid(self, ontology_manager, sample_ontology_graph):
        """Test validation of invalid WDO class"""
        with patch.object(ontology_manager, 'ontology', sample_ontology_graph):
            assert ontology_manager.validate_wdo_class("NonExistentClass") is False
            assert ontology_manager.validate_wdo_class("") is False
    
    def test_suggest_classes_for_file_type(self, ontology_manager, sample_ontology_graph):
        """Test class suggestions based on file type"""
        with patch.object(ontology_manager, 'ontology', sample_ontology_graph):
            # Test Python file suggestions
            suggestions = ontology_manager.suggest_classes_for_file_type("source_code", ".py")
            assert "SourceCodeFile" in suggestions
            
            # Test general source code suggestions
            suggestions = ontology_manager.suggest_classes_for_file_type("source_code", ".js")
            assert "SourceCodeFile" in suggestions
    
    def test_get_class_hierarchy(self, ontology_manager, sample_ontology_graph):
        """Test retrieval of class hierarchy"""
        with patch.object(ontology_manager, 'ontology', sample_ontology_graph):
            hierarchy = ontology_manager.get_class_hierarchy("PythonSourceCodeFile")
            
            assert "DigitalInformationCarrier" in hierarchy
            assert "SourceCodeFile" in hierarchy
            assert "PythonSourceCodeFile" in hierarchy
    
    def test_ontology_stats_structure(self, ontology_manager, sample_ontology_graph):
        """Test structure of ontology stats"""
        with patch.object(ontology_manager, 'ontology', sample_ontology_graph):
            stats = ontology_manager.get_ontology_stats()
            
            required_keys = ["total_triples", "classes", "properties", "individuals"]
            for key in required_keys:
                assert key in stats
                assert isinstance(stats[key], int)
                assert stats[key] >= 0 